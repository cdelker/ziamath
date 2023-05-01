Usage
=====

Installation
------------

Ziamath can be installed using pip:

.. code-block:: bash

    pip install ziamath


Ziamath depends only on two pure-Python packages: `Ziafont <https://ziafont.readthedocs.io>`_, for reading TTF font files, and `latex2mathml <https://pypi.org/project/latex2mathml/>`_ for parsing Latex math expressions.

|

Drawing Equations
-----------------

The :py:class:`ziamath.zmath.Math` class processes and draws a given MathML <math> element.
The Math class has a Jupyter representation that shows the SVG
image as the output of a cell.
To render a `MathML <https://www.w3.org/TR/MathML3/>`_ string:

.. jupyter-execute::

    import ziamath as zm

    eqn = zm.Math('''
                  <mrow>
                      <msup>
                          <mi>x</mi>
                          <mn>2</mn>
                      </msup>
                  </mrow>
                  ''')
    eqn

To get the raw SVG, create the Math object, then use :py:meth:`ziamath.zmath.Math.svg` for the SVG as a string:

.. jupyter-execute::

    eqn.svg()[:80]  # Only show first 80 characters...

or :py:meth:`ziamath.zmath.Math.svgxml` for an XML ElementTree.

.. jupyter-execute::

    eqn.svgxml()


The Math class takes optional parameters for font file name and font size.
The font file must be math-enabled, with an embedded 'MATH' table.

|

Drawing Latex
-------------
 
To render a math expression in Latex format, create the Math object using :py:meth:`ziamath.zmath.Latex`:

.. jupyter-execute::

    zm.Latex(r'c = \pm \sqrt{a^2 + b^2}')

The Latex class inherits from the Math class.

|


Display Mode and Inline Mode
****************************

Latex math is drawn in display (block) mode by default. To render inline (text) mode, set the `inline` parameter to `True`.

.. jupyter-execute::

    zm.Latex(r'\sum_a^b', inline=False)  # Default display mode

.. jupyter-execute::

    zm.Latex(r'\sum_a^b', inline=True)  # Inline mode


|


Mixed Math and Text
-------------------

:py:meth:`ziamath.zmath.Math.fromlatextext` creates a MathML <math> element with text embedded in <mtext> elements.
It takes a string input with math expressions enclosed between single dollar signs $..$ for inline-mode math, and double dollar signs $$..$$ for block or display style math.
This method works for single line math and text expressions.

.. jupyter-execute::

    zm.Math.fromlatextext(r'The volume of a sphere is $V = \frac{4}{3}\pi r^3$.', textstyle='sans')

The `textstyle` argument provides styling to the plain text, and `mathstyle` provides styling
to the math expressions. Both arguments may be an allowable MathML "mathvariant" attribute, such as 'sans', 'serif', 'italic', 'bold', 'sans-bold', etc.

Text Objects
------------

Another option for mixed math and text is the :py:class:`ziamath.zmath.Text` class.
It takes a string, which may contain multiple lines and math expressions enclosed in $..$ or $$..$$,
and draws directly to SVG. The text is drawn directly; no <math> or <mtext> elements are accessible.
Different fonts may be used for the plain text and math portions.

.. jupyter-execute::

    zm.Text(
        r'''The volume of a sphere is
    $V = \frac{4}{3}\pi r^3$
    or in terms of diameter,
    $ V = \frac{\pi d^3}{6}$.
    ''', halign='center')

Text objects support rotation (in degrees) and color (CSS named color or hex color value):

.. jupyter-execute::

    zm.Text('$\\sqrt{a}$', rotation=30, color='mediumslateblue')

