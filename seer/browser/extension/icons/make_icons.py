"""Generate seer extension icons. Run once: python make_icons.py"""
from PIL import Image, ImageDraw
from pathlib import Path


def render(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Background circle (deep blue-gray)
    pad = max(1, size // 16)
    d.ellipse((pad, pad, size - pad, size - pad), fill=(28, 33, 51, 255))
    # Eye outer (white ring)
    inset = size // 5
    d.ellipse(
        (inset, inset + size // 8, size - inset, size - inset - size // 8),
        outline=(245, 245, 250, 255),
        width=max(1, size // 32),
    )
    # Pupil (green — connected state)
    pup = size // 4
    cx = size // 2
    cy = size // 2
    d.ellipse((cx - pup // 2, cy - pup // 2, cx + pup // 2, cy + pup // 2), fill=(60, 200, 90, 255))
    return img


def main() -> None:
    out = Path(__file__).resolve().parent
    for sz in (16, 48, 128):
        render(sz).save(out / f"icon-{sz}.png", "PNG", optimize=True)
        print(f"wrote icon-{sz}.png")


if __name__ == "__main__":
    main()
