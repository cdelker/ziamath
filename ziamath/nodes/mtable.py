''' <mtable> Math Element '''
from xml.etree import ElementTree as ET
from collections import namedtuple
from copy import copy

from ziafont.fonttypes import BBox

from . import Mnode


class Mtable(Mnode, tag='mtable'):
    ''' Table node '''
    def __init__(self, element: ET.Element, parent: 'Mnode', **kwargs):
        super().__init__(element, parent, **kwargs)
        self._setup(**kwargs)

    def _setup(self, **kwargs) -> None:
        kwargs = copy(kwargs)
        rowspace = self.size_px('0.3em')
        colspace = self.size_px('0.3em')
        column_align_table = self.element.get('columnalign', 'center')

        Cell = namedtuple('Cell', 'node columnalign')

        # Build node objects from table cells
        rows = []
        for rowelm in self.element:
            assert rowelm.tag == 'mtr'
            column_align_row = rowelm.get('columnalign', column_align_table).split()

            cells = []
            for i, cellelm in enumerate(rowelm):
                assert cellelm.tag == 'mtd'

                if 'columnalign' in cellelm.attrib:
                    column_align = cellelm.get('columnalign')
                elif i < len(column_align_row):
                    column_align = column_align_row[i]
                else:  # repeat last entry of columnalign
                    column_align = column_align_row[-1]

                cells.append(Cell(Mnode.fromelement(cellelm, parent=self, **kwargs),
                                  column_align))
            rows.append(cells)

        # Compute size of each cell to size rows and columns
        rowheights = []  # Maximum height ABOVE baseline
        rowdepths = []   # Maximum distanve BELOW baseline
        for row in rows:
            rowheights.append(max([cell.node.bbox.ymax for cell in row]))
            rowdepths.append(min([cell.node.bbox.ymin for cell in row]))

        colwidths = [0] * max(len(r) for r in rows)
        for row in rows:
            for c, col in enumerate(row):
                colwidths[c] = max(colwidths[c], col.node.bbox.xmax - col.node.bbox.xmin)
        
        if self.element.get('equalrows') == 'true':
            rowheights = [max(rowheights)] * len(rows)
            rowdepths = [min(rowdepths)] * len(rows)
        if self.element.get('equalcolumns') == 'true':
            colwidths = [max(colwidths)] * len(colwidths)

        # Make Baseline of the table half the height
        # Compute baselines to each row
        totheight = sum(rowheights) - sum(rowdepths) + rowspace*(len(rows)-1)
        width = sum(colwidths) + colspace*len(colwidths)
        ytop = -totheight/2 - self.units_to_points(self.font.math.consts.axisHeight)
        baselines = []
        y = ytop
        for h, d in zip(rowheights, rowdepths):
            baselines.append(y + h)
            y += h - d + rowspace

        for r, row in enumerate(rows):
            x = colspace/2
            for c, cell in enumerate(row):
                self.nodes.append(cell.node)
                cellw = cell.node.bbox.xmax - cell.node.bbox.xmin
                if cell.columnalign == 'center':
                    xcell = x + colwidths[c]/2-cellw/2
                elif cell.columnalign == 'right':
                    xcell = x + colwidths[c]-cellw
                else:
                    xcell = x

                self.nodexy.append((xcell, baselines[r]))
                x += colwidths[c] + colspace

        ymin = min([cell.node.bbox.ymin-baselines[-1] for cell in rows[-1]])
        ymax = max([-baselines[0]+cell.node.bbox.ymax for cell in rows[0]])
        self.bbox = BBox(0, width, ymin, ymax)
