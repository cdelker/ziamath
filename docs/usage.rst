Usage
=====

All math expressions are created and drawn using the :py:class:`ziamath.zmath.Math` class.
The Math class has a Jupyter representation that shows the SVG
image as the output of a cell.
To render a `MathML <https://www.w3.org/TR/MathML3/>`_ string:

.. jupyter-execute::

    import ziamath as zm

    zm.Math('''
        <mrow>
            <msup>
                <mi>x</mi>
                <mn>2</mn>
            </msup>
        </mrow>
        ''')

To get the raw SVG, create the Math object, then use :py:meth:`ziamath.zmath.Math.svg` for the SVG as a string, or :py:meth:`ziamath.zmath.Math.svgxml` for an XML ElementTree.

.. jupyter-execute::

    zm.Math('''
        <mrow>
            <msup>
                <mi>x</mi>
                <mn>2</mn>
            </msup>
        </mrow>
        ''').svgxml()


The Math class takes optional parameters for font file name and font size.
The font file must be math-enabled, with an embedded 'MATH' table.


Drawing Latex
-------------
 
To render a math expression in Latex format, create the Math object using :py:meth:`ziamath.zmath.Math.fromlatex`:

.. jupyter-execute::

    zm.Math.fromlatex(r'c = \pm \sqrt{a^2 + b^2}')


Text containing embedded math, enclosed within $..$, can also be drawn using :py:meth:`ziamath.zmath.Math.fromlatextext`.

.. jupyter-execute::

    zm.Math.fromlatextext(r'The volume of a sphere is $V = \frac{4}{3}\pi r^3$.', textstyle='sans')

The `textstyle` argument provides styling to the plain text, and `mathstyle` provides styling
to the math expressions. Both arguments may be an allowable MathML "mathvariant" attribute, such as 'sans', 'serif', 'italic', 'bold', 'sans-bold', etc.


Drawing on an existing SVG
--------------------------

To draw math expressions on an existing SVG, create the SVG XML structure using an `XML Element Tree <https://docs.python.org/3/library/xml.etree.elementtree.html>`_.
Then use :py:meth:`ziamath.zmath.Math.drawon`, with the x and y position and svg to draw on:

.. jupyter-execute::

    from IPython.display import SVG
    from xml.etree import ElementTree as ET

    svg = ET.Element('svg')
    svg.attrib['width'] = '200'
    svg.attrib['height'] = '100'
    svg.attrib['xmlns'] = 'http://www.w3.org/2000/svg'
    svg.attrib['viewBox'] = f'0 0 100 100'
    circ = ET.SubElement(svg, 'circle')
    circ.attrib['cx'] = '20'
    circ.attrib['cy'] = '25'
    circ.attrib['r'] = '25'
    circ.attrib['fill'] = 'orange'

    myequation = zm.Math.fromlatex(r'\int_0^1 f(x) \mathrm{d}x', size=18)
    myequation.drawon(50, 45, svg)

    SVG(ET.tostring(svg))


SVG Version Compatibility
-------------------------

Some SVG renderers, including recent versions of Inkscape and some OS built-in image viewers, are not fully compatible with the SVG 2.0 specification.
Set the `svg2` Font parameter to `False` for better compatibility. This may result in larger file sizes
as each glyph is included as its own <path> element rather than being reused with <symbol> and <use> elements.

.. code-block:: python

    zm.Math.fromlatextext('$x^2 + y^2$', svg2=False)


Limitations
-----------

Not every MathML element is implemented at this time.
Unsupported elements and attributes inculde:

- <mstyle>
- <ms>
- <mglyph>
- <merror>
- <menclose>
- <mmultiscripts>
- <mlabeledtr>
- color and background attributes
- scriptlevel attribute
- table alignment attributes


See some :ref:`examples` of expressions drawn with Ziamath.


Math Class
----------

.. autoclass:: ziamath.zmath.Math
    :members: