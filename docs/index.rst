Ziamath
=======

Ziamath renders MathML or LaTeX Math expressions as SVG paths using only the Python standard library. Does not require a Latex installation, nor rely on any third party services, but rather uses math-enabled fonts, such as `STIXTwoMath-Regular <https://www.stixfonts.org/>`_ which comes included with Ziamath
for use by default. The resulting SVGs are drawn entirely with <path> elements, so the image does not depend on
having the font available.


Example
-------

To render from MathML:

.. jupyter-execute::

    import ziamath as zm
    zm.Math(
    '''<mrow>
         <mi> y </mi>
         <mo> = </mo>
         <mi> f </mi>
         <mo> &ApplyFunction; </mo>
         <mrow>
           <mo> ( </mo>
           <mi> x </mi>
           <mo> ) </mo>
         </mrow>
       </mrow>''')

|

To render from Latex:

.. jupyter-execute::

    zm.Latex(r'\frac{1}{1-x^2}')

|

Demo
----

See Ziamath in action as it runs in your browser through PyScript `here <https://cdelker.bitbucket.io/pyscript/ziamath.html>`_!

|

Support
-------

If you appreciate Ziamath, buy me a coffee to show your support!

.. raw:: html

    <script type="text/javascript" src="https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js" data-name="bmc-button" data-slug="cdelker" data-color="#FFDD00" data-emoji=""  data-font="Cookie" data-text="Buy me a coffee" data-outline-color="#000000" data-font-color="#000000" data-coffee-color="#ffffff" ></script>

|

----

Source code is available on `Github <https://github.com/cdelker/ziamath>`_.

Ziamath is also used by the `Ziaplot <https://ziaplot.readthedocs.io>`_ and `Schemdraw <https://schemdraw.readthedocs.io>`_ Python packages, and was used for rendering the SVG and PNG equations on `MathGrabber <https://mathgrabber.com>`_.

|

----

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   usage.rst
   options.rst
   examples.rst
   test.rst
   changes.rst
   api.rst
