"""Build the README graphics: banner with the pixel doll, project cards, badges and footer.

needs: pip install fonttools brotli, plus latin woff2 files from Google Fonts: Fredoka (pass its path),
and InstrumentSerif-normal.woff2, InstrumentSerif-italic.woff2, GeistMono-normal.woff2 in the same folder.
contrib.json is a list of [date, weekday_row, week_col, level] (only used for the local Pac-Man preview;
the live graph comes from scripts/pacman_graph.py via the workflow).
usage: python scripts/art/build_assets.py <fredoka.woff2> scripts/art/bc_week.json <contrib.json> <out_dir>
"""
import base64, io, json, math, os, random, sys
from datetime import date
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sprite as SP

FONT, BC_JSON, CONTRIB_JSON, OUT = sys.argv[1:5]
# the banner uses Instrument Serif (title) and Geist Mono (typing line), kept next to the Fredoka file
FONT_DIR = os.path.dirname(os.path.abspath(FONT))
SERIF = os.path.join(FONT_DIR, "InstrumentSerif-normal.woff2")
SERIF_IT = os.path.join(FONT_DIR, "InstrumentSerif-italic.woff2")
MONO = os.path.join(FONT_DIR, "GeistMono-normal.woff2")
os.makedirs(OUT, exist_ok=True)

# palette: a warm sunset over a night sky
NIGHT = "#170f26"
AMBER, CORAL, PINK, PURPLE, LILAC = "#ffb347", "#ff6f59", "#ef476f", "#9d4edd", "#c08cf5"
TEAL, BLUSH, CREAM, PAC = "#5ce1e6", "#f7a1c4", "#fff1e6", "#ffd23f"
GHOSTS = [CORAL, BLUSH, TEAL, AMBER]

THEME = {
    "light": dict(card="#fff5ef", stroke="#f3d6c8", panel="#ffffff", fg="#2b1d38", muted="#7a6584",
                  cell="#f5e9ee", street="#f6e4ea", dot="#e3cfd8",
                  chips=["#ffe3cc", "#ffd5dc", "#ecdcff"], chip_fg="#4a2d57",
                  levels=["#f3e8ef", "#ffd9b3", "#ffab80", "#f2708e", "#a855c8"]),
    "dark":  dict(card="#1d1429", stroke="#33264a", panel="#120b1c", fg="#fbeff8", muted="#b6a3c2",
                  cell="#21172e", street="#251a33", dot="#3b2d4b",
                  chips=["#3d2a2a", "#40223a", "#2f2547"], chip_fg="#ffe9dc",
                  levels=["#21172e", "#4e2a47", "#8c3b5d", "#e0607e", "#ffb347"]),
}

INFERNO = [(0.0, (0, 0, 4)), (0.1, (22, 11, 57)), (0.2, (66, 10, 104)), (0.3, (106, 23, 110)),
           (0.4, (147, 38, 103)), (0.5, (188, 55, 84)), (0.6, (221, 81, 58)), (0.7, (243, 120, 25)),
           (0.8, (252, 165, 10)), (0.9, (246, 215, 70)), (1.0, (252, 255, 164))]


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def tohex(c):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in c)


def mix(a, b, t):
    return tohex(tuple(x + (y - x) * t for x, y in zip(hexrgb(a), hexrgb(b))))


def inferno(v):
    v = max(0.0, min(1.0, v))
    for (t0, c0), (t1, c1) in zip(INFERNO, INFERNO[1:]):
        if v <= t1:
            return tohex(tuple(x + (y - x) * (v - t0) / (t1 - t0) for x, y in zip(c0, c1)))
    return tohex(INFERNO[-1][1])


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- fonts
class Face:
    """One weight/style of a font (Fredoka by default), subset to the text an SVG needs, plus glyph advances."""

    def __init__(self, weight, text, path=None, style="normal"):
        f = TTFont(path or FONT)
        if "fvar" in f:
            axis = next(a for a in f["fvar"].axes if a.axisTag == "wght")
            f = instancer.instantiateVariableFont(f, {"wght": min(max(weight, axis.minValue), axis.maxValue)})
        self.style = style
        self.upm = f["head"].unitsPerEm
        cmap = f.getBestCmap()
        self.adv = {ch: f["hmtx"][cmap[ord(ch)]][0] for ch in set(text) if ord(ch) in cmap}
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "liga"]
        sub = subset.Subsetter(opts)
        sub.populate(text=text)
        sub.subset(f)
        buf = io.BytesIO()
        f.flavor = "woff2"
        f.save(buf)
        self.weight = weight
        self.b64 = base64.b64encode(buf.getvalue()).decode()

    def width(self, s, size):
        return sum(self.adv.get(ch, self.upm * 0.5) for ch in s) * size / self.upm

    def css(self, family):
        return (f"@font-face{{font-family:'{family}';font-weight:{self.weight};font-style:{self.style};"
                f"src:url(data:font/woff2;base64,{self.b64}) format('woff2')}}")


def fonts_css(spec):
    """spec: {weight: text} -> (css, {weight: Face})"""
    faces = {w: Face(w, t) for w, t in spec.items()}
    return "".join(f.css("Fredoka") for f in faces.values()), faces


