// Reads [{code, lang}] as JSON on stdin and writes the highlighted HTML for
// each, in order, as a JSON array. Both themes are kept as CSS variables on
// every token, so a block follows whichever data-theme it sits under.
import { createHighlighter } from "shiki";

const THEMES = { light: "github-light", dark: "github-dark" };

let input = "";
for await (const chunk of process.stdin) input += chunk;
const items = JSON.parse(input);

const highlighter = await createHighlighter({
  themes: Object.values(THEMES),
  langs: [...new Set(items.map((item) => item.lang))],
});

const html = items.map(({ code, lang }) =>
  highlighter.codeToHtml(code, { lang, themes: THEMES, defaultColor: false }),
);
process.stdout.write(JSON.stringify(html));
