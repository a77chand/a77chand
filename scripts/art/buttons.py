"""Old-web 88x31 buttons for the profile README.

needs: pip install fonttools, plus Silkscreen 400 and 700 latin woff2 from Google Fonts.
usage: python scripts/art/buttons.py <silk-400.woff2> <silk-700.woff2> <out_dir>
"""
import base64, math, os, sys
from fontTools.ttLib import TTFont

R400, R700, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
W, H, FS = 88, 31, 8


class Silk:
    def __init__(self, path, weight):
        self.b64 = base64.b64encode(open(path, "rb").read()).decode()
        f = TTFont(path)
        self.upm, self.cmap, self.hmtx, self.weight = f["head"].unitsPerEm, f.getBestCmap(), f["hmtx"], weight

    def width(self, s, size=FS):
        return sum(self.hmtx[self.cmap[ord(c)]][0] for c in s) * size / self.upm

    def css(self):
        return f"@font-face{{font-family:'Silk';font-weight:{self.weight};src:url(data:font/woff2;base64,{self.b64}) format('woff2')}}"


S4, S7 = Silk(R400, 400), Silk(R700, 700)
FONT_CSS = S4.css() + S7.css() + "text{font-family:'Silk',monospace;font-size:8px}"


def bevel(bg, hi, lo):
    """Classic raised button: light top-left edge, dark bottom-right edge."""
    return (f'<rect width="{W}" height="{H}" fill="{lo}"/>'
            f'<rect width="{W - 1}" height="{H - 1}" fill="{hi}"/>'
            f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" fill="{bg}"/>')


def text(s, x, y, color, weight=400, anchor="start", shadow=None):
    out = ""
    if shadow:
        out += f'<text x="{x + 1}" y="{y + 1}" font-weight="{weight}" text-anchor="{anchor}" fill="{shadow}">{s}</text>'
    return out + f'<text x="{x}" y="{y}" font-weight="{weight}" text-anchor="{anchor}" fill="{color}">{s}</text>'


def svg(name, label, body, css=""):
    with open(os.path.join(OUT, f"btn-{name}.svg"), "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{label}" shape-rendering="crispEdges">'
                f'<style>{FONT_CSS}{css}@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>{body}</svg>')


def fits(*pairs):
    for s, face, x in pairs:
        assert x + face.width(s) <= W - 3, (s, x + face.width(s))


def pac_d(r, deg):
    a = math.radians(deg)
    return f"M0,0 L{r * math.cos(a):.2f},{-r * math.sin(a):.2f} A{r},{r} 0 1,0 {r * math.cos(a):.2f},{r * math.sin(a):.2f} Z"


# 1. pac-man approved
fits(("PAC-MAN", S7, 25), ("APPROVED", S4, 25))
svg("pacman", "pac-man approved",
    bevel("#000000", "#5a5a7a", "#1a1a24")
    + f'<g transform="translate(12,15.5)" shape-rendering="geometricPrecision"><path d="{pac_d(7, 38)}" fill="#ffd23f">'
      f'<animate attributeName="d" values="{pac_d(7, 38)};{pac_d(7, 3)};{pac_d(7, 38)}" dur=".35s" repeatCount="indefinite"/></path></g>'
    + "".join(f'<rect x="{x}" y="27" width="1" height="1" fill="#ffd23f" opacity=".7"/>' for x in range(26, 84, 4))
    + text("PAC-MAN", 25, 13, "#ffd23f", 700) + text("APPROVED", 25, 23, "#ffffff"))

# 2. powered by heatmaps (the gradient slides like a colour bar)
fits(("POWERED BY", S4, 44 - S4.width("POWERED BY") / 2), ("HEATMAPS", S7, 44 - S7.width("HEATMAPS") / 2))
svg("heatmaps", "powered by heatmaps",
    '<defs><linearGradient id="h" x1="0" x2="176" gradientUnits="userSpaceOnUse" spreadMethod="reflect">'
    '<stop offset="0" stop-color="#3b0f70"/><stop offset=".3" stop-color="#b5367a"/><stop offset=".6" stop-color="#fb8761"/><stop offset="1" stop-color="#fcfdbf"/>'
    '<animateTransform attributeName="gradientTransform" type="translate" values="0;-88;0" dur="6s" repeatCount="indefinite"/></linearGradient></defs>'
    + bevel("url(#h)", "#ffd9c2", "#2a0b3d")
    + text("POWERED BY", 44, 13, "#ffffff", anchor="middle", shadow="#2a0b3d")
    + text("HEATMAPS", 44, 24, "#ffffff", 700, anchor="middle", shadow="#2a0b3d"))

# 3. webgpu inside
chip = ('<rect x="6" y="9" width="13" height="13" fill="#5ce1e6"/><rect x="9" y="12" width="7" height="7" fill="#1b1230"/>'
        '<rect x="11" y="14" width="3" height="3" fill="#5ce1e6"/>'
        + "".join(f'<rect x="{x}" y="7" width="1" height="2" fill="#5ce1e6"/><rect x="{x}" y="22" width="1" height="2" fill="#5ce1e6"/>' for x in (8, 11, 14, 17))
        + "".join(f'<rect x="4" y="{y}" width="2" height="1" fill="#5ce1e6"/><rect x="19" y="{y}" width="2" height="1" fill="#5ce1e6"/>' for y in (11, 14, 17, 20)))
fits(("WEBGPU", S7, 27), ("INSIDE", S4, 27))
svg("webgpu", "webgpu inside",
    bevel("#1b1230", "#5b4a8a", "#0a0614") + chip
    + text("WEBGPU", 27, 13, "#5ce1e6", 700) + text("INSIDE", 27, 23, "#fff1e6")
    + '<rect class="led" x="80" y="5" width="3" height="3" fill="#7dff8a"/>',
    ".led{animation:led 1.1s steps(1) infinite}@keyframes led{50%{opacity:.15}}")

# 4. uwaterloo cs
fits(("UWATERLOO", S7, 44 - S7.width("UWATERLOO") / 2), ("CS STUDENT", S4, 44 - S4.width("CS STUDENT") / 2))
svg("uwaterloo", "uwaterloo cs student",
    bevel("#000000", "#e4b429", "#5a4300")
    + '<rect x="1" y="1" width="86" height="2" fill="#fed34c"/><rect x="1" y="28" width="86" height="2" fill="#fed34c"/>'
    + text("UWATERLOO", 44, 14, "#fed34c", 700, anchor="middle") + text("CS STUDENT", 44, 24, "#ffffff", anchor="middle"))

# 5. best viewed at night
stars = "".join(f'<rect class="s s{i % 3}" x="{x}" y="{y}" width="1" height="1" fill="#fff1e6"/>'
                for i, (x, y) in enumerate([(4, 4), (20, 26), (31, 3), (47, 27), (60, 4), (74, 26), (83, 9), (12, 25), (40, 2)]))
moon = '<circle cx="11" cy="12" r="6" fill="#ffd23f" shape-rendering="geometricPrecision"/><circle cx="14" cy="10" r="5.2" fill="#170f26" shape-rendering="geometricPrecision"/>'
fits(("BEST VIEWED", S4, 21), ("AT NIGHT", S7, 21))
svg("night", "best viewed at night",
    bevel("#170f26", "#6b4f9e", "#08050f") + stars + moon
    + text("BEST VIEWED", 21, 14, "#fff1e6") + text("AT NIGHT", 21, 24, "#c08cf5", 700),
    ".s{animation:tw 2.4s steps(1) infinite}.s1{animation-delay:-.8s}.s2{animation-delay:-1.6s}@keyframes tw{50%{opacity:.1}}")

# 6. hacked at ellehacks
heart = "".join(f'<rect x="{6 + c}" y="{10 + r}" width="1" height="1" fill="#ffffff"/>'
                for r, row in enumerate([".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."])
                for c, px in enumerate(row) if px == "#")
fits(("HACKED AT", S4, 17), ("ELLEHACKS", S7, 17))
svg("ellehacks", "hacked at ellehacks",
    bevel("#ef476f", "#ffb3c6", "#8a1534") + f'<g class="beat">{heart}</g>'
    + text("HACKED AT", 17, 13, "#fff1e6") + text("ELLEHACKS", 17, 23, "#ffffff", 700, shadow="#8a1534"),
    ".beat{animation:beat 1s steps(1) infinite}@keyframes beat{50%{opacity:.35}}")

print(sorted(os.listdir(OUT)))