FAM = "font-family:'Fredoka','Nunito','Trebuchet MS',sans-serif"


def write(name, svg):
    with open(os.path.join(OUT, name), "w") as f:
        f.write(svg)
    return len(svg)


def ghost(x, y, s, color, cls="", pupil_cls="pp"):
    body = (f"M{-s},{s} V{-0.1 * s} A{s},{s} 0 0,1 {s},{-0.1 * s} V{s} "
            f"L{0.66 * s},{0.72 * s} L{0.33 * s},{s} L0,{0.72 * s} L{-0.33 * s},{s} L{-0.66 * s},{0.72 * s} Z")
    return (f'<g transform="translate({x},{y})"><g class="{cls}"><path d="{body}" fill="{color}"/>'
            f'<ellipse cx="{-0.38 * s:.1f}" cy="{-0.12 * s:.1f}" rx="{0.26 * s:.1f}" ry="{0.32 * s:.1f}" fill="#fff"/>'
            f'<ellipse cx="{0.38 * s:.1f}" cy="{-0.12 * s:.1f}" rx="{0.26 * s:.1f}" ry="{0.32 * s:.1f}" fill="#fff"/>'
            f'<g class="{pupil_cls}"><circle cx="{-0.44 * s:.1f}" cy="{-0.08 * s:.1f}" r="{0.13 * s:.1f}" fill="#2b2d6e"/>'
            f'<circle cx="{0.32 * s:.1f}" cy="{-0.08 * s:.1f}" r="{0.13 * s:.1f}" fill="#2b2d6e"/></g></g></g>')


def pac_d(r, deg):
    a = math.radians(deg)
    return f"M0,0 L{r * math.cos(a):.2f},{-r * math.sin(a):.2f} A{r},{r} 0 1,0 {r * math.cos(a):.2f},{r * math.sin(a):.2f} Z"


def pacman(r, color=PAC):
    return (f'<path d="{pac_d(r, 38)}" fill="{color}"><animate attributeName="d" '
            f'values="{pac_d(r, 38)};{pac_d(r, 3)};{pac_d(r, 38)}" dur=".3s" repeatCount="indefinite"/></path>')


# ---------------------------------------------------------------- header
# mid-tone colours that read on both GitHub's white and its near-black background
ROSE, VIOLET, INK = "#e0457b", "#7b5cf0", "#7a7391"


