from io import BytesIO
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

from .template_catalog import TEMPLATES

SIZE = 1080


class ImageRenderError(Exception):
    pass


def get_font(size, bold=False):
    filename = "bold.ttf" if bold else "regular.ttf"
    font_path = Path(settings.BASE_DIR) / "static" / "fonts" / filename

    if font_path.exists():
        return ImageFont.truetype(str(font_path), size=size)

    try:
        return ImageFont.truetype(
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
            size=size,
        )
    except OSError:
        return ImageFont.load_default(size=size)


def wrap_text(draw, text, font, max_width):
    lines = []

    for paragraph in text.splitlines():
        if not paragraph.strip():
            lines.append("")
            continue

        line = ""

        for word in paragraph.split():
            candidate = f"{line} {word}".strip()

            if draw.textlength(candidate, font=font) <= max_width:
                line = candidate
                continue

            if line:
                lines.append(line)
                line = ""

            # Split words that are wider than the available space.
            for character in word:
                if (
                    line
                    and draw.textlength(line + character, font=font)
                    > max_width
                ):
                    lines.append(line)
                    line = character
                else:
                    line += character

        if line:
            lines.append(line)

    return "\n".join(lines)


def draw_fitted_text(
    draw, text, box, fill, max_size, min_size=14, bold=False
):
    if not text:
        return

    left, top, right, bottom = box
    max_width = right - left
    max_height = bottom - top

    for size in range(max_size, min_size - 1, -2):
        font = get_font(size, bold=bold)
        wrapped = wrap_text(draw, text, font, max_width)
        spacing = max(4, size // 5)

        bounds = draw.multiline_textbbox(
            (0, 0),
            wrapped,
            font=font,
            spacing=spacing,
        )

        if (
            bounds[2] - bounds[0] <= max_width
            and bounds[3] - bounds[1] <= max_height
        ):
            draw.multiline_text(
                (left - bounds[0], top - bounds[1]),
                wrapped,
                font=font,
                fill=fill,
                spacing=spacing,
            )
            return

    raise ImageRenderError(
        "This text is too long for the image. Try a shorter message."
    )


def contrasting_color(color):
    color = color.lstrip("#")
    red, green, blue = (
        int(color[index:index + 2], 16) for index in (0, 2, 4)
    )
    brightness = 0.299 * red + 0.587 * green + 0.114 * blue
    return "#171717" if brightness > 155 else "#FFFFFF"


def paste_logo(canvas, brand):
    if not brand.logo:
        return

    with brand.logo.open("rb") as logo_file:
        with Image.open(logo_file) as source:
            logo = ImageOps.exif_transpose(source).convert("RGBA")
            logo.thumbnail((120, 120), Image.Resampling.LANCZOS)

    canvas.paste(logo, (880, 70), logo)


def template_background(spec, brand, custom_color=""):
    if custom_color:
        return custom_color

    return {
        "brand": brand.primary_color,
        "paper": "#F1EBDF",
        "dark": "#171A17",
        "jungle": "#173D2A",
    }[spec["theme"]]


def draw_jungle(draw):
    # Decorative leaves around the edges.
    leaf_colors = ["#285A39", "#397547", "#608C48"]

    for index in range(12):
        y = index * 95 - 20
        color = leaf_colors[index % len(leaf_colors)]

        draw.ellipse((-55, y, 85, y + 150), fill=color)
        draw.line((0, y + 130, 70, y + 25), fill="#A0B76C", width=2)

        draw.ellipse((995, y + 30, 1135, y + 180), fill=color)
        draw.line(
            (1010, y + 55, 1080, y + 165),
            fill="#A0B76C",
            width=2,
        )


def open_fitted_photo(source, size):
    source.seek(0)

    with Image.open(source) as original:
        photo = ImageOps.exif_transpose(original).convert("RGB")
        return ImageOps.fit(
            photo,
            size,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )


def render_post(
    template,
    brand,
    headline,
    body_text,
    photos=None,
    background_color="",
    text_color="",
    preview=False,
):
    spec = TEMPLATES.get(template.layout)

    if spec is None:
        raise ImageRenderError("Choose one of the new photo templates.")

    photos = photos or []
    required_count = len(spec["slots"])

    if not preview and len(photos) != required_count:
        raise ImageRenderError(
            f"This template needs {required_count} photos."
        )

    background = template_background(spec, brand, background_color)
    foreground = text_color or contrasting_color(background)

    canvas = Image.new("RGB", (SIZE, SIZE), background)
    draw = ImageDraw.Draw(canvas)

    if spec["theme"] == "jungle":
        draw_jungle(draw)

    for index, (x, y, width, height) in enumerate(spec["slots"]):
        # A visible paper border around each photo.
        if not spec.get("circle"):
            draw.rectangle(
                (x - 8, y - 8, x + width + 8, y + height + 8),
                fill="#FAF7EF",
            )

        if preview:
            photo = Image.new(
                "RGB",
                (width, height),
                ["#A8B69D", "#D1C2A8", "#81998A", "#B6A997"][index % 4],
            )
            photo_draw = ImageDraw.Draw(photo)
            photo_draw.ellipse(
                (
                    width * 0.15,
                    height * 0.1,
                    width * 0.85,
                    height * 0.8,
                ),
                fill="#E7E3D4",
            )
            photo_draw.polygon(
                [
                    (0, height),
                    (width * 0.5, height * 0.4),
                    (width, height),
                ],
                fill="#566F5B",
            )
        else:
            photo = open_fitted_photo(
                photos[index],
                (width, height),
            )

        if spec.get("circle"):
            mask = Image.new("L", (width, height), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, width - 1, height - 1), fill=255)
            mask = mask.filter(ImageFilter.GaussianBlur(0.5))
            canvas.paste(photo, (x, y), mask)
        else:
            canvas.paste(photo, (x, y))

    draw_fitted_text(
        draw,
        headline,
        spec["headline"],
        foreground,
        max_size=88,
        min_size=12,
        bold=True,
    )

    draw_fitted_text(
        draw,
        body_text,
        spec["body"],
        foreground,
        max_size=32,
        min_size=10,
    )

    # These photo layouts use the brand colors and voice.
    # They reserve their space for photos and text rather than a logo.

    output = BytesIO()

    if preview:
        canvas.thumbnail((360, 360), Image.Resampling.LANCZOS)

    canvas.save(output, format="PNG")

    return ContentFile(
        output.getvalue(),
        name=f"{uuid4().hex}.png",
    )