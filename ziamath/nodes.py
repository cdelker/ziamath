''' Math element nodes '''

from __future__ import annotations
from typing import Optional, Union, MutableMapping

from copy import copy
from collections import ChainMap
import itertools
import xml.etree.ElementTree as ET

from ziafont import Font
from ziafont.fonttypes import BBox
from ziafont.glyph import SimpleGlyph, fmt

from .config import config
from .drawable import Drawable
from .styles import styledstr
from .zmath import MathFont
from . import operators
from . import drawable


def getstyle(element: ET.Element) -> dict:
    ''' Get style arguments based on "mathvariant" in mathml '''
    variant = element.attrib.get('mathvariant', '')
    styleargs: dict[str, Union[str, bool]] = {}
    if 'italic' in variant and 'normal' not in variant:
        styleargs['italic'] = True
    if 'normal' in variant:
        styleargs['normal'] = True
    if 'bold' in variant:
        styleargs['bold'] = True
    if 'double' in variant:
        styleargs['style'] = 'double'
    if 'script' in variant:
        styleargs['style'] = 'script'
    if 'sans' in variant:
        styleargs['style'] = 'sans'
    if 'mono' in variant:
        styleargs['style'] = 'mono'
    if 'fraktur' in variant:
        styleargs['style'] = 'fraktur'
    if 'displaystyle' in element.attrib:
        styleargs['displaystyle'] = element.attrib['displaystyle'].lower() == 'true'
    if 'mathcolor' in element.attrib:
        styleargs['mathcolor'] = element.attrib['mathcolor']
    if 'mathbackground' in element.attrib:
        styleargs['mathbackground'] = element.attrib['mathbackground']
    if 'display' in element.attrib:
        styleargs['display'] = element.attrib['display'] != 'inline'
    return styleargs


def makenode(element: ET.Element, parent: 'Mnode', **kwargs) -> 'Mnode':
    ''' Create node from the MathML element

        Args:
            element: MathML XML element
            size: Font size for element
            parent: Parent node
    '''
    if element.tag == 'mi' and element.text in operators.names:
        # Workaround for some latex2mathml operators coming back as identifiers
        element.tag = 'mo'

    node = {'math': Mrow,
            'mrow': Mrow,
            'mi': Midentifier,
            'mn': Mnumber,
            'mo': Moperator,
            'msup': Msup,
            'msub': Msub,
            'msubsup': Msubsup,
            'mover': Mover,
            'munder': Munder,
            'munderover': Munderover,
            'mfrac': Mfrac,
            'msqrt': Msqrt,
            'mroot': Mroot,
            'mtext': Mtext,
            'mspace': Mspace,
            'mfenced': Mfenced,
            'menclose': Menclose,
            'mpadded': Mpadded,
            'mphantom': Mphantom,
            'mtable': Mtable,
            'mtd': Mrow,
            'mstyle': Mstyle,
            }.get(element.tag, None)

    if element.tag == 'mo':
        infer_opform(0, element, parent)

    if node:
        return node(element, parent, **kwargs)
    else:
        print('Undefined Element', element)
        return Mrow(element, parent)


def getspaceems(space: str) -> float:
    ''' Get space in ems from the string. Can be number or named space width. '''
    if space.endswith('em'):
        f = float(space[:-2])
    else:
        f = {"veryverythinmathspace": 1/18,
             "verythinmathspace": 2/18,
             "thinmathspace": 3/18,
             "mediummathspace": 4/18,
             "thickmathspace": 5/18,
             "verythickmathspace": 6/18,
             "veryverythickmathspace": 7/18,
             "negativeveryverythinmathspace": -1/18,
             "negativeverythinmathspace": -2/18,
             "negativethinmathspace": -3/18,
             "negativemediummathspace": -4/18,
             "negativethickmathspace": -5/18,
             "negativeverythickmathspace": -6/18,
             "negativeveryverythickmathspace": -7/18,
            }.get(space, 0)
    return f


def getdimension(size: str, emscale: float) -> float:
    ''' Get dimension from string. Either in em or px '''
    try:
        s = float(size)
    except ValueError:
        if size.endswith('em'):
            s = float(size[:-2]) / emscale
        elif size.endswith('px'):
            s = float(size[:-2])
        else:
            raise ValueError(f'Undefined size {s}')
    return s


def getelementtext(element: ET.Element) -> str:
    ''' Get text of XML element '''
    try:
        txt = element.text.strip()  # type: ignore
    except AttributeError:
        txt = ''
    return txt


def subglyph(glyph: SimpleGlyph, font: MathFont) -> SimpleGlyph:
    ''' Substitute glyphs using font GSUB ssty feature. This 
        substitutes glyphs like \prime for use in sub/superscripts.
    '''
    if font.gsub:
        glyphids = font.gsub.sub([glyph.index], font.features)
        if glyphids[0] != glyph.index:
            glyph = font.glyph_fromid(glyphids[0])
    return glyph


