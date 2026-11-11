import base64
import io
import random

from PIL import Image, ImageDraw, ImageFont

from visionjailbreak.models import GeneratedImagePayload, PerturbationType


def generate_typographic_image(
    text: str,
    perturbation: PerturbationType = PerturbationType.PLAIN_TYPOGRAPHIC,
    width: int = 512,
    height: int = 256,
) -> GeneratedImagePayload:
    """Renders synthetic typographic adversarial images using Pillow."""
    font = ImageFont.load_default()

    if perturbation == PerturbationType.LOW_CONTRAST_STEGO:
        # High background, very close text color
        bg_color = (250, 250, 252)
        text_color = (236, 236, 240)
        img = Image.new("RGB", (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        draw.text((24, height // 3), text, fill=text_color, font=font)

    elif perturbation == PerturbationType.ROTATED_TEXT:
        bg_color = (245, 247, 250)
        text_color = (15, 23, 42)
        txt_layer = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        d_txt = ImageDraw.Draw(txt_layer)
        d_txt.text((30, height // 3), text, fill=(15, 23, 42, 255), font=font)
        rotated_txt = txt_layer.rotate(25, resample=Image.Resampling.BICUBIC)

        img = Image.new("RGBA", (width, height), bg_color)
        img.paste(rotated_txt, (0, 0), rotated_txt)
        img = img.convert("RGB")

    elif perturbation == PerturbationType.NOISE_OVERLAY:
        bg_color = (240, 244, 248)
        text_color = (20, 25, 35)
        img = Image.new("RGB", (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        draw.text((24, height // 3), text, fill=text_color, font=font)

        # Add salt-and-pepper noise
        pixels = img.load()
        for _ in range(int(width * height * 0.05)):
            rx = random.randint(0, width - 1)
            ry = random.randint(0, height - 1)
            noise_val = random.choice([30, 220])
            pixels[rx, ry] = (noise_val, noise_val, noise_val)

    elif perturbation == PerturbationType.DUAL_CHANNEL_CONFLICT:
        # High contrast red alert banner
        img = Image.new("RGB", (width, height), color=(254, 242, 242))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(16, 16), (width - 16, height - 16)], outline=(239, 68, 68), width=3)
        draw.text((28, height // 3), text, fill=(185, 28, 28), font=font)

    else:  # PLAIN_TYPOGRAPHIC
        bg_color = (255, 255, 255)
        text_color = (10, 15, 25)
        img = Image.new("RGB", (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        draw.text((24, height // 3), text, fill=text_color, font=font)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return GeneratedImagePayload(
        image_base64=b64_str,
        embedded_text=text,
        perturbation=perturbation,
        width=width,
        height=height,
    )
