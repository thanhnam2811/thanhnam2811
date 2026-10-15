#!/usr/bin/env python3
"""Build the profile README images (banner, project cards, stack strip) as static SVGs.

All text is converted to <path> outlines, so the images render identically on GitHub
without embedded or external fonts. Edit CONTENT / THEMES below and re-run:

    python3 scripts/build_assets.py --fonts DIR --icons DIR [--out assets]

DIR for --fonts must contain SpaceGrotesk.ttf (variable), JetBrainsMono-Regular.ttf and
JetBrainsMono-Bold.ttf. DIR for --icons holds simple-icons SVGs named after CONTENT["stack"]
slugs (https://github.com/simple-icons/simple-icons, CC0). Requires fontTools.
"""
import argparse
import re
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

THEMES = {
    "light": dict(bg="#FAFAF9", fg="#0C0A09", muted="#57534E", line="#E7E5E4", accent="#4D7C0F", dot="#D6D3D1"),
    "dark": dict(bg="#0D1117", fg="#F0F6FC", muted="#8B949E", line="#30363D", accent="#A3E635", dot="#30363D"),
}

CONTENT = {
    "label": "GAME SERVER DEVELOPER  ·  ONKY STUDIO",
    "name": "Thái Thành Nam",
    "tagline": "Real-time game backends in Node.js & TypeScript",
    "cards": [
        ("matching-man",
         "Matchmaking-as-a-service for game servers. Multi-tenant queues, Elo ratings, HMAC-signed webhook delivery.",
         "NestJS · Next.js · Prisma · PostgreSQL"),
        ("gapafo",
         "Multi-tenant backend for reusable game services. Decisions recorded as ADRs, every phase ends with executable evidence.",
         "Fastify · PostgreSQL · TypeScript"),
        ("tiny-link",
         "Production-grade URL shortener with click analytics and CI/CD to production.",
         "Fastify · Next.js · Redis · PostgreSQL"),
        ("namtt.dev",
         "Localized portfolio with scroll-driven animation.",
         "Next.js · TailwindCSS · GSAP"),
    ],
    # (simple-icons slug, label)
    "stack": [
        ("nodedotjs", "Node.js"), ("typescript", "TypeScript"), ("nestjs", "NestJS"), ("fastify", "Fastify"),
        ("socketdotio", "Socket.IO"), ("postgresql", "PostgreSQL"), ("redis", "Redis"), ("prisma", "Prisma"),
        ("docker", "Docker"), ("githubactions", "Actions"), ("nextdotjs", "Next.js"), ("react", "React"),
    ],
}


def fmt(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


class Face:
    def __init__(self, font):
        self.font = font
        self.gs = font.getGlyphSet()
        self.cmap = font.getBestCmap()
        self.upm = font["head"].unitsPerEm
        self.hmtx = font["hmtx"]

    def glyph(self, ch):
        name = self.cmap.get(ord(ch))
        if name is None:
            raise SystemExit(f"glyph missing for {ch!r} (U+{ord(ch):04X})")
        return name

    def width(self, text, size, tracking=0.0):
        s = size / self.upm
        return sum(self.hmtx[self.glyph(c)][0] * s + tracking for c in text) - (tracking if text else 0)

    def path(self, text, x, y, size, anchor="start", tracking=0.0):
        w = self.width(text, size, tracking)
        if anchor == "end":
            x -= w
        elif anchor == "middle":
            x -= w / 2
        s = size / self.upm
        parts = []
        for c in text:
            g = self.glyph(c)
            pen = SVGPathPen(self.gs, ntos=fmt)
            self.gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x, y)))
            d = pen.getCommands()
            if d:
                parts.append(d)
            x += self.hmtx[g][0] * s + tracking
        return "".join(parts)

    def wrap(self, text, size, max_w):
        lines, cur = [], ""
        for word in text.split():
            trial = f"{cur} {word}".strip()
            if cur and self.width(trial, size) > max_w:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        return lines + [cur]


def load_faces(fonts_dir):
    def var(w):
        return Face(instancer.instantiateVariableFont(TTFont(fonts_dir / "SpaceGrotesk.ttf"), {"wght": w}))
    return dict(
        grot_bold=var(700), grot_reg=var(450),
        mono=Face(TTFont(fonts_dir / "JetBrainsMono-Regular.ttf")),
        mono_bold=Face(TTFont(fonts_dir / "JetBrainsMono-Bold.ttf")),
    )


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img">{body}</svg>\n')


def frame(w, h, c, r=14):
    return f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{r}" fill="{c["bg"]}" stroke="{c["line"]}"/>'


