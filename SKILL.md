---
name: ampulheta-video-agent
description: Transforma qualquer arquivo de audio de narracao (.wav/.mp3) em um video animado 2D completo (16:9, 1920x1080, 30 FPS) no estilo exato do canal Ampulheta (2D flat-vector cut-out, chiaroscuro dessaturado, camera sub-pixel em eixo unico, cortes secos sem jump-cut e mixagem de trilha/SFX a -6.0 dB). Use quando o usuario entregar um audio de locucao e pedir para gerar a animacao ou video completo no estilo Ampulheta.
---
# Ampulheta Video Agent

Transforma um arquivo de audio de narracao em um video documentario animado 2D (`1920x1080`, `30 FPS`) seguindo a engenharia reversa forense do canal **Ampulheta** (`@ampulheta_ac`).

## When to Use

- O usuario fornece um arquivo de audio de narracao (`.wav` ou `.mp3`) e pede para criar o video animado no estilo **Ampulheta**.
- O usuario pede para animar um roteiro historico ou documentario em 2D flat-vector com estetica chiaroscuro e camera cinematografica calma.
- O usuario usa este repositorio em **Claude Code**, **OpenAI Codex** ou **Gemini** para produzir videos longos em blocos sincronizados ao audio.

## Regras de Ouro (Anti-Defeitos)

1. **Zero Deformacao de Malha (`cv2.remap` proibido em cenarios):** Nunca aplique ondas senoidais ou deformacao elastica sobre a imagem inteira. Os planos 2D devem permanecer 100% rigidos e nitidos.
2. **Zero Fade Fantasma e Zero Chicote de Camera nos Cortes:** Todas as transicoes entre cenas sao **cortes secos instantaneos (0-frame hard cuts)** cravados nas pausas da voz. Nunca use `crossfade`/`dissolve` entre planos normais e nunca acelere a camera (`whip-pan` ou `zoom-kick`) antes/depois do corte.
3. **Zero Jump-Cut no Mesmo Cenario:** Nunca corte de um cenario vazio para exatamente o mesmo cenario no mesmo angulo apenas fazendo um personagem "brotar do nada". Todo corte deve mudar para um ambiente ou angulo de camera 100% distinto.
4. **Camera Sub-Pixel em Eixo Unico:** Em cada plano (`shot`), a camera se move em **apenas um unico eixo** por vez usando `cv2.warpAffine` com matriz `float32`:
   - Apenas *Push-In* linear lento (`1.01 -> 1.055`, ~4.5% de zoom, `focus_nx=0.50`, `focus_ny=0.50` fixos); OU
   - Apenas *Pan Horizontal* linear lento em zoom fixo (`zoom=1.06`, `focus_nx` variando de `0.35 -> 0.62`, `focus_ny=0.45` fixo); OU
   - Apenas *Zoom-Out* linear lento (`1.055 -> 1.01`, `focus_nx=0.50`, `focus_ny=0.50` fixos).
5. **Zero Legendas ou Letreiros Toscos:** Nunca queime legendas faladas na tela. Mapas usam apenas rotulos geograficos em portugues integrados ao pergaminho.
6. **Audio Master Intocado + Trilha/SFX a -6.0 dB:** A narracao original e o relogio mestre imutavel. A soma de trilha sonora (cordas graves com harmonicos naturais) + efeitos sonoros fica travada exatamente a **-6.0 dB** (50% do RMS com gate da voz).

## Steps

### Fase 1: Analise Acustica e Planejamento de Planos (`scripts/audio_analyzer.py`)

1. Execute `python3 scripts/audio_analyzer.py --audio <caminho_do_audio.wav> --out work/shots_plan.json` para medir a duracao exata, detectar pausas de fala, calcular o RMS com gate da locucao (tipicamente em torno de `-19 dBFS`) e dividir a linha do tempo em planos de **3.5 a 6.5 segundos** alinhados as pausas naturais da fala.
2. Transcreva ou alinhe cada segmento de `shots_plan.json` com a frase correspondente da locucao e defina:
   - `scene_type`: `"character_scene"` ou `"parchment_map"`.
   - `camera_axis`: `"push_in"`, `"zoom_out"` ou `"pan_right"` / `"pan_left"` (nunca repita o mesmo angulo de fundo em dois planos seguidos).
   - `prompt_2d`: Prompt de geracao de imagem seguindo o guia `references/STYLE_GUIDE_AMPULHETA.md`.

