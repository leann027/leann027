"""Genera banner-dark.svg y banner-light.svg: una galaxia en espiral animada solo con CSS.

Requiere fonttools (pip install fonttools) y estas fuentes, guardadas en una carpeta aparte:
  https://cdn.jsdelivr.net/npm/@fontsource/plus-jakarta-sans@5.0.0/files/plus-jakarta-sans-latin-700-normal.woff  -> jakarta-700.woff
  https://cdn.jsdelivr.net/npm/@fontsource/jetbrains-mono@5.0.0/files/jetbrains-mono-latin-400-normal.woff  -> jbmono-400.woff

Uso: python3 scripts/make_banner.py <carpeta-de-fuentes> assets
"""
import math
import random
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONTS, OUT = Path(sys.argv[1]), Path(sys.argv[2])
W, H = 1200, 300
CX, CY, R = 925, 150, 370
TILT, SQUASH = -14, 0.5


def num(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def text_path(font_file, text, size, x, y, tracking=0.0):
    font = TTFont(FONTS / font_file)
    glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
    scale = size / font["head"].unitsPerEm
    pen, cursor = SVGPathPen(glyphs, ntos=num), x
    for ch in text:
        name = cmap[ord(ch)]
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, cursor, y)))
        cursor += glyphs[name].width * scale + tracking
    return pen.getCommands(), cursor


def dots(points):
    return "".join(f"M{num(x)} {num(y)}h0" for x, y in points)


def spiral(rng, n, arms=3, pitch=0.3, width=0.2):
    """Puntos por brazo y tamaño: {(brazo, tamaño): [(x, y), ...]}."""
    out = {}
    for _ in range(n):
        arm = rng.randrange(arms)
        r = 34 + (R - 34) * rng.random() ** 1.5
        theta = arm * 2 * math.pi / arms + math.log(r / 34) / pitch
        spread = width * (1 - 0.35 * r / R)
        theta += rng.gauss(0, spread)
        rr = r + rng.gauss(0, 8)
        size = rng.choices((0, 1, 2), (6, 3, 1))[0]
        out.setdefault((arm, size), []).append((rr * math.cos(theta), rr * math.sin(theta)))
    return out


def clouds(rng, arms=3, pitch=0.3):
    items = []
    for arm in range(arms):
        for step in range(4):
            r = 80 + step * 72 + rng.uniform(-10, 10)
            theta = arm * 2 * math.pi / arms + math.log(r / 34) / pitch + rng.uniform(-0.12, 0.12)
            items.append((arm, r * math.cos(theta), r * math.sin(theta), rng.uniform(30, 52)))
    return items


THEMES = {
    "dark": dict(
        bg0="#05070d", bg1="#0a0f1c", border="#1e2a3a", name="#f4f7fb", sub="#2dd9c3",
        star="#c9d6e8", arms=["#2dd9c3", "#f472b6", "#a78bfa", "#fbbf24"],
        cloud_op=0.2, dust_op=0.95, core="#e8fffb", core2="#2dd9c3", hole="#04060b", ring="#d9fff8",
        blend="screen",
    ),
    "light": dict(
        bg0="#f7f8fc", bg1="#eef1f8", border="#d5dbe6", name="#111827", sub="#0f766e",
        star="#5b6b82", arms=["#0f8f80", "#d6337f", "#6d4fd8", "#c27803"],
        cloud_op=0.14, dust_op=0.85, core="#3b2f8f", core2="#0f8f80", hole="#111827", ring="#111827",
        blend="multiply",
    ),
}


