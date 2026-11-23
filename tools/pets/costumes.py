#!/usr/bin/env python3
"""Costumed pets made by compositing onto the classic Clauddy sheets.

Reads native/assets/{working,moods}-sheet.png, finds the body in each frame,
draws a costume in chunky pixels with the sprite's dark outline, and writes
native/assets/<id>-{working,moods}.png. Prints each pet's boxes for skins.rs.

    python3 tools/pets/costumes.py            # needs Pillow and numpy
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ASSETS = Path(__file__).resolve().parents[2] / "native" / "assets"
FRAME = 256
OUTLINE = (24, 8, 8, 255)

# (file, cols, rows, cell size in px, head centre x, head width)
SHEETS = {
    "working": ("working-sheet.png", 4, 2, 7, 112.5, 105),
    "moods": ("moods-sheet.png", 4, 4, 8, 130.5, 123),
}

PALETTE = {
    "w": (246, 241, 232),  # toque
    "s": (200, 190, 182),
    "b": (232, 225, 214),
    "d": (186, 176, 168),
    "k": (60, 54, 70),  # pirate hat
    "j": (40, 36, 48),
    "g": (232, 182, 62),
    "W": (240, 236, 226),  # skull
    "o": (176, 120, 66),  # spoon
    "p": (140, 92, 50),
    "r": (206, 52, 52),  # headband
    "q": (160, 36, 40),
    "m": (196, 204, 218),  # mirror, wrench
    "M": (242, 246, 252),
    "n": (176, 184, 198),
    "N": (92, 98, 114),
    "y": (246, 196, 40),  # hard hat
    "Y": (255, 228, 112),
    "h": (206, 150, 24),
    "e": (24, 120, 90),  # helmet
    "E": (244, 244, 244),
    "f": (150, 150, 162),  # flag pole
}

HELMET = PALETTE["e"]

TOQUE = [
    "..www..wwww..www..",
    ".wwwwwwwwwwwwwwww.",
    "wwwwwwwwwwwwwwwwws",
    "wwwwwwwwwwwwwwwwss",
    ".wwwwswwwwswwwwss.",
    "...wwswwwwswwwss..",
    "...bbbbbbbbbbbb...",
    "...dddddddddddd...",
]

# drawn at a finer cell than the hats
SPOON = [
    ".ooo.",
    "ooooo",
    "oppoo",
    "oppoo",
    "ooooo",
    ".ooo.",
    "..o..",
    "..o..",
    "..o..",
    "..o..",
    "..o..",
    "..p..",
]

TRICORN = [
    "......kkkkkk......",
    "....kkkkWWWkkk....",
    "...kkkkWjWjWkkk...",
    "...kkkkkWWWkkkj...",
    "..kkkkkkWkWkkkjj..",
    "kggggggggggggggggk",
    ".kkkkkkkkkkkkkkjj.",
]

MIRROR = [
    ".mmm.",
    "mmMmm",
    "mMMmm",
    "mmmmm",
    ".mmm.",
]

HARD_HAT = [
    "......yyyyyy......",
    "....yyyyYYyyyy....",
    "...yyyyyYYyyyyy...",
    "...yyyyyYYyyyyh...",
    "...yyyyyYYyyyhh...",
    "yyyyyyyyyyyyyyyyhh",
]

WRENCH = [
    "n...n",
    "n...n",
    "nn.nn",
    ".nnn.",
    "..n..",
    "..n..",
    "..n..",
    "..n..",
    "..n..",
    ".nNn.",
    ".nnn.",
]

DOME = [
    "...eeeeEEeeee...",
    ".eeeeeeEEeeeeee.",
    "eeeeeeeEEeeeeeee",
]

# flying away from the body, its pole on the right
FLAG = [
    "EjEjEjf",
    "jEjEjEf",
    "EjEjEjf",
    "jEjEjEf",
    "......f",
    "......f",
    "......f",
    "......f",
    "......f",
    "......f",
]

# the knot and its tails, in two poses so they flutter
TAILS = [
    ["rr....", "rrrrr.", "rr.qrr", "rrq..."],
    ["rr....", "rrrr..", "rrqrrr", "rr..qr"],
]


def grid_layer(grid, cell):
    """A grid of palette letters as an RGBA image, one cell per letter."""
    h, w = len(grid), max(len(r) for r in grid)
    im = Image.new("RGBA", (w * cell, h * cell), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch in PALETTE:
                d.rectangle([x * cell, y * cell, (x + 1) * cell - 1, (y + 1) * cell - 1], fill=PALETTE[ch] + (255,))
    return im


def outlined(layer, px=4):
    """The layer with the sprite's dark outline around it."""
    pad = Image.new("RGBA", (layer.width + 2 * px, layer.height + 2 * px), (0, 0, 0, 0))
    pad.alpha_composite(layer, (px, px))
    grown = pad.getchannel("A").filter(ImageFilter.MaxFilter(2 * px + 1))
    out = Image.new("RGBA", pad.size, OUTLINE)
    out.putalpha(grown)
    out.alpha_composite(pad)
    return out, px


def paste(frame, layer, x, y):
    art, px = outlined(layer)
    frame.alpha_composite(art, (int(round(x)) - px, int(round(y)) - px))


def body_mask(a, tol=28):
    r, g, b, al = (a[..., i].astype(int) for i in range(4))
    return (al > 200) & (abs(r - 212) < tol) & (abs(g - 108) < tol) & (abs(b - 78) < tol)


def head_top(a):
    rows = np.where(body_mask(a).sum(1) >= 40)[0]
    return int(rows[0])


def lift_zz(frame, kind, i, top, dx):
    """Take the sleeping row's zz out of a hat's way: cut here, put back `dx` to the right."""
    if kind != "moods" or not 4 <= i < 8:
        return None
    px = np.array(frame)
    region = np.zeros((FRAME, FRAME), bool)
    region[: top + 2, 176 : FRAME - dx] = True
    cream = region & (px[..., 0] > 190) & (px[..., 1] > 180) & (px[..., 2] > 140) & (px[..., 3] > 0)
    ys, xs = np.where(cream)
    # the letters with their dark edge, but not the head's own outline under them
    lift = np.zeros_like(cream)
    lift[max(ys.min() - 3, 0) : ys.max() + 4, max(xs.min() - 3, 176) : min(xs.max() + 4, FRAME - dx)] = True
    yy, xx = np.mgrid[0:FRAME, 0:FRAME]
    lift &= cream | (yy < top - 7) | (xx > 198)
    zz = Image.fromarray(np.where(lift[..., None], px, 0).astype("uint8"), "RGBA")
    frame.paste(Image.fromarray(np.where(lift[..., None], 0, px).astype("uint8"), "RGBA"))
    return lambda: frame.alpha_composite(zz, (dx, 0))


def eye_slot(xs, ys, left, width, top):
    return (ys >= top + 0.15 * width) & (ys <= top + 0.55 * width) & (xs >= left + 0.07 * width) & (xs <= left + 0.93 * width)


def dye(frame, a, kind, left, width, top, rgb, where):
    """Recolour the body where `where(xs, ys)` holds, keeping its own shading."""
    px = np.array(frame).astype(float)
    ys, xs = np.mgrid[0:FRAME, 0:FRAME]
    # the body and its ears only: not the flames beside it, nor the desk under the hands
    floor = top + (0.86 if kind == "working" else 1.0) * width
    mask = body_mask(a, 32) & (xs > left - 19) & (xs < left + width + 19) & (ys >= top - 2) & (ys <= floor)
    mask &= where(xs, ys)
    lum = a[..., :3].astype(float).sum(-1) / (212 + 108 + 78)  # the original's, so dyes can overlap
    for c, v in enumerate(rgb):
        px[..., c] = np.where(mask, np.clip(v * lum, 0, 255), px[..., c])
    frame.paste(Image.fromarray(px.astype("uint8"), "RGBA"))


