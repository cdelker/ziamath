''' <mroot> and <msqrt> Math Elements '''
from typing import Optional
import xml.etree.ElementTree as ET

from ziafont.fonttypes import BBox

from ..drawable import Glyph, HLine
from . import Mnode


class Mroot(Mnode, tag='mroot'):
    ''' Nth root '''
    def __init__(self, element: ET.Element, parent: 'Mnode', **kwargs):
        super().__init__(element, parent, **kwargs)
        self.base, self.degree = self._getbase(**kwargs)
        self._setup(**kwargs)

    def _getbase(self, **kwargs) -> tuple[Mnode, Optional[Mnode]]:
        ''' Get base and optional degree nodes for the root '''
        base = Mnode.fromelement(self.element[0], parent=self, **kwargs)
        self.increase_child_scriptlevel(self.element[1])
        degree = Mnode.fromelement(self.element[1], parent=self, **kwargs)
        return base, degree

    def _setup(self, **kwargs) -> None:
        height = self.base.bbox.ymax - self.base.bbox.ymin

        # Get the right root glyph to fit the contents
        rglyph = self.font.math.variant(self.font.glyphindex('√'),
                                        self.points_to_units(height))
        rootnode = Glyph(rglyph, '√', self.glyphsize, self.style, **kwargs)

        if self.style.displaystyle:
            verticalgap = self.units_to_points(self.font.math.consts.radicalDisplayStyleVerticalGap)
        else:
            verticalgap = self.units_to_points(self.font.math.consts.radicalVerticalGap)

        # Shift radical up/down to ensure minimum and consistent gap between top of text and overbar
        # Keep contents at the same height.
        rtop = (self.base.bbox.ymax + verticalgap +
                self.units_to_points(self.font.math.consts.radicalRuleThickness))
        yrad = -(rtop - self.units_to_points(rglyph.path.bbox.ymax))
        ytop = yrad - self.units_to_points(rglyph.path.bbox.ymax)

        # If the root has a degree, draw it next as it
        # determines radical x position
        self.nodes = []
        x = 0.
        if self.degree:
            x += self.units_to_points(self.font.math.consts.radicalKernBeforeDegree)
            ydeg = ytop * self.font.math.consts.radicalDegreeBottomRaisePercent/100
            self.nodes.append(self.degree)
            self.nodexy.append((x, ydeg))
            x += self.degree.bbox.xmax
            x += self.units_to_points(self.font.math.consts.radicalKernAfterDegree)

        self.nodes.append(rootnode)
        self.nodexy.append((x, yrad))
        x += rootnode.bbox.xmax
        self.nodes.append(self.base)
        self.nodexy.append((x, 0))
        width = self.base.bbox.xmax

        if (lastg := self.base.lastglyph()):
            if (italicx := self.font.math.italicsCorrection.getvalue(lastg.index)):
                width += self.units_to_points(italicx)

        self.nodes.append(HLine(
            width, self.units_to_points(self.font.math.consts.radicalRuleThickness),
            style=self.style, **kwargs))
        self.nodexy.append((x, yrad - self.units_to_points(rglyph.path.bbox.ymax)))
        xmin = self.units_to_points(rglyph.path.bbox.xmin)
        xmax = x + width
        ymin = min(-yrad + self.units_to_points(rglyph.path.bbox.ymin),
                   self.base.bbox.ymin)
        if self.degree:
            ymax = max(-yrad + self.units_to_points(rglyph.path.bbox.ymax),
                       -ydeg+self.degree.bbox.ymax)
        else:
            ymax = -yrad + self.units_to_points(rglyph.path.bbox.ymax)
        self.bbox = BBox(xmin, xmax, ymin, ymax)


class Msqrt(Mroot, tag='msqrt'):
    ''' Square root '''
    def _getbase(self, **kwargs) -> tuple[Mnode, Optional[Mnode]]:
        ''' Get base and optional degree nodes for the root '''
        if len(self.element) > 1:
            row = ET.Element('mrow')
            row.extend(list(self.element))
            base = Mnode.fromelement(row, parent=self, **kwargs)
        else:
            base = Mnode.fromelement(self.element[0], parent=self, **kwargs)
        return base, None
