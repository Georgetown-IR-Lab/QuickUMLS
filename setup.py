from setuptools import setup

requires = [
    'leveldb>=0.193',
    'numpy>=1.8.2',
    'spacy>=1.6.0',
    'unidecode>=0.4.19'
    ]

setup(name='QuickUMLS',
      version='1.0',
      description='Forked from https://github.com/Georgetown-IR-Lab/QuickUMLS',
      author='Tiago Ferreira',
      author_email='hello@tiagoferreira.me',
      url='https://github.com/tiago-ferreiraa/QuickUMLS',
      zip_safe=False,
      install_requires=requires,
      )
