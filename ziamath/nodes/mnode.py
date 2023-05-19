''' Math node - parent class of all math nodes '''
from __future__ import annotations
from typing import Optional, MutableMapping, Type
import logging
from xml.etree import ElementTree as ET

from ziafont.fonttypes import BBox
from ziafont.glyph import SimpleGlyph, fmt

from ..mathfont import MathFont
from ..drawable import Drawable
from ..styles import MathStyle, parse_style
from ..config import config
from .. import operators
from .spacing import space_ems
from .nodetools import elementtext, infer_opform

_node_classes: dict[str, Type['Mnode']] = {}


class Mnode(Drawable):
    ''' Math Drawing Node

        Args:
            element: XML element for the node
            size: base font size in points
            parent: Mnode of parent
    '''
    mtag = 'mnode'

    def __init__(self, element: ET.Element, parent: 'Mnode', **kwargs):
        super().__init__()
        self.element = element
        self.font: MathFont = parent.font
        self.parent = parent
        self.size: float = parent.size
        self.style: MathStyle = parse_style(self.element, parent.style)
        self.params: MutableMapping[str, str] = {}
        self.nodes: list[Drawable] = []
        self.nodexy: list[tuple[float, float]] = []
        self.glyphsize = max(
            self.size * (self.font.math.consts.scriptPercentScaleDown/100)**self.style.scriptlevel,
            self.font.basesize*config.minsizefraction)
        if self.style.mathsize:
            self.glyphsize = self.ems_to_pts(space_ems(self.style.mathsize))

        self._font_pts_per_unit = self.size / self.font.info.layout.unitsperem
        self._glyph_pts_per_unit = self.glyphsize / self.font.info.layout.unitsperem
        self.bbox = BBox(0, 0, 0, 0)

    def __init_subclass__(cls, tag: str) -> None:
        ''' Register this subclass so fromelement() can find it '''
        _node_classes[tag] = cls
        cls.mtag = tag

    @classmethod
    def fromelement(cls, element: ET.Element, parent: 'Mnode', **kwargs) -> 'Mnode':
        ''' Construct a new node from the element and its parent '''
        if element.tag in ['math', 'mtd', 'mtr']:
            element.tag = 'mrow'

        if element.tag == 'mi' and elementtext(element) in operators.names:
            # Workaround for some latex2mathml operators coming back as identifiers
            element.tag = 'mo'

        if element.tag == 'mo':
            infer_opform(0, element, parent)

        node = _node_classes.get(element.tag, None)
        if node:
            return node(element, parent, **kwargs)

        logging.warning('Undefined element %s', element)
        return _node_classes['mrow'](element, parent, **kwargs)

    def _setup(self, **kwargs) -> None:
        ''' Calculate node position assuming this node is at 0, 0. Also set bbox. '''
        self.bbox = BBox(0, 0, 0, 0)

    def units_to_points(self, value: float) -> float:
        ''' Convert value in font units to points at this glyph size '''
        return value * self._glyph_pts_per_unit

    def font_units_to_points(self, value: float) -> float:
        ''' Convert value in font units to points at the base font size '''
        return value * self._font_pts_per_unit

    def points_to_units(self, value: float) -> float:
        ''' Convert points back to font units '''
        return value / self._glyph_pts_per_unit

    def ems_to_pts(self, value: float) -> float:
        ''' Convert ems at this glyph size to points '''
        return value * self.glyphsize

    def increase_child_scriptlevel(self, element: ET.Element) -> None:
        ''' Increase the child element's script level one higher
            than this element, if not overridden in child's attributes
        '''
        element.attrib.setdefault('scriptlevel', str(self.style.scriptlevel+1))

    def leftsibling(self) -> Optional[Drawable]:
        ''' Left node sibling. The one that was just placed. '''
        try:
            node = self.parent.nodes[-1]
            if node.mtag == 'mrow' and node.nodes:
                node = node.nodes[-1]
        except (IndexError, AttributeError):
            node = None

        return node

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

    def draw(self, x: float, y: float, svg: ET.Element) -> tuple[float, float]:
        ''' Draw the node on the SVG

            Args:
                x: Horizontal position in SVG coordinates
                y: Vertical position in SVG coordinates
                svg: SVG drawing as XML
        '''
        if config.debug:
            rect = ET.SubElement(svg, 'rect')
            rect.set('x', fmt(x + self.bbox.xmin))
            rect.set('y', fmt(y - self.bbox.ymax))
            rect.set('width', fmt((self.bbox.xmax - self.bbox.xmin)))
            rect.set('height', fmt((self.bbox.ymax - self.bbox.ymin)))
            rect.set('fill', 'none')
            rect.set('stroke', 'blue')
            rect.set('stroke-width', '0.2')
            base = ET.SubElement(svg, 'path')
            base.set('d', f'M {x} 0 L {x+self.bbox.xmax} 0')
            base.set('stroke', 'red')

        if self.style.mathbackground not in ['none', None]:
            rect = ET.SubElement(svg, 'rect')
            rect.set('x', fmt(x + self.bbox.xmin))
            rect.set('y', fmt(y - self.bbox.ymax))
            rect.set('width', fmt((self.bbox.xmax - self.bbox.xmin)))
            rect.set('height', fmt((self.bbox.ymax - self.bbox.ymin)))
            rect.set('fill', str(self.style.mathbackground))

        nodex = nodey = 0.
        for (nodex, nodey), node in zip(self.nodexy, self.nodes):
            node.draw(x+nodex, y+nodey, svg)
        return x+nodex, y+nodey
