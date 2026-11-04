#!/usr/bin/env python3
"""Conservative, opt-in PPTX text properties and native slide-number fields.

Never merges text boxes, changes geometry, guesses overflow, or rewrites themes.
Requires lxml. Changes are applied atomically; input and output may be identical.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
import posixpath
import tempfile
import uuid
import zipfile

from lxml import etree as ET

NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
}
OWN_NAME = 'AcademicPPTX Slide Number'
MAX_UNCOMPRESSED = 256 * 1024 * 1024


def tag(prefix, name):
    return '{' + NS[prefix] + '}' + name


def parse(data):
    parser = ET.XMLParser(resolve_entities=False, no_network=True, remove_blank_text=False)
    tree = ET.fromstring(data, parser)
    if tree.getroottree().docinfo.doctype:
        raise ValueError('DOCTYPE declarations are not supported in PPTX XML')
    return tree


def xml_bytes(root):
    return ET.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)


def rels_path(part):
    directory, basename = posixpath.split(part)
    return posixpath.join(directory, '_rels', basename + '.rels')


def resolve_part(source, target):
    result = posixpath.normpath(posixpath.join(posixpath.dirname(source), target))
    if target.startswith('/'):
        result = target.lstrip('/')
    if result.startswith('../') or result == '..' or '\\' in result:
        raise ValueError('Invalid package relationship target')
    return result


def relationships(parts, source):
    path = rels_path(source)
    if path not in parts:
        return {}
    return {r.get('Id'): r for r in parse(parts[path])}


def slide_order(parts):
    pres = parse(parts['ppt/presentation.xml'])
    if pres.tag != tag('p', 'presentation'):
        raise ValueError('Only transitional OOXML presentations are supported')
    rels = relationships(parts, 'ppt/presentation.xml')
    order = []
    for node in pres.findall('p:sldIdLst/p:sldId', NS):
        rel = rels.get(node.get(tag('r', 'id')))
        if rel is None or rel.get('TargetMode') == 'External':
            raise ValueError('Missing or external slide relationship')
        path = resolve_part('ppt/presentation.xml', rel.get('Target', ''))
        if path not in parts or path in order:
            raise ValueError('Missing or duplicate slide part')
        order.append(path)
    size = pres.find('p:sldSz', NS)
    if size is None:
        raise ValueError('Missing slide size')
    return order, int(size.get('cx')), int(size.get('cy'))


def has_number(root):
    return bool(root.xpath('.//a:fld[@type="slidenum"] | .//p:ph[@type="sldNum"]', namespaces=NS))


def inherited_number(parts, source, visited=None):
    visited = set() if visited is None else visited
    if source in visited:
        return False
    visited.add(source)
    for rel in relationships(parts, source).values():
        if rel.get('TargetMode') == 'External':
            continue
        kind = rel.get('Type', '').rsplit('/', 1)[-1]
        if kind not in {'slideLayout', 'slideMaster'}:
            continue
        target = resolve_part(source, rel.get('Target', ''))
        if target not in parts:
            raise ValueError('Missing slide layout/master')
        if has_number(parse(parts[target])) or inherited_number(parts, target, visited):
            return True
    return False


def apply_text(root, font=None, ea_font=None, word_wrap=False):
    """Only explicit regular text properties; no theme, math, or geometry edits."""
    changed = False
    for body in root.findall('.//p:txBody', NS):
        for paragraph in body.findall('a:p', NS):
            if word_wrap:
                props = paragraph.find('a:pPr', NS)
                if props is None:
                    props = ET.Element(tag('a', 'pPr'))
                    paragraph.insert(0, props)
                    changed = True
                for key in ('eaLnBrk', 'latinLnBrk'):
                    if props.get(key) != '0':
                        props.set(key, '0')
                        changed = True
            if font or ea_font:
                # Explicit defaults cover runs which inherit their typeface.
                props = paragraph.find('a:pPr', NS)
                if props is None:
                    props = ET.Element(tag('a', 'pPr'))
                    paragraph.insert(0, props)
                    changed = True
                default = props.find('a:defRPr', NS)
                if default is None:
                    default = ET.Element(tag('a', 'defRPr'))
                    extension = props.find('a:extLst', NS)
                    props.insert(list(props).index(extension) if extension is not None else len(props), default)
                    changed = True
                run_props = paragraph.xpath('./a:pPr/a:defRPr | ./a:r/a:rPr | ./a:fld/a:rPr | ./a:endParaRPr', namespaces=NS)
                for run in paragraph.findall('a:r', NS):
                    if run.find('a:rPr', NS) is None:
                        new = ET.Element(tag('a', 'rPr'))
                        run.insert(0, new)
                        run_props.append(new)
                        changed = True
                for rp in run_props:
                    for local, face in [('latin', font), ('ea', ea_font)]:
                        if not face:
                            continue
                        item = rp.find('a:' + local, NS)
                        if item is None:
                            item = ET.Element(tag('a', local))
                            # Keep DrawingML character-properties child sequence.
                            later = {'ea', 'cs', 'sym', 'hlinkClick', 'hlinkMouseOver', 'rtl', 'extLst'} if local == 'latin' else {'cs', 'sym', 'hlinkClick', 'hlinkMouseOver', 'rtl', 'extLst'}
                            index = next((i for i, el in enumerate(rp) if ET.QName(el).localname in later), len(rp))
                            rp.insert(index, item)
                            changed = True
                        if item.get('typeface') != face:
                            item.set('typeface', face)
                            changed = True
    return changed


def number_shape(root, width, height, number, font):
    ids = [int(x) for x in root.xpath('.//p:cNvPr/@id', namespaces=NS)]
    sp = ET.Element(tag('p', 'sp'))
    nv = ET.SubElement(sp, tag('p', 'nvSpPr'))
    ET.SubElement(nv, tag('p', 'cNvPr'), id=str(max(ids, default=0) + 1), name=OWN_NAME)
    ET.SubElement(nv, tag('p', 'cNvSpPr'), txBox='1')
    ET.SubElement(nv, tag('p', 'nvPr'))
    geometry = ET.SubElement(sp, tag('p', 'spPr'))
    transform = ET.SubElement(geometry, tag('a', 'xfrm'))
    ET.SubElement(transform, tag('a', 'off'), x=str(round(width * .87)), y=str(round(height * .93)))
    ET.SubElement(transform, tag('a', 'ext'), cx=str(round(width * .08)), cy=str(round(height * .04)))
    rect = ET.SubElement(geometry, tag('a', 'prstGeom'), prst='rect')
    ET.SubElement(rect, tag('a', 'avLst'))
    ET.SubElement(geometry, tag('a', 'noFill'))
    body = ET.SubElement(sp, tag('p', 'txBody'))
    ET.SubElement(body, tag('a', 'bodyPr'), wrap='none', lIns='0', tIns='0', rIns='0', bIns='0')
    ET.SubElement(body, tag('a', 'lstStyle'))
    p = ET.SubElement(body, tag('a', 'p'))
    ET.SubElement(p, tag('a', 'pPr'), algn='r')
    fld = ET.SubElement(p, tag('a', 'fld'), id='{' + str(uuid.uuid4()).upper() + '}', type='slidenum')
    rp = ET.SubElement(fld, tag('a', 'rPr'), lang='en-US', sz='1200')
    fill = ET.SubElement(rp, tag('a', 'solidFill'))
    ET.SubElement(fill, tag('a', 'srgbClr'), val='666666')
    ET.SubElement(rp, tag('a', 'latin'), typeface=font or 'Arial')
    ET.SubElement(fld, tag('a', 't')).text = str(number)
    return sp


def apply_number(root, parts, path, width, height, number, skip, font):
    tree = root.find('p:cSld/p:spTree', NS)
    if tree is None:
        raise ValueError('Missing slide shape tree')
    owned = tree.xpath('./p:sp[p:nvSpPr/p:cNvPr[@name=$name]]', namespaces=NS, name=OWN_NAME)
    # Preserve user/template fields. We only own uniquely named generated shapes.
    others = deepcopy(root)
    for sp in others.xpath('.//p:sp[p:nvSpPr/p:cNvPr[@name=$name]]', namespaces=NS, name=OWN_NAME):
        sp.getparent().remove(sp)
    existing = has_number(others) or inherited_number(parts, path)
    if skip or existing:
        for sp in owned:
            tree.remove(sp)
        return bool(owned)
    if owned:
        changed = False
        for sp in owned[1:]:
            tree.remove(sp)
            changed = True
        text = owned[0].find('.//a:fld[@type="slidenum"]/a:t', NS)
        if text is None:
            raise ValueError('Malformed generated slide-number field')
        if text.text != str(number):
            text.text = str(number)
            changed = True
        return changed
    new_shape = number_shape(root, width, height, number, font)
    extension = tree.find('p:extLst', NS)
    tree.insert(list(tree).index(extension) if extension is not None else len(tree), new_shape)
    return True


def process(src, dst, *, font=None, ea_font=None, word_wrap=False, slide_numbers=False, skip_numbers=(1,)):
    src, dst = Path(src), Path(dst)
    with zipfile.ZipFile(src) as zin:
        infos = zin.infolist()
        if len({i.filename for i in infos}) != len(infos):
            raise ValueError('Duplicate ZIP entries are not supported')
        if sum(i.file_size for i in infos) > MAX_UNCOMPRESSED:
            raise ValueError('PPTX exceeds 256 MiB uncompressed safety limit')
        parts = {i.filename: zin.read(i) for i in infos}
    for name, data in parts.items():
        if name.endswith(('.xml', '.rels')):
            parse(data)
    order, width, height = slide_order(parts)
    changed_slides = 0
    for number, path in enumerate(order, 1):
        root = parse(parts[path])
        changed = apply_text(root, font, ea_font, word_wrap)
        if slide_numbers:
            changed = apply_number(root, parts, path, width, height, number, number in skip_numbers, font) or changed
        if changed:
            parts[path] = xml_bytes(root)
            changed_slides += 1
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=dst.parent, suffix='.pptx', delete=False) as handle:
            temporary = Path(handle.name)
        with zipfile.ZipFile(temporary, 'w') as zout:
            for info in infos:
                zout.writestr(info, parts[info.filename])
        with zipfile.ZipFile(temporary) as verified:
            bad = verified.testzip()
            if bad:
                raise ValueError('Corrupt output ZIP member: ' + bad)
            for name in verified.namelist():
                if name.endswith(('.xml', '.rels')):
                    parse(verified.read(name))
        temporary.replace(dst)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return changed_slides


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('src')
    parser.add_argument('dst')
    parser.add_argument('--font', help='Explicit Latin typeface; otherwise preserve')
    parser.add_argument('--ea-font', help='Explicit East Asian typeface; otherwise preserve')
    parser.add_argument('--word-wrap', action='store_true', help='Set paragraph East Asian/Latin word-break properties; does not guarantee fit')
    parser.add_argument('--slide-numbers', action='store_true', help='Add native fields only where no existing/template numbering is detected')
    parser.add_argument('--skip-numbers', default='1', help='Comma-separated positions in actual slide order, default: 1')
    args = parser.parse_args()
    try:
        skip = {int(v.strip()) for v in args.skip_numbers.split(',') if v.strip()}
        if any(v < 1 for v in skip):
            raise ValueError('skip positions must be positive')
        count = process(args.src, args.dst, font=args.font, ea_font=args.ea_font, word_wrap=args.word_wrap,
                        slide_numbers=args.slide_numbers, skip_numbers=skip)
    except (ValueError, OSError, zipfile.BadZipFile, KeyError, ET.XMLSyntaxError) as exc:
        parser.exit(1, 'Error: ' + str(exc) + '\n')
    print(f'Updated {count} slide(s). Render and inspect the final deck before delivery.')


if __name__ == '__main__':
    main()
