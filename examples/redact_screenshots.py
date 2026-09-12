#!/usr/bin/env python3
"""Create deterministic public-demo screenshots with full-person privacy overlays.

The source screenshots stay outside the public repository. This helper accepts
one or more manually selected person boxes and covers each box with an opaque,
abstract avatar. It never attempts face detection or reconstruction.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PALETTE = ((22, 39, 35), (205, 183, 104), (120, 164, 151))


def parse_box(value: str) -> tuple[int, int, int, int]:
    try:
        box = tuple(int(part) for part in value.split(","))
    except ValueError as error:
        raise argparse.ArgumentTypeError("box must be x1,y1,x2,y2") from error
    if len(box) != 4 or box[2] <= box[0] or box[3] <= box[1]:
        raise argparse.ArgumentTypeError("box must be x1,y1,x2,y2 with positive size")
    return box  # type: ignore[return-value]


def draw_avatar(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], number: int) -> None:
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    margin = max(4, min(width, height) // 16)
    color = PALETTE[(number - 1) % len(PALETTE)]
    accent = PALETTE[number % len(PALETTE)]

    # A large opaque geometric privacy avatar: no face details and no circle mask.
    draw.rounded_rectangle((x1, y1, x2, y2), radius=margin * 2, fill=color)
    head_w, head_h = int(width * 0.32), int(height * 0.28)
    head_x = x1 + (width - head_w) // 2
    head_y = y1 + int(height * 0.10)
    draw.rectangle((head_x, head_y, head_x + head_w, head_y + head_h), fill=accent)

    body_top = head_y + head_h + margin
    body_left = x1 + int(width * 0.19)
    body_right = x2 - int(width * 0.19)
    body_bottom = y2 - int(height * 0.10)
    draw.polygon(
        ((body_left, body_top), (body_right, body_top),
         (x2 - int(width * 0.08), body_bottom),
         (x1 + int(width * 0.08), body_bottom)),
        fill=accent,
    )

    line_w = max(2, min(width, height) // 35)
    draw.line((x1 + int(width * 0.12), y1 + int(height * 0.70),
               x2 - int(width * 0.12), y1 + int(height * 0.70)),
              fill=PALETTE[0], width=line_w)
    draw.line((x1 + int(width * 0.18), y1 + int(height * 0.82),
               x2 - int(width * 0.18), y1 + int(height * 0.82)),
              fill=PALETTE[0], width=line_w)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--box", action="append", required=True, type=parse_box,
                        help="opaque person-cover box: x1,y1,x2,y2; repeat for each person")
    parser.add_argument("--label-box", action="append", default=[], type=parse_box,
                        help="optional speaker-label box to anonymize; repeat as needed")
    args = parser.parse_args()

    image = Image.open(args.input).convert("RGB")
    draw = ImageDraw.Draw(image)
    for number, box in enumerate(args.box, 1):
        draw_avatar(draw, box, number)
    for number, box in enumerate(args.label_box, 1):
        x1, y1, x2, y2 = box
        draw.rectangle(box, fill=PALETTE[0])
        draw.text((x1 + 4, y1 + 2), f"DEMO {number}", fill=(232, 238, 230),
                  font=ImageFont.load_default())

    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output, quality=94, optimize=True)
    print(f"wrote {args.output} ({image.width}x{image.height})")


if __name__ == "__main__":
    main()
