"""
Banner SVG ureticisi (dark.svg / light.svg).
Girdi (portrait_dither.py'nin ciktilari, kaynak-of-truth):
  dark_dots.npy, light_dots.npy
Cikti: dark.svg, light.svg + banner_metrics.json (olcum raporu)
"""
import json
import numpy as np

RNG = np.random.default_rng(7)

# ---------------------------------------------------------------- geometri
BANNER_W, BANNER_H = 1180, 610
TITLEBAR_H = 36
PAD = 16
GRID_W, GRID_H = 300, 340  # portre veri uzayi (birim: hucre)

FRAME_X = PAD
FRAME_W = round(BANNER_W * 0.38) - PAD  # sol ~38%
FRAME_Y = TITLEBAR_H + PAD + 22  # 22px: VISUAL.MAP etiketi icin
FRAME_H = BANNER_H - FRAME_Y - PAD

CELL = min(FRAME_W / GRID_W, FRAME_H / GRID_H)
DRAW_W, DRAW_H = GRID_W * CELL, GRID_H * CELL
OFFSET_X = FRAME_X + (FRAME_W - DRAW_W) / 2
OFFSET_Y = FRAME_Y + (FRAME_H - DRAW_H) / 2

PANEL_LEFT = FRAME_X + FRAME_W + PAD + 8
PANEL_RIGHT = BANNER_W - PAD
PANEL_W = PANEL_RIGHT - PANEL_LEFT
PANEL_TOP = TITLEBAR_H + PAD

ROW_FONT = 14
HEADER_FONT = 13
LIVE_FONT = 12
PILL_FONT = 14
ROW_SPACING = 23
CHAR_W = ROW_FONT * 0.6      # monospace varsayimi (satir metni)
DOT_ADVANCE = 6.0            # noktali liderin karakter araligi

# ---------------------------------------------------------- zamanlama (sn)
INTRO_FADE = 2.0
N_INTRO_GROUPS = 60

PALETTE = {
    "dark": {
        "bg": "#0A101F", "panel_border": "#1C2333",
        "portrait": "#A78BFA", "chrome": "#22D3EE", "accent": "#10B981",
        "live": "#EF4444", "text_value": "#E5E7EB", "text_label": "#8B93A7",
        "text_dim": "#586178", "pill_text": "#06251C",
    },
    "light": {
        "bg": "#F6F8FA", "panel_border": "#D7DEE8",
        "portrait": "#7C3AED", "chrome": "#0891B2", "accent": "#10B981",
        "live": "#DC2626", "text_value": "#1F2937", "text_label": "#5B6472",
        "text_dim": "#94A0B4", "pill_text": "#06251C",
    },
}

ROWS = [
    ("Subject", "Tolga Duy"),
    ("Role", "Backend Engineer"),
    ("Origin", "Ankara, Turkiye"),
    ("Education", "Bachelor's Degree - Computer Engineering"),
    ("Status", "Building + Learning + Shipping"),
    ("ToolChain", "VS Code, Git, Android Studio, Figma, PyCharm"),
    ("Core.Lang", "Python, TypeScript, Kotlin, C#, Node.js, Java"),
    ("Core.Frontend", "Node.js, HTML5, CSS3"),
    ("Core.Backend", "Django, Nginx, Docker, FastAPI"),
    ("Core.Database", "PostgreSQL, Supabase, MongoDB, SQLite"),
    ("Core.Infra", "Firebase, Cloudflare"),
    ("Grid.Mail", "tolgaduy@outlook.com"),
    ("Grid.LinkedIn", "linkedin.com/in/tolga-duy"),
    ("Grid.GitHub", "github.com/tolgadydev"),
]


# ------------------------------------------------------------------ helpers
def dots_to_path_runs(coords):
    """coords: iterable (x,y) int. Ayni satirdaki bitisik hucreleri tek 'rect'
    alt-yoluna birlestirir (yatay run-length). shape-rendering=crispEdges ile
    kullanilir; font glif YOK, sadece dikdortgen path komutlari."""
    by_row = {}
    for x, y in coords:
        by_row.setdefault(int(y), []).append(int(x))
    parts = []
    for y in sorted(by_row):
        xs = sorted(set(by_row[y]))
        start = prev = xs[0]
        for x in xs[1:]:
            if x == prev + 1:
                prev = x
                continue
            n = prev - start + 1
            parts.append(f"M{start},{y}h{n}v1h{-n}z")
            start = prev = x
        n = prev - start + 1
        parts.append(f"M{start},{y}h{n}v1h{-n}z")
    return "".join(parts)


def evenness_metric(dot_xy, group_ids, n_groups):
    global_c = dot_xy.mean(axis=0)
    dot_spread = np.sqrt(np.mean(np.sum((dot_xy - global_c) ** 2, axis=1)))
    centroids = []
    for g in range(n_groups):
        pts = dot_xy[group_ids == g]
        if len(pts):
            centroids.append(pts.mean(axis=0))
    centroids = np.array(centroids)
    group_spread = np.sqrt(np.mean(np.sum((centroids - global_c) ** 2, axis=1)))
    return float(group_spread / dot_spread)


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def text_el(x, y, s, size, color, anchor="start", weight="normal",
            text_length=None, extra=""):
    tl = f' textLength="{text_length:.2f}" lengthAdjust="spacingAndGlyphs"' if text_length else ""
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="ui-monospace,SFMono-Regular,'
            f'Menlo,Consolas,monospace" font-size="{size}" fill="{color}" '
            f'text-anchor="{anchor}" font-weight="{weight}"{tl}{extra}>{esc(s)}</text>')


def build_row(label, value, y, colors):
    label_w = len(label) * CHAR_W
    value_w = len(value) * CHAR_W
    label_x = PANEL_LEFT
    value_x = PANEL_RIGHT - value_w
    leader_start = label_x + label_w + 6
    leader_end = value_x - 6
    leader_w = max(0.0, leader_end - leader_start)
    n_dots = max(3, int(leader_w // DOT_ADVANCE))
    parts = [text_el(label_x, y, label, ROW_FONT, colors["text_label"], text_length=label_w)]
    parts.append(text_el(leader_start, y, "·" * n_dots, ROW_FONT, colors["text_dim"],
                          text_length=n_dots * DOT_ADVANCE))
    parts.append(text_el(value_x, y, value, ROW_FONT, colors["text_value"], text_length=value_w))
    return "".join(parts), n_dots


# ---------------------------------------------------------------- katmanlar
def build_intro_layer(dot_xy, colors):
    n = len(dot_xy)
    perm = RNG.permutation(n)
    group_of = np.empty(n, dtype=int)
    for i, idx in enumerate(perm):
        group_of[idx] = i % N_INTRO_GROUPS
    evenness = evenness_metric(dot_xy, group_of, N_INTRO_GROUPS)

    begins = RNG.uniform(0.0, INTRO_FADE - 0.35, N_INTRO_GROUPS)
    parts = [f'<g id="portrait-intro" opacity="1">']
    for g in range(N_INTRO_GROUPS):
        coords = dot_xy[group_of == g]
        if len(coords) == 0:
            continue
        d = dots_to_path_runs(coords)
        b = begins[g]
        parts.append(
            f'<path d="{d}" fill="{colors["portrait"]}" opacity="0" '
            f'shape-rendering="crispEdges">'
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{b:.3f}s" dur="0.35s" fill="freeze"/>'
            f'</path>'
        )
    parts.append("</g>")
    return "".join(parts), evenness


def build_chrome(colors, theme):
    parts = []
    parts.append(f'<rect x="0" y="0" width="{BANNER_W}" height="{BANNER_H}" rx="10" '
                  f'fill="{colors["bg"]}" stroke="{colors["panel_border"]}"/>')
    parts.append(f'<rect x="0" y="0" width="{BANNER_W}" height="{TITLEBAR_H}" rx="10" '
                  f'fill="{colors["panel_border"]}" opacity="0.35"/>')
    parts.append(f'<rect x="0" y="{TITLEBAR_H/2}" width="{BANNER_W}" height="{TITLEBAR_H/2}" '
                  f'fill="{colors["panel_border"]}" opacity="0.35"/>')
    for i, c in enumerate(["#EF4444", "#F59E0B", "#10B981"]):
        parts.append(f'<circle cx="{18+i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{c}" opacity="0.85"/>')
    parts.append(text_el(BANNER_W / 2, TITLEBAR_H / 2 + 4, "profile.sh --live", 12,
                          colors["text_dim"], anchor="middle"))
    parts.append(f'<rect x="{FRAME_X}" y="{FRAME_Y}" width="{FRAME_W}" height="{FRAME_H}" '
                  f'rx="6" fill="none" stroke="{colors["panel_border"]}"/>')
    parts.append(text_el(FRAME_X + 4, FRAME_Y - 8, "VISUAL.MAP", 11, colors["chrome"]))
    return "".join(parts)


def build_info_panel(colors):
    parts = []
    header_y = PANEL_TOP + 8
    parts.append(text_el(PANEL_LEFT, header_y, "SYSTEM.INFO", HEADER_FONT, colors["chrome"]))

    pill_y = header_y
    pill_text = "@tolgadydev"
    pill_w = len(pill_text) * PILL_FONT * 0.62 + 20
    pill_x = PANEL_RIGHT - pill_w
    parts.append(f'<rect x="{pill_x:.2f}" y="{pill_y-15}" width="{pill_w:.2f}" height="22" '
                 f'rx="11" fill="{colors["accent"]}"/>')
    parts.append(text_el(pill_x + pill_w / 2, pill_y, pill_text, PILL_FONT, colors["pill_text"],
                          anchor="middle", weight="bold"))

    row_y0 = pill_y + 34
    for i, (label, value) in enumerate(ROWS):
        y = row_y0 + i * ROW_SPACING
        row_svg, _ = build_row(label, value, y, colors)
        parts.append(row_svg)
        if label in ("ToolChain", "Core.Infra"):
            parts.append(f'<line x1="{PANEL_LEFT}" y1="{y+10}" x2="{PANEL_RIGHT}" y2="{y+10}" '
                         f'stroke="{colors["panel_border"]}" stroke-width="1"/>')
    return "".join(parts)


def build_svg(theme, dot_bool_grid, metrics):
    colors = PALETTE[theme]
    ys, xs = np.where(dot_bool_grid)
    dot_xy = np.stack([xs, ys], axis=1).astype(float)

    intro_svg, evenness = build_intro_layer(dot_xy, colors)

    portrait_group = (
        f'<g transform="translate({OFFSET_X:.2f},{OFFSET_Y:.2f}) scale({CELL:.4f})">'
        f'{intro_svg}</g>'
    )

    chrome_svg = build_chrome(colors, theme)
    panel_svg = build_info_panel(colors)

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{BANNER_W}" height="{BANNER_H}" '
        f'viewBox="0 0 {BANNER_W} {BANNER_H}">'
        f'<title>Tolga Duy - profile.sh --live</title>'
        f'{chrome_svg}'
        f'<clipPath id="visualmap-clip-{theme}"><rect x="{FRAME_X}" y="{FRAME_Y}" '
        f'width="{FRAME_W}" height="{FRAME_H}"/></clipPath>'
        f'<g clip-path="url(#visualmap-clip-{theme})">{portrait_group}</g>'
        f'{panel_svg}'
        f'</svg>'
    )

    metrics[theme] = {
        "dot_count": int(len(dot_xy)),
        "intro_evenness": evenness,
        "svg_bytes": len(svg.encode("utf-8")),
    }
    return svg


def main():
    dark_dots = np.load("dark_dots.npy")
    light_dots = np.load("light_dots.npy")

    metrics = {}
    dark_svg = build_svg("dark", dark_dots, metrics)
    light_svg = build_svg("light", light_dots, metrics)

    with open("dark.svg", "w", encoding="utf-8") as f:
        f.write(dark_svg)
    with open("light.svg", "w", encoding="utf-8") as f:
        f.write(light_svg)

    with open("banner_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    for theme, m in metrics.items():
        print(f"[{theme}] dots={m['dot_count']} "
              f"evenness={m['intro_evenness']:.4f} (hedef ~0.05) "
              f"size={m['svg_bytes']/1024:.1f}KB")


if __name__ == "__main__":
    main()
