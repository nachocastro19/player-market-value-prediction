"""Create tightly cropped, SVG-conversion-ready TransferLens PNG assets."""

from pathlib import Path

from PIL import Image


ASSET_DIR = Path(__file__).resolve().parents[1] / "app" / "visual_identity"
PADDING_PX = 32


def crop_asset(source: Path) -> Path:
    """Crop transparent margins without resampling or changing artwork pixels."""
    with Image.open(source) as opened:
        image = opened.convert("RGBA")
        bounds = image.getchannel("A").getbbox()
        if bounds is None:
            raise ValueError(f"Asset has no visible pixels: {source}")

        artwork = image.crop(bounds)
        artwork_width, artwork_height = artwork.size

        if "_mark_" in source.name:
            canvas_width = canvas_height = max(artwork.size) + (2 * PADDING_PX)
        else:
            canvas_width = artwork_width + (2 * PADDING_PX)
            canvas_height = artwork_height + (2 * PADDING_PX)

        canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
        offset = (
            (canvas_width - artwork_width) // 2,
            (canvas_height - artwork_height) // 2,
        )
        canvas.alpha_composite(artwork, offset)

        destination = source.with_name(f"{source.stem}_cropped.png")
        canvas.save(destination, format="PNG", optimize=True)
        return destination


def main() -> None:
    sources = sorted(
        path
        for path in ASSET_DIR.glob("transferlens_*.png")
        if not path.stem.endswith("_cropped") and not path.stem.endswith("_universal")
    )
    for source in sources:
        destination = crop_asset(source)
        with Image.open(destination) as result:
            print(f"{source.name} -> {destination.name} {result.size}")


if __name__ == "__main__":
    main()
