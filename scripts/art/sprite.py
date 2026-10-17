"""Pixel doll of Anusha: nerdy glasses, holding an open laptop (lid with stickers facing out).

Builds a grid of material keys, then colours it with swappable palettes.
usage: python3 sprite.py <out_dir>   (writes sprite.json + preview SVGs)
"""
import json, math, os, sys

W, H = 46, 94
CX = 23


class Canvas:
    def __init__(self):
        self.g = [[None] * W for _ in range(H)]

    def put(self, x, y, k):
        if 0 <= x < W and 0 <= y < H:
            self.g[y][x] = k

    def get(self, x, y):
        return self.g[y][x] if 0 <= x < W and 0 <= y < H else None

    def fill(self, test, k, only=None):
        for y in range(H):
            for x in range(W):
                if test(x + 0.5, y + 0.5) and (only is None or self.g[y][x] in only):
                    self.g[y][x] = k

    def rect(self, x0, y0, x1, y1, k):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, k)

    def poly(self, pts, k, only=None):
        def inside(px, py):
            c = False
            for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
                if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
                    c = not c
            return c
        self.fill(inside, k, only)

    def capsule(self, x0, y0, x1, y1, r, k):
        """A thick line with round ends, for limbs."""
        def near(px, py):
            dx, dy = x1 - x0, y1 - y0
            t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy)))
            return (px - x0 - t * dx) ** 2 + (py - y0 - t * dy) ** 2 <= r * r
        self.fill(near, k)

    def pix(self, rows, x0, y0, legend):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in legend:
                    self.put(x0 + i, y0 + j, legend[ch])


# raised right arm for the wave: (elbow, wrist, hand centre)
WAVE = {"wave1": ((37, 31), (37.6, 23), (37.8, 19.6)),
        "wave2": ((37, 31), (40.2, 24), (40.9, 20.8))}


