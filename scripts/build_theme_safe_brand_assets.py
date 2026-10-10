"""Put the dark-theme brand artwork on fixed navy tiles for both UI themes."""

from pathlib import Path

from PIL import Image, ImageDraw


VISUAL_IDENTITY = Path(__file__).resolve().parents[1] / "app" / "visual_identity"
ASSETS = (
    ("transferlens_mark_dark_512_cropped.png", "transferlens_mark_universal.png"),
    (
        "transferlens_wordmark_dark_1200x300_cropped.png",
        "transferlens_wordmark_universal.png",
    ),
)


def main() -> None:
    for source_name, output_name in ASSETS:
        with Image.open(VISUAL_IDENTITY / source_name) as source:
            artwork = source.convert("RGBA")

        tile = Image.new("RGBA", artwork.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(tile)
        width, height = tile.size
        draw.rounded_rectangle(
            (1, 1, width - 2, height - 2),
            radius=min(width, height) // 7,
            fill="#0B1320",
            outline="#278965",
            width=2,
        )
        tile.alpha_composite(artwork)
        tile.save(VISUAL_IDENTITY / output_name, optimize=True)


if __name__ == "__main__":
    main()
