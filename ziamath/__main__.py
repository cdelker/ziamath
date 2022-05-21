import argparse

parser = argparse.ArgumentParser(description="Process some integers.")

parser.add_argument(
    "src", metavar="INPUT", nargs='?', default=None, help="source file"
)

parser.add_argument(
    "-o", dest="dest", metavar="OUTPUT", default=None, help="destination file"
)

parser.add_argument(
    "--cache",
    dest="cache",
    action="store_true",
    default=None,
    help="reference identical glyph",
)

parser.add_argument(
    "--no-cache",
    dest="cache",
    action="store_false",
    help="identical glyph duplicated",
)

parser.add_argument(
    "--latex",
    dest="latex",
    action="store_true",
    default=None,
    help="input is latex",
)

parser.add_argument(
    "--precision",
    "-p",
    dest="precision",
    type=int,
    default=None,
    help="decimal precision to use in SVG path coordinates",
)

parser.add_argument(
    "--size",
    "-s",
    dest="size",
    type=int,
    default=None,
    help="font size to use in pixels",
)

parser.add_argument(
    "--font",
    "-f",
    default=None,
    dest="font_file",
    help="font file, must contain MATH typesetting table",
)

parser.add_argument(
    "--defs",
    action="store_true",
    default=None,
    help="Put symbols inside defs",
)


################


def as_source(path, mode="rb"):
    if path and path != "-":
        return open(path, mode)
    from sys import stdin

    return stdin.buffer if "b" in mode else stdin


def as_sink(path, mode="wb"):
    if path and path != "-":
        return open(path, mode)
    from sys import stdout

    return stdout.buffer if "b" in mode else stdout


args = parser.parse_args()

from xml.etree import ElementTree as ET

kwopt = {}

if args.size is not None:
    kwopt["size"] = args.size

if args.cache is not None:
    kwopt["svg2"] = args.cache

if args.precision is not None:
    from .zmath import set_precision

    set_precision(args.precision)

if args.font_file is not None:
    kwopt["font"] = args.font_file

# print(args, kwopt)

with as_source(args.src) as src:
    from .zmath import Math

    if args.latex:
        mml = Math.fromlatex(src.read().decode("UTF-8").strip(), **kwopt)
        svg = mml.svgxml()
    else:
        mml = ET.parse(src)
        mmr = Math(mml.getroot(), **kwopt)
        svg = mmr.svgxml()
    if args.defs:
        defs = None
        for p in list(svg.iter("symbol")):
            if not defs:
                defs = ET.SubElement(svg, "defs")
            svg.remove(p)
            defs.append(p)
    with as_sink(args.dest, "wb") as w:
        etr = ET.ElementTree(svg)
        etr.write(w)
