"""
Reading the colours a field is drawn in.
"""

import base64

from playwright.sync_api import Locator, Page

# Transitions would leave a read halfway between two states.
STILL = (
    "*, *::before, *::after, input::-webkit-slider-thumb "
    "{ transition: none !important; }"
)


def still(page: Page) -> Page:
    page.add_style_tag(content=STILL)
    return page


def token(page: Page, name: str) -> str:
    """
    A colour token as the browser computes it, to compare with a computed style.
    """
    return page.evaluate(
        """name => {
            const probe = document.createElement("i");
            probe.style.color = `var(--color-${name})`;
            document.body.append(probe);
            const color = getComputedStyle(probe).color;
            probe.remove();
            return color;
        }""",
        name,
    )


def css(locator: Locator, prop: str) -> str:
    return locator.evaluate("(el, prop) => getComputedStyle(el)[prop]", prop)


def row_of_pixels(page: Page, x: float, y: float, length: int) -> list[str]:
    """
    The colours on screen from x rightwards along y, as rgb() strings.

    For what no computed style reports, such as a range input's thumb.
    """
    png = page.screenshot(clip={"x": x, "y": y, "width": length, "height": 1})
    return page.evaluate(
        """async src => {
            const image = new Image();
            image.src = src;
            await image.decode();
            const canvas = document.createElement("canvas");
            canvas.width = image.width;
            canvas.height = 1;
            const context = canvas.getContext("2d");
            context.drawImage(image, 0, 0);
            const data = context.getImageData(0, 0, image.width, 1).data;
            const out = [];
            for (let i = 0; i < data.length; i += 4) {
                out.push(`rgb(${data[i]}, ${data[i + 1]}, ${data[i + 2]})`);
            }
            return out;
        }""",
        "data:image/png;base64," + base64.b64encode(png).decode(),
    )
