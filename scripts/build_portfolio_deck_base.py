#!/usr/bin/env python3
"""Write the blank 960 x 540 pt base for the portfolio deck.

`gslides mutate create` always makes a 720 x 405 pt page and the CLI cannot set page
size or edit masters. The parent slide standard needs a 960 x 540 pt grid and one
inherited automatic page number, so the base is a minimal .pptx: a content layout
(short yellow accent, edge-reaching navy footer line, slide-number placeholder) and a
clean cover layout, with one sample slide of each. Upload it to Drive with conversion
to Google Slides; scripts/build_portfolio_deck_gslides.py then fills the result.

Usage: build_portfolio_deck_base.py OUTPUT.pptx
"""
import sys
import zipfile
from xml.sax.saxutils import escape

EMU = 12700
NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
CT = 'application/vnd.openxmlformats-officedocument.'
GROUP = ('<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
         '<p:grpSpPr/>')


def e(value):
    return int(round(value * EMU))


def rect(idn, name, x, y, w, h, colour):
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{idn}" name="{name}"/><p:cNvSpPr/><p:nvPr userDrawn="1"/>'
            f'</p:nvSpPr><p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/>'
            f'</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="{colour}"/>'
            '</a:solidFill><a:ln><a:noFill/></a:ln></p:spPr></p:sp>')


def number(idn, geometry=True):
    xfrm = (f'<a:xfrm><a:off x="{e(859)}" y="{e(498)}"/><a:ext cx="{e(60)}" cy="{e(20)}"/></a:xfrm>'
            if geometry else '')
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{idn}" name="Slide number"/><p:cNvSpPr><a:spLocks noGrp="1"/>'
            f'</p:cNvSpPr><p:nvPr><p:ph type="sldNum" sz="quarter" idx="12"/></p:nvPr></p:nvSpPr>'
            f'<p:spPr>{xfrm}</p:spPr><p:txBody><a:bodyPr lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"/>'
            '<a:lstStyle><a:lvl1pPr algn="r"><a:defRPr sz="1000"><a:solidFill><a:srgbClr val="59636E"/>'
            '</a:solidFill><a:latin typeface="Google Sans"/></a:defRPr></a:lvl1pPr></a:lstStyle>'
            '<a:p><a:fld id="{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}" type="slidenum"><a:rPr lang="en-AU"/>'
            '<a:t>‹#›</a:t></a:fld></a:p></p:txBody></p:sp>')


def tree(shapes):
    return f'<p:cSld><p:spTree>{GROUP}{shapes}</p:spTree></p:cSld>'


def theme():
    colours = ''.join(f'<a:{k}><a:srgbClr val="{v}"/></a:{k}>' for k, v in [
        ('dk1', '1C2333'), ('lt1', 'FFFFFF'), ('dk2', '31688E'), ('lt2', 'FBFAF6'),
        ('accent1', '1C2333'), ('accent2', 'FFDD04'), ('accent3', '31688E'),
        ('accent4', '46576C'), ('accent5', 'C64040'), ('accent6', '59636E'),
        ('hlink', '31688E'), ('folHlink', '46576C')])
    fill = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    line = f'<a:ln w="9525">{fill}</a:ln>'
    effect = '<a:effectStyle><a:effectLst/></a:effectStyle>'
    return (f'{HEAD}<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Cultural Blend">'
            f'<a:themeElements><a:clrScheme name="Cultural Blend">{colours}</a:clrScheme>'
            '<a:fontScheme name="Google Sans"><a:majorFont><a:latin typeface="Google Sans"/><a:ea typeface=""/>'
            '<a:cs typeface=""/></a:majorFont><a:minorFont><a:latin typeface="Google Sans"/><a:ea typeface=""/>'
            '<a:cs typeface=""/></a:minorFont></a:fontScheme><a:fmtScheme name="Flat">'
            f'<a:fillStyleLst>{fill * 3}</a:fillStyleLst><a:lnStyleLst>{line * 3}</a:lnStyleLst>'
            f'<a:effectStyleLst>{effect * 3}</a:effectStyleLst><a:bgFillStyleLst>{fill * 3}</a:bgFillStyleLst>'
            '</a:fmtScheme></a:themeElements></a:theme>')


def rels(items):
    body = ''.join(f'<Relationship Id="rId{i}" Type="{REL}/{kind}" Target="{target}"/>'
                   for i, (kind, target) in enumerate(items, 1))
    return (f'{HEAD}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'{body}</Relationships>')


def parts():
    white = '<p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>'
    clr_map = ('<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" '
               'accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" '
               'folHlink="folHlink"/>')
    master = (f'{HEAD}<p:sldMaster {NS}><p:cSld>{white}<p:spTree>{GROUP}{number(2)}</p:spTree></p:cSld>{clr_map}'
              '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/>'
              '<p:sldLayoutId id="2147483650" r:id="rId2"/></p:sldLayoutIdLst></p:sldMaster>')
    content = (f'{HEAD}<p:sldLayout {NS} type="blank" preserve="1"><p:cSld name="Content"><p:spTree>{GROUP}'
               f'{rect(2, "Section accent", 43.5, 44, 28, 2, "FFDD04")}'
               f'{rect(3, "Footer line", 0, 492, 960, 1.5, "1C2333")}{number(4)}</p:spTree></p:cSld></p:sldLayout>')
    cover = f'{HEAD}<p:sldLayout {NS} type="blank" preserve="1">' + tree('').replace(
        '<p:cSld>', '<p:cSld name="Cover">') + '</p:sldLayout>'
    presentation = (f'{HEAD}<p:presentation {NS}><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/>'
                    '</p:sldMasterIdLst><p:sldIdLst><p:sldId id="256" r:id="rId2"/><p:sldId id="257" r:id="rId3"/>'
                    f'</p:sldIdLst><p:sldSz cx="{e(960)}" cy="{e(540)}"/><p:notesSz cx="{e(540)}" cy="{e(960)}"/>'
                    '</p:presentation>')
    slide = lambda shapes: f'{HEAD}<p:sld {NS}>{tree(shapes)}</p:sld>'
    types = ''.join(f'<Override PartName="/ppt/{p}" ContentType="{CT}{c}+xml"/>' for p, c in [
        ('presentation.xml', 'presentationml.presentation.main'),
        ('slideMasters/slideMaster1.xml', 'presentationml.slideMaster'),
        ('slideLayouts/slideLayout1.xml', 'presentationml.slideLayout'),
        ('slideLayouts/slideLayout2.xml', 'presentationml.slideLayout'),
        ('slides/slide1.xml', 'presentationml.slide'), ('slides/slide2.xml', 'presentationml.slide'),
        ('theme/theme1.xml', 'theme')])
    return {
        '[Content_Types].xml': f'{HEAD}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                               '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                               f'<Default Extension="xml" ContentType="application/xml"/>{types}</Types>',
        '_rels/.rels': rels([('officeDocument', 'ppt/presentation.xml')]),
        'ppt/presentation.xml': presentation,
        'ppt/_rels/presentation.xml.rels': rels([('slideMaster', 'slideMasters/slideMaster1.xml'),
                                                 ('slide', 'slides/slide1.xml'), ('slide', 'slides/slide2.xml'),
                                                 ('theme', 'theme/theme1.xml')]),
        'ppt/theme/theme1.xml': theme(),
        'ppt/slideMasters/slideMaster1.xml': master,
        'ppt/slideMasters/_rels/slideMaster1.xml.rels': rels([('slideLayout', '../slideLayouts/slideLayout1.xml'),
                                                              ('slideLayout', '../slideLayouts/slideLayout2.xml'),
                                                              ('theme', '../theme/theme1.xml')]),
        'ppt/slideLayouts/slideLayout1.xml': content,
        'ppt/slideLayouts/_rels/slideLayout1.xml.rels': rels([('slideMaster', '../slideMasters/slideMaster1.xml')]),
        'ppt/slideLayouts/slideLayout2.xml': cover,
        'ppt/slideLayouts/_rels/slideLayout2.xml.rels': rels([('slideMaster', '../slideMasters/slideMaster1.xml')]),
        'ppt/slides/slide1.xml': slide(''),
        'ppt/slides/_rels/slide1.xml.rels': rels([('slideLayout', '../slideLayouts/slideLayout2.xml')]),
        'ppt/slides/slide2.xml': slide(number(2, geometry=False)),
        'ppt/slides/_rels/slide2.xml.rels': rels([('slideLayout', '../slideLayouts/slideLayout1.xml')]),
    }


def main():
    with zipfile.ZipFile(sys.argv[1], 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, text in parts().items():
            archive.writestr(name, text)


if __name__ == '__main__':
    main()