def chef(frame, a, kind, i, cell, cx, width, top):
    zz = lift_zz(frame, kind, i, top, 22)
    hat = grid_layer(TOQUE, cell)
    paste(frame, hat, cx - hat.width / 2, top + 6 - hat.height)
    if kind == "moods":
        spoon = grid_layer(SPOON, 5)
        paste(frame, spoon, cx - width / 2 - 49, top + 30)
    if zz:
        zz()


def pirate(frame, a, kind, i, cell, cx, width, top):
    left = cx - width / 2
    zz = lift_zz(frame, kind, i, top, 22)
    d = ImageDraw.Draw(frame)
    eye_x, eye_y = left + 0.335 * width, top + 0.33 * width
    # the strap, from under the hat on one side to the other
    d.line([left + 2, top + 0.30 * width, left + width - 2, top + 0.10 * width], fill=OUTLINE, width=cell // 2 + 1)
    half = 0.105 * width
    d.rectangle([eye_x - half, eye_y - 1.35 * half, eye_x + half, eye_y + 1.5 * half], fill=OUTLINE)
    hat = grid_layer(TRICORN, cell)
    paste(frame, hat, cx - hat.width / 2, top + 6 - hat.height)
    if zz:
        zz()


def ninja(frame, a, kind, i, cell, cx, width, top):
    left = cx - width / 2
    # a sword on the back: drawn, then the original art put back over it
    back = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(back)
    x0, y0, x1, y1 = left + 34, top + 30, left - 22, top - 50
    d.line([x0, y0, x1, y1], fill=OUTLINE, width=cell + 12)
    d.line([x0, y0, x1, y1], fill=(96, 100, 128, 255), width=cell + 4)
    for k in (0.2, 0.45, 0.7):  # the grip's wrap
        wx, wy = x1 + (x0 - x1) * k * 0.6, y1 + (y0 - y1) * k * 0.6
        d.line([wx - 6, wy - 4, wx + 6, wy + 4], fill=(52, 54, 76, 255), width=3)
    d.ellipse([x1 - 8, y1 - 8, x1 + 8, y1 + 8], fill=OUTLINE)
    d.ellipse([x1 - 4, y1 - 4, x1 + 4, y1 + 4], fill=PALETTE["g"] + (255,))
    gx, gy = left + 1, top - 15
    d.line([gx - 17, gy - 12, gx + 17, gy + 12], fill=OUTLINE, width=cell + 8)
    d.line([gx - 14, gy - 10, gx + 14, gy + 10], fill=PALETTE["g"] + (255,), width=cell)
    back.alpha_composite(frame)
    frame.paste(back)

    # the suit, but for a slot at the eyes
    dye(frame, a, kind, left, width, top, (50, 56, 86), lambda xs, ys: ~eye_slot(xs, ys, left, width, top))

    band = Image.new("RGBA", (int(width) + 8, int(1.25 * cell)), PALETTE["r"] + (255,))
    ImageDraw.Draw(band).rectangle([0, band.height - cell // 3, band.width, band.height], fill=PALETTE["q"] + (255,))
    by = top + 0.15 * width - band.height - 2
    paste(frame, band, left - 4, by)
    tails = grid_layer(TAILS[i % 2], cell - 2)
    paste(frame, tails, left + width + 6, by - 2)


def doctor(frame, a, kind, i, cell, cx, width, top):
    left = cx - width / 2
    # the white coat, from under the eyes down
    dye(frame, a, kind, left, width, top, (244, 244, 248), lambda xs, ys: ys > top + 0.6 * width)
    if kind == "moods":
        d = ImageDraw.Draw(frame)
        tube, y0, y1 = (58, 62, 80, 255), top + 0.6 * width, top + 0.78 * width
        d.line([left + 0.3 * width, y0, cx, y1], fill=tube, width=5)
        d.line([left + 0.7 * width, y0, cx, y1], fill=tube, width=5)
        d.ellipse([cx - 9, y1 - 5, cx + 9, y1 + 13], fill=OUTLINE)
        d.ellipse([cx - 5, y1 - 1, cx + 5, y1 + 9], fill=PALETTE["m"] + (255,))
        x, y, u = left + 0.14 * width, top + 0.66 * width, 4  # a red cross on the coat
        d.rectangle([x + u, y, x + 2 * u - 1, y + 3 * u - 1], fill=PALETTE["r"] + (255,))
        d.rectangle([x, y + u, x + 3 * u - 1, y + 2 * u - 1], fill=PALETTE["r"] + (255,))
    # the head mirror on its strap
    strap = Image.new("RGBA", (int(width) + 8, cell), (84, 90, 108, 255))
    paste(frame, strap, left - 4, top + 0.15 * width - cell - 4)
    mirror = grid_layer(MIRROR, cell - 2)
    paste(frame, mirror, cx - mirror.width / 2, top + 0.15 * width - cell - mirror.height + 6)


def engineer(frame, a, kind, i, cell, cx, width, top):
    zz = lift_zz(frame, kind, i, top, 22)
    hat = grid_layer(HARD_HAT, cell)
    paste(frame, hat, cx - hat.width / 2, top + 8 - hat.height)
    if kind == "moods":
        wrench = grid_layer(WRENCH, 5)
        paste(frame, wrench, cx - width / 2 - 49, top + 30)
    if zz:
        zz()


def driver(frame, a, kind, i, cell, cx, width, top):
    left = cx - width / 2
    # the helmet and the suit, open at the eyes, with a stripe over the top
    dye(frame, a, kind, left, width, top, HELMET, lambda xs, ys: ~eye_slot(xs, ys, left, width, top))
    dye(frame, a, kind, left, width, top, (244, 244, 244), lambda xs, ys: (abs(xs - cx) < cell) & (ys < top + 0.15 * width))
    dome = grid_layer(DOME, cell)
    paste(frame, dome, cx - dome.width / 2, top + 6 - dome.height)
    if kind == "moods":
        flag = grid_layer(FLAG, 5)
        paste(frame, flag, left - 26 - flag.width, top + 6)


PETS = {"ninja": ninja, "pirate": pirate, "chef": chef, "doctor": doctor, "engineer": engineer, "driver": driver}


def bbox(frames):
    """The opaque box of several frames together, as fractions of a frame."""
    boxes = [f.getchannel("A").point(lambda v: 255 if v > 30 else 0).getbbox() for f in frames]
    l, t = min(b[0] for b in boxes), min(b[1] for b in boxes)
    r, b = max(b[2] for b in boxes), max(b[3] for b in boxes)
    return [round(v / FRAME, 3) for v in (l, t, r, b)]


def build(pet, draw):
    boxes = {}
    for kind, (name, cols, rows, cell, cx, width) in SHEETS.items():
        src = Image.open(ASSETS / name).convert("RGBA")
        out = Image.new("RGBA", src.size, (0, 0, 0, 0))
        frames = []
        for i in range(cols * rows):
            x, y = (i % cols) * FRAME, (i // cols) * FRAME
            frame = src.crop((x, y, x + FRAME, y + FRAME))
            a = np.array(frame)
            draw(frame, a, kind, i, cell, cx, width, head_top(a))
            out.paste(frame, (x, y))
            frames.append(frame)
        out.save(ASSETS / f"{pet}-{kind}.png", optimize=True)
        if kind == "working":
            boxes["work_box"] = bbox(frames)
        else:
            boxes["fire_box"] = bbox(frames[8:12])
            boxes["stand_box"] = bbox(frames[0:4])
    return boxes


if __name__ == "__main__":
    for pet, draw in PETS.items():
        print(pet, build(pet, draw))