def header(style="long", skin="medium", hair="black", outfit="sage"):
    """Transparent banner for both themes: title, typing line pac-man eats, ghosts, and the pixel doll."""
    W, H = 960, 250
    title = "hi, i'm anusha :)"
    lines = ["cs student @ uwaterloo",
             "i make ml models show their work",
             "deepfake detectors & wildfire maps",
             "and pac-man, but for trick-or-treating"]
    t_roman, t_ital = "hi, i'm  :)", "anusha"
    fr, fi = Face(400, t_roman, SERIF), Face(400, t_ital, SERIF_IT, "italic")
    f5 = Face(500, "".join(lines), MONO)
    css = fr.css("Instrument Serif") + fi.css("Instrument Serif") + f5.css("Geist Mono")
    X0, BASE, SIZE, R = 26, 144, 18, 8
    TS = 50
    title_w = fr.width("hi, i'm ", TS) + fi.width("anusha", TS) + fr.width(" :)", TS)
    PY = BASE - SIZE * 0.34
    TYPE, HOLD, SPEED = 0.065, 1.7, 420

    # build the timeline
    t, plan = 0.0, []
    for line in lines:
        xs, x = [], X0
        for ch in line:
            w = f5.width(ch, SIZE)
            xs.append((x, w))
            x += w
        start = t
        typed = [start + 0.3 + k * TYPE for k in range(len(line))]
        hold_end = typed[-1] + HOLD
        p0, p1 = X0 - 36, x + 36
        p_end = hold_end + (p1 - p0) / SPEED
        eaten = [hold_end + max(0.0, (cx + w / 2 - R * 0.6 - p0)) / SPEED for cx, w in xs]
        plan.append(dict(line=line, xs=xs, typed=typed, eaten=eaten, start=start, hold_end=hold_end,
                         p0=p0, p1=p1, p_end=p_end, end_x=x))
        t = p_end + 0.35
    T = round(t, 3)

    def kt(v):
        return f"{min(v / T, 0.9999):.4f}"

    chars = []
    for p in plan:
        for (x, w), a, b, ch in zip(p["xs"], p["typed"], p["eaten"], p["line"]):
            if ch == " ":
                continue
            chars.append(f'<text x="{x:.1f}" y="{BASE}" opacity="0">{esc(ch)}<animate attributeName="opacity" '
                         f'values="0;1;0" keyTimes="0;{kt(a)};{kt(b)}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></text>')

    # cursor: jumps after each typed char, hidden while pac-man eats
    cx_vals, cx_keys, co_vals, co_keys = [], [], [], []
    for p in plan:
        cx_vals.append(f"{X0:.1f}"); cx_keys.append(p["start"])
        acc = X0
        for (x, w), a in zip(p["xs"], p["typed"]):
            acc = x + w
            cx_vals.append(f"{acc + 3:.1f}"); cx_keys.append(a)
        co_vals += ["1", "0"]; co_keys += [p["start"], p["hold_end"]]
    cursor = (f'<g class="blink"><rect x="0" y="{BASE - SIZE * 0.8:.1f}" width="2.5" height="{SIZE * 1.0:.1f}" rx="1" fill="{VIOLET}">'
              f'<animate attributeName="x" values="{";".join(cx_vals)}" keyTimes="{";".join(kt(k) if i else "0" for i, k in enumerate(cx_keys))}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/>'
              f'<animate attributeName="opacity" values="{";".join(co_vals)}" keyTimes="{";".join(kt(k) if i else "0" for i, k in enumerate(co_keys))}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/>'
              f'</rect></g>')

    # pac-man: slides across each line after it has been read
    tv, tk, ov, ok = [f"{plan[0]['p0']:.1f},{PY:.1f}"], ["0"], ["0"], ["0"]
    for p in plan:
        tv += [f"{p['p0']:.1f},{PY:.1f}", f"{p['p1']:.1f},{PY:.1f}"]
        tk += [kt(p["hold_end"]), kt(p["p_end"])]
        ov += ["1", "0"]; ok += [kt(p["hold_end"]), kt(p["p_end"])]
    tv.append(f"{plan[0]['p0']:.1f},{PY:.1f}"); tk.append("1")
    pac = (f'<g opacity="0"><g>{pacman(R, "#f5b700")}</g>'
           f'<animateTransform attributeName="transform" type="translate" values="{";".join(tv)}" keyTimes="{";".join(tk)}" dur="{T}s" repeatCount="indefinite"/>'
           f'<animate attributeName="opacity" values="{";".join(ov)}" keyTimes="{";".join(ok)}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></g>')

    gang = (ghost(690, 82, 17, BLUSH, cls="bob b0") + ghost(736, 176, 14, TEAL, cls="bob b2")
            + ghost(942, 34, 11, CORAL, cls="bob b1"))
    # the pixel doll, standing on the right with her laptop
    SC, SX, SY = 2.5, 812, 8
    rows = SP.build(style)
    # a 10 s loop: stand, wave hello with a "hi!" bubble, stand, hop with sparkles, stand
    frames = "".join(f'<g class="{cls}">{SP.svg_rects(SP.build(style, pose), None, SX, SY, SC)}</g>'
                     for cls, pose in (("fi", "idle"), ("fw1", "wave1"), ("fw2", "wave2")))
    doll = (f'<g class="jump"><g class="hop">{frames}'
            f'<g class="blk">{SP.eye_rects(SP.blink(rows), None, SX, SY, SC)}</g></g></g>')
    hi = ["#...#.#", "#.....#", "###.#.#", "#.#.#..", "#.#.#.#"]
    bubble_rows = ([".###########.", "#WWWWWWWWWWW#"]
                   + ["#WW" + r.replace("#", "T").replace(".", "W") + "WW#" for r in hi]
                   + ["#WWWWWWWWWWW#", ".#######WW##.", "........#WW#.", ".........###."])
    bub_col = {"#": "#25162e", "W": "#ffffff", "T": ROSE}
    BX, BY = 790, 16
    bubble = "".join(f'<rect x="{BX + i * SC:.1f}" y="{BY + j * SC:.1f}" width="{SC + 0.1}" height="{SC + 0.1}" fill="{bub_col[ch]}"/>'
                     for j, r in enumerate(bubble_rows) for i, ch in enumerate(r) if ch in bub_col)
    def sparkle(x, y, big, color):
        arm = 2 if big else 1
        cells = [(0, 0)] + [(d * k, 0) for k in range(1, arm + 1) for d in (-1, 1)] + [(0, d * k) for k in range(1, arm + 1) for d in (-1, 1)]
        return "".join(f'<rect x="{x + cx * SC:.1f}" y="{y + cy * SC:.1f}" width="{SC + 0.1}" height="{SC + 0.1}" fill="{"#ffffff" if (cx, cy) == (0, 0) and big else color}"/>' for cx, cy in cells)
    spots = [(792, 92, "#f5b700"), (934, 104, VIOLET), (800, 176, ROSE), (938, 186, TEAL)]
    spark_a = "".join(sparkle(x, y, i % 2 == 0, c) for i, (x, y, c) in enumerate(spots))
    spark_b = "".join(sparkle(x, y, i % 2 == 1, c) for i, (x, y, c) in enumerate(spots))
    doll += f'<g class="bub">{bubble}</g><g class="spa">{spark_a}</g><g class="spb">{spark_b}</g>'
    doll_css = SP.palette_css(SP.palette(skin, hair, outfit))

    static_line = f'<text class="static" x="{X0}" y="{BASE}" style="display:none">{esc(lines[0])}</text>'
    stops = f'<stop offset="0" stop-color="{ROSE}"/><stop offset="1" stop-color="{VIOLET}"/>'
    return W, H, f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="hi, i'm anusha :)">