def build(mode):
    t = THEMES[mode]
    rng = random.Random(27)
    arms = spiral(rng, 760)
    far = spiral(rng, 150, width=0.55)
    cloud_items = clouds(rng)
    sizes = (2, 3.2, 5)

    bg_stars = [(rng.uniform(0, W), rng.uniform(0, H)) for _ in range(70)]
    twinkle = [(rng.uniform(420, W - 12), rng.uniform(10, H - 10)) for _ in range(24)]

    name_d, _ = text_path("jakarta-700.woff", "Leandro Guidolin", 70, 60, 150, tracking=-0.8)
    sub_d, _ = text_path("jbmono-400.woff", "Software developer · Web & 3D", 29, 62, 200)

    arm_grad = "".join(
        f'<radialGradient id="n{i}"><stop stop-color="{c}" stop-opacity="{t["cloud_op"]}"/>'
        f'<stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>'
        for i, c in enumerate(t["arms"])
    )
    cloud_svg = "".join(
        f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(r)}" fill="url(#n{a})"/>'
        for a, x, y, r in cloud_items
    )

    def layer(points, opacity):
        return "".join(
            f'<path stroke="{t["arms"][a]}" stroke-width="{sizes[s]}" opacity="{opacity}" d="{dots(p)}"/>'
            for (a, s), p in sorted(points.items())
        )

    twinkle_svg = "".join(
        f'<path class="tw t{i % 3}" stroke-width="{2.2 if i % 4 == 0 else 1.6}" d="{dots([p])}"/>'
        for i, p in enumerate(twinkle)
    )

    style = (
        "@keyframes s{to{transform:rotate(360deg)}}"
        "@keyframes w{0%,100%{opacity:.15}50%{opacity:1}}"
        ".a{animation:s 120s linear infinite}"
        ".b{animation:s 190s linear infinite}"
        ".tw{opacity:.15;animation:w 5s ease-in-out infinite}"
        ".t1{animation-delay:-1.7s;animation-duration:6.5s}"
        ".t2{animation-delay:-3.4s;animation-duration:8s}"
        "@media (prefers-reduced-motion:reduce){.a,.b,.tw{animation:none}.tw{opacity:.6}}"
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t">
<title id="t">Leandro Guidolin, software developer</title>
<style>{style}</style>
<defs>
<linearGradient id="bg" x2="1" y2="1"><stop stop-color="{t['bg0']}"/><stop offset="1" stop-color="{t['bg1']}"/></linearGradient>
<linearGradient id="fade"><stop offset=".42" stop-color="{t['bg0']}"/><stop offset=".62" stop-color="{t['bg0']}" stop-opacity="0"/></linearGradient>
<radialGradient id="core"><stop stop-color="{t['core']}" stop-opacity=".95"/><stop offset=".3" stop-color="{t['core2']}" stop-opacity=".42"/><stop offset="1" stop-color="{t['core2']}" stop-opacity="0"/></radialGradient>
{arm_grad}
<clipPath id="c"><rect width="{W}" height="{H}" rx="20"/></clipPath>
</defs>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<path stroke="{t['star']}" stroke-width="1.4" stroke-linecap="round" opacity=".45" d="{dots(bg_stars)}"/>
<g stroke="{t['star']}" stroke-linecap="round">{twinkle_svg}</g>
<g transform="translate({CX} {CY}) rotate({TILT}) scale(1 {SQUASH})" fill="none" stroke-linecap="round">
<g class="b">{cloud_svg}{layer(far, 0.34)}</g>
<g class="a">{layer(arms, t['dust_op'])}</g>
<circle r="150" fill="url(#core)"/>
<circle r="17" fill="{t['hole']}"/>
<circle r="19" stroke="{t['ring']}" stroke-width="2.6" opacity=".95"/>
</g>
<rect width="{W}" height="{H}" fill="url(#fade)"/>
<path fill="{t['name']}" d="{name_d}"/>
<path fill="{t['sub']}" d="{sub_d}"/>
</g>
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="19.5" fill="none" stroke="{t['border']}" stroke-width="1.5"/>
</svg>
"""


for mode in THEMES:
    path = OUT / f"banner-{mode}.svg"
    path.write_text(build(mode), encoding="utf-8")
    print(path.name, path.stat().st_size)