class Mnode(drawable.Drawable):
    ''' Math Drawing Node

        Args:
            element: XML element for the node
            size: font size
            parent: Mnode of parent
    '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        self.element = element
        self.font: MathFont = parent.font
        self.parent = parent
        self.size: float = parent.size
        self.scriptlevel = int(self.element.attrib.get('scriptlevel', scriptlevel))
        self.style: MutableMapping[str, Union[str, bool]] = ChainMap(getstyle(self.element), copy(parent.style))
        self.nodes: list[drawable.Drawable] = []
        self.nodexy: list[tuple[float, float]] = []

        self.glyphsize = max(self.size * (self.font.math.consts.scriptPercentScaleDown / 100)**self.scriptlevel,
                            self.font.basesize*config.minsizefraction)
        self.emscale = self.glyphsize / self.font.info.layout.unitsperem

    def _setup(self, **kwargs) -> None:
        ''' Calculate node position assuming this node is at 0, 0. Also set bbox. '''
        self.bbox = BBox(0, 0, 0, 0)

    def displaystyle(self):
        ''' Determine whether the node should be drawn in display style '''
        return self.style.get('displaystyle', self.style.get('display', True))

    def leftsibling(self) -> Optional[drawable.Drawable]:
        ''' Left node sibling. The one that was just placed. '''
        parent = self.parent
        while isinstance(parent, Mstyle):
            parent = parent.parent

        try:
            node = parent.nodes[-1]
        except (IndexError, AttributeError):
            node = None

        return node

    def firstglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the first glyph in this node '''
        return None

    def lastglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the last glyph in this node '''
        return None

    def lastchar(self) -> Optional[str]:
        ''' Get the last character in this node '''
        return None

    def draw(self, x: float, y: float, svg: ET.Element) -> tuple[float, float]:
        ''' Draw the node on the SVG

            Args:
                x: Horizontal position in SVG coordinates
                y: Vertical position in SVG coordinates
                svg: SVG drawing as XML
        '''
        if config.debug:
            rect = ET.SubElement(svg, 'rect')
            rect.attrib['x'] = fmt(x)
            rect.attrib['y'] = fmt(y - self.bbox.ymax)
            rect.attrib['width'] = fmt((self.bbox.xmax - self.bbox.xmin))
            rect.attrib['height'] = fmt((self.bbox.ymax - self.bbox.ymin))
            rect.attrib['fill'] = 'none'
            rect.attrib['stroke'] = 'blue'
            rect.attrib['stroke-width'] = '0.2'
            base = ET.SubElement(svg, 'path')
            base.attrib['d'] = f'M {x} 0 L {x+self.bbox.xmax} 0'
            base.attrib['stroke'] = 'red'

        if 'mathbackground' in self.style:
            rect = ET.SubElement(svg, 'rect')
            rect.set('x', fmt(x))
            rect.set('y', fmt(y - self.bbox.ymax))
            rect.set('width', fmt((self.bbox.xmax - self.bbox.xmin)))
            rect.set('height', fmt((self.bbox.ymax - self.bbox.ymin)))
            rect.set('fill', self.style['mathbackground'])  # type: ignore
            
        xi = yi = 0.
        for (xi, yi), node in zip(self.nodexy, self.nodes):
            node.draw(x+xi, y+yi, svg)
        return x+xi, y+yi


class Midentifier(Mnode):
    ''' Identifier node <mi> '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        super().__init__(element, parent, scriptlevel, **kwargs)

        # Identifiers are italic unless longer than one character
        text = getelementtext(self.element)
        if len(text) == 1 and 'italic' not in self.style and 'normal' not in self.style:
            self.style['italic'] = True
        if len(text) > 1:
            text = '\U00002009' + text
            if not isinstance(parent, (Msub, Msup, Msubsup)):
                text = text + '\U00002009'
        self.string = styledstr(text, **self.style)
        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        ymin = 9999
        ymax = -9999
        x = 0
        for char in self.string:
            glyph = self.font.glyph(char)
            if kwargs.get('sup') or kwargs.get('sub'):
                glyph = subglyph(glyph, self.font)

            self.nodes.append(drawable.Glyph(glyph, char, self.glyphsize, self.emscale, self.style, **kwargs))
            self.nodexy.append((x, 0))
            x += glyph.advance() * self.emscale
            ymin = min(ymin, glyph.path.bbox.ymin * self.emscale)
            ymax = max(ymax, glyph.path.bbox.ymax * self.emscale)

        try:
            xmin = self.nodes[0].bbox.xmin  # type:ignore
            xmax = self.nodexy[-1][0] + max(self.nodes[-1].bbox.xmax, glyph.advance()*self.emscale)  # type:ignore
        except IndexError:
            xmin = 0
            xmax = x
        self.bbox = BBox(xmin, xmax, ymin, ymax) 

    def firstglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the first glyph in this node '''
        try:
            return self.nodes[0].firstglyph()
        except IndexError:
            return None

    def lastglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the last glyph in this node '''
        try:
            return self.nodes[-1].lastglyph()
        except IndexError:
            return None

    def lastchar(self) -> Optional[str]:
        ''' Get the last character in this node '''
        try:
            return self.nodes[-1].lastchar()
        except IndexError:
            return None


class Mnumber(Midentifier):
    ''' Number node <mn> '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        Mnode.__init__(self, element, parent, scriptlevel, **kwargs)
        self.string = styledstr(getelementtext(self.element), **self.style)
        self._setup(**kwargs)


class Mtext(Midentifier):
    ''' Text Node <mtext> '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        Mnode.__init__(self, element, parent, scriptlevel, **kwargs)
        # Don't use getelementtext since it strips whitespace
        self.string = ''
        if self.element.text:
            self.string = styledstr(self.element.text, **self.style)
        self._setup(**kwargs)


def infer_opform(i: int, child: ET.Element, mrow: Mnode) -> None:
    ''' Infer form (prefix, postfix, infix) of operator child within
        element mrow. Appends 'form' attribute to child.

        Args:
            i: Index of child within parent
            child: XML element of child
            mrow: Mnode of parent element
    '''
    # Infer form for operators
    if 'form' not in child.attrib:
        if isinstance(mrow, (Msub, Msup, Msubsup)):
            form = 'prefix'
        elif i == 0:
            form = 'prefix'
        elif i == len(mrow.element) - 1:
            form = 'postfix'
        else:
            form = 'infix'
        child.attrib['form'] = form


def isstretchy(text: str, font: MathFont) -> bool:
    ''' Check if glyph is in font's extendedShapeCoverage list '''
    if text:
        glyph = font.glyph(text[0])
        return font.math.isextended(glyph.index)
    return False


class Mrow(Mnode):
    ''' Math row, list of vertically aligned Mnodes '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        super().__init__(element, parent, scriptlevel, **kwargs)
        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        kwargs = copy(kwargs)
        node: Mnode
        self.nodes = []

        # Break mrow into lines - to handle mspace linebreak (// in latex)
        lines = []
        line: list[ET.Element] = []
        for i, child in enumerate(self.element):
            if child.tag == 'mi' and child.text in operators.names:
                # Workaround for some latex2mathml operators coming back as identifiers
                child.tag = 'mo'

            if child.tag == 'mo':
                infer_opform(i, child, self)
            if child.tag == 'mspace' and child.attrib.get('linebreak', None) == 'newline':
                lines.append(line)
                line = []
            else:
                line.append(child)
        lines.append(line)

        if len(lines) > 1:
            # Multiline - process each line as an mrow so we can get its bounding box
            for i, line in enumerate(lines):
                mrowelm = ET.Element('mrow')
                mrowelm.extend(line)
                node = Mrow(mrowelm, parent=self, scriptlevel=self.scriptlevel)
                self.nodes.append(node)

            y = 0
            for i, node in enumerate(self.nodes):  # type: ignore
                if i > 0:
                    y += (node.bbox.ymax - self.nodes[i-1].bbox.ymin + self.font.math.consts.mathLeading*self.emscale*2)  # type: ignore
                self.nodexy.append((0, y))
            xmax = max([n.bbox.xmax for n in self.nodes])    # type: ignore
            ymin = -y+self.nodes[-1].bbox.ymin    # type: ignore
            ymax = self.nodes[0].bbox.ymax    # type: ignore
            self.bbox = BBox(0, xmax, ymin, ymax)
        else:
            # Single line
            ymax = -9999
            ymin = 9999
            i = 0
            x = 0
            while i < len(line):
                child = line[i]
                text = getelementtext(child)
                if child.tag == 'mo':
                    if (isstretchy(text, self.font) and
                        child.attrib.get('form') == 'prefix' and
                        child.attrib.get('stretchy') != 'false'):
                        fencekwargs = copy(kwargs)
                        j = 0
                        for j in range(i+1, len(self.element)):
                            if self.element[j].tag == 'mo' and self.element[j].attrib.get('form') == 'postfix':
                                children = self.element[i+1: j]
                                fencekwargs['open'] = getelementtext(child)
                                fencekwargs['close'] = getelementtext(self.element[j])
                                break
                        else:  # No postfix closing fence. Enclose remainder of row.
                            children = self.element[i+1:]
                            fencekwargs['open'] = getelementtext(child)
                            fencekwargs['close'] = None
                        fencekwargs['separators'] = ''
                        fenced = ET.Element('mfenced')
                        fenced.attrib.update(child.attrib)
                        fenced.attrib.update(fencekwargs)
                        if len(children) > 0:
                            frow = ET.SubElement(fenced, 'mrow')
                            frow.extend(children)
                        node = Mfenced(fenced, parent=self, scriptlevel=self.scriptlevel, **kwargs)
                        i = j + 1

                    else:
                        if text == '':
                            i += 1
                            continue  # InvisibleTimes, etc.
                        node = Moperator(child, parent=self, scriptlevel=self.scriptlevel, **kwargs)
                        i += 1
                else:
                    node = makenode(child, parent=self, scriptlevel=self.scriptlevel, **kwargs)
                    i += 1

                self.nodes.append(node)
                self.nodexy.append((x, 0))
                x += node.bbox.xmax
                ymax = max(ymax, node.bbox.ymax)
                ymin = min(ymin, node.bbox.ymin)
            self.bbox = BBox(0, x, ymin, ymax)

    def firstglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the first glyph in this node '''
        i = 0
        while (i < len(self.nodes) and 
               isinstance(self.nodes[i], Mspace) and 
               self.nodes[i].width <= 0):  # type:ignore
            i += 1  # Negative space shouldn't count as first glyph

        try:
            glyph = self.nodes[i].firstglyph()
        except IndexError:
            return None
        return glyph

    def lastglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the last glyph in this node '''
        try:
            return self.nodes[-1].lastglyph()
        except IndexError:
            return None

    def lastchar(self) -> Optional[str]:
        ''' Get the last character in this node '''
        try:
            return self.nodes[-1].lastchar()
        except IndexError:
            return None

        
class Mfenced(Mnode):
    ''' Mfence element. Puts contents in parenthesis or other fence glyphs, with
        optional separators between components.
    '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        Mnode.__init__(self, element, parent, scriptlevel, **kwargs)
        self.openchr = element.attrib.get('open', '(')
        self.closechr = element.attrib.get('close', ')')
        self.separators = element.attrib.get('separators', ',').replace(' ', '')
        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        separator_elms = [ET.fromstring(f'<mo>{k}</mo>') for k in self.separators]
        fencedelms: Union[list[ET.Element], ET.Element] = []
        # Insert separators
        if len(self.element) > 1 and len(self.separators) > 0:
            fencedelms = list(itertools.chain.from_iterable(
                itertools.zip_longest(self.element, separator_elms, fillvalue=separator_elms[-1])))   # flatten
            fencedelms = fencedelms[:len(self.element)*2-1]  # Remove any separators at end
        else:
            # Single element in fence, no separators
            fencedelms = self.element

        mrowelm = ET.Element('mrow')
        mrowelm.extend(fencedelms)
        mrow = Mrow(mrowelm, parent=self, scriptlevel=self.scriptlevel)
        # standard size fence glyph
        openglyph = self.font.glyph(self.openchr)
        mglyph = drawable.Glyph(openglyph, self.openchr, self.glyphsize, self.emscale, self.style, **kwargs)

        if len(mrow.nodes) == 0:
            # Opening fence with nothing in it
            height = mglyph.bbox.ymax - mglyph.bbox.ymin
            fencebbox = mglyph.bbox
        else:
            height = max(mrow.bbox.ymax, mglyph.bbox.ymax) - min(mrow.bbox.ymin, mglyph.bbox.ymin)
            # height-adjusted fence glyph variant
            openglyph = self.font.math.variant(openglyph.index, height/self.emscale, vert=True)
            mglyph = drawable.Glyph(openglyph, self.openchr, self.glyphsize,
                                    self.emscale, self.style, **kwargs)

            if mrow.bbox.ymax > mglyph.bbox.ymax or mrow.bbox.ymin < mglyph.bbox.ymin:
                height = max(mrow.bbox.ymax, -mrow.bbox.ymin)*2
                openglyph = self.font.math.variant(self.font.glyph(self.openchr).index, height/self.emscale, vert=True)
                mglyph = drawable.Glyph(openglyph, self.openchr, self.glyphsize,
                                        self.emscale, self.style, **kwargs)
                
            fencebbox = mrow.bbox

        self.nodes = []
        x = yofst = base = 0
        yglyphmin = yglyphmax = 0

        if self.openchr:
            self.nodes.append(mglyph)
            self.nodexy.append((x, yofst))
            x += openglyph.advance() * self.emscale
            yglyphmin = min(-yofst+mglyph.bbox.ymin, yglyphmin)
            yglyphmax = max(-yofst+mglyph.bbox.ymax, yglyphmax)

        if len(fencedelms) > 0:
            self.nodes.append(mrow)
            self.nodexy.append((x, base))
            x += fencebbox.xmax

        if self.closechr:
            try:
                if isinstance(mrow.nodes[-1].nodes[-1], Mfrac):
                    # Mfrac adds space to right, remove it for fence
                    x -= getspaceems('thinmathspace') * self.emscale * self.font.info.layout.unitsperem
            except (IndexError, AttributeError):
                pass

            closeglyph = self.font.glyph(self.closechr)
            closeglyph = self.font.math.variant(closeglyph.index, height/self.emscale, vert=True)
            mglyph = drawable.Glyph(closeglyph, self.closechr, self.glyphsize,
                                    self.emscale, self.style, **kwargs)
            self.nodes.append(mglyph)
            self.nodexy.append((x, yofst))
            x += closeglyph.advance() * self.emscale
            yglyphmin = min(-yofst+mglyph.bbox.ymin, yglyphmin)
            yglyphmax = max(-yofst+mglyph.bbox.ymax, yglyphmax)
            
        self.bbox = BBox(0, x, min(yglyphmin, fencebbox.ymin), max(yglyphmax, fencebbox.ymax))

    def firstglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the first glyph in this node '''
        try:
            return self.nodes[0].firstglyph()
        except IndexError:
            return None

    def lastglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the last glyph in this node '''
        try:
            return self.nodes[-1].lastglyph()
        except IndexError:
            return None

    def lastchar(self) -> Optional[str]:
        ''' Get the last character in this node '''
        try:
            return self.nodes[-1].lastchar()
        except IndexError:
            return None


class Moperator(Mnumber):
    ''' Operator math element '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        Mnode.__init__(self, element, parent, scriptlevel, **kwargs)
        self.string = styledstr(getelementtext(self.element), **self.style)
        self.form = element.attrib.get('form', 'infix')

        # Load parameters from operators table for deciding how much space
        # to add on either side of the operator
        self.params = operators.get_params(self.string, self.form)
        self.params.update(element.attrib)
        self.width = kwargs.get('width', None)
        self._setup(**kwargs)

    def _setup(self, **kwargs):
        glyphs = [self.font.glyph(char) for char in self.string]

        if kwargs.get('sup') or kwargs.get('sub'):
            addspace = False  # Dont add lspace/rspace when in super/subscripts
            glyphs = [subglyph(g, self.font) for g in glyphs]
        else:
            addspace = True

        x = 0
        self.nodes = []

        # Add lspace
        if addspace:
            lspace = getspaceems(self.params.get('lspace', '0')) * self.emscale * self.font.info.layout.unitsperem
            x += lspace

        ymin = 999
        ymax = -999
        for glyph, char in zip(glyphs, self.string):
            if self.params.get('largeop') == 'true' and self.displaystyle():
                minh = self.font.math.consts.displayOperatorMinHeight
                glyph = self.font.math.variant(glyph.index, minh, vert=True)

            if self.width:
                glyph = self.font.math.variant(glyph.index, self.width / self.emscale, vert=False)

            self.nodes.append(drawable.Glyph(
                glyph, char, self.glyphsize, self.emscale, self.style, **kwargs))
            self.nodexy.append((x, 0))
            x += glyph.advance() * self.emscale
            ymin = min(ymin, glyph.path.bbox.ymin * self.emscale)
            ymax = max(ymax, glyph.path.bbox.ymax * self.emscale)

        if addspace:
            rspace = getspaceems(self.params.get('rspace', '0')) * self.emscale * self.font.info.layout.unitsperem
            x += rspace

        self.bbox = BBox(glyphs[0].path.bbox.xmin * self.emscale, x, ymin, ymax)


def place_super(base: Mnode, superscript: Mnode, font: MathFont, emscale: float) -> tuple[float, float, float]:
    ''' Superscript. Can be above the operator (like sum) or regular super '''
    if (hasattr(base, 'params') and base.params.get('movablelimits') == 'true'  # type: ignore
        and base.displaystyle()):
        x = -(base.bbox.xmax - base.bbox.xmin) / 2 - (superscript.bbox.xmax - superscript.bbox.xmin) / 2
        supy = -base.bbox.ymax - font.math.consts.upperLimitGapMin * emscale + superscript.bbox.ymin
        xadvance = 0
    else:
        x = 0
        lastg = base.lastglyph()
        shiftup = font.math.consts.superscriptShiftUp

        if hasattr(base, 'params'):
            x -= getspaceems(base.params.get('rspace', '0')) / emscale  # type: ignore

        if lastg:
            italicx = font.math.italicsCorrection.getvalue(lastg.index)
            if italicx and base.lastchar() not in operators.integrals:
                x += italicx * emscale
            firstg = superscript.firstglyph()
            if firstg:
                if font.math.kernInfo:
                    kern, shiftup = font.math.kernsuper(lastg, firstg)
                    x += kern * emscale
                else:
                    shiftup = lastg.bbox.ymax - \
                        (superscript.bbox.ymax - superscript.bbox.ymin)/2/emscale
            else:  # eg ^/frac
                shiftup = lastg.bbox.ymax
        supy = -shiftup * emscale
        xadvance = x + superscript.bbox.xmax
        
        if (isinstance(base, Midentifier) and 
            base.element and base.element.text and 
            len(base.element.text) > 1):
                xadvance += getspaceems('thinmathspace') * emscale * font.info.layout.unitsperem
    return x, supy, xadvance


def place_sub(base: Mnode, subscript: Mnode, font: MathFont, emscale: float):
    ''' Calculate subscript. Can be below the operator (like sum) or regular sub '''
    if hasattr(base, 'params') and base.params.get('movablelimits') == 'true' and base.displaystyle():  # type: ignore
        x = -(base.bbox.xmax - base.bbox.xmin) / 2 - (subscript.bbox.xmax - subscript.bbox.xmin) / 2
        suby = -base.bbox.ymin + font.math.consts.lowerLimitGapMin * emscale + subscript.bbox.ymax
        xadvance = 0
    else:
        lastg = base.lastglyph()
        shiftdn = font.math.consts.subscriptShiftDown
        x = 0
        if hasattr(base, 'params'):
            x -= getspaceems(base.params.get('rspace', '0')) / emscale  # type: ignore

        if lastg:
            italicx = font.math.italicsCorrection.getvalue(lastg.index)
            if italicx and base.lastchar() in operators.integrals:
                x -= italicx * emscale  # Shift back on integrals
            firstg = subscript.firstglyph()
            if firstg:
                if font.math.kernInfo:
                    kern, shiftdn = font.math.kernsub(lastg, firstg)
                    x += kern * emscale
                else:
                    shiftdn = -lastg.bbox.ymin + \
                        (subscript.bbox.ymax - subscript.bbox.ymin)/2/emscale
            else:
                shiftdn = -lastg.bbox.ymin
        suby = shiftdn * emscale
        xadvance = x + subscript.bbox.xmax
    return x, suby, xadvance


class Msup(Mnode):
    ''' Superscript Node '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        super().__init__(element, parent, scriptlevel, **kwargs)
        assert len(self.element) == 2
        self.base = makenode(self.element[0], parent=self, scriptlevel=self.scriptlevel, **kwargs)
        kwargs['sup'] = True
        self.superscript = makenode(self.element[1], parent=self,
                                    scriptlevel=self.scriptlevel+1, **kwargs)
        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        self.nodes.append(self.base)
        self.nodexy.append((0, 0))
        x = self.base.bbox.xmax

        supx, supy, xadv = place_super(
            self.base, self.superscript, self.font, self.emscale)
        self.nodes.append(self.superscript)
        self.nodexy.append((x+supx, supy))
        if self.base.bbox.ymax > self.base.bbox.ymin:
            xmin = self.base.bbox.xmin
            xmax = x + xadv
            ymin = min(self.base.bbox.ymin, -supy + self.superscript.bbox.ymin)
            ymax = max(self.base.bbox.ymax, -supy + self.superscript.bbox.ymax)
        else:  # Empty base
            xmin = 0
            ymin = -supy
            xmax = x + xadv
            ymax = -supy + self.superscript.bbox.ymax
        self.bbox = BBox(xmin, xmax, ymin, ymax)

    def firstglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the first glyph in this node '''
        try:
            return self.nodes[0].firstglyph()
        except IndexError:
            return None

    def lastglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the last glyph in this node '''
        try:
            return self.nodes[-1].lastglyph()
        except IndexError:
            return None

    def lastchar(self) -> Optional[str]:
        ''' Get the last character in this node '''
        try:
            return self.nodes[-1].lastchar()
        except IndexError:
            return None


class Msub(Mnode):
    ''' Subscript Node '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        super().__init__(element, parent, scriptlevel, **kwargs)
        assert len(self.element) == 2
        self.base = makenode(self.element[0], parent=self, scriptlevel=self.scriptlevel, **kwargs)
        kwargs['sub'] = True
        self.subscript = makenode(self.element[1], parent=self,
                                  scriptlevel=self.scriptlevel+1, **kwargs)
        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        self.nodes.append(self.base)
        self.nodexy.append((0, 0))
        x = self.base.bbox.xmax

        subx, suby, xadv = place_sub(self.base, self.subscript, self.font, self.emscale)
        self.nodes.append(self.subscript)
        self.nodexy.append((x + subx, suby))
        xmin = self.base.bbox.xmin
        xmax = x + xadv
        ymin = min(self.base.bbox.ymin, -suby+self.subscript.bbox.ymin)
        ymax = max(self.base.bbox.ymax, -suby+self.subscript.bbox.ymax)
        self.bbox = BBox(xmin, xmax, ymin, ymax)

    def firstglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the first glyph in this node '''
        try:
            return self.nodes[0].firstglyph()
        except IndexError:
            return None

    def lastglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the last glyph in this node '''
        try:
            return self.nodes[-1].lastglyph()
        except IndexError:
            return None

    def lastchar(self) -> Optional[str]:
        ''' Get the last character in this node '''
        try:
            return self.nodes[-1].lastchar()
        except IndexError:
            return None


class Msubsup(Mnode):
    ''' Subscript and Superscript together '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        super().__init__(element, parent, scriptlevel, **kwargs)
        assert len(self.element) == 3
        self.base = makenode(self.element[0], parent=self, scriptlevel=self.scriptlevel, **kwargs)
        kwargs['sup'] = True
        kwargs['sub'] = True
        self.subscript = makenode(self.element[1], parent=self, scriptlevel=self.scriptlevel+1, **kwargs)
        self.superscript = makenode(self.element[2], parent=self, scriptlevel=self.scriptlevel+1, **kwargs)
        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        self.nodes.append(self.base)
        self.nodexy.append((0, 0))
        x = self.base.bbox.xmax
        subx, suby, xadvsub = place_sub(self.base, self.subscript, self.font, self.emscale)
        supx, supy, xadvsup = place_super(self.base, self.superscript, self.font, self.emscale)

        # Ensure subSuperscriptGapMin between scripts
        if (suby - self.subscript.bbox.ymax) - (supy-self.superscript.bbox.ymin) < self.font.math.consts.subSuperscriptGapMin*self.emscale:
            diff = self.font.math.consts.subSuperscriptGapMin*self.emscale - (suby - self.subscript.bbox.ymax) + (supy-self.superscript.bbox.ymin)
            suby += diff/2
            supy -= diff/2

        self.nodes.append(self.subscript)
        self.nodexy.append((x + subx, suby))
        self.nodes.append(self.superscript)
        self.nodexy.append((x + supx, supy))

        if self.base.bbox.ymax > self.base.bbox.ymin:
            xmin = self.base.bbox.xmin
            xmax = max(x + xadvsup, x + xadvsub)
            ymin = min(-self.base.bbox.ymin, -suby + self.subscript.bbox.ymin)
            ymax = max(self.base.bbox.ymax, -supy + self.superscript.bbox.ymax)
        else:  # Empty base
            xmin = 0
            ymin = -suby
            xmax = x + max(xadvsub, xadvsup)
            ymax = -supy + self.superscript.bbox.ymax
        
        self.bbox = BBox(xmin, xmax, ymin, ymax)

    def firstglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the first glyph in this node '''
        try:
            return self.nodes[0].firstglyph()
        except IndexError:
            return None

    def lastglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the last glyph in this node '''
        try:
            return self.nodes[-1].lastglyph()
        except IndexError:
            return None

    def lastchar(self) -> Optional[str]:
        ''' Get the last character in this node '''
        try:
            return self.nodes[-1].lastchar()
        except IndexError:
            return None


def place_over(base: Mnode, over: Mnode, font: MathFont, emscale: float) -> tuple[float, float]:
    ''' Place node over another one

        Args:
            base: Base node
            over: Node to draw over the base
            font: Font
            emscale: Font scale

        Returns:
            x, y: position for over node
    '''
    # Center the accent by default
    x = ((base.bbox.xmax - base.bbox.xmin) - (over.bbox.xmax-over.bbox.xmin)) / 2 - over.bbox.xmin

    # Use font-specific accent attachment if defined
    if len(base.nodes) == 1 and isinstance(base.nodes[0], drawable.Glyph):
        gid = base.nodes[0].glyph.index
        basex = font.math.topattachment(gid)
        if basex is not None:
            x = basex*emscale - (over.bbox.xmax-over.bbox.xmin)/2

    y = -base.bbox.ymax-font.math.consts.overbarVerticalGap*emscale
    y += over.bbox.ymin
    return x, y



class Mover(Mnode):
    ''' Over node '''

    # Accents are drawn same scriptlevel as base
    ACCENTS = [
        0x005E, # \hat, \widehat
        0x02D9, # \dot
        0x02C7, # \check
        0x007E, # \tilde, \widetilde
        0x00B4, # \acute
        0x0060, # \grave
        0x00A8, # \ddot
        0x20DB, # \dddot
        0x20DC, # \ddddot
        0x02D8, # \breve
        0x00AF, # \bar
        0x02DA, # \mathring
        ]

    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        super().__init__(element, parent, scriptlevel, **kwargs)
        kwargs = copy(kwargs)
        assert len(self.element) == 2
        self.base = makenode(self.element[0], parent=self, scriptlevel=self.scriptlevel, **kwargs)
        kwargs['width'] = self.base.bbox.xmax - self.base.bbox.xmin

        if self.element[1].text and len(self.element[1].text) == 1 and ord(self.element[1].text) in self.ACCENTS:
            overscriptlevel = self.scriptlevel
        else:
            overscriptlevel = self.scriptlevel + 1

        self.over = makenode(self.element[1], parent=self, scriptlevel=overscriptlevel, **kwargs)
        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        overx, overy = place_over(self.base, self.over, self.font, self.emscale)
        basex = 0.
        if overx < 0:
            basex = -overx
            overx = 0.

        self.nodes.append(self.base)
        self.nodexy.append((basex, 0))
        self.nodes.append(self.over)
        self.nodexy.append((overx, overy))
        xmin = min(overx, self.base.bbox.xmin)
        xmax = max(overx+self.over.bbox.xmax, self.base.bbox.xmax)
        ymin = self.base.bbox.ymin
        ymax = -overy + self.over.bbox.ymax
        self.bbox = BBox(xmin, xmax, ymin, ymax)


def place_under(base: Mnode, under: Mnode, font: MathFont, emscale: float) -> tuple[float, float]:
    ''' Place node under another one
        Args:
            base: Base node
            under: Node to draw under the base
            font: Font
            emscale: Font scale

        Returns:
            x, y: position for under node
    '''
    # TODO accent parameter used to raise/lower
    x = ((base.bbox.xmax - base.bbox.xmin) - (under.bbox.xmax-under.bbox.xmin)) / 2 - under.bbox.xmin
    y = -base.bbox.ymin + font.math.consts.underbarVerticalGap*emscale
    y += (under.bbox.ymax)
    return x, y


class Munder(Mnode):
    ''' Under node '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        super().__init__(element, parent, scriptlevel, **kwargs)
        kwargs = copy(kwargs)
        assert len(self.element) == 2
        self.base = makenode(self.element[0], parent=self, scriptlevel=self.scriptlevel, **kwargs)
        kwargs['sub'] = True
        kwargs['width'] = self.base.bbox.xmax - self.base.bbox.xmin
        self.under = makenode(self.element[1], parent=self, scriptlevel=self.scriptlevel+1, **kwargs)
        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        underx, undery = place_under(self.base, self.under, self.font, self.emscale)

        basex = 0.
        if underx < 0:
            basex = -underx
            underx = 0

        self.nodes.append(self.base)
        self.nodexy.append((basex, 0))
        self.nodes.append(self.under)
        self.nodexy.append((underx, undery))

        xmin = min(underx, self.base.bbox.xmin)
        xmax = max(underx+self.under.bbox.xmax, self.base.bbox.xmax)
        ymin = -undery + self.under.bbox.ymin
        ymax = self.base.bbox.ymax
        self.bbox = BBox(xmin, xmax, ymin, ymax)


class Munderover(Mnode):
    ''' Under bar and over bar '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        super().__init__(element, parent, scriptlevel, **kwargs)
        kwargs = copy(kwargs)
        assert len(self.element) == 3
        self.base = makenode(self.element[0], parent=self, scriptlevel=self.scriptlevel, **kwargs)
        kwargs['width'] = self.base.bbox.xmax - self.base.bbox.xmin
        self.under = makenode(self.element[1], parent=self, scriptlevel=self.scriptlevel+1, **kwargs)

        if self.element[1].text and len(self.element[1].text) == 1 and ord(self.element[1].text) in Mover.ACCENTS:
            overscriptlevel = self.scriptlevel
        else:
            kwargs['sup'] = True
            overscriptlevel = self.scriptlevel + 1

        self.over = makenode(self.element[1], parent=self, scriptlevel=overscriptlevel, **kwargs)

        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        self.nodes = []
        overx, overy = place_over(self.base, self.over, self.font, self.emscale)
        underx, undery = place_under(self.base, self.under, self.font, self.emscale)

        basex = 0.
        if overx < 0 or underx < 0:
            basex = max(-overx, -underx)
            overx, underx = overx - min(overx, underx), underx - min(overx, underx)

        self.nodes.append(self.base)
        self.nodexy.append((basex, 0))
        self.nodes.append(self.over)
        self.nodes.append(self.under)
        self.nodexy.append((overx, overy))
        self.nodexy.append((underx, undery))
        xmin = min(underx, overx, basex+self.base.bbox.xmin)
        xmax = max(underx+self.under.bbox.xmax, overx+self.over.bbox.xmax, basex+self.base.bbox.xmax)
        ymin = -undery + self.under.bbox.ymin
        ymax = -overy + self.over.bbox.ymax
        self.bbox = BBox(xmin, xmax, ymin, ymax)


class Mfrac(Mnode):
    ''' Fraction node '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        self.style = ChainMap(getstyle(element), copy(parent.style))
        if not element.attrib.get('displaystyle') == 'true' and (
            (kwargs.get('frac') or kwargs.get('sup')
            or kwargs.get('sub') or not self.displaystyle())):
            if 'scriptlevel' in element.attrib:
                element.attrib['scriptlevel'] = str(int(element.attrib['scriptlevel']) + 1)
            scriptlevel += 1

        super().__init__(element, parent, scriptlevel, **kwargs)
        assert len(self.element) == 2
        kwargs['frac'] = True
        self.numerator = makenode(self.element[0], parent=self,
                                  scriptlevel=self.scriptlevel, **kwargs)
        self.denominator = makenode(self.element[1], parent=self,
                                    scriptlevel=self.scriptlevel, **kwargs)
        self._setup(**kwargs)
        # TODO: bevelled attribute for x/y fractions with slanty bar

    def _setup(self, **kwargs) -> None:
        ynum = -self.font.math.consts.fractionNumeratorShiftUp * self.emscale
        ydenom = + self.font.math.consts.fractionDenominatorShiftDown * self.emscale
        denombox = self.denominator.bbox
        numbox = self.numerator.bbox

        if ynum + numbox.ymin < 0:
            ynum += numbox.ymin + self.font.math.consts.fractionNumeratorGapMin * self.emscale
        if ydenom - denombox.ymax < 0:
            ydenom -= ydenom - denombox.ymax + self.font.math.consts.fractionDenominatorGapMin * self.emscale

        x = 0.
        if self.leftsibling():
            if isinstance(self.leftsibling(), Mfrac):
                x = getspaceems('verythinmathspace') * self.emscale * self.font.info.layout.unitsperem
            else:
                x = getspaceems('thinmathspace') * self.emscale * self.font.info.layout.unitsperem
        # COULD DO: adjust denominator ydenom to match the sibling
        # and/or adjust sibling's denominator

        width = max(numbox.xmax, denombox.xmax)
        xnum = x + (width - (numbox.xmax - numbox.xmin))/2
        xdenom = x + (width - (denombox.xmax - denombox.xmin))/2
        self.nodes.append(self.numerator)
        self.nodes.append(self.denominator)
        self.nodexy.append((xnum, ynum))
        self.nodexy.append((xdenom, ydenom))

        linethick = self.font.math.consts.fractionRuleThickness*self.emscale
        if 'linethickness' in self.element.attrib:
            lt = self.element.attrib['linethickness']
            try:
                linethick = getdimension(lt, self.emscale)
            except ValueError:
                linethick = {'thin': linethick * .5,
                             'thick': linethick * 2}.get(lt, linethick)

        bary = -self.font.math.consts.axisHeight*self.emscale
        self.nodes.append(drawable.HLine(width, linethick, style=self.style, **kwargs))
        self.nodexy.append((x, bary))

        # Calculate/cache bounding box
        xmin = 0
        xmax = x + max(numbox.xmax, denombox.xmax)
        xmax += getspaceems('thinmathspace')* self.emscale * self.font.info.layout.unitsperem
        ymin = (-ydenom) + denombox.ymin
        ymax = (-ynum) + numbox.ymax
        self.bbox = BBox(xmin, xmax, ymin, ymax)


class Mroot(Mnode):
    ''' Nth root '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        super().__init__(element, parent, scriptlevel, **kwargs)
        self.base = makenode(element[0], parent=self, scriptlevel=self.scriptlevel, **kwargs)
        self.degree: Optional[Mnode]
        self.degree = makenode(element[1], parent=self, scriptlevel=self.scriptlevel+1, **kwargs)
        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        height = self.base.bbox.ymax - self.base.bbox.ymin

        # Get the right glyph to fit the contents
        rglyph = self.font.math.variant(self.font.glyphindex('√'), height/self.emscale, vert=True)
        rootnode = drawable.Glyph(rglyph, '√', self.glyphsize, self.emscale, self.style, **kwargs)

        # Shift radical up/down to ensure minimum gap between top of text and overbar
        # Keep contents at the same height.
        rtop = self.base.bbox.ymax + self.font.math.consts.radicalVerticalGap * self.emscale + \
               self.font.math.consts.radicalRuleThickness * self.emscale
        if ((self.base.bbox.ymin < rglyph.path.bbox.ymin*self.emscale) or
            (rglyph.path.bbox.ymax*self.emscale < self.base.bbox.ymax + self.font.math.consts.radicalVerticalGap * self.emscale)):
            yrad = -(rtop - rglyph.path.bbox.ymax * self.emscale)
        else:
            yrad = 0

        ytop = yrad - rglyph.path.bbox.ymax * self.emscale

        # If the root has a degree, draw it next as it
        # determines radical x position
        self.nodes = []
        x = 0
        if self.degree:
            x += self.font.math.consts.radicalKernBeforeDegree * self.emscale
            ydeg = ytop * self.font.math.consts.radicalDegreeBottomRaisePercent/100
            self.nodes.append(self.degree)
            self.nodexy.append((x, ydeg))
            x += self.degree.bbox.xmax
            x += self.font.math.consts.radicalKernAfterDegree * self.emscale

        self.nodes.append(rootnode)
        self.nodexy.append((x, yrad))
        x += rootnode.bbox.xmax
        self.nodes.append(self.base)
        self.nodexy.append((x, 0))
        width = self.base.bbox.xmax - self.base.bbox.xmin

        lastg = self.base.lastglyph()
        if lastg:
            italicx = self.font.math.italicsCorrection.getvalue(lastg.index)
            if italicx:
                width += italicx * self.emscale

        self.nodes.append(drawable.HLine(width, self.font.math.consts.radicalRuleThickness * self.emscale, style=self.style, **kwargs))
        self.nodexy.append((x, yrad-rglyph.path.bbox.ymax * self.emscale))
        xmin = rglyph.path.bbox.xmin * self.emscale
        xmax = x + width
        ymin = min(-yrad + rglyph.path.bbox.ymin * self.emscale, self.base.bbox.ymin)
        if self.degree:
            ymax = max(-yrad + rglyph.path.bbox.ymax * self.emscale, -ydeg+self.degree.bbox.ymax)
        else:
            ymax = -yrad + rglyph.path.bbox.ymax * self.emscale
        self.bbox = BBox(xmin, xmax, ymin, ymax)


class Msqrt(Mroot):
    ''' Square root '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        Mnode.__init__(self, element, parent, scriptlevel, **kwargs)
        if len(self.element) > 1:
            row = ET.Element('mrow')
            row.extend(list(self.element))
            self.base = makenode(row, parent=self, scriptlevel=self.scriptlevel, **kwargs)
        else:
            self.base = makenode(self.element[0], parent=self, scriptlevel=self.scriptlevel, **kwargs)
        self.degree = None
        self._setup(**kwargs)


class Menclose(Mnode):
    ''' Enclosure '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        super().__init__(element, parent, scriptlevel, **kwargs)
        if len(self.element) > 1:
            row = ET.Element('mrow')
            row.extend(list(self.element))
            self.base = makenode(row, parent=self, scriptlevel=self.scriptlevel, **kwargs)
        else:
            self.base = makenode(self.element[0], parent=self, scriptlevel=self.scriptlevel, **kwargs)
        self.notation = element.attrib.get('notation', 'box').split()
        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        pad = self.font.math.consts.radicalRuleThickness * self.emscale * 2
        height = self.base.bbox.ymax - self.base.bbox.ymin + pad * 2
        width = self.base.bbox.xmax - self.base.bbox.xmin + pad * 2
        lw = self.font.math.consts.radicalRuleThickness * self.emscale
        basex = pad
        xarrow = 0
        yarrow = 0

        if 'box' in self.notation:
            self.nodes.append(drawable.Box(width, height, lw, style=self.style, **kwargs))
            self.nodexy.append((0, -self.base.bbox.ymax+height-pad))
        if 'circle' in self.notation:
            self.nodes.append(drawable.Ellipse(width, height, lw, style=self.style, **kwargs))
            self.nodexy.append((0, -self.base.bbox.ymax+height-pad))
        if 'roundedbox' in self.notation:
            self.nodes.append(drawable.Box(width, height, lw, style=self.style, cornerradius=lw*4, **kwargs))
            self.nodexy.append((0, -self.base.bbox.ymax+height-pad))
            
        if ('top' in self.notation or
            'longdiv' in self.notation or
            'actuarial' in self.notation):
            self.nodes.append(drawable.HLine(width, lw, style=self.style, **kwargs))
            self.nodexy.append((0, -self.base.bbox.ymax-pad))
        if ('bottom' in self.notation or
            'madruwb' in self.notation or
            'phasorangle' in self.notation):
            self.nodes.append(drawable.HLine(width, lw, style=self.style, **kwargs))
            self.nodexy.append((0, -self.base.bbox.ymin+pad))
        if ('right' in self.notation or
            'madruwb' in self.notation or
            'actuarial' in self.notation):
            self.nodes.append(drawable.VLine(height, lw, style=self.style, **kwargs))
            self.nodexy.append((self.base.bbox.xmax+pad*2, -self.base.bbox.ymax-pad))
        if ('left' in self.notation or
            'longdiv' in self.notation):
            self.nodes.append(drawable.VLine(height, lw, style=self.style, **kwargs))
            self.nodexy.append((0, -self.base.bbox.ymax-pad))
        if 'verticalstrike' in self.notation:
            self.nodes.append(drawable.VLine(height, lw, style=self.style, **kwargs))
            self.nodexy.append((width/2, -self.base.bbox.ymax-pad))
        if 'horizontalstrike' in self.notation:
            self.nodes.append(drawable.HLine(width, lw, style=self.style, **kwargs))
            self.nodexy.append((0, -self.base.bbox.ymin-height/2))
            
        if 'updiagonalstrike' in self.notation:
            self.nodes.append(drawable.Diagonal(width, -height, lw, style=self.style, **kwargs))
            self.nodexy.append((0, -self.base.bbox.ymin-height+pad))
        if 'downdiagonalstrike' in self.notation:
            self.nodes.append(drawable.Diagonal(width, height, lw, style=self.style, **kwargs))
            self.nodexy.append((0, -self.base.bbox.ymin+pad))
        if 'phasorangle' in self.notation:
            self.nodes.append(drawable.Diagonal(height/3, -height, lw, style=self.style, **kwargs))
            self.nodexy.append((0, -self.base.bbox.ymin-height+pad))
            basex += height/4  # Shift base right a bit so it fits under angle

        if 'updiagonalarrow' in self.notation:
            self.nodes.append(drawable.Diagonal(width, -height, lw, style=self.style, arrow=True, **kwargs))
            self.nodexy.append((0, -self.base.bbox.ymin-height+pad))
            xarrow = self.nodes[-1].arroww  # type: ignore
            yarrow = self.nodes[-1].arrowh  # type: ignore

        self.nodes.append(self.base)
        self.nodexy.append((basex, 0))

        self.bbox = BBox(0, basex+width+xarrow, self.base.bbox.ymin-pad, height-pad+yarrow)


class Mspace(Mnode):
    ''' Blank space '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        super().__init__(element, parent, scriptlevel, **kwargs)
        self.width = getspaceems(element.attrib.get('width', '0'))  * self.emscale * self.font.info.layout.unitsperem
        self.height = getspaceems(element.attrib.get('height', '0'))  * self.emscale * self.font.info.layout.unitsperem
        self.depth = getspaceems(element.attrib.get('depth', '0'))  * self.emscale * self.font.info.layout.unitsperem
        self._setup(**kwargs)
        
    def _setup(self, **kwargs) -> None:
        self.bbox = BBox(0, self.width, -self.depth, self.height)


class Mpadded(Mrow):
    ''' Mpadded element - Mrow with extra whitespace '''
    def _setup(self, **kwargs):
        super()._setup(**kwargs)
        width = self.element.attrib.get('width', None)
        lspace = self.element.attrib.get('lspace', 0)
        height = self.element.attrib.get('height', None)
        depth = self.element.attrib.get('depth', None)
        xmin, xmax, ymin, ymax = self.bbox

        def adjust(valstr: str, param: float) -> float:
            if valstr.startswith('+') or valstr.startswith('-'):
                sign = width[0]
                if sign == '+':
                    param += getdimension(valstr[1:], self.emscale)
                else:
                    param -= getdimension(valstr[1:], self.emscale)
            elif valstr.endswith('%'):
                param *= float(valstr[:-1])/100
            else:
                param = getdimension(valstr, self.emscale)
            return param

        if width:
            xmax = adjust(width, xmax)
        if height:
            ymax = adjust(height, ymax)
        if depth:
            ymin = -adjust(depth, ymin)
        if lspace:
            xshift = adjust(lspace, 0)
            for i, (x, y) in range(len(self.nodexy)):
                self.nodexy[i] = (x + xshift, y)
        self.bbox = BBox(0, xmax, ymin, ymax)


class Mphantom(Mrow):
    ''' Phantom element. Takes up space but not drawn. '''
    def _setup(self, **kwargs) -> None:
        kwargs['phantom'] = True
        super()._setup(**kwargs)


class Mtable(Mnode):
    ''' Table node '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        super().__init__(element, parent, scriptlevel, **kwargs)
        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        kwargs = copy(kwargs)
        rowspace = getdimension('0.2em', self.emscale)
        colspace = getdimension('0.2em', self.emscale)
        column_align_table = self.element.attrib.get('columnalign', 'center')
        
        # Build node objects from table cells
        rows = []
        for rowelm in self.element:
            assert rowelm.tag == 'mtr'
            column_align_row = rowelm.attrib.get('columnalign', column_align_table).split()

            cells = []
            for i, cellelm in enumerate(rowelm):
                assert cellelm.tag == 'mtd'
                
                if 'columnalign' in cellelm.attrib:
                    column_align = cellelm.attrib.get('columnalign')
                elif i < len(column_align_row):
                    column_align = column_align_row[i]
                else:  # repeat last entry of columnalign
                    column_align = column_align_row[-1]

                cells.append(makenode(cellelm, parent=self, scriptlevel=self.scriptlevel, **kwargs))
                cells[-1].columnalign = column_align
            rows.append(cells)

        # Compute size of each cell to size rows and columns
        rowheights = []  # Maximum height ABOVE baseline
        rowdepths = []   # Maximum distanve BELOW baseline
        for row in rows:
            rowheights.append(max([cell.bbox.ymax for cell in row]))
            rowdepths.append(min([cell.bbox.ymin for cell in row]))

        colwidths = []
        for col in [list(i) for i in zip(*rows)]:  # transposed
            colwidths.append(max([cell.bbox.xmax - cell.bbox.xmin for cell in col]))

        if self.element.attrib.get('equalrows') == 'true':
            rowheights = [max(rowheights)] * len(rows)
            rowdepths = [min(rowdepths)] * len(rows)
        if self.element.attrib.get('equalcolumns') == 'true':
            colwidths = [max(colwidths)] * len(colwidths)

        # Make Baseline of the table half the height
        # Compute baselines to each row
        totheight = sum(rowheights) - sum(rowdepths) + rowspace*(len(rows)-1)
        width = sum(colwidths) + colspace*len(colwidths)
        ytop = -totheight/2 - self.font.math.consts.axisHeight*self.emscale
        baselines = []
        y = ytop
        for h, d in zip(rowheights, rowdepths):
            baselines.append(y + h)
            y += h - d + rowspace

        for r, row in enumerate(rows):
            x = colspace/2
            for c, cell in enumerate(row):
                self.nodes.append(cell)
                cellw = cell.bbox.xmax - cell.bbox.xmin
                if cell.columnalign == 'center':
                    xcell = x + colwidths[c]/2-cellw/2
                elif cell.columnalign == 'right':
                    xcell = x + colwidths[c]-cellw
                else:
                    xcell = x

                self.nodexy.append((xcell, baselines[r]))
                x += colwidths[c] + colspace

        ymin = min([cell.bbox.ymin-baselines[-1] for cell in rows[-1]])
        ymax = max([-baselines[0]+cell.bbox.ymax for cell in rows[0]])
        self.bbox = BBox(0, width, ymin, ymax)


class Mstyle(Mrow):
    ''' Mstyle element - just an mrow with parameters '''
    def __init__(self, element: ET.Element, parent: 'Mnode', scriptlevel: int = 0, **kwargs):
        for elm in element:
            elm.attrib.update(element.attrib)
        super().__init__(element, parent, scriptlevel, **kwargs)
