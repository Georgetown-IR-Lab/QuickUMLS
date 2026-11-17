"""Query the fictional test vocabulary with: python tests/standin.py "amber stone"."""
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from pprint import pprint
from tempfile import TemporaryDirectory
from unittest.mock import patch

import nltk
import spacy
from nltk.corpus.reader import WordListCorpusReader

from quickumls import QuickUMLS, constants

FIXTURES = Path(__file__).resolve().parent / 'fixtures'


def build_index(index, *flags):
    index.mkdir()
    subprocess.run([sys.executable, '-m', 'quickumls.install', '--skip-spacy', *flags,
                    str(FIXTURES / 'umls'), str(index)], check=True, stdout=subprocess.DEVNULL)


@contextmanager
def standin_index():
    with TemporaryDirectory() as tmp:
        index = Path(tmp) / 'index'
        build_index(index, '-L', '-U')
        model = Path(tmp) / 'english'
        spacy.blank('en').to_disk(model)
        with patch.object(nltk.data, 'path', [str(FIXTURES)]):
            words = WordListCorpusReader(str(FIXTURES / 'corpora/stopwords'), ['english'])
            with patch('nltk.corpus.stopwords', words), patch.dict(constants.SPACY_LANGUAGE_MAP, ENG=str(model)):
                yield index


if __name__ == '__main__':
    with standin_index() as index:
        pprint(QuickUMLS(index).match(' '.join(sys.argv[1:]) or 'amber stone'))
