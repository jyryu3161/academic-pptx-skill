# Academic design system

## Theme selection

Default remains **academic-blue**, matching the original skill. Choose one whole theme per deck and use named tokens rather than hardcoded per-slide colors. Institution-provided templates take precedence; adapt only within their requirements.

| Token | academic-blue (default) | accessible-teal | print |
|---|---|---|---|
| background | FFFFFF | FFFFFF | FFFFFF |
| primary/title | 1F4E79 | 004D40 | 111111 |
| accent | 2E75B6 | 00695C | 404040 |
| body | 2D2D2D | 2D2D2D | 111111 |
| muted/source | 595959 | 595959 | 595959 |
| surface | EBF3FA | E0F2F1 | F2F2F2 |
| highlight background | FFF2CC | FFF3E0 | E6E6E6 |
| highlight text | 5C4100 | 5C3100 | 111111 |
| onPrimary | FFFFFF | FFFFFF | FFFFFF |

The additional teal theme is an option, not a claim that every chart using it is color-vision safe. For categorical data, consider blue `0072B2`, orange `D55E00`, green `009E73`, purple `CC79A7`; pair with shapes/line styles and text labels. Do not use these colors for small text without checking contrast. Use ordered lightness for sequential scales; diverging scales only when there is a meaningful center. Avoid rainbow heatmaps and red/green-only comparisons. Keep a biological group or model's encoding stable throughout the deck.

## Typography and Korean

- Latin default: Arial when available; otherwise a verified installed sans-serif such as Liberation Sans. Explicitly select the font used for rendering; do not claim identical cross-platform metrics.
- Korean: use an installed family such as Noto Sans CJK KR, Malgun Gothic, or Apple SD Gothic Neo. Pick one for the delivery target and verify it there if possible. Arial does not contain a complete Korean character set.
- Keep Latin/Korean size, baseline and weight visually compatible. Set East Asian font properties as well as Latin properties when the generator supports them.
- Do not substitute equation, Greek or symbol fonts without checking every affected symbol. Prefer Unicode text for simple symbols and editable equations when feasible.
- Preserve semantic italics (species/gene conventions), superscripts, subscripts, minus signs and units. Do not normalize them blindly.
- Use deliberate paragraph spacing and normal spaces. Avoid fragile manual line breaks in prose; a deliberate break in a title is acceptable after rendering.

## Composition and accessibility

Use a consistent grid with intentional whitespace, not maximal box widths. Main slides: title band, one evidence region, interpretation and small source region. Legends must not cover data. Reserve the footer before placing content. Presentation layout is not a web page: do not transfer hover-only content, scrolling, tiny captions or decorative card grids from web-design guidance.

Target a contrast ratio of at least 4.5:1 for text as a conservative design check, then assess projection/readability at real display size. This is a design target, not a claim of full accessibility compliance. Non-text chart elements need sufficient contrast and redundant encodings. Add figure alt text and check reading order in the delivery format; a PDF export is not automatically tagged or accessible. Test grayscale for the print theme.

## Token discipline

When generating, resolve theme tokens once (see the global defaults in slide_patterns.md). Do not recolor imported scientific images unless permitted and scientifically faithful. Label illustrative diagrams as schematic. Never invent an institution's logo or brand standards.
