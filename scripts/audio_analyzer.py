#!/usr/bin/env python3
"""
Analisador Acustico e Gerador de Plano de Cortes (Padrao Ampulheta)
Mede duracao exata, RMS com gate da voz, detecta pausas naturais da fala e divide o audio
em planos (shots) de 3.5s a 6.0s para animacao sincronizada.
"""

import os
import json
import wave
import argparse
import numpy as np


def analyze_voice_wav(wav_path, min_shot_dur=3.4, max_shot_dur=6.2):
    with wave.open(wav_path, "rb") as w:
        sr = w.getframerate()
        n_ch = w.getnchannels()
        n_frames = w.getnframes()
        raw = w.readframes(n_frames)

    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if n_ch > 1:
        samples = samples.reshape(-1, n_ch).mean(axis=1)

    duration = len(samples) / float(sr)
    win = int(sr * 0.05)  # janelas de 50ms
    rms_series = np.array([
        np.sqrt(np.mean(samples[i:i + win] ** 2))
        for i in range(0, len(samples) - win, win)
    ])

    voiced = rms_series[rms_series > 0.02]
    gated_rms = float(np.mean(voiced)) if len(voiced) > 0 else 0.10
    gated_db = 20.0 * np.log10(gated_rms + 1e-8)
    target_bed_rms = gated_rms * (10.0 ** (-6.0 / 20.0))

    # Detecta candidatos a corte nas pausas naturais (rms < 0.012)
    cuts = [0.0]
    t_cursor = 0.0
    while t_cursor + max_shot_dur < duration:
        search_start = t_cursor + min_shot_dur
        search_end = min(duration - 1.5, t_cursor + max_shot_dur)
        idx0 = int(search_start / 0.05)
        idx1 = int(search_end / 0.05)
        if idx1 > idx0 and idx1 <= len(rms_series):
            best_idx = idx0 + int(np.argmin(rms_series[idx0:idx1]))
            cut_t = round(best_idx * 0.05, 2)
        else:
            cut_t = round(search_end, 2)
        cuts.append(cut_t)
        t_cursor = cut_t
    cuts.append(round(duration, 2))

    axes = ["push_in", "pan_right", "zoom_out", "pan_left"]
    shots = []
    for i in range(len(cuts) - 1):
        s, e = cuts[i], cuts[i + 1]
        shots.append({
            "id": f"s{i+1:03d}",
            "start": s,
            "end": e,
            "duration": round(e - s, 2),
            "frame_start": int(round(s * 30)),
            "frame_end": int(round(e * 30)),
            "camera_axis": axes[i % len(axes)],
            "scene_description": "Preencher com a cena correspondente ao trecho da locucao",
            "eyes_xy": [],
            "lamps": []
        })

    return {
        "audio_file": os.path.basename(wav_path),
        "sample_rate": sr,
        "duration_seconds": round(duration, 3),
        "total_frames_30fps": int(round(duration * 30)),
        "voice_gated_rms": round(gated_rms, 5),
        "voice_gated_dbfs": round(gated_db, 2),
        "target_music_sfx_rms_minus_6db": round(target_bed_rms, 5),
        "shots_count": len(shots),
        "shots": shots
    }


def main():
    parser = argparse.ArgumentParser(description="Analisa audio de narracao e gera plano de cortes Ampulheta.")
    parser.add_argument("--audio", required=True, help="Caminho para o arquivo .wav da narracao")
    parser.add_argument("--out", default="shots_plan.json", help="Arquivo JSON de saida")
    args = parser.parse_args()

    plan = analyze_voice_wav(args.audio)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    print(f"[OK] Plano gerado com {plan['shots_count']} cenas ({plan['duration_seconds']}s) em: {args.out}")


if __name__ == "__main__":
    main()
