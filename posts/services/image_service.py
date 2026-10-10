from io import BytesIO
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont, ImageOps


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


def render_post(template, brand, headline, body_text):
    primary = brand.primary_color
    secondary = brand.secondary_color

    if template.layout == "bold":
        canvas = Image.new("RGB", (SIZE, SIZE), primary)
        draw = ImageDraw.Draw(canvas)
        foreground = contrasting_color(primary)

        draw_fitted_text(
            draw, brand.name.upper(),
            (80, 85, 820, 145),
            foreground, 30, bold=True,
        )
        draw.line((80, 210, 1000, 210), fill=foreground, width=2)

        draw_fitted_text(
            draw, headline,
            (80, 280, 1000, 660),
            foreground, 108, bold=True,
        )
        draw_fitted_text(
            draw, body_text,
            (80, 710, 1000, 915),
            foreground, 38,
        )

        draw.rectangle((80, 980, 1000, 992), fill=secondary)

    elif template.layout == "minimal":
        canvas = Image.new("RGB", (SIZE, SIZE), secondary)
        draw = ImageDraw.Draw(canvas)
        foreground = contrasting_color(secondary)

        draw.rectangle((0, 0, 24, SIZE), fill=primary)

        draw_fitted_text(
            draw, brand.name.upper(),
            (85, 85, 820, 145),
            foreground, 30, bold=True,
        )
        draw.rectangle((85, 235, 185, 245), fill=primary)

        draw_fitted_text(
            draw, headline,
            (85, 300, 995, 670),
            foreground, 92, bold=True,
        )
        draw_fitted_text(
            draw, body_text,
            (85, 720, 995, 925),
            foreground, 36,
        )

        draw.line((85, 985, 995, 985), fill=foreground, width=2)

    else:
        raise ImageRenderError("This template layout is not supported.")

    paste_logo(canvas, brand)

    output = BytesIO()
    canvas.save(output, format="PNG")

    return ContentFile(
        output.getvalue(),
        name=f"{uuid4().hex}.png",
    )