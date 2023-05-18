''' Node spacing functions '''


def space_ems(space: str) -> float:
    ''' Get space in ems from a string. Can be number or named space width. '''
    if space.endswith('em'):
        value = float(space[:-2])
    else:
        value = {"veryverythinmathspace": 1/18,
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
    return value


def topoints(size: str, fontsize: float) -> float:
    ''' Get dimension from string. Either in em or px '''
    try:
        points = float(size)
    except ValueError as exc:
        if size.endswith('em'):
            points = float(size[:-2]) * fontsize
        elif size.endswith('px'):
            points = float(size[:-2])
        elif size.endswith('pt'):
            points = float(size[:-2]) * 1.333
        else:
            raise ValueError(f'Undefined size {size}') from exc
    return points
