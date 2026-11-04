import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

from lxml import etree as ET
from pptx import Presentation
from pptx.util import Inches, Pt

spec = importlib.util.spec_from_file_location('fix', Path(__file__).parents[1] / 'scripts/fix_pptx_text.py')
fix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fix)


def parts(path):
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}


def rewrite(path, change):
    data = parts(path)
    change(data)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, b in data.items():
            z.writestr(n, b)


class TextFixTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.src = Path(self.temp.name) / 'source.pptx'
        self.dst = Path(self.temp.name) / 'output.pptx'
        prs = Presentation()
        for i in range(3):
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            text = slide.shapes.add_textbox(Inches(.5), Inches(.5), Inches(4), Inches(1))
            p = text.text_frame.paragraphs[0]
            p.text = f'Result {i}: 한국어 example & uncertainty'
            p.runs[0].font.name = 'Calibri'
            p.runs[0].font.size = Pt(20)
        prs.save(self.src)
        # python-pptx's default master contains numbering placeholders. Remove
        # them from this fixture to test insertion, not duplicate avoidance.
        def clean(data):
            for name in list(data):
                if name.startswith(('ppt/slideMasters/', 'ppt/slideLayouts/')) and name.endswith('.xml'):
                    root = fix.parse(data[name])
                    for node in root.xpath('.//p:sp[.//p:ph[@type="sldNum"]]', namespaces=fix.NS):
                        node.getparent().remove(node)
                    data[name] = fix.xml_bytes(root)
        rewrite(self.src, clean)

    def test_no_options_preserves_every_part(self):
        self.assertEqual(fix.process(self.src, self.dst), 0)
        self.assertEqual(parts(self.src), parts(self.dst))

    def test_wrap_preserves_geometry_and_is_idempotent(self):
        before = parts(self.src)
        self.assertEqual(fix.process(self.src, self.dst, word_wrap=True), 3)
        after = parts(self.dst)
        for path in fix.slide_order(after)[0]:
            r1, r2 = fix.parse(before[path]), fix.parse(after[path])
            self.assertEqual(r1.xpath('.//a:xfrm/a:off/@x', namespaces=fix.NS), r2.xpath('.//a:xfrm/a:off/@x', namespaces=fix.NS))
            self.assertEqual(r1.xpath('.//a:xfrm/a:ext/@cx', namespaces=fix.NS), r2.xpath('.//a:xfrm/a:ext/@cx', namespaces=fix.NS))
            self.assertEqual(r1.xpath('.//a:t/text()', namespaces=fix.NS), r2.xpath('.//a:t/text()', namespaces=fix.NS))
            self.assertTrue(all(v == '0' for v in r2.xpath('.//a:pPr/@eaLnBrk', namespaces=fix.NS)))
        self.assertEqual(fix.process(self.dst, self.dst, word_wrap=True), 0)
        self.assertEqual(after, parts(self.dst))
        Presentation(self.dst)

    def test_explicit_font_handles_escaping_and_east_asian(self):
        fix.process(self.src, self.dst, font='Research & Sans', ea_font='맑은 고딕')
        root = fix.parse(parts(self.dst)['ppt/slides/slide1.xml'])
        self.assertIn('Research & Sans', root.xpath('.//a:latin/@typeface', namespaces=fix.NS))
        self.assertIn('맑은 고딕', root.xpath('.//a:ea/@typeface', namespaces=fix.NS))
        self.assertEqual(fix.process(self.dst, self.dst, font='Research & Sans', ea_font='맑은 고딕'), 0)
        Presentation(self.dst)

    def test_numbering_follows_presentation_order_not_filename(self):
        def reorder(data):
            root = fix.parse(data['ppt/presentation.xml'])
            order = root.find('p:sldIdLst', fix.NS)
            order.insert(0, order[-1])
            data['ppt/presentation.xml'] = fix.xml_bytes(root)
        rewrite(self.src, reorder)
        fix.process(self.src, self.dst, slide_numbers=True)
        data = parts(self.dst)
        order = fix.slide_order(data)[0]
        self.assertEqual(order[0], 'ppt/slides/slide3.xml')
        for i, name in enumerate(order, 1):
            fields = fix.parse(data[name]).xpath('.//a:fld[@type="slidenum"]/a:t/text()', namespaces=fix.NS)
            self.assertEqual(fields, [] if i == 1 else [str(i)])
        saved = parts(self.dst)
        self.assertEqual(fix.process(self.dst, self.dst, slide_numbers=True), 0)
        self.assertEqual(saved, parts(self.dst))
        # Reorder again: our fields move/refresh; the title becomes unnumbered.
        rewrite(self.dst, reorder)
        fix.process(self.dst, self.dst, slide_numbers=True)
        data = parts(self.dst)
        for i, name in enumerate(fix.slide_order(data)[0], 1):
            fields = fix.parse(data[name]).xpath('.//a:fld[@type="slidenum"]/a:t/text()', namespaces=fix.NS)
            self.assertEqual(fields, [] if i == 1 else [str(i)])
        Presentation(self.dst)

    def test_existing_custom_number_preserved(self):
        def custom(data):
            root = fix.parse(data['ppt/slides/slide2.xml'])
            sp = fix.number_shape(root, 9144000, 6858000, 88, 'Calibri')
            sp.find('p:nvSpPr/p:cNvPr', fix.NS).set('name', 'User number')
            root.find('p:cSld/p:spTree', fix.NS).append(sp)
            data['ppt/slides/slide2.xml'] = fix.xml_bytes(root)
        rewrite(self.src, custom)
        original = parts(self.src)['ppt/slides/slide2.xml']
        fix.process(self.src, self.dst, slide_numbers=True)
        self.assertEqual(parts(self.dst)['ppt/slides/slide2.xml'], original)

    def test_inherited_numbers_prevent_duplicate(self):
        def inherited(data):
            name = 'ppt/slideMasters/slideMaster1.xml'
            root = fix.parse(data[name])
            sp = fix.number_shape(root, 9144000, 6858000, 1, 'Arial')
            sp.find('p:nvSpPr/p:cNvPr', fix.NS).set('name', 'Template number')
            root.find('p:cSld/p:spTree', fix.NS).append(sp)
            data[name] = fix.xml_bytes(root)
        rewrite(self.src, inherited)
        self.assertEqual(fix.process(self.src, self.dst, slide_numbers=True), 0)
        self.assertEqual(parts(self.src), parts(self.dst))

    def test_xml_prefixes_are_preserved(self):
        def prefixes(data):
            name = 'ppt/slides/slide2.xml'
            data[name] = data[name].replace(b'xmlns:a=', b'xmlns:draw=').replace(b'<a:', b'<draw:').replace(b'</a:', b'</draw:')
        rewrite(self.src, prefixes)
        fix.process(self.src, self.dst, word_wrap=True)
        content = parts(self.dst)['ppt/slides/slide2.xml']
        self.assertIn(b'<draw:pPr', content)
        self.assertNotIn(b'ns0:', content)

    def test_invalid_input_does_not_touch_destination(self):
        self.dst.write_bytes(b'keep existing output')
        def invalid(data):
            data['ppt/slides/slide2.xml'] = b'<broken'
        rewrite(self.src, invalid)
        with self.assertRaises(ET.XMLSyntaxError):
            fix.process(self.src, self.dst, word_wrap=True)
        self.assertEqual(self.dst.read_bytes(), b'keep existing output')

    def test_changed_skip_removes_only_owned_fields(self):
        fix.process(self.src, self.dst, slide_numbers=True, skip_numbers=())
        fix.process(self.dst, self.dst, slide_numbers=True, skip_numbers=(1, 2))
        for i in range(1, 4):
            root = fix.parse(parts(self.dst)[f'ppt/slides/slide{i}.xml'])
            fields = root.xpath('.//a:fld[@type="slidenum"]/a:t/text()', namespaces=fix.NS)
            self.assertEqual(fields, [] if i < 3 else ['3'])

    def test_existing_wrap_attributes_are_updated_without_duplicates(self):
        def attributes(data):
            name = 'ppt/slides/slide1.xml'
            root = fix.parse(data[name])
            paragraph = root.find('.//p:txBody/a:p', fix.NS)
            props = ET.Element(fix.tag('a', 'pPr'), eaLnBrk='1', latinLnBrk='1')
            paragraph.insert(0, props)
            data[name] = fix.xml_bytes(root)
        rewrite(self.src, attributes)
        fix.process(self.src, self.dst, word_wrap=True)
        root = fix.parse(parts(self.dst)['ppt/slides/slide1.xml'])
        self.assertEqual(root.xpath('.//a:pPr/@eaLnBrk', namespaces=fix.NS), ['0'])
        self.assertEqual(root.xpath('.//a:pPr/@latinLnBrk', namespaces=fix.NS), ['0'])

    def test_non_slide_parts_stay_byte_identical(self):
        before = parts(self.src)
        fix.process(self.src, self.dst, word_wrap=True, font='Arial', ea_font='Malgun Gothic', slide_numbers=True)
        after = parts(self.dst)
        slides = set(fix.slide_order(before)[0])
        self.assertTrue(all(before[n] == after[n] for n in before if n not in slides))

    def test_properties_and_shapes_insert_before_extensions(self):
        def extensions(data):
            name = 'ppt/slides/slide2.xml'
            root = fix.parse(data[name])
            paragraph = root.find('.//p:txBody/a:p', fix.NS)
            props = ET.Element(fix.tag('a', 'pPr'))
            ET.SubElement(props, fix.tag('a', 'extLst'))
            paragraph.insert(0, props)
            ET.SubElement(root.find('p:cSld/p:spTree', fix.NS), fix.tag('p', 'extLst'))
            data[name] = fix.xml_bytes(root)
        rewrite(self.src, extensions)
        fix.process(self.src, self.dst, font='Arial', slide_numbers=True)
        root = fix.parse(parts(self.dst)['ppt/slides/slide2.xml'])
        props = root.find('.//p:txBody/a:p/a:pPr', fix.NS)
        self.assertEqual(props[-1].tag, fix.tag('a', 'extLst'))
        self.assertEqual(props[-2].tag, fix.tag('a', 'defRPr'))
        self.assertEqual(root.find('p:cSld/p:spTree', fix.NS)[-1].tag, fix.tag('p', 'extLst'))

    def test_doctype_rejected(self):
        with self.assertRaises(ValueError):
            fix.parse(b'<!DOCTYPE x [<!ENTITY value "unsafe">]><x>&value;</x>')


if __name__ == '__main__':
    unittest.main()
