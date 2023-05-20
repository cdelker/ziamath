''' <mn> number math element '''
import xml.etree.ElementTree as ET

from ziafont.fonttypes import BBox

from ..styles import styledstr
from ..drawable import Glyph
from .nodetools import subglyph, elementtext
from .mnode import Mnode


class Mnumber(Mnode, tag='mn'):
    ''' Mnumber node <mn> '''
    def __init__(self, element: ET.Element, parent: 'Mnode', **kwargs):
        super().__init__(element, parent, **kwargs)
        self.string = self._getstring()
        self._setup(**kwargs)

    def _getstring(self) -> str:
        ''' Get the styled string for this node '''
        text = elementtext(self.element)
        return styledstr(text, self.style.mathvariant)

    def _setup(self, **kwargs) -> None:
        ymin = 9999.
        ymax = -9999.
        x = 0.

        if (leftsibling := self.leftsibling()) and leftsibling.mtag == 'mfenced':
            x = self.size_px('verythinmathspace')

        for char in self.string:
            glyph = self.font.glyph(char)
            if kwargs.get('sup') or kwargs.get('sub'):
                glyph = subglyph(glyph, self.font)

            self.nodes.append(
                Glyph(glyph, char, self.glyphsize, self.style, **kwargs))

            if self.nodes[-1].bbox.xmin < 0:
                # don't let glyphs run together if xmin < 0
                x -= self.nodes[-1].bbox.xmin

            self.nodexy.append((x, 0))
            x += self.units_to_points(glyph.advance())
            ymin = min(ymin, self.units_to_points(glyph.path.bbox.ymin))
            ymax = max(ymax, self.units_to_points(glyph.path.bbox.ymax))

        try:
            xmin = self.nodes[0].bbox.xmin
            xmax = self.nodexy[-1][0] + max(self.nodes[-1].bbox.xmax,
                                            self.units_to_points(glyph.advance()))
        except IndexError:
            xmin = 0.
            xmax = x
        self.bbox = BBox(xmin, xmax, ymin, ymax)


class Midentifier(Mnumber, tag='mi'):
    ''' Number node <mn> '''
    def _getstring(self) -> str:
        ''' Get the styled string for the identifier. Applies
            italics if single-char identifier, and extra whitespace
            if function (eg 'sin')
        '''
        text = elementtext(self.element)

        if (len(text) == 1
                and not self.style.mathvariant.italic
                and not self.style.mathvariant.normal):
            self.style.mathvariant.italic = True

        if len(text) > 1:
            text = '\U00002009' + text
            if self.parent.mtag not in ['msub', 'msup', 'msubsup']:
                text = text + '\U00002009'

        return styledstr(text, self.style.mathvariant)


class Mtext(Mnumber, tag='mtext'):
    ''' Text Node <mtext> '''
    def _getstring(self) -> str:
        string = ''
        if self.element.text:
            # Don't use elementtext() since it strips whitespace
            string = styledstr(self.element.text, self.style.mathvariant)
        return string
