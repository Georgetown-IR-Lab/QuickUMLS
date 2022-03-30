import contextlib
import io
import os
import sys

from setuptools import find_packages, setup

PACKAGES = find_packages()

# From https://github.com/explosion/spaCy/blob/master/setup.py
@contextlib.contextmanager
def chdir(new_dir):
    old_dir = os.getcwd()
    try:
        os.chdir(new_dir)
        sys.path.insert(0, new_dir)
        yield
    finally:
        del sys.path[0]
        os.chdir(old_dir)


def setup_package():
    root = os.path.abspath(os.path.dirname(__file__))

    with open("README.md") as reader:
        readme = reader.read()

    with open("requirements.txt") as f:
        requirements = f.read().splitlines()

    dependency_links = []
    i = 0
    while i < len(requirements):
        if requirements[i].startswith("https://"):
            dependency_links.append(requirements.pop(i))
        else:
            i += 1

    # From https://github.com/explosion/spaCy/blob/master/setup.py
    with chdir(root):
        with io.open(os.path.join(root, "quickumls", "about.py"), encoding="utf8") as f:
            about = {}
            exec(f.read(), about)

    setup(
        name=about["__title__"],
        version=about["__version__"],
        description=(
            "QuickUMLS is a tool for fast, unsupervised biomedical "
            "concept extraction from medical text"
        ),
        packages=PACKAGES,
        long_description=readme,
        long_description_content_type="text/markdown",
        author=about["__author__"],
        author_email=about["__email__"],
        url="https://github.com/Georgetown-IR-Lab/QuickUMLS",
        license=about["__license__"],
        install_requires=requirements,
        dependency_links=dependency_links,
        classifiers=[
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 2",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Development Status :: 5 - Production/Stable",
            "Topic :: Scientific/Engineering :: Artificial Intelligence",
            "Topic :: Scientific/Engineering :: Bio-Informatics",
        ],
    )


if __name__ == "__main__":
    setup_package()