<style>
{css}
.t{{font-family:'Instrument Serif',Georgia,'Times New Roman',serif}}
.m{{font-family:'Geist Mono',ui-monospace,SFMono-Regular,Menlo,monospace}}
.blink{{animation:bl 1s steps(1) infinite}}@keyframes bl{{50%{{opacity:0}}}}
.bob{{animation:bob 2.4s ease-in-out infinite}}@keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-7px)}}}}
.b1{{animation-delay:-.6s}}.b2{{animation-delay:-1.2s}}
.pp{{animation:look 6s ease-in-out infinite}}@keyframes look{{0%,40%{{transform:translateX(0)}}50%,90%{{transform:translateX(3px)}}100%{{transform:translateX(0)}}}}
.hop{{animation:hop 2s steps(1) infinite}}@keyframes hop{{50%{{transform:translateY(-2.5px)}}}}
.fw1,.fw2,.bub,.spa,.spb,.blk{{opacity:0}}
.fi,.fw1,.fw2,.bub,.spa,.spb,.blk{{animation-duration:10s;animation-timing-function:steps(1,end);animation-iteration-count:infinite}}
.fi{{animation-name:fi}}@keyframes fi{{0%{{opacity:1}}20%{{opacity:0}}44%,100%{{opacity:1}}}}
.fw1{{animation-name:w1}}@keyframes w1{{0%{{opacity:0}}20%{{opacity:1}}23%{{opacity:0}}26%{{opacity:1}}29%{{opacity:0}}32%{{opacity:1}}35%{{opacity:0}}38%{{opacity:1}}41%,100%{{opacity:0}}}}
.fw2{{animation-name:w2}}@keyframes w2{{0%{{opacity:0}}23%{{opacity:1}}26%{{opacity:0}}29%{{opacity:1}}32%{{opacity:0}}35%{{opacity:1}}38%{{opacity:0}}41%{{opacity:1}}44%,100%{{opacity:0}}}}
.bub{{animation-name:bb}}@keyframes bb{{0%{{opacity:0}}21%{{opacity:1}}46%,100%{{opacity:0}}}}
.blk{{animation-name:bk}}@keyframes bk{{0%{{opacity:0}}12%{{opacity:1}}13.5%{{opacity:0}}52%{{opacity:1}}53.5%{{opacity:0}}84%{{opacity:1}}85.5%,100%{{opacity:0}}}}
.spa{{animation-name:sa}}@keyframes sa{{0%{{opacity:0}}63%{{opacity:1}}66%{{opacity:0}}69%{{opacity:1}}72%,100%{{opacity:0}}}}
.spb{{animation-name:sb}}@keyframes sb{{0%{{opacity:0}}66%{{opacity:1}}69%{{opacity:0}}72%{{opacity:1}}75%,100%{{opacity:0}}}}
.jump{{animation:jp 10s infinite}}@keyframes jp{{0%,60%{{transform:translateY(0);animation-timing-function:ease-in}}61.5%{{transform:translateY(2px);animation-timing-function:ease-out}}64.5%{{transform:translateY(-10px);animation-timing-function:ease-in}}67.5%{{transform:translateY(0)}}68.5%{{transform:translateY(1.5px)}}70%,100%{{transform:translateY(0)}}}}
/*doll*/{doll_css}/*/doll*/
@media (prefers-reduced-motion:reduce){{.typing{{display:none}}.static{{display:inline!important}}.bob,.pp,.hop,.blink,.blk,.jump,.fi,.fw1,.fw2,.bub,.spa,.spb{{animation:none}}}}
</style>
<defs><linearGradient id="tg" gradientUnits="userSpaceOnUse" x1="{X0}" y1="0" x2="{X0 + title_w:.0f}" y2="0">{stops}</linearGradient></defs>
{doll}
<text class="t" x="{X0 - 1}" y="106" font-size="{TS}" fill="url(#tg)">hi, i'm <tspan font-style="italic">anusha</tspan> :)</text>
<g class="typing m" font-size="{SIZE}" font-weight="500" fill="{INK}">{"".join(chars)}{cursor}{pac}</g>
<g class="m" font-size="{SIZE}" font-weight="500" fill="{INK}">{static_line}</g>
{gang}
</svg>'''


# ---------------------------------------------------------------- project cards
CW, CH = 300, 232
PX, PY_, PW, PH = 14, 14, 272, 150


def card(theme, name, desc, chips, art, art_css="", label=""):
    t = THEME[theme]
    text = name + "".join(desc) + "".join(chips) + label
    css, faces = fonts_css({600: name + label, 400: "".join(desc), 500: "".join(chips)})
    chip_svg, x = [], 20
    for i, c in enumerate(chips):
        w = faces[500].width(c, 12.5) + 20
        chip_svg.append(f'<rect x="{x:.1f}" y="330" width="{w:.1f}" height="24" rx="12" fill="{t["chips"][i % 3]}"/>'
                        f'<text x="{x + w / 2:.1f}" y="346.5" font-size="12.5" font-weight="500" text-anchor="middle" fill="{t["chip_fg"]}">{esc(c)}</text>')
        x += w + 7
    desc_svg = "".join(f'<text x="20" y="{PY_ + PH + 54 + i * 18}" font-size="13.5" fill="{t["muted"]}">{esc(d)}</text>' for i, d in enumerate(desc))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CW} {CH}" width="{CW}" height="{CH}" role="img" aria-label="{esc(name)}: {esc(" ".join(desc))}">
<style>
{css}
text{{{FAM}}}
{art_css}
</style>
<rect x="1" y="1" width="{CW - 2}" height="{CH - 2}" rx="22" fill="{t["card"]}" stroke="{t["stroke"]}" stroke-width="1.5"/>
<rect x="{PX}" y="{PY_}" width="{PW}" height="{PH}" rx="15" fill="{t["panel"]}"/>
<clipPath id="pc"><rect x="{PX}" y="{PY_}" width="{PW}" height="{PH}" rx="15"/></clipPath>
<g clip-path="url(#pc)">{art}</g>
<text x="20" y="{PY_ + PH + 32}" font-size="20" font-weight="600" fill="{t["fg"]}">{esc(name)}</text>
{desc_svg}
{"".join(chip_svg)}
</svg>'''


