"""Draw Pac-Man eating a GitHub user's contribution graph (light + dark SVG).

Reads the public contribution calendar, so it needs no token and nothing beyond the standard library.
usage: python scripts/pacman_graph.py <github-user> <out_dir>
"""
import math, os, re, sys, urllib.request
from datetime import date

USER, OUT = sys.argv[1], sys.argv[2]

PAC, CORAL, TEAL = "#ffd23f", "#ff6f59", "#5ce1e6"
THEME = {
    "light": dict(muted="#7a6584", pac="#f2b705", levels=["#f3e8ef", "#ffd9b3", "#ffab80", "#f2708e", "#a855c8"]),
    "dark": dict(muted="#b6a3c2", pac=PAC, levels=["#21172e", "#4e2a47", "#8c3b5d", "#e0607e", "#ffb347"]),
}
# Fredoka, subset to the labels drawn below (SIL Open Font License)
FONT_CSS = "@font-face{font-family:'Fredoka';font-weight:400;src:url(data:font/woff2;base64,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) format('woff2')}"
FAM = "font-family:'Fredoka','Nunito','Trebuchet MS',sans-serif"


def fetch_days(user):
    req = urllib.request.Request(f"https://github.com/users/{user}/contributions",
                                 headers={"User-Agent": "pacman-graph"})
    html = urllib.request.urlopen(req, timeout=30).read().decode()
    cells = re.findall(r'data-date="([0-9-]+)" id="contribution-day-component-(\d+)-(\d+)" data-level="(\d)"', html)
    if len(cells) < 300:
        sys.exit(f"could not read the contribution calendar for {user} ({len(cells)} days found)")
    return [(d, int(r), int(c), int(l)) for d, r, c, l in cells]


def ghost(s, color):
    body = (f"M{-s},{s} V{-0.1 * s} A{s},{s} 0 0,1 {s},{-0.1 * s} V{s} "
            f"L{0.66 * s},{0.72 * s} L{0.33 * s},{s} L0,{0.72 * s} L{-0.33 * s},{s} L{-0.66 * s},{0.72 * s} Z")
    return (f'<path d="{body}" fill="{color}"/>'
            f'<ellipse cx="{-0.38 * s:.1f}" cy="{-0.12 * s:.1f}" rx="{0.26 * s:.1f}" ry="{0.32 * s:.1f}" fill="#fff"/>'
            f'<ellipse cx="{0.38 * s:.1f}" cy="{-0.12 * s:.1f}" rx="{0.26 * s:.1f}" ry="{0.32 * s:.1f}" fill="#fff"/>'
            f'<circle cx="{-0.44 * s:.1f}" cy="{-0.08 * s:.1f}" r="{0.13 * s:.1f}" fill="#2b2d6e"/>'
            f'<circle cx="{0.32 * s:.1f}" cy="{-0.08 * s:.1f}" r="{0.13 * s:.1f}" fill="#2b2d6e"/>')


def pac_d(r, deg):
    a = math.radians(deg)
    return f"M0,0 L{r * math.cos(a):.2f},{-r * math.sin(a):.2f} A{r},{r} 0 1,0 {r * math.cos(a):.2f},{r * math.sin(a):.2f} Z"


def render(days, theme):
    t = THEME[theme]
    ncols = max(d[2] for d in days) + 1
    C, G = 12, 3
    P = C + G
    ox, oy = 30, 30
    W, H = ox + ncols * P + 12, oy + 7 * P + 26
    cells, targets = [], []
    for d, row, col, lvl in days:
        x, y = ox + col * P, oy + row * P
        cells.append(f'<rect x="{x}" y="{y}" width="{C}" height="{C}" rx="3" fill="{t["levels"][lvl]}"/>')
        if lvl:
            targets.append((col, row, x, y))
    targets.sort()

    # pac-man walks the gaps, column first then row, eating every day with contributions
    cxy = lambda col, row: (ox + col * P + C / 2, oy + row * P + C / 2)
    pts = [cxy(-1.6, 4)]
    for col, row, _, _ in targets:
        px, py = pts[-1]
        tx, ty = cxy(col, row)
        if px != tx:
            pts.append((tx, py))
        if py != ty:
            pts.append((tx, ty))
    pts.append((pts[-1][0], cxy(0, 4)[1]))
    pts.append((cxy(ncols + 0.8, 4)[0], cxy(0, 4)[1]))
    route = [pts[0]] + [p for a, p in zip(pts, pts[1:]) if p != a]
    seg = [math.dist(a, b) for a, b in zip(route, route[1:])]
    L = sum(seg)
    SPEED = 150
    T = round(L / SPEED + 1.0, 2)          # a short rest off-screen before the loop restarts
    move = (L / SPEED) / T

    def frac_at(pt):
        acc = 0
        for (a, b), s in zip(zip(route, route[1:]), seg):
            acc += s
            if b == pt:
                return acc / L * move
        return 0

    eaten = [f'<rect x="{x}" y="{y}" width="{C}" height="{C}" rx="3" fill="{t["levels"][0]}" opacity="0">'
             f'<animate attributeName="opacity" values="0;1" keyTimes="0;{frac_at(cxy(col, row)):.4f}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></rect>'
             for col, row, x, y in targets]
    path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in route)
    ghosts = ""
    for color, lag in [(CORAL, 0.55), (TEAL, 1.05)]:
        lf = lag / T
        end = min(move + lf, 0.999)
        ghosts += (f'<g opacity="0"><g>{ghost(6, color)}</g>'
                   f'<animateMotion path="{path}" dur="{T}s" repeatCount="indefinite" keyPoints="0;0;1;1" keyTimes="0;{lf:.4f};{end:.4f};1" calcMode="linear"/>'
                   f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;{lf:.4f};{end:.4f}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></g>')
    pac = (f'<g><path d="{pac_d(7, 38)}" fill="{t["pac"]}"><animate attributeName="d" values="{pac_d(7, 38)};{pac_d(7, 3)};{pac_d(7, 38)}" dur=".3s" repeatCount="indefinite"/></path>'
           f'<animateMotion path="{path}" dur="{T}s" repeatCount="indefinite" rotate="auto" keyPoints="0;1;1" keyTimes="0;{move:.4f};1" calcMode="linear"/></g>')

    months, last = [], None
    for d, row, col, lvl in days:
        m = date.fromisoformat(d).strftime("%b")
        if row == 0 and m != last and col < ncols - 1:
            months.append(f'<text x="{ox + col * P}" y="{oy - 9}" font-size="11" fill="{t["muted"]}">{m}</text>')
            last = m
    week = "".join(f'<text x="{ox - 6}" y="{oy + r * P + 10}" font-size="10" text-anchor="end" fill="{t["muted"]}">{n}</text>'
                   for r, n in [(1, "Mon"), (3, "Wed"), (5, "Fri")])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="pac-man eating {USER}\'s github contribution graph">'
            f"<style>{FONT_CSS}text{{{FAM}}}</style>"
            f'{"".join(months)}{week}{"".join(cells)}{"".join(eaten)}{ghosts}{pac}</svg>')


if __name__ == "__main__":
    days = fetch_days(USER)
    os.makedirs(OUT, exist_ok=True)
    for theme in THEME:
        with open(os.path.join(OUT, f"pacman-contrib-{theme}.svg"), "w") as f:
            f.write(render(days, theme))
    print(f"{sum(1 for d in days if d[3])} active days drawn")
