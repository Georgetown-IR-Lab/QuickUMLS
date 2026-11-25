import sys
import unittest
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import spacy
from nltk.corpus.reader import WordListCorpusReader

from quickumls import QuickUMLS, install
from quickumls.about import __version__


class DistributionTest(unittest.TestCase):
    def test_installed_version(self):
        self.assertEqual(version("quickumls"), __version__)

    def test_install_and_match(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = root / "index"
            index.mkdir()
            (root / "MRCONSO.RRF").write_text(
                "C_TEST_001|ENG|||||Y|||||TEST|||emberleaf||||\n", encoding="utf-8"
            )
            (root / "MRSTY.RRF").write_text("C_TEST_001|T047|||||\n", encoding="utf-8")

            (root / "english").write_text("the\n", encoding="utf-8")
            words = WordListCorpusReader(str(root), ["english"])
            with patch("nltk.corpus.stopwords", words), patch("spacy.load", return_value=spacy.blank("en")):
                with patch.object(sys, "argv", ["quickumls.install", str(root), str(index)]):
                    install.main()
                matches = QuickUMLS(index).match("emberleaf")

            self.assertEqual([hit["cui"] for group in matches for hit in group], ["C_TEST_001"])