def art_face(theme):
    t = THEME[theme]
    P, cx, cy = 4.1, 150, 91
    rx, ry = 9.6, 12.4
    spots = [(-3.6, -2.2, 2.4, 1.0), (3.0, 5.6, 2.2, 0.75), (1.0, -8.5, 2.6, 0.35)]
    base, hot = [], []
    for j in range(-15, 16):
        for i in range(-12, 13):
            k = ry if j < 0 else ry * (1 - 0.06 * max(0, j) / ry)
            w = rx * (1 - 0.18 * max(0, j - 4) / (ry - 4)) if j > 4 else rx
            if (i / w) ** 2 + (j / k) ** 2 > 1:
                continue
            if any(((i - ex) / 2.2) ** 2 + ((j + 2.2) / 1.1) ** 2 <= 1 for ex in (-3.6, 3.6)):
                continue
            if abs(j - 6) <= 0.5 and abs(i) <= 3:
                continue
            x, y = cx + i * P, cy + j * P
            h = min(1.0, sum(a * math.exp(-((i - hx) ** 2 + (j - hy) ** 2) / (2 * s * s)) for hx, hy, s, a in spots))
            base.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.45" fill="{t["dot"]}"/>')
            if h > 0.12:
                col = inferno(0.4 + 0.6 * h) if theme == "dark" else inferno(0.3 + 0.58 * h)
                hot.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{1.45 + 0.35 * h:.2f}" fill="{col}" fill-opacity="{min(1, 0.25 + h):.2f}"/>')
    bx0, by0, bx1, by1, L = cx - 52, cy - 64, cx + 52, cy + 62, 10
    br = (f'M{bx0},{by0 + L}V{by0}H{bx0 + L} M{bx1 - L},{by0}H{bx1}V{by0 + L} '
          f'M{bx1},{by1 - L}V{by1}H{bx1 - L} M{bx0 + L},{by1}H{bx0}V{by1 - L}')
    art = (f'<g>{"".join(base)}</g><g class="hot">{"".join(hot)}</g>'
           f'<path d="{br}" fill="none" stroke="{t["muted"]}" stroke-width="1.6" stroke-linecap="round"/>'
           f'<rect x="{bx1 - 78}" y="{by0 - 9}" width="78" height="19" rx="9.5" fill="{PINK}"/>'
           f'<text x="{bx1 - 39}" y="{by0 + 4.5}" font-size="12" font-weight="600" text-anchor="middle" fill="#fff">fake 57.5%</text>'
           f'<rect class="scan" x="{bx0 + 3}" y="{by0}" width="{bx1 - bx0 - 6}" height="1.6" rx=".8" fill="{TEAL}"/>')
    css = (".hot{animation:pulse 2.8s ease-in-out infinite}@keyframes pulse{0%,100%{opacity:1}50%{opacity:.55}}"
           f".scan{{animation:scan 3.4s linear infinite}}@keyframes scan{{0%{{transform:translateY(0);opacity:0}}8%,92%{{opacity:.8}}100%{{transform:translateY({by1 - by0}px);opacity:0}}}}"
           "@media (prefers-reduced-motion:reduce){.hot,.scan{animation:none}.scan{opacity:0}}")
    return art, css


def art_bc(theme):
    t = THEME[theme]
    cells = json.load(open(BC_JSON))
    px, py = 3.4, 5.7
    rows = max(c[0] for c in cells)
    ox, oy = PX + (PW - 49 * px) / 2 - px, PY_ + (PH - 24 * py) / 2
    pmax = max(c[2] for c in cells)
    rects, dots = [], []
    rnd = random.Random(3)
    for row, col, p, n in cells:
        q = math.sqrt(p / pmax)
        x, y = ox + col * px, oy + (rows - row) * py
        fill = (mix(t["cell"], inferno(0.2 + 0.8 * q), min(1, 0.2 + q * 1.4)) if theme == "dark"
                else mix(t["cell"], inferno(0.25 + 0.65 * q), min(1, 0.15 + q * 1.3)))
        rects.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{px - 0.8:.1f}" height="{py - 1.1:.1f}" rx=".8" fill="{fill}"/>')
        if n > 0:
            dots.append(f'<circle class="ig" cx="{x + (px - 0.8) / 2:.1f}" cy="{y + (py - 1.1) / 2:.1f}" r="1.2" '
                        f'fill="{"#fff" if theme == "dark" else "#2b1d38"}" style="animation-delay:{0.3 + rnd.random() * 2.2:.2f}s"/>')
    art = "".join(rects) + "".join(dots)
    css = (".ig{animation:pop .5s cubic-bezier(.3,1.6,.5,1) both;transform-box:fill-box;transform-origin:center}"
           "@keyframes pop{0%{opacity:0;transform:scale(0)}100%{opacity:.95;transform:scale(1)}}"
           "@media (prefers-reduced-motion:reduce){.ig{animation:none}}")
    return art, css


