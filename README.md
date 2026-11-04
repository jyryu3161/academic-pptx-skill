# Academic Presentations Skill

Communication-first academic slides for conference talks, seminars, thesis defenses, grant briefings and lab meetings. This fork extends the original skill and the supplied text-layout revision while keeping the original **navy `1F4E79` / blue `2E75B6` default**.

## What's improved

- Argument-led outlines, action titles and evidence-first slide patterns.
- Optional teal and print themes with semantic color tokens; consistent default palette.
- Korean/English typography and realistic font-fallback guidance.
- Biomedical, AI/ML benchmark, systems-biology, docking and grant-aim patterns.
- Explicit uncertainty, units, sample definitions, provenance and claim-strength checks.
- Semantic bullet lists, conservative opt-in XML text settings and native slide-number fields.
- References before conclusions, so the main talk ends on takeaways and contact details.
- No blanket box merging/widening or destructive global font reset.

## Use

Install the repository's skill folder using your assistant platform's supported custom-skill workflow, with SKILL.md at the skill root. Load it together with the platform's available presentation/PPTX implementation skill. Platform menus and dependencies vary; this skill is not a standalone deck generator.

Example requests:

- “Make a 15-minute research presentation from this paper. Keep the default theme.”
- “학위논문 심사 발표를 한국어로 만들어줘. 기본 남색 스킴을 유지해줘.”
- “Use the accessible-teal theme, with marker shapes and labels for the comparison.”
- “Prepare a print-friendly grant-aim deck; distinguish preliminary results from proposed work.”

The original PDF advice summary remains in the repository. The Markdown guides are the current source of instructions where they differ.

## Files

- [SKILL.md](SKILL.md): entry point and workflow.
- [content_guidelines.md](content_guidelines.md): argument, citations and narrative.
- [slide_patterns.md](slide_patterns.md): compositional PptxGenJS examples; illustrative, not research evidence.
- [design_system.md](design_system.md): palettes, typography and accessibility.
- [research_patterns.md](research_patterns.md): research-specific evidence and structure.
- [pptx_text_rules.md](pptx_text_rules.md): text layout, optional helper and final visual QA.
- [scripts/fix_pptx_text.py](scripts/fix_pptx_text.py): conservative XML postprocessor.
- tests/: regression tests for the helper.

## Optional helper and tests

```bash
python -m pip install -r requirements.txt
python scripts/fix_pptx_text.py input.pptx output.pptx --word-wrap
python scripts/fix_pptx_text.py input.pptx output.pptx --slide-numbers --skip-numbers 1
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

Python 3.10+ is required. Test tooling is separate from the prose skill. Rendering needs your chosen generator and a presentation renderer. Unit tests do not prove PowerPoint visual fidelity, font availability or accessibility. See [VALIDATION.md](VALIDATION.md) for validation scope.

## Background and license

The original guidelines draw on Barbara Minto's *Pyramid Principle*, Naegle (2021), “Ten simple rules for effective presentation slides,” *PLOS Computational Biology*, and academic presentation practice. Existing MIT copyright and permission notice are retained in [LICENSE](LICENSE). This fork adapts the supplied text-layout revision's principles while replacing its unsafe automatic geometry edits with opt-in behavior.
