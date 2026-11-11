# Guia Forense de Estilo Visual e Animacao - Padrao Ampulheta

Este documento consolida a engenharia reversa quadro a quadro dos videos **"PESTE NEGRA: a historia completa"** (`https://www.youtube.com/watch?v=P0VF4KHaBHk`) e **"VIKINGS: a historia completa"** (`https://www.youtube.com/watch?v=joGp8dSOdYI`) do canal **Ampulheta** (`@ampulheta_ac`).

---

## 1. Paleta de Cores e Tratamento Chiaroscuro

O estilo Ampulheta **nao** e um sepia monocolor alaranjado. Ele combina **cores locais terrosas dessaturadas** com forte contraste **chiaroscuro** (sombras profundas em ardosia/carvao contra fontes de luz quente localizadas):

| Elemento Visual | Faixa HEX | Faixa RGB | Funcao na Composicao |
| :--- | :--- | :--- | :--- |
| **Pele (Luz / Interior)** | `#E5C4A5` a `#D8B291` | `(229, 196, 165)` a `(216, 178, 145)` | Tom de pele natural quente (pessego/areia) |
| **Pele (Frio / Neve)** | `#E0B38F` a `#CD9F7B` | `(224, 179, 143)` a `(205, 159, 123)` | Tom de pele sob atmosfera fria |
| **Contornos Vetoriais** | `#1A1410` a `#211C18` | `(26, 20, 16)` a `(33, 28, 24)` | Linha fina continua de carvao/marrom escuro |
| **Sombras e Areas Escuras** | `#0D131A` a `#1B2A3A` | `(13, 19, 26)` a `(27, 42, 58)` | Sombras profundas em azul-ardosia/carvao e vinheta |
| **Pedra / Pergaminho** | `#DFD5C6` a `#C2B6A6` | `(223, 213, 198)` a `(194, 182, 166)` | Fachadas neoclassicas, muros e mapas |
| **Vermelho Historico** | `#9E2B25` a `#7A1F1B` | `(158, 43, 37)` a `(122, 31, 27)` | Estandartes, tapecarias e setas de campanha |
| **Luz Quente Localizada** | `#F5C45C` a `#E6A15C` | `(245, 196, 92)` a `(230, 161, 92)` | Lampioes, janelas acesas, velas e feixes de sol |

---

## 2. Design de Personagens e Mapas (Prompts de Imagem)

### Template de Prompt - Cena com Personagem
```text
2D flat-vector historical animation frame in the exact visual style of a 2D cut-out puppet history explainer channel (like Ampulheta): clean thin dark-charcoal vector outlines (#1A1410), flat atmospheric coloring with desaturated earthy local tones, deep slate-charcoal shadows (#141B24), and warm golden-amber localized light (#F5C45C). [DESCRICAO DA CENA]. Characters have simplified geometric rounded-rectangle heads, small solid dark bead eyes, flat trapezoidal noses, minimal horizontal mouth lines, and clean flat-vector period garments. Clean 2D vector animation art, no text, no woodcut hatching.
```

### Template de Prompt - Mapa em Pergaminho (em Portugues)
```text
2D flat-vector historical animation map frame in the exact visual style of Ampulheta: aged warm tan and beige parchment map (#C4B59D) of [REGIAO] with clean thin dark-brown vector coastline and border outlines, small hand-drawn triangular mountain icons, slate-blue sea water (#2C3E50), and dark burgundy-red dashed campaign arrows (#9E2B25), with a creeping dark shadow overlay. All geographic labels must be in Portuguese ([LISTA DE ROTULOS EM PORTUGUES]). Clean 2D flat-vector map art, no 3D terrain.
```

---

## 3. Regras de Camera, Transicoes e Ritmo

1. **Duracao de Cada Plano:** Entre **3.0 e 6.0 segundos**, cortando sempre nas pausas respiratorias da locucao.
2. **Um Unico Eixo de Camera por Plano:**
   - **Push-In:** `zoom` vai de `1.01` para `1.055` linearmente; `focus_nx=0.50`, `focus_ny=0.50`.
   - **Zoom-Out:** `zoom` vai de `1.055` para `1.01` linearmente; `focus_nx=0.50`, `focus_ny=0.50`.
   - **Pan Horizontal:** `zoom=1.06` fixo; `focus_nx` vai de `0.35` para `0.62` linearmente; `focus_ny=0.45` fixo.
3. **Cortes 100% Secos:** Sem `crossfade`, sem `whip-pan`, sem `zoom-kick` e sem *jump-cut* sobre o mesmo fundo.