### Fase 2: Geracao dos Quadros Base 2D Vetoriais

1. Para cada plano de `shots_plan.json`, gere a arte base 16:9 seguindo rigorosamente a especificacao de `references/STYLE_GUIDE_AMPULHETA.md`:
   - **Personagens:** Cartoon vetorial 2D *cut-out*, contorno fino escuro (`#1A1410`), cabeca geometrica com cantos arredondados, olhos em ponto preto solido (*bead eyes*), nariz trapezoidal chapado, boca em linha simples, roupas historicas em blocos limpos.
   - **Mapas:** Pergaminho envelhecido (`#C4B59D`), costas maritimas em azul-ardosia (`#2C3E50`), montanhas triangulares desenhadas a mao, rotas tracejadas bordô (`#9E2B25`), sombra escura de ocupacao/avanco e todos os rotulos em **portugues**.
2. Para videos longos (ex.: 10 a 15 minutos), trabalhe em **blocos de 60 segundos** (12 a 15 planos por bloco) para garantir calibracao exata das coordenadas de olhos, luzes e camera de cada cena sem estourar o contexto.

### Fase 3: Deteccao de Coordenadas e Animacao via Codigo (`scripts/ampulheta_engine.py`)

1. Para cada quadro com personagem, detecte automaticamente o centro dos dois olhos de ponto preto (`left_eye_xy`, `right_eye_xy`) usando limiarizacao de luminancia (`gray < 45`) na regiao do rosto, e as coordenadas das fontes de luz (`hsv[:,:,2] > 235`).
2. Renderize cada plano a `30 FPS` usando `scripts/ampulheta_engine.py`, que aplica:
   - **Color Grading Chiaroscuro + Textura de Papel no Espaco da Arte:** Dessatura meios-tons em 38%, puxa sombras para azul-ardosia/carvao (`#141B24`), preserva vermelhos bordô (`#9E2B25`) e pele pessego/areia (`#D8B291`), e aplica a textura de papel/tela *antes* da matriz de camera para que a textura se mova junto com o desenho.
   - **Micro-Animacao Vetorial Limpa:** Piscadas de 2 quadros na cor exata da pele local, deslocamento de olhar (`gaze_dx`, `gaze_dy`), leve movimento de sobrancelha, fumaca vetorial, ponteiros de relogio, passaros em 2 quadros no ceu, poeira em feixes de sol e pulsacao suave de luzes ambar (`#F5C45C`).
   - **Camera Sub-Pixel (`cv2.warpAffine` float32) + Vinheta Fixa na Tela:** Aplica o movimento linear de eixo unico e finaliza com a vinheta escura (`#0D131A`) fixa nas bordas da tela.

### Fase 4: Sintese de Trilha de Cordas + Mixagem Master a -6.0 dB e Renderizacao FFmpeg

1. Gere a faixa de musica + SFX com `synthesize_bowed_string_note` (violoncelo/viola com harmonicos naturais e filtro passa-baixas) e normalize o RMS da cama sonora exatamente para `voice_rms * 10^(-6.0 / 20.0)`.
2. Muxe o video H.264 (`-crf 18 -pix_fmt yuv420p`) com o audio AAC (`192k`) e valide os quadros de corte antes de entregar.

## Gotchas

- **Textura de papel congelada:** Se voce aplicar a textura de papel *depois* do `cv2.warpAffine`, ela parecera uma sujeira grudada na lente enquanto o desenho se move atras. Aplique sempre a textura na imagem base antes do movimento de camera.
- **Corte de camera com numeros inteiros:** Nunca faca zoom/pan usando `frame[y1:y2, x1:x2]` com indices `int`, pois isso gera trepidacao (*pixel stepping*) em movimentos lentos. Use sempre `cv2.warpAffine` com matriz `np.float32`.
- **Piscada com cor errada:** Sempre amostre a cor da pele diretamente do pixel da bochecha/testa da imagem ja tratada (`im_graded[y, x]`) para desenhar a palpebra durante a piscada.