def art_pac(theme):
    t = THEME[theme]
    route = [(70, 170), (70, 92), (236, 92), (236, 170), (154, 170), (154, 238), (70, 238), (70, 170)]
    seg = [math.dist(a, b) for a, b in zip(route, route[1:])]
    L = sum(seg)
    T = round(L / 46, 2)
    streets = [((40, 92), (266, 92)), ((40, 170), (266, 170)), ((40, 238), (266, 238)),
               ((70, 60), (70, 252)), ((154, 60), (154, 252)), ((236, 60), (236, 252))]
    st = "".join(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{t["street"]}" stroke-width="15" stroke-linecap="round"/>' for a, b in streets)
    pellets, s = [], 10.0
    while s < L - 6:
        acc, i = s, 0
        while acc > seg[i]:
            acc -= seg[i]
            i += 1
        (x0, y0), (x1, y1) = route[i], route[i + 1]
        x, y = x0 + (x1 - x0) * acc / seg[i], y0 + (y1 - y0) * acc / seg[i]
        pellets.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.8" fill="{t["muted"]}"><animate attributeName="opacity" values="1;0" keyTimes="0;{s / L:.4f}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></circle>')
        s += 11
    def house(x, y, lit):
        h = f'<path d="M{x},{y}V{y - 8}L{x + 7},{y - 14}L{x + 14},{y - 8}V{y}Z" fill="{t["panel"]}" stroke="{t["muted"]}" stroke-width="1.5" stroke-linejoin="round"/>'
        if lit:
            h += f'<rect x="{x + 5}" y="{y - 6}" width="4" height="6" rx="1" fill="{AMBER}"/><circle cx="{x + 7}" cy="{y - 20}" r="2.6" fill="{PINK}"/>'
        return h
    houses = "".join(house(x, y, lit) for x, y, lit in
                     [(96, 80, True), (188, 80, False), (98, 158, False), (186, 158, True), (194, 226, True), (96, 226, False)])
    ring = (f'<circle cx="193" cy="150" r="30" fill="{CORAL}" fill-opacity=".08" stroke="{CORAL}" stroke-width="1.2" stroke-dasharray="3 3"/>'
            f'<text x="193" y="114" font-size="11" font-weight="600" text-anchor="middle" fill="{t["muted"]}">25 m</text>')
    path_d = "M" + " L".join(f"{x},{y}" for x, y in route)
    pac_col = PAC if theme == "dark" else "#f2b705"
    gh = ghost(0, 0, 8, CORAL)
    art = (f'<g transform="translate(46,-17) scale(.68)">{st}{ring}{houses}<g>{"".join(pellets)}</g>'
           f'<g>{pacman(9.5, pac_col)}<animateMotion path="{path_d}" dur="{T}s" repeatCount="indefinite" rotate="auto"/></g>'
           f'<g>{gh}<animateMotion path="{path_d}" dur="{T}s" begin="{-(T - 1.1):.2f}s" repeatCount="indefinite"/></g></g>')
    return art, ""


def art_huddle(theme):
    """Friends huddled together (Bluetooth chatter between them), one who wandered off with a check-in ping."""
    t = THEME[theme]
    grid = "".join(f'<circle cx="{x}" cy="{y}" r="1.1" fill="{t["dot"]}"/>'
                   for x in range(PX + 10, PX + PW, 12) for y in range(PY_ + 9, PY_ + PH, 12))
    friends = [(92, 76, CORAL), (134, 58, TEAL), (124, 112, AMBER)]
    away = (214, 96, PURPLE)
    links = "".join(f'<line class="bt" x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{t["muted"]}" stroke-width="1.6" '
                    f'stroke-dasharray="2 5" stroke-linecap="round" stroke-opacity=".7"/>'
                    for a, b in [(friends[0], friends[1]), (friends[1], friends[2]), (friends[2], friends[0])])
    trail = (f'<path d="M136,108 C160,128 184,118 200,104" fill="none" stroke="{t["muted"]}" stroke-width="1.4" '
             f'stroke-dasharray="1 6" stroke-linecap="round" stroke-opacity=".55"/>')
    face_col = "#2b1d38"

    def friend(x, y, col):
        return (f'<circle cx="{x}" cy="{y}" r="13" fill="{col}"/>'
                f'<circle cx="{x - 4}" cy="{y - 2}" r="1.7" fill="{face_col}"/><circle cx="{x + 4}" cy="{y - 2}" r="1.7" fill="{face_col}"/>'
                f'<path d="M{x - 3.5},{y + 3.5} Q{x},{y + 6.5} {x + 3.5},{y + 3.5}" fill="none" stroke="{face_col}" stroke-width="1.5" stroke-linecap="round"/>')
    ax, ay, acol = away
    ring = "".join(f'<circle class="ping" cx="{ax}" cy="{ay}" r="13" fill="none" stroke="{PINK}" stroke-width="1.6" style="animation-delay:{d}s"/>'
                   for d in (0, 1.1))
    pill = (f'<rect x="{ax - 41}" y="{ay - 44}" width="82" height="19" rx="9.5" fill="{PINK}"/>'
            f'<text x="{ax}" y="{ay - 30.5}" font-size="12" font-weight="600" text-anchor="middle" fill="#fff">still okay?</text>')
    lx, ly = PX + PW - 22, PY_ + PH - 26
    lock = (f'<g transform="translate({lx},{ly})" fill="none" stroke="{t["muted"]}" stroke-width="1.6" stroke-linecap="round">'
            f'<rect x="-6" y="0" width="12" height="9.5" rx="2.2"/><path d="M-3.6,0V-3.2a3.6,3.6 0 0 1 7.2,0V0"/></g>')
    art = (f'<g>{grid}</g>{links}{trail}{"".join(friend(*f) for f in friends)}{ring}{friend(ax, ay, acol)}{pill}{lock}')
    css = (".ping{animation:ping 2.2s ease-out infinite;transform-box:fill-box;transform-origin:center}"
           "@keyframes ping{0%{transform:scale(1);opacity:.9}100%{transform:scale(2.3);opacity:0}}"
           ".bt{animation:bt 1.6s linear infinite}@keyframes bt{to{stroke-dashoffset:-14}}"
           "@media (prefers-reduced-motion:reduce){.ping,.bt{animation:none}}")
    return art, css


# ---------------------------------------------------------------- pac-man contribution graph
def contrib(theme):
    t = THEME[theme]
    days = json.load(open(CONTRIB_JSON))
    ncols = max(d[2] for d in days) + 1
    C, G = 12, 3
    P = C + G
    W = 30 + ncols * P + 12
    ox, oy = 30, 30
    H = oy + 7 * P + 26
    css, faces = fonts_css({400: "JanFebMarAprMayJunJulAugSepOctNovDecMonWedFri0123456789 contributionslastyear"})
    cells, targets = [], []
    for d, row, col, lvl in days:
        x, y = ox + col * P, oy + row * P
        cells.append(f'<rect x="{x}" y="{y}" width="{C}" height="{C}" rx="3" fill="{t["levels"][lvl]}"/>')
        if lvl:
            targets.append((col, row, x, y))
    targets.sort()
    # route: along the gaps, column first then row, eating each lit day
    cxy = lambda col, row: (ox + col * P + C / 2, oy + row * P + C / 2)
    pts = [cxy(-1.6, 4)]
    for col, row, _, _ in targets:
        px_, py_ = pts[-1]
        tx, ty = cxy(col, row)
        if px_ != tx:
            pts.append((tx, py_))
        if py_ != ty:
            pts.append((tx, ty))
    pts.append((pts[-1][0], cxy(0, 4)[1]))
    pts.append((cxy(ncols + 0.8, 4)[0], cxy(0, 4)[1]))
    dedup = [pts[0]] + [p for a, p in zip(pts, pts[1:]) if p != a]
    seg = [math.dist(a, b) for a, b in zip(dedup, dedup[1:])]
    L = sum(seg)
    SPEED = 150
    T = round(L / SPEED + 1.0, 2)   # small rest off-screen before looping
    move_frac = (L / SPEED) / T

    def frac_at(pt):
        acc = 0
        for (a, b), s in zip(zip(dedup, dedup[1:]), seg):
            if b == pt:
                return (acc + s) / L * move_frac
            acc += s
        return 0

    eaten = []
    for col, row, x, y in targets:
        f = frac_at(cxy(col, row))
        eaten.append(f'<rect x="{x}" y="{y}" width="{C}" height="{C}" rx="3" fill="{t["levels"][0]}" opacity="0">'
                     f'<animate attributeName="opacity" values="0;1" keyTimes="0;{f:.4f}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></rect>')
    path_d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in dedup)
    kp = f'keyPoints="0;1;1" keyTimes="0;{move_frac:.4f};1" calcMode="linear"'
    pac_col = PAC if theme == "dark" else "#f2b705"
    ghosts = ""
    for i, (c, lag) in enumerate([(CORAL, 0.55), (TEAL, 1.05)]):
        lf = lag / T
        ghosts += (f'<g opacity="0">{ghost(0, 0, 6, c)}'
                   f'<animateMotion path="{path_d}" dur="{T}s" repeatCount="indefinite" keyPoints="0;0;1;1" keyTimes="0;{lf:.4f};{min(move_frac + lf, 0.999):.4f};1" calcMode="linear"/>'
                   f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;{lf:.4f};{min(move_frac + lf, 0.999):.4f}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></g>')
    months, last = [], None
    for d, row, col, lvl in days:
        if row != 0:
            continue
        m = date.fromisoformat(d).strftime("%b")
        if m != last and col < ncols - 1:
            months.append(f'<text x="{ox + col * P}" y="{oy - 9}" font-size="11" fill="{t["muted"]}">{m}</text>')
            last = m
    week = "".join(f'<text x="{ox - 6}" y="{oy + r * P + 10}" font-size="10" text-anchor="end" fill="{t["muted"]}">{n}</text>'
                   for r, n in [(1, "Mon"), (3, "Wed"), (5, "Fri")])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="pac-man eating a77chand's github contribution graph">
<style>
{css}
text{{{FAM}}}
</style>
{"".join(months)}{week}
{"".join(cells)}
{"".join(eaten)}
{ghosts}
<g>{pacman(7, pac_col)}<animateMotion path="{path_d}" dur="{T}s" repeatCount="indefinite" rotate="auto" {kp}/></g>
</svg>'''


# ---------------------------------------------------------------- footer
def footer():
    W, H = 960, 150
    wave = "M0,78 C120,52 220,104 340,82 C470,58 560,102 690,80 C800,62 880,90 960,74 V150 H0 Z"
    wave2 = "M0,98 C140,80 240,120 380,100 C520,80 620,118 760,100 C860,88 920,104 960,96 V150 H0 Z"
    gang = "".join(ghost(x, y, 14, c, cls=f"sw s{i}") for i, (x, y, c) in
                   enumerate([(250, 74, CORAL), (300, 80, BLUSH), (350, 80, TEAL), (400, 74, AMBER)]))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="four little ghosts swimming in a sunset-coloured wave">
<style>
.sw{{animation:sw 2.6s ease-in-out infinite}}@keyframes sw{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-8px)}}}}
.s1{{animation-delay:-.65s}}.s2{{animation-delay:-1.3s}}.s3{{animation-delay:-1.95s}}
.pp{{animation:look 5s ease-in-out infinite}}@keyframes look{{0%,40%{{transform:translateX(0)}}50%,90%{{transform:translateX(3px)}}100%{{transform:translateX(0)}}}}
@media (prefers-reduced-motion:reduce){{.sw,.pp{{animation:none}}}}
</style>
<defs><linearGradient id="fw" x1="0" x2="1"><stop offset="0" stop-color="{AMBER}"/><stop offset=".35" stop-color="{CORAL}"/><stop offset=".65" stop-color="{PINK}"/><stop offset="1" stop-color="{PURPLE}"/></linearGradient></defs>
{gang}
<path d="{wave}" fill="url(#fw)" opacity=".55"/>
<path d="{wave2}" fill="url(#fw)"/>
</svg>'''


# ---------------------------------------------------------------- badges
def badge(label, color, icon):
    css, faces = fonts_css({600: label})
    w = faces[600].width(label, 14) + 54
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} 34" width="{w:.0f}" height="34" role="img" aria-label="{label}">
<style>{css} text{{{FAM}}}</style>
<rect width="{w:.0f}" height="34" rx="17" fill="{color}"/>
<g transform="translate(15,17)" fill="none" stroke="#fff" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{icon}</g>
<text x="36" y="22" font-size="14" font-weight="600" fill="#fff">{label}</text>
</svg>'''


ICONS = {
    "portfolio": '<circle r="7"/><ellipse rx="3" ry="7"/><path d="M-7,0H7"/>',
    "linkedin": '<rect x="-7" y="-7" width="14" height="14" rx="3"/><path d="M-3.5,-1V4M1,4V-1M1,1.5C1,-1.5 4.5,-1.5 4.5,1V4"/><circle cx="-3.5" cy="-3.6" r=".5" fill="#fff"/>',
    "email": '<rect x="-7.5" y="-5.5" width="15" height="11" rx="2"/><path d="M-7,-4.5L0,1L7,-4.5"/>',
}

sizes = {}
W, H, svg = header()
sizes["header.svg"] = write("header.svg", svg)
sizes["footer.svg"] = write("footer.svg", footer())
for name, label, color in [("portfolio", "my corner of the internet", CORAL), ("linkedin", "linkedin", PINK), ("email", "email", PURPLE)]:
    sizes[f"badge-{name}.svg"] = write(f"badge-{name}.svg", badge(label, color, ICONS[name]))
for th in THEME:
    a, c = art_face(th)
    sizes[f"card-ethicura-{th}.svg"] = write(f"card-ethicura-{th}.svg", card(th, "ethicura-ai", ["spots deepfakes, shows why"], [], a, c, "fake 57.5%"))
    a, c = art_bc(th)
    sizes[f"card-wildfire-{th}.svg"] = write(f"card-wildfire-{th}.svg", card(th, "wildfire-risk", ["weekly fire risk across b.c."], [], a, c))
    a, c = art_pac(th)
    sizes[f"card-packween-{th}.svg"] = write(f"card-packween-{th}.svg", card(th, "pack_ween", ["pac-man for trick-or-treating"], [], a, c, "25 m"))
    a, c = art_huddle(th)
    sizes[f"card-huddle-{th}.svg"] = write(f"card-huddle-{th}.svg", card(th, "huddle", ["who's okay on a night out"], [], a, c, "still okay?"))
    sizes[f"pacman-contrib-{th}.svg"] = write(f"pacman-contrib-{th}.svg", contrib(th))
for k, v in sizes.items():
    print(f"{k:28s} {v / 1024:6.1f} KB")
