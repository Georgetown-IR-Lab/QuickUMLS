from setuptools import setup

import quickumls

with open('README.md') as reader:
    readme = reader.read()

setup(
    name=quickumls.__title__,
    version=quickumls.__version__,
    description=(
        'QuickUMLS is a tool for fast, unsupervised biomedical '
        'concept extraction from medical text'
    ),
    long_description=readme,
    author=quickumls.__author__,
    author_email='luca@ir.cs.georgetown.edu',
    url='https://github.com/Georgetown-IR-Lab/QuickUMLS',
    license=quickumls.__license__,
    packages=['quickumls'],
    install_requires=[],
)
