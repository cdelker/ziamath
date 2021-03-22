import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name = 'ziamath',
    version = '0.1',
    description = 'Render MathML and LaTeX Math to SVG without Latex installation',
    author = 'Collin J. Delker',
    author_email = 'ziaplot@collindelker.com',
    url = 'https://ziamath.readthedocs.io/',
    long_description=long_description,
    long_description_content_type="text/markdown",
    project_urls={
        'Source': 'https://bitbucket.org/cdelker/ziamath',
    },
    python_requires='>=3.8',
    packages=setuptools.find_packages(),
    package_data = {'ziamath': ['py.typed'],
                    'ziamath.fonts': ['STIXTwoMath-Regular.ttf']},
    zip_safe=False,
    keywords = ['MathML', 'LaTeX', 'math', 'font', 'truetype', 'opentype', 'svg'],
    install_requires=['ziafont'],
    extras_require={
        'latex':  ['latex2mathml'],
    },
    classifiers = [
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Development Status :: 4 - Beta',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Intended Audience :: Education',
    'Intended Audience :: Science/Research',
    'Intended Audience :: End Users/Desktop',
    'Intended Audience :: Developers',
    ],
)
