# Validation scope

Validated on 2026-11-04:

- 13 automated helper tests: no-option preservation, repeated runs, wrap properties without duplicate attributes, escaped Latin/East Asian fonts, unchanged geometry and non-slide parts, custom/inherited numbering, real slide order after reordering, changed skip list, XML prefix and element ordering, invalid input atomicity, and DOCTYPE rejection.
- Python compilation of the helper.
- Markdown relative-link check and JavaScript syntax checks for the 13 compositional snippets. This is not an end-to-end execution of every PptxGenJS example.
- A three-slide synthetic Korean/English PPTX created and reopened with python-pptx, converted to PDF with LibreOffice, and rendered page 2 visually inspected: Korean glyphs and native field cache `2` visible without corruption. Fontconfig cache warnings occurred but did not prevent conversion.

Not validated: Microsoft PowerPoint desktop opening/field refresh, every host's installed fonts, all possible OOXML extensions, every template's inherited-number visibility, arbitrary deck overflow, full accessibility conformance or production research content. The helper is not a schema validator. Final decks still require source/content and visual QA after all changes.

No blanket merging/widening or browser JS postprocessor is included. Inherited number placeholders are treated conservatively to avoid duplicates, so a hidden template placeholder may need enabling in PowerPoint rather than helper insertion. Existing custom field caches are preserved.

Run tests from the repository root:

```bash
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
python -m py_compile scripts/fix_pptx_text.py
```