def banner(f, c):
    W, H = 1200, 300
    out = [frame(W, H, c, 16)]
    # dot grid fading to the left, with a hole for the mark
    mx, my, ms = 960, 96, 108
    for gx in range(30):
        for gy in range(11):
            x, y = 720 + gx * 16, 36 + gy * 24
            if x > W - 28 or (mx - 20 <= x <= mx + ms + 20 and my - 20 <= y <= my + ms + 20):
                continue
            op = ((x - 720) / 480) ** 1.5 * 0.9
            if op > 0.04:
                out.append(f'<circle cx="{x}" cy="{y}" r="1.6" fill="{c["dot"]}" opacity="{op:.2f}"/>')
    # mark: a square split on the diagonal (accent / outline)
    out.append(f'<polygon points="{mx + ms},{my} {mx + ms},{my + ms} {mx},{my + ms}" fill="{c["accent"]}"/>')
    out.append(f'<polygon points="{mx},{my + ms - 14} {mx},{my} {mx + ms - 14},{my}" fill="none" '
               f'stroke="{c["fg"]}" stroke-width="2" stroke-linejoin="round"/>')
    out.append(f'<path d="{f["mono_bold"].path(CONTENT["label"], 72, 92, 14, tracking=1.6)}" fill="{c["accent"]}"/>')
    out.append(f'<path d="{f["grot_bold"].path(CONTENT["name"], 68, 184, 82, tracking=-2)}" fill="{c["fg"]}"/>')
    out.append(f'<path d="{f["grot_reg"].path(CONTENT["tagline"], 72, 238, 25)}" fill="{c["muted"]}"/>')
    return svg(W, H, "".join(out))


def card(f, c, title, desc, chips):
    W, H = 600, 190
    out = [frame(W, H, c, 12)]
    out.append(f'<rect x="32" y="30" width="24" height="3" rx="1.5" fill="{c["accent"]}"/>')
    out.append(f'<path d="{f["mono_bold"].path(title, 32, 66, 21)}" fill="{c["fg"]}"/>')
    # arrow (up-right), drawn as strokes so it needs no glyph
    ax, ay = 556, 48
    out.append(f'<path d="M{ax} {ay + 12}L{ax + 12} {ay}M{ax + 1} {ay}H{ax + 12}V{ay + 11}" fill="none" '
               f'stroke="{c["muted"]}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
    lines = f["grot_reg"].wrap(desc, 16, W - 64)
    assert len(lines) <= 3, f"description too long for {title}"
    for i, line in enumerate(lines):
        out.append(f'<path d="{f["grot_reg"].path(line, 32, 98 + i * 23, 16)}" fill="{c["muted"]}"/>')
    out.append(f'<path d="{f["mono"].path(chips, 32, H - 28, 12.5, tracking=0.2)}" fill="{c["fg"]}" opacity=".78"/>')
    # transparent margin so adjacent cards never touch
    return svg(W + 20, H + 20, f'<g transform="translate(10 10)">{"".join(out)}</g>')


def icon_d(icons_dir, slug):
    m = re.search(r'<path d="([^"]+)"', (icons_dir / f"{slug}.svg").read_text())
    if not m:
        raise SystemExit(f"no path in {slug}.svg")
    return m.group(1)


def stack(f, c, icons_dir):
    cell, n = 100, len(CONTENT["stack"])
    W, H = 1200, 132
    x0 = (W - cell * n) / 2
    out = [frame(W, H, c, 14)]
    for i, (slug, label) in enumerate(CONTENT["stack"]):
        cx = x0 + i * cell + cell / 2
        s = 34 / 24
        out.append(f'<path transform="translate({fmt(cx - 17)} 30) scale({fmt(s)})" d="{icon_d(icons_dir, slug)}" fill="{c["fg"]}"/>')
        out.append(f'<path d="{f["mono"].path(label, cx, 100, 11.5, "middle")}" fill="{c["muted"]}"/>')
    return svg(W, H, "".join(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", type=Path, required=True)
    ap.add_argument("--icons", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "assets")
    a = ap.parse_args()
    a.out.mkdir(exist_ok=True)
    f = load_faces(a.fonts)
    for theme, c in THEMES.items():
        files = {f"banner-{theme}.svg": banner(f, c), f"stack-{theme}.svg": stack(f, c, a.icons)}
        for title, desc, chips in CONTENT["cards"]:
            files[f"card-{title.replace('.', '-')}-{theme}.svg"] = card(f, c, title, desc, chips)
        for name, data in files.items():
            (a.out / name).write_text(data)
    print(f"wrote {len(list(a.out.glob('*.svg')))} files to {a.out}")


if __name__ == "__main__":
    main()
