# Text, wrapping and slide-number rules

The supplied design revision identified real issues: text reflow across renderers, fragmented bullet lists, Korean line breaking and static slide numbers. Integrate those principles at generation time; **do not blindly merge or widen existing shapes**.

## Generate semantic text

- One semantic list = one text box with separate paragraphs. Mixed emphasis uses runs within each paragraph. Separate labels, columns, diagram nodes and independently animated objects may correctly be separate shapes.
- Allocate modest width and height slack within the grid. There is no universal 8%/0.4-inch repair. Do not widen into an adjacent figure or beyond a margin.
- Keep normal wrapping for prose. `wrap="none"` is appropriate only for a label already verified to fit. Never infer fit from box height alone.
- For Korean, choose an installed East Asian font explicitly and render in the target environment. Requesting whole-word line breaking can help but does not guarantee no awkward wrap; split a dense slide or revise copy rather than forcing a long unbreakable phrase.
- Preserve equations, citations, superscripts and rich-text emphasis. Text extraction is a content check, not a geometry or semantic-list validator.

## Optional conservative helper

Requires Python 3.10+ and `lxml` (install from requirements.txt). No option means no text-property or geometry changes. The helper validates ZIP/XML and writes atomically, including safe in-place operation.

```bash
python scripts/fix_pptx_text.py input.pptx output.pptx --word-wrap
python scripts/fix_pptx_text.py input.pptx output.pptx --font Arial --ea-font "Malgun Gothic" --word-wrap
python scripts/fix_pptx_text.py input.pptx output.pptx --slide-numbers --skip-numbers 1
```

- `--word-wrap` sets `eaLnBrk="0"` and `latinLnBrk="0"` on slide text paragraphs without changing their boxes.
- `--font` and `--ea-font` are opt-in replacements for Latin/East Asian properties in regular slide text, not themes, charts or equations. They do not install or embed fonts. Inspect mixed-symbol text before choosing them.
- `--slide-numbers` uses the order in presentation.xml and relationships, not slide filenames. It inserts native fields only when no slide/layout/master numbering is detected. It updates its own cached values and avoids duplicates on repeated runs.
- `--skip-numbers` uses one-based positions in current presentation order (default: 1). It removes only helper-owned numbers from skipped slides; it does not remove the template's number fields.
- The helper conservatively treats inherited numbering placeholders as existing, even when the application may hide them. Some templates therefore need numbering enabled manually in PowerPoint rather than a new helper field. It does not evaluate visibility or rewrite template settings.
- Native fields normally refresh in PowerPoint, but renderer behavior varies. Re-run after reordering if cached values need refreshing, and visually check the final export.

The attachment's blanket merge/width-expansion algorithm and browser JS equivalent are intentionally not shipped: geometric proximity is insufficient evidence that boxes form one list, and repeated widening can corrupt layouts. Repair list structure in the source generator. Do not use this helper as an overflow detector, PPTX schema validator or replacement for visual QA.

## Final QA sequence

1. Generate PPTX from the verified source content.
2. Apply only needed helper options, preferably to a new output file.
3. Open/read the package and extract text; confirm no content loss.
4. Render **the final output** (e.g. LibreOffice → PDF → PNG), inspect every slide at presentation scale and in thumbnail overview.
5. Check Korean/English wraps, missing glyphs, axes/units, callouts, footers, field values and print/contrast behavior. Fix at source and repeat.
6. When available, reopen in the delivery version of PowerPoint and verify fonts/fields. Disclose if this application-specific test was not possible.
