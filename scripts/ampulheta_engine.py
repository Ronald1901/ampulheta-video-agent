#!/usr/bin/env python3
"""
Motor de Animacao 2D, Color Grading Chiaroscuro e Camera Sub-Pixel (Padrao Ampulheta)
- Zero cv2.remap / zero ondulacao de malha
- Zero crossfade fantasma / zero whip-pan / zero jump-cut no mesmo fundo
- Textura de papel aplicada no espaco da arte (antes do warpAffine) + vinheta fixa na tela
- Camera sub-pixel em ponto flutuante (cv2.warpAffine float32) em eixo unico por plano
- Mixagem automatica de cordas graves com harmonicos naturais + SFX a -6.0 dB
"""

import os
import math
import wave
import subprocess
import numpy as np
import cv2

FPS = 30
W, H = 1920, 1080


def ease_in_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 4.0 * t * t * t if t < 0.5 else 1.0 - pow(-2.0 * t + 2.0, 3) / 2.0


def build_paper_canvas_texture(h, w, seed=101):
    """Gera textura fina de papel/tela no espaco da arte (move-se junto com o desenho)."""
    rng = np.random.RandomState(seed)
    fine_grain = rng.normal(0.0, 1.0, (h, w)).astype(np.float32)
    coarse = rng.normal(0.0, 1.0, (h // 2, w // 2)).astype(np.float32)
    coarse = cv2.resize(coarse, (w, h), interpolation=cv2.INTER_LINEAR)
    y_idx, x_idx = np.ogrid[:h, :w]
    weave = 0.25 * np.sin(x_idx * 1.4) + 0.25 * np.sin(y_idx * 1.4)
    tex = (0.55 * fine_grain + 0.35 * coarse + 0.10 * weave).astype(np.float32)
    return tex * 2.4


def build_charcoal_vignette_mask(h, w, strength=0.42):
    """Gera mascara de vinheta chiaroscuro escura (#0D131A) fixa nas bordas da tela."""
    Y, X = np.ogrid[:h, :w]
    cx, cy = w * 0.5, h * 0.5
    dist = np.sqrt(((X - cx) / cx) ** 2 + ((Y - cy) / cy) ** 2)
    falloff = np.clip((dist - 0.35) / 0.85, 0.0, 1.0) ** 1.85
    return np.clip(falloff * strength, 0.0, 0.65).astype(np.float32)


def apply_ampulheta_color_grade(img_bgr, canvas_tex, skin_mask=None):
    """
    Aplica o tratamento de cor forense do canal Ampulheta:
    - Meios-tons terrosos dessaturados (#C2B6A6)
    - Sombras profundas em azul-ardosia/carvao (#141B24)
    - Vermelhos bordo preservados (#9E2B25) e pele pessego/areia (#D8B291)
    - Textura de papel embutida antes da camera
    """
    img_f = img_bgr.astype(np.float32) / 255.0
    b, g, r = img_f[:, :, 0], img_f[:, :, 1], img_f[:, :, 2]

    lum = 0.114 * b + 0.587 * g + 0.299 * r
    red_dominance = np.clip((r - g - 0.18) * 3.5, 0.0, 1.0)
    glow_mask = np.clip((lum - 0.72) / 0.25, 0.0, 1.0)

    desat_factor = 0.58 + 0.28 * red_dominance
    if skin_mask is not None:
        desat_factor = np.maximum(desat_factor, skin_mask * 0.76)

    b_d = lum + (b - lum) * desat_factor
    g_d = lum + (g - lum) * desat_factor
    r_d = lum + (r - lum) * desat_factor

    shadow_w = np.clip((0.52 - lum) / 0.52, 0.0, 1.0) ** 1.35 * (1.0 - red_dominance * 0.7)
    mid_w = np.clip(1.0 - np.abs(lum - 0.55) / 0.40, 0.0, 1.0) * (1.0 - red_dominance * 0.8)
    if skin_mask is not None:
        mid_w = mid_w * (1.0 - skin_mask * 0.75)
        shadow_w = shadow_w * (1.0 - skin_mask * 0.65)

    b_graded = b_d + 0.055 * shadow_w + 0.038 * mid_w
    g_graded = g_d + 0.010 * shadow_w - 0.008 * mid_w
    r_graded = r_d - 0.048 * shadow_w - 0.042 * mid_w

    graded = np.stack([b_graded, g_graded, r_graded], axis=-1)
    graded = np.clip(graded, 0.0, 1.0)
    graded = np.clip((graded - 0.5) * 1.12 + 0.485, 0.0, 1.0)

    graded[:, :, 0] -= glow_mask * 0.03
    graded[:, :, 1] += glow_mask * 0.02
    graded[:, :, 2] += glow_mask * 0.05

    out_255 = np.clip(graded * 255.0 + canvas_tex[:, :, None], 0.0, 255.0)
    return out_255.astype(np.uint8)


def apply_screen_vignette(frame_bgr, vig_alpha):
    """Aplica a vinheta chiaroscuro escura (#0D131A) fixa na tela."""
    f = frame_bgr.astype(np.float32)
    slate_dark = np.array([24.0, 18.0, 13.0], dtype=np.float32)
    f = f * (1.0 - vig_alpha[:, :, None]) + slate_dark * vig_alpha[:, :, None]
    return np.clip(f, 0, 255).astype(np.uint8)


def subpixel_camera_render(img_bgr, zoom, focus_nx, focus_ny, out_w=W, out_h=H):
    """Renderiza camera sub-pixel em ponto flutuante (cv2.warpAffine float32) sem pixel stepping."""
    sh, sw = img_bgr.shape[:2]
    base_scale = max(out_w / float(sw), out_h / float(sh))
    scale = base_scale * float(zoom)

    scaled_w = sw * scale
    scaled_h = sh * scale

    avail_dx = max(0.0, scaled_w - out_w)
    avail_dy = max(0.0, scaled_h - out_h)

    tx = -avail_dx * float(np.clip(focus_nx, 0.0, 1.0))
    ty = -avail_dy * float(np.clip(focus_ny, 0.0, 1.0))

    M = np.array([
        [scale, 0.0, tx],
        [0.0, scale, ty]
    ], dtype=np.float32)

    return cv2.warpAffine(
        img_bgr, M, (out_w, out_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REFLECT_101
    )


def animate_eyes_and_brows(img, left_eye_xy, right_eye_xy, skin_bgr, outline_bgr, gaze_dx=0.0, gaze_dy=0.0, blink_amount=0.0, brow_lift=0.0):
    """Anima olhos de ponto preto (bead eyes), sobrancelhas e piscada de 2 quadros na cor exata da pele."""
    out = img.copy()
    for (ex, ey) in [left_eye_xy, right_eye_xy]:
        cx, cy = int(round(ex)), int(round(ey))
        cv2.circle(out, (cx, cy), 13, tuple(int(c) for c in skin_bgr), -1, cv2.LINE_AA)
        cv2.rectangle(out, (cx - 14, cy - 26), (cx + 14, cy - 11), tuple(int(c) for c in skin_bgr), -1)

        by = int(round(cy - 18 - brow_lift))
        cv2.line(out, (cx - 11, by + 1), (cx + 11, by - 1), tuple(int(c) for c in outline_bgr), 3, cv2.LINE_AA)

        gx = int(round(cx + gaze_dx))
        gy = int(round(cy + gaze_dy))
        if blink_amount < 0.85:
            cv2.circle(out, (gx, gy), 9, tuple(int(c) for c in outline_bgr), -1, cv2.LINE_AA)
            if blink_amount > 0.15:
                lid_y = int(round(gy - 9 + 18 * blink_amount))
                cv2.rectangle(out, (gx - 11, gy - 11), (gx + 11, lid_y), tuple(int(c) for c in skin_bgr), -1)
                cv2.line(out, (gx - 10, lid_y), (gx + 10, lid_y), tuple(int(c) for c in outline_bgr), 2, cv2.LINE_AA)
        else:
            cv2.line(out, (cx - 10, cy + 2), (cx + 10, cy + 2), tuple(int(c) for c in outline_bgr), 3, cv2.LINE_AA)
    return out


def draw_flapping_birds(img, birds, t, color_bgr=(34, 38, 46)):
    """Desenha silhuetas de passaros batendo asas em loop de 2 quadros no ceu."""
    out = img.copy()
    for b in birds:
        bx = b["x0"] + b["vx"] * t
        by = b["y0"] + b["vy"] * t + math.sin(t * 2.2 + b["phase"]) * 2.0
        span = b["span"]
        flap_state = int((t * b["flap_hz"] + b["phase"]) % 2)
        wing_y = -span * 0.42 if flap_state == 0 else span * 0.22
        mid_y = -span * 0.18 if flap_state == 0 else span * 0.05

        pts_left = np.array([
            [bx, by],
            [bx - span * 0.5, by + mid_y],
            [bx - span, by + wing_y],
            [bx - span * 0.45, by + mid_y + 2.0],
        ], dtype=np.int32)
        pts_right = np.array([
            [bx, by],
            [bx + span * 0.5, by + mid_y],
            [bx + span, by + wing_y],
            [bx + span * 0.45, by + mid_y + 2.0],
        ], dtype=np.int32)
        cv2.fillPoly(out, [pts_left, pts_right], color_bgr, cv2.LINE_AA)
    return out


def add_pulsing_lamp_glows(img, lamps, t):
    """Adiciona halos de luz ambar pulsante (#F5C45C) em lampioes, velas e janelas."""
    overlay = np.zeros_like(img, dtype=np.float32)
    h, w = img.shape[:2]
    Y, X = np.ogrid[:h, :w]
    for idx, (lx, ly, radius, intensity) in enumerate(lamps):
        pulse = 0.88 + 0.12 * math.sin(t * 3.2 + idx * 1.3)
        r = radius * (0.97 + 0.05 * math.sin(t * 2.5 + idx))
        dist2 = (X - lx) ** 2 + (Y - ly) ** 2
        falloff = np.exp(-dist2 / (2.0 * (r ** 2))) * intensity * pulse
        overlay[:, :, 0] += falloff * 92.0
        overlay[:, :, 1] += falloff * 196.0
        overlay[:, :, 2] += falloff * 245.0
    return np.clip(img.astype(np.float32) + overlay, 0, 255).astype(np.uint8)


def draw_coffee_steam(img, cup_xy, t):
    """Desenha fios de vapor vetorial subindo suavemente."""
    overlay = img.copy()
    cx, cy = cup_xy
    for wisp_i in range(2):
        phase = t * 2.2 + wisp_i * math.pi
        pts = []
        for s in range(18):
            frac = s / 17.0
            yy = cy - frac * 48.0
            xx = cx + (wisp_i - 0.5) * 10.0 + math.sin(frac * 4.5 - phase) * (4.2 * frac + 1.0)
            pts.append([int(round(xx)), int(round(yy))])
        pts_arr = np.array(pts, dtype=np.int32)
        cv2.polylines(overlay, [pts_arr], False, (210, 222, 232), 3, cv2.LINE_AA)
    return cv2.addWeighted(overlay, 0.35, img, 0.65, 0)


def draw_sunbeam_dust(img, t, poly_pts):
    """Desenha feixe de luz solar matinal e particulas de poeira flutuando."""
    beam = img.copy()
    pts = np.array(poly_pts, dtype=np.int32)
    cv2.fillPoly(beam, [pts], (135, 200, 242), cv2.LINE_AA)
    pulse = 0.08 + 0.02 * math.sin(t * 1.6)
    out = cv2.addWeighted(beam, pulse, img, 1.0 - pulse, 0)

    mote_layer = out.copy()
    np.random.seed(42)
    for i in range(24):
        u = np.random.uniform(0.08, 0.92)
        v = np.random.uniform(0.08, 0.92)
        top_x = 200 + u * 180
        top_y = 80 + u * 260
        bot_x = 420 + u * 380
        bot_y = 320 + u * 340
        mx = top_x + v * (bot_x - top_x) + math.sin(t * 1.1 + i) * 9.0
        my = top_y + v * (bot_y - top_y) - (t * 6.5 + i * 7.0) % 60.0
        rad = 2 if i % 3 == 0 else 1
        cv2.circle(mote_layer, (int(mx), int(my)), rad, (185, 220, 245), -1, cv2.LINE_AA)
    return cv2.addWeighted(mote_layer, 0.45, out, 0.55, 0)


def synthesize_bowed_string_note(t_arr, duration, freq, vibrato_hz=4.2, vibrato_depth=0.0020):
    """Sintetiza nota de violoncelo/viola com harmonicos naturais de corda friccionada."""
    vib = 1.0 + vibrato_depth * np.sin(2.0 * np.pi * vibrato_hz * t_arr)
    phase = 2.0 * np.pi * freq * np.cumsum(vib) / float(len(t_arr) / duration)
    sig = (
        1.00 * np.sin(phase)
        + 0.38 * np.sin(2.0 * phase + 0.3)
        + 0.16 * np.sin(3.0 * phase + 0.7)
        + 0.07 * np.sin(4.0 * phase + 1.2)
    )
    return sig / 1.61
