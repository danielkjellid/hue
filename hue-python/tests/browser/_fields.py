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


def contrast(locator: Locator) -> float:
    """
    The WCAG contrast ratio of an element's text against what is behind it.

    The colours are composited, so a translucent text or fill counts as it
    shows: the backgrounds of the element and its ancestors, over the canvas.
    """
    return locator.evaluate(
        """el => {
            const canvas = document.createElement("canvas");
            canvas.width = canvas.height = 1;
            const context = canvas.getContext("2d", { willReadFrequently: true });
            const rgba = (color) => {
                context.clearRect(0, 0, 1, 1);
                context.fillStyle = color;
                context.fillRect(0, 0, 1, 1);
                const [r, g, b, a] = context.getImageData(0, 0, 1, 1).data;
                return { r, g, b, a: a / 255 };
            };
            const over = (top, under) => ({
                r: top.r * top.a + under.r * (1 - top.a),
                g: top.g * top.a + under.g * (1 - top.a),
                b: top.b * top.a + under.b * (1 - top.a),
                a: 1,
            });
            const fills = [];
            for (let at = el; at; at = at.parentElement) {
                fills.unshift(rgba(getComputedStyle(at).backgroundColor));
            }
            const back = fills.reduce((under, fill) => over(fill, under), {
                r: 255, g: 255, b: 255, a: 1,
            });
            const front = over(rgba(getComputedStyle(el).color), back);
            const channel = (v) => {
                v /= 255;
                return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
            };
            const luminance = ({ r, g, b }) =>
                0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
            const [light, dark] = [luminance(front), luminance(back)].sort(
                (a, b) => b - a
            );
            return (light + 0.05) / (dark + 0.05);
        }"""
    )
