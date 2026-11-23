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
}

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
    box = (176, 0, FRAME - dx, top + 2)
    px = np.array(frame.crop(box))
    cream = (px[..., 0] > 190) & (px[..., 1] > 180) & (px[..., 2] > 140) & (px[..., 3] > 0)
    zz = Image.fromarray(np.where(cream[..., None], px, 0).astype("uint8"), "RGBA")
    frame.paste(Image.fromarray(np.where(cream[..., None], 0, px).astype("uint8"), "RGBA"), box)
    return lambda: frame.alpha_composite(zz, (box[0] + dx, 0))


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

    # the suit: the body's own shading, in navy, but for a slot at the eyes
    px = np.array(frame).astype(float)
    mask = body_mask(a, 32)
    ys, xs = np.mgrid[0:FRAME, 0:FRAME]
    # the body and its ears only: not the flames beside it, nor the desk under the hands
    floor = top + (0.86 if kind == "working" else 1.0) * width
    mask &= (xs > left - 19) & (xs < left + width + 19) & (ys >= top - 2) & (ys <= floor)
    slot = (ys >= top + 0.15 * width) & (ys <= top + 0.55 * width) & (xs >= left + 0.07 * width) & (xs <= left + 0.93 * width)
    suit = mask & ~slot
    lum = px[..., :3].sum(-1) / (212 + 108 + 78)
    for c, v in enumerate((50, 56, 86)):
        px[..., c] = np.where(suit, np.clip(v * lum, 0, 255), px[..., c])
    frame.paste(Image.fromarray(px.astype("uint8"), "RGBA"))

    band = Image.new("RGBA", (int(width) + 8, int(1.25 * cell)), PALETTE["r"] + (255,))
    ImageDraw.Draw(band).rectangle([0, band.height - cell // 3, band.width, band.height], fill=PALETTE["q"] + (255,))
    by = top + 0.15 * width - band.height - 2
    paste(frame, band, left - 4, by)
    tails = grid_layer(TAILS[i % 2], cell - 2)
    paste(frame, tails, left + width + 6, by - 2)


PETS = {"ninja": ninja, "pirate": pirate, "chef": chef}


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
