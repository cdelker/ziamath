''' Math Font extends Ziafont with MATH table '''

from __future__ import annotations
from typing import Union
from pathlib import Path

from ziafont import Font

from .mathtable import MathTable


class MathFont(Font):
    ''' Extend ziafont by reading MATH table and a base font size

        Args:
            fname: File name of font
            basesize: Default font size
            svg2: Use SVG2.0 specification. Disable for compatibility.
    '''
    def __init__(self, fname: Union[str, Path], basesize: float=24, svg2: bool=True):
        super().__init__(fname, svg2=svg2)
        self.basesize = basesize
        if 'MATH' not in self.tables:
            raise ValueError('Font has no MATH table!')
        self.math = MathTable(self)