def build(style="long", pose="idle"):
    """style: long | shoulder.  pose: idle | wave1 | wave2 (laptop in one hand, waving with the other)"""
    holding = pose == "idle"
    c = Canvas()
    # ---- back hair
    if style == "long":
        c.poly([(12, 13), (14, 7), (19, 3.5), (27, 3.5), (32, 7), (34, 13), (35, 30), (36, 44), (37, 54),
                (34, 57), (31, 55), (28, 57), (25, 55), (21, 55), (18, 57), (15, 55), (12, 57), (9, 54),
                (10, 44), (11, 30)], "j")
    else:  # chin-length bob
        c.poly([(12, 13), (14, 7), (19, 3.5), (27, 3.5), (32, 7), (34, 13), (35, 22), (36, 31),
                (33, 33), (29, 31), (17, 31), (13, 33), (10, 31), (11, 22)], "j")
    # ---- neck
    c.rect(21, 26, 25, 31, "s")
    c.rect(22, 26, 24, 29, "S")
    # ---- legs, socks, shoes
    for lx in (17, 25):
        c.poly([(lx, 58), (lx + 5, 58), (lx + 4.6, 72), (lx + 4, 84), (lx + 1, 84), (lx + 0.4, 72)], "S")
        c.put(lx + 2, 71, "s")             # knee
        c.poly([(lx + 0.2, 74), (lx + 4.8, 74), (lx + 4.2, 86), (lx + 0.8, 86)], "O")
        c.rect(lx, 74, lx + 4, 74, "o")
        c.rect(lx, 76, lx + 4, 76, "o")
        c.poly([(lx - 1, 86), (lx + 5.5, 86), (lx + 6, 89), (lx + 6, 91), (lx - 1.5, 91), (lx - 1.5, 89)], "F")
        c.rect(lx - 1, 91, lx + 5, 92, "f")
        c.rect(lx + 1, 87, lx + 3, 87, "f")    # mary jane strap shine
    # ---- skirt (pleated)
    c.poly([(15, 49), (31, 49), (33, 59), (13, 59)], "K")
    for x in (17, 20, 23, 26, 29):
        for y in range(52, 59):
            if c.get(x, y) == "K":
                c.put(x, y, "q")
    # ---- oversized sweater
    c.poly([(16, 30), (30, 30), (33, 33), (33, 40), (31, 50), (15, 50), (13, 40), (13, 33)], "T")
    c.rect(15, 49, 31, 51, "t")
    for x in range(15, 32, 2):
        c.put(x, 50, "T")
    # peter-pan collar
    c.pix(["cccc..cccc", ".cccccccc.", "..cC..Cc.."], 18, 30, {"c": "c", "C": "C"})
    # sleeves hanging down the sides, bending in to hold the laptop
    c.poly([(13, 32), (16, 32), (16, 46), (17, 48), (12, 48), (11, 44), (11.5, 36)], "T")
    if holding:
        c.poly([(30, 32), (33, 32), (34.5, 36), (35, 44), (34, 48), (29, 48), (30, 46)], "T")
    for y in range(36, 46):
        c.put(12, y, "t")
        if holding:
            c.put(33, y, "t")
    c.rect(12, 46, 16, 47, "t")   # cuffs
    if holding:
        c.rect(30, 46, 34, 47, "t")
    # ---- laptop lid, stickers facing out
    c.poly([(14, 37), (32, 37), (32.5, 49), (13.5, 49)], "L")
    c.rect(14, 48, 32, 48, "m")
    c.rect(13, 49, 33, 50, "m")       # base seen edge-on
    c.pix([".yyy.", "yyy..", "yy...", "yyy..", ".yyy."], 16, 39, {"y": "y"})                           # pac-man sticker
    c.pix([".ppp.", "ppppp", "pwpwp", "ppppp", "p.p.p"], 21, 41, {"p": "p", "w": "w"})                  # ghost sticker
    c.pix([".n.n.", "nnnnn", ".nnn.", "..n.."], 27, 39, {"n": "n"})                                     # heart sticker
    c.pix(["m.m", ".m.", "m.m"], 28, 44, {"m": "m"})   # tiny </> -ish sticker
    # hands gripping the sides of the lid
    c.pix(["SSS", "sSS", "sSs"], 13, 46, {"S": "S", "s": "s"})
    if holding:
        c.pix(["SSS", "SSs", "sSs"], 30, 46, {"S": "S", "s": "s"})
    # ---- face
    def face(x, y):
        dx, dy = (x - 23) / 8.6, (y - 17.2) / 9.6
        if dy > 0:
            dx /= (1 - 0.32 * dy ** 1.5)
        return dx * dx + dy * dy <= 1
    c.fill(face, "S")
    # ---- front hair: bangs and face-framing locks
    bang_bottom = [12, 13, 14, 14, 13, 12, 13, 14, 15, 14, 13, 12, 12, 13, 14, 14, 13, 12, 13, 14, 15, 15, 14]
    for i, yb in enumerate(bang_bottom):
        x = 12 + i
        for y in range(4, yb + 1):
            if c.get(x, y) in ("S", "j", None) and (x - 23) ** 2 / 11.5 ** 2 + (y - 13) ** 2 / 9.8 ** 2 <= 1:
                c.put(x, y, "H")
    # shadow the bangs cast on the forehead
    for x in range(W):
        for y in range(H - 1):
            if c.get(x, y) == "H" and c.get(x, y + 1) == "S":
                c.put(x, y + 1, "s")
    lock_len = 40 if style == "long" else 30
    for side in (-1, 1):
        x0 = 13 if side < 0 else 31
        c.poly([(x0, 12), (x0 + 2.5, 12), (x0 + 2 + side * 0.5, 22), (x0 + 1.5 + side * 1, lock_len), (x0 - 0.5 + side * 1, lock_len - 2), (x0 - 0.5, 22)], "H")
    # hair shading + shine
    for x, y in [(15, 10), (16, 9), (17, 8)]:
        c.put(x, y, "h")
    c.pix(["..kkk.kk..", ".k........"], 18, 6, {"k": "k"})
    for y in range(16, lock_len - 1):
        c.put(14 if y % 4 else 15, y, "h")
        c.put(32 if y % 4 else 31, y, "h")
    # star clip
    c.pix([".Y.", "YYY", ".Y."], 29, 8, {"Y": "y"})
    # ---- eyes, glasses, blush, mouth
    eye = ["llll.", ".EwE", ".EEE", ".eEe"]
    c.pix(eye, 16, 17, {"l": "l", "E": "E", "w": "w", "e": "e"})
    c.pix([".llll", "EwE.", "EEE.", "eEe."], 26, 17, {"l": "l", "E": "E", "w": "w", "e": "e"})
    ring = lambda cx: [(round(cx + 3.7 * math.cos(a)), round(19 + 3.4 * math.sin(a))) for a in [i * math.pi / 12 for i in range(24)]]
    for cxr in (18.0, 28.0):
        for x, y in set(ring(cxr)):
            if c.get(x, y) in ("S", "s", "H", "h"):
                c.put(x, y, "G")
    c.rect(22, 18, 24, 18, "G")
    c.put(17, 16, "g"); c.put(27, 16, "g")   # lens glints
    c.put(16, 23, "r"); c.put(17, 23, "r"); c.put(29, 23, "r"); c.put(30, 23, "r")
    c.put(23, 22, "s")
    if holding:
        c.pix(["M.M", ".M."], 22, 24, {"M": "M"})
    else:
        c.pix(["MMM", ".M."], 22, 24, {"M": "M"})       # open, happy mouth while waving
        (ex, ey), (wx, wy), (hx, hy) = WAVE[pose]
        c.capsule(31.5, 33, ex, ey, 2.4, "T")             # upper arm, in front of her hair
        c.capsule(ex, ey, wx, wy, 2.1, "T")
        c.capsule(ex + 0.6, ey - 1, wx + 0.6, wy + 1, 0.6, "t")
        c.capsule(wx, wy + 0.6, wx + (hx - wx) * 0.3, wy, 2.2, "t")   # cuff
        c.fill(lambda x, y: ((x - hx) / 1.8) ** 2 + ((y - hy) / 2.2) ** 2 <= 1, "S")
        c.put(round(hx - 2), round(hy + 0.5), "S")        # thumb
        c.put(round(hx + 1), round(hy + 1), "s")
    # ---- outline: one dark pixel ring around the whole silhouette
    filled = [[c.g[y][x] is not None for x in range(W)] for y in range(H)]
    for y in range(H):
        for x in range(W):
            if not filled[y][x] and any(0 <= x + dx < W and 0 <= y + dy < H and filled[y + dy][x + dx]
                                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                c.g[y][x] = "X"
    return ["".join(k or "." for k in row) for row in c.g]


# blink frame: eyes closed (only the eye pixels change)
def blink(rows):
    out = [list(r) for r in rows]
    for y in range(17, 21):
        for x in range(16, 31):
            if out[y][x] in "Ewe" or (y == 17 and out[y][x] == "l"):
                out[y][x] = "S" if y < 20 else "l"
            if y == 20 and out[y][x] == "l" and not (16 <= x <= 20 or 26 <= x <= 30):
                out[y][x] = "S"
    return ["".join(r) for r in out]


SKIN = {  # base, shade, blush
    "porcelain": ("#fbe3d2", "#ebc1aa", "#f6a3a8"),
    "light": ("#f3cba8", "#dca783", "#ee8f95"),
    "medium": ("#d8a07a", "#b97f5c", "#d9707a"),
    "tan": ("#b47853", "#935d3e", "#c4606a"),
    "deep": ("#7d4d33", "#603826", "#a8505a"),
}
HAIR = {  # front, shade, back, shine
    "black": ("#2a2230", "#1a141f", "#140f18", "#5b5068"),
    "dark brown": ("#4a2c22", "#351e18", "#26150f", "#7d5240"),
    "brown": ("#7a4a30", "#5c3522", "#43261a", "#a8714f"),
    "auburn": ("#9c3f28", "#7a2e1c", "#5c2214", "#d06a48"),
    "pink": ("#f29bbf", "#d877a0", "#b95d85", "#ffd1e3"),
}
OUTFIT = {  # sweater, sweater shade, skirt, pleat
    "lilac": ("#b9a2e6", "#9a80cc", "#4b3470", "#3a2659"),
    "pink": ("#f7a8c8", "#de86ab", "#6d2b4f", "#55203d"),
    "sage": ("#a9c79f", "#87a77e", "#3f5a43", "#2f4532"),
    "cream": ("#f2e2c4", "#d6c09d", "#7a4f3a", "#5e3b2b"),
}
FIXED = {
    "X": "#25162e", "l": "#25162e", "M": "#9b3b54", "E": "#5a3424", "e": "#3a2018", "w": "#ffffff",
    "G": "#25162e", "g": "#ffffff", "c": "#ffffff", "C": "#d9d2e6",
    "O": "#fff6ec", "o": "#f2708e", "F": "#2b2036", "f": "#5d4f6e",
    "L": "#d9dbe8", "m": "#a9abc4", "y": "#ffd23f", "p": "#f7a1c4", "n": "#5ce1e6",
}


def palette(skin, hair, outfit):
    s, h, o = SKIN[skin], HAIR[hair], OUTFIT[outfit]
    p = dict(FIXED)
    p.update({"S": s[0], "s": s[1], "r": s[2], "H": h[0], "h": h[1], "j": h[2], "k": h[3],
              "T": o[0], "t": o[1], "K": o[2], "q": o[3]})
    return p


CLS = {k: f"p{i}" for i, k in enumerate("XlMEewGgcCOoFfLmypnSsrHhjkTtKq")}


def paint(pal, k):
    return f'class="{CLS[k]}"' if pal is None else f'fill="{pal[k]}"'


def palette_css(pal):
    return "".join(f".{CLS[k]}{{fill:{v}}}" for k, v in pal.items())


def _paths(cells, pal, ox, oy, scale):
    """cells: {key: [(x, y, run)]} -> one <path> per colour, so rows of a colour merge without seams."""
    out = []
    for k, runs in cells.items():
        d = "".join(f"M{ox + x * scale:.2f} {oy + y * scale:.2f}h{n * scale:.2f}v{scale:.2f}h{-n * scale:.2f}z" for x, y, n in runs)
        out.append(f'<path {paint(pal, k)} d="{d}"/>')
    return '<g shape-rendering="crispEdges">' + "".join(out) + "</g>"


def svg_rects(rows, pal, ox=0.0, oy=0.0, scale=1.0):
    """pal=None writes class="p<n>" (colour comes from palette_css) instead of a fill."""
    cells = {}
    for y, row in enumerate(rows):
        x = 0
        while x < W:
            k = row[x]
            if k == ".":
                x += 1
                continue
            x2 = x
            while x2 + 1 < W and row[x2 + 1] == k:
                x2 += 1
            cells.setdefault(k, []).append((x, y, x2 - x + 1))
            x = x2 + 1
    return _paths(cells, pal, ox, oy, scale)


def eye_rects(rows, pal, ox, oy, scale):
    """Only the face band (rows 16-21), drawn on top for the blink frame."""
    cells = {}
    for y in range(16, 22):
        for x in range(14, 33):
            if rows[y][x] != ".":
                cells.setdefault(rows[y][x], []).append((x, y, 1))
    return _paths(cells, pal, ox, oy, scale)


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    data = {"w": W, "h": H, "styles": {}, "blink": {}, "skin": SKIN, "hair": HAIR, "outfit": OUTFIT, "fixed": FIXED}
    for st in ("long", "shoulder"):
        rows = build(st)
        data["styles"][st] = rows
        data["blink"][st] = blink(rows)
    json.dump(data, open(os.path.join(out, "sprite.json"), "w"))
    # contact sheet of a few combinations, 6x, for checking
    combos = [("long", "medium", "dark brown", "lilac"), ("long", "light", "black", "pink"),
              ("shoulder", "tan", "black", "sage"), ("long", "deep", "dark brown", "cream"),
              ("shoulder", "porcelain", "pink", "lilac")]
    sc = 5
    parts = []
    for i, (st, sk, hr, of) in enumerate(combos):
        pal = palette(sk, hr, of)
        parts.append(svg_rects(data["styles"][st], pal, ox=10 + i * (W * sc + 20), oy=10, scale=sc))
    parts.append(svg_rects(data["blink"]["long"], palette("medium", "dark brown", "lilac"), ox=10 + 5 * (W * sc + 20), oy=10, scale=sc))
    tw = 10 + 6 * (W * sc + 20)
    open(os.path.join(out, "sheet.svg"), "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {tw} {H * sc + 20}" width="{tw}" height="{H * sc + 20}">'
        f'<rect width="{tw}" height="{H * sc + 20}" fill="#3a2d4f"/>{"".join(parts)}</svg>')
    print("ok")
