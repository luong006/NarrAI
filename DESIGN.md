# DESIGN SYSTEM & TOKENS: NarrAI

## 1. Typography Hierarchy
- **App UI & Navigation:** `Plus Jakarta Sans`, sans-serif (clean, geometric, contemporary).
- **Manuscript Reading & Editor:** `Merriweather` / `Lora`, serif (warm, editorial, optimized for sustained narrative reading with `line-height: 1.75`).
- **Monospace / Statistics:** `JetBrains Mono` (for word counts, timestamps, token metrics).

## 2. Color Tokens (WCAG AA Compliant)
| Token | Light Value | Dark Value | Purpose |
|---|---|---|---|
| `--bg-app` | `#F8FAFC` | `#0B0F19` | Overall workspace canvas |
| `--bg-surface` | `#FFFFFF` | `#141E33` | Cards, modals, sidebars |
| `--bg-paper` | `#FAF8F5` | `#111827` | Manuscript writing paper |
| `--text-primary`| `#0F172A` | `#F8FAFC` | High-contrast body text (>10:1) |
| `--text-muted` | `#475569` | `#94A3B8` | Subtitles, labels (>4.5:1) |
| `--brand-primary`| `#4338CA` | `#6366F1` | Primary actions (5.8:1 on light) |
| `--accent-orange`| `#C2410C` | `#EA580C` | Story generation action (4.9:1) |
| `--accent-green` | `#047857` | `#10B981` | Comic serialization action (4.6:1) |

## 3. Shadows & Elevation
- Neutral elevation shadows (`box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.07)`).
- Absolutely NO chromatic/purple glow shadows.

## 4. Manga Reader Domain Tokens
- Border: `6px solid #111111`
- Gutter: `8px`
- Layout: Responsive 2-column manga spread (`grid-auto-flow: dense`)
- Dialogue bubble: `background: rgba(255, 255, 255, 0.96); border: 2px solid #000; border-radius: 12px;`
