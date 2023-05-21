''' <mrow> Math Elelment '''
from __future__ import annotations
from typing import Optional, Union
from copy import copy
from xml.etree import ElementTree as ET

from ziafont.fonttypes import BBox
from ziafont.glyph import SimpleGlyph, fmt

from ..drawable import Drawable
from .. import operators
from .nodetools import infer_opform, elementtext
from .mnode import Mnode


class Mrow(Mnode, tag='mrow'):
    ''' Math row, list of vertically aligned Mnodes '''
    def __init__(self, element: ET.Element, parent: 'Mnode', **kwargs):
        super().__init__(element, parent, **kwargs)
        self._setup(**kwargs)

    def _break_lines(self) -> list[list[ET.Element]]:
        ''' Break mrow into lines - to handle mspace linebreak (// in latex) '''
        lines = []
        line: list[ET.Element] = []
        for i, child in enumerate(self.element):
            if child.tag == 'mi' and elementtext(child) in operators.names:
                # Workaround for some latex2mathml operators coming back as identifiers
                child.tag = 'mo'

            if child.tag == 'mo':
                infer_opform(i, child, self)
            if child.tag == 'mspace' and child.get('linebreak', None) == 'newline':
                lines.append(line)
                line = []
            else:
                line.append(child)
        lines.append(line)
        return lines

    def _setup_multilines(self, lines: list[list[ET.Element]], **kwargs) -> None:
        ''' Multiline mrow - process each line as an mrow so we can
            get its bounding box '''
        node: Union[Mnode, Drawable]
        for i, line in enumerate(lines):
            mrowelm = ET.Element('mrow')
            mrowelm.extend(line)
            node = Mrow(mrowelm, parent=self)
            self.nodes.append(node)

        y = 0
        for i, node in enumerate(self.nodes):
            if i > 0:
                y += (node.bbox.ymax - self.nodes[i-1].bbox.ymin +
                      2 * self.units_to_points(self.font.math.consts.mathLeading))
            self.nodexy.append((0, y))
        xmin = min([n.bbox.xmin for n in self.nodes])
        xmax = max([n.bbox.xmax for n in self.nodes])
        ymin = -y+self.nodes[-1].bbox.ymin
        ymax = self.nodes[0].bbox.ymax
        self.bbox = BBox(xmin, xmax, ymin, ymax)

    def _setup_single_line(self, line: list[ET.Element], **kwargs) -> None:
        ''' Single line mrow '''
        ymax = -9999
        ymin = 9999
        height = kwargs.pop('height', None)
        i = 0
        x = xmin = xmax = 0.
        while i < len(line):
            child = line[i]
            text = elementtext(child)
            if child.tag == 'mo':
                if (text in operators.fences
                        and child.get('form') == 'prefix'
                        and child.get('stretchy') != 'false'):
                    fencekwargs = copy(kwargs)
                    j = 0
                    for j in range(i+1, len(self.element)):
                        if (self.element[j].tag == 'mo'
                                and self.element[j].get('form') == 'postfix'
                                and elementtext(self.element[j]) in operators.fences):
                            children = self.element[i+1: j]
                            fencekwargs['open'] = elementtext(child)
                            fencekwargs['close'] = elementtext(self.element[j])
                            break
                    else:  # No postfix closing fence. Enclose remainder of row.
                        children = self.element[i+1:]
                        fencekwargs['open'] = elementtext(child)
                        fencekwargs['close'] = None
                    fencekwargs['separators'] = ''
                    fenced = ET.Element('mfenced')
                    fenced.attrib.update(child.attrib)
                    fenced.attrib.update(fencekwargs)
                    fenced.extend(children)
                    node = Mnode.fromelement(fenced, parent=self, **kwargs)
                    i = j + 1

                else:
                    if text == '':
                        i += 1
                        continue  # InvisibleTimes, etc.
                    node = Mnode.fromelement(child, parent=self, height=height, **kwargs)
                    i += 1
            else:
                node = Mnode.fromelement(child, parent=self, **kwargs)
                i += 1

            self.nodes.append(node)
            self.nodexy.append((x, 0))
            xmax = max(xmax, x + node.bbox.xmax)
            xmin = min([nxy[0]+n.bbox.xmin for nxy, n in zip(self.nodexy, self.nodes)])
            ymax = max(ymax, node.bbox.ymax)
            ymin = min(ymin, node.bbox.ymin)
            x += node.xadvance()
        self.bbox = BBox(xmin, xmax, ymin, ymax)

    def _setup(self, **kwargs) -> None:
        kwargs = copy(kwargs)
        self.nodes = []

        lines = self._break_lines()
        if len(lines) > 1:
            self._setup_multilines(lines, **kwargs)
        else:
            self._setup_single_line(lines[0], **kwargs)

    def firstglyph(self) -> Optional[SimpleGlyph]:
        ''' Get the first glyph in this node '''
        i = 0
        while (i < len(self.nodes) and
               isinstance(self.nodes[i], Mnode) and
               self.nodes[i].mtag == 'mspace' and
               self.nodes[i].width <= 0):  # type: ignore
            i += 1  # Negative space shouldn't count as first glyph

        try:
            glyph = self.nodes[i].firstglyph()
        except IndexError:
            return None
        return glyph


class Merror(Mrow, tag='merror'):
    ''' Error node <merror>. Just an <mrow> with border and fill. '''
    def draw(self, x: float, y: float, svg: ET.Element) -> tuple[float, float]:
        xend, yend = super().draw(x, y, svg)
        border = ET.SubElement(svg, 'rect')
        border.set('x', fmt(x + self.bbox.xmin - 1))
        border.set('y', fmt(y - self.bbox.ymax - 1))
        border.set('width', fmt((self.bbox.xmax - self.bbox.xmin)+2))
        border.set('height', fmt((self.bbox.ymax - self.bbox.ymin)+2))
        border.set('fill', 'yellow')
        border.set('fill-opacity', '0.2')
        border.set('stroke', 'red')
        border.set('stroke-width', '1')
        return xend, yend