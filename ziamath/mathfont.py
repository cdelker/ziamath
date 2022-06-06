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
    '''
    def __init__(self, fname: Union[str, Path], basesize: float=24):
        super().__init__(fname)
        self.basesize = basesize
        if 'MATH' not in self.tables:
            raise ValueError('Font has no MATH table!')
        self.math = MathTable(self)

