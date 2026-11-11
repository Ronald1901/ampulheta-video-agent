# Ampulheta Video Agent (`ampulheta-video-agent`)

Pipeline completo e **Skill Universal para Agentes de IA** (**Claude Code**, **OpenAI Codex CLI**, **Gemini**) que transforma qualquer arquivo de áudio de narração (`.wav` ou `.mp3`) em um vídeo documentário animado 2D (`16:9`, `1920x1080`, `30 FPS`) no estilo exato do canal **Ampulheta** (`@ampulheta_ac`).

---

## Como Funciona (Fluxo Audio-to-Video)

Você entrega **apenas o arquivo de áudio da narração** para o agente e ele executa as 4 etapas automaticamente:

1. **Análise Acústica e Mapa de Cortes (`scripts/audio_analyzer.py`):**
   - Mede a duração exata ao milissegundo, calcula o RMS com *gate* da voz e detecta as pausas respiratórias naturais da locução.
   - Divide o áudio em planos (*shots*) de **3.5 a 6.0 segundos** com cortes secos cravados nas pausas da fala.
2. **Geração dos Quadros Base 2D Vetoriais (`references/STYLE_GUIDE_AMPULHETA.md`):**
   - Cria os cenários e personagens no traço 2D *flat-vector cut-out* do Ampulheta: contorno fino carvão (`#1A1410`), cabeça geométrica com cantos arredondados, olhos de ponto preto sólido (*bead eyes*), nariz trapezoidal chapado, boca em linha simples e mapas em pergaminho com rótulos em português.
3. **Motor de Animação e Color Grading via Código (`scripts/ampulheta_engine.py`):**
   - **Tratamento Chiaroscuro Dessaturado:** Sombras profundas em azul-ardósia/carvão (`#141B24`), meios-tons de pedra/pergaminho (`#C2B6A6`), vermelhos bordô (`#9E2B25`), pele pêssego/areia (`#D8B291`) e luzes âmbar localizadas (`#F5C45C`).
   - **Textura de Papel no Espaço da Arte + Vinheta na Tela:** A textura fina de papel/tela é aplicada na imagem base *antes* do movimento de câmera (movendo-se junto com o desenho), enquanto a vinheta escura (`#0D131A`) fica ancorada nas bordas da tela.
   - **Micro-Animações Vetoriais Limpas:** Piscadas de 2 quadros na cor exata da pele local, deslocamento de pupila/olhar, movimento sutil de sobrancelha, fumaça do café em curvas vetoriais, ponteiro de relógio, pássaros em 2 quadros no céu, poeira em feixes de sol e pulsação suave de lampiões.
   - **Câmera Sub-Pixel em Eixo Único (`cv2.warpAffine` float32):** Movimento ultracalmo em um único eixo por plano (*Push-In* linear de `4.5%`, *Pan Horizontal* constante ou *Zoom-Out* linear de `4.5%`), sem trepidação de pixels inteiros.
4. **Síntese de Cordas Graves + Mixagem Master a `-6.0 dB`:**
   - A narração original permanece 100% intocada como relógio mestre.
   - Sintetiza violoncelo/viola com harmônicos naturais e filtro passa-baixas + efeitos sonoros sutis travados exatamente a **-6.0 dB** (50% do RMS com *gate* da voz).

---

## Regras Críticas Anti-Defeitos (Obrigatórias para Qualquer Agente)

- **PROIBIDO `cv2.remap` / Ondulação de Malha:** Nunca aplique deformação senoidal ou elástica sobre o cenário. Os planos 2D são 100% rígidos.
- **PROIBIDO Crossfade Fantasma ou Chicote de Câmera:** Todas as transições entre planos são **cortes secos instantâneos (0-frame hard cuts)** sem aceleração brusca (*whip-pan* ou *zoom-kick*).
- **PROIBIDO Jump-Cut no Mesmo Cenário:** Nunca corte de uma rua vazia para a mesma rua no mesmo ângulo apenas fazendo o personagem surgir do nada. Cada corte exige um ambiente ou ângulo de câmera 100% distinto.
- **PROIBIDO Legendas ou Letreiros na Tela:** O vídeo não possui legendas faladas nem caixas de texto sobrepostas.

---

## Estrutura do Repositório

```text
ampulheta-video-agent/
├── README.md                           # Documentação principal e guia rápido
├── SKILL.md                            # Skill universal (Claude Code / Gemini / Codex)
├── CLAUDE.md                           # Instruções automáticas para o Claude Code CLI
├── AGENTS.md                           # Instruções automáticas para o OpenAI Codex CLI / Cursor
├── requirements.txt                    # Dependências Python (numpy, opencv-python, pillow)
├── references/
│   └── STYLE_GUIDE_AMPULHETA.md        # Paleta HEX/RGB forense, templates de prompts e regras de câmera
├── scripts/
│   ├── audio_analyzer.py               # Analisador de áudio (.wav) e gerador de shots_plan.json
│   └── ampulheta_engine.py             # Motor completo de color grading, animação 2D, câmera sub-pixel e mix -6dB
└── examples/
    └── render_10s_berlin_example.py    # Exemplo completo dos primeiros 10s ("E se a Alemanha vencesse")
```

---

## Como Usar em Cada Agente

### 1. Claude Code (`claude`)
Clone o repositório, coloque seu áudio na pasta e rode:
```bash
git clone https://github.com/Ronald1901/ampulheta-video-agent.git
cd ampulheta-video-agent
claude "Aqui está meu áudio narracao.wav. Gere o vídeo animado completo no estilo Ampulheta seguindo o pipeline do repositório."
```

### 2. OpenAI Codex CLI (`codex`)
```bash
git clone https://github.com/Ronald1901/ampulheta-video-agent.git
cd ampulheta-video-agent
codex "Use o pipeline deste repositório para criar a animação completa sincronizada ao arquivo narracao.wav."
```

### 3. Instalação Direta como Skill (`npx skills` / Gemini / Claude)
O arquivo `SKILL.md` na raiz segue o padrão oficial de Skills para agentes.
