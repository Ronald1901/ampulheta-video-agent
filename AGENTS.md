# AGENTS.md - Instruções de Execução para OpenAI Codex / Agentes Autônomos

Quando o usuário fornecer um arquivo de áudio (`.wav` ou `.mp3`) e pedir para gerar o vídeo animado:

1. Leia integralmente `SKILL.md` e `references/STYLE_GUIDE_AMPULHETA.md` antes de escrever qualquer código.
2. Execute `python3 scripts/audio_analyzer.py --audio <arquivo_de_audio> --out work/shots_plan.json` para obter a duração exata, o RMS da voz e os timestamps de corte nas pausas naturais.
3. Para vídeos longos (> 1 minuto), trabalhe em blocos sequenciais de **60 segundos** para garantir que cada cena tenha seu quadro 2D específico e suas coordenadas de olhos (`left_eye_xy`, `right_eye_xy`) e postes/luzes (`lamps`) calibradas sem erro.
4. Use a arquitetura exata de `scripts/ampulheta_engine.py`:
   - **Nunca** use `cv2.remap` (causa ondulação artificial).
   - **Nunca** use `crossfade`/`dissolve` ou *whip-pan* nos cortes (use apenas cortes secos 0-frame).
   - **Nunca** faça *jump-cut* mantendo o mesmo fundo com um personagem surgindo do nada.
   - Use apenas **1 eixo de câmera por plano** (`push_in`, `zoom_out` ou `pan_right`) via `subpixel_camera_render` (`cv2.warpAffine` em `float32`).
   - Aplique `apply_ampulheta_color_grade` com a textura de papel no espaço da arte (antes da câmera) e `apply_screen_vignette` depois da câmera.
   - Mantenha a trilha de cordas (`synthesize_bowed_string_note`) + SFX a exatos `-6.0 dB` abaixo do RMS com gate da locução.
