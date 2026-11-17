import io
import os
import unittest
from collections import defaultdict
from contextlib import ExitStack, redirect_stderr
from pathlib import Path
from unittest.mock import patch

import spacy
from spacy.tokens import Span
from unidecode import unidecode

from quickumls import QuickUMLS, server
from quickumls import spacy_component  # Register the spaCy factory.
from standin import FIXTURES, build_index, standin_index

SANDBOX = Path(__file__).resolve().parents[1] / '.sandbox'


class BuiltIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stack = ExitStack()
        cls.addClassCleanup(stack.close)
        cls.index = stack.enter_context(standin_index())
        cls.matcher = QuickUMLS(cls.index, threshold=1)
        cls.addClassCleanup(delattr, cls, 'matcher')

    def test_match_flags(self):
        cases = [({}, ['amber stone']),
                 ({'best_match': False}, ['amber', 'amber stone', 'stone']),
                 ({'ignore_syntax': True}, ['amber stone', 'the']),
                 ({'best_match': False, 'ignore_syntax': True}, ['amber', 'amber stone', 'stone', 'the'])]
        for flags, terms in cases:
            with self.subTest(flags=flags):
                matches = self.matcher.match('amber stone the', **flags)
                self.assertCountEqual([g[0]['term'] for g in matches], terms)
        self.assertEqual(len(self.matcher.match('amber', best_match=False)), 1)
        self.assertEqual(self.matcher.match('amber, pebble')[0][0]['term'], 'amber')
        self.assertEqual(self.matcher.match('amber, pebble', ignore_syntax=True)[0][0]['term'], 'amber, pebble')

    def test_index_round_trip(self):
        hits = self.matcher.match('A CAFÉ.')[0]
        self.assertCountEqual([(h['cui'], h['semtypes'], h['preferred']) for h in hits],
                              [('C4', {'T047', 'T184'}, 0), ('C5', {'T184'}, 1)])
        self.assertTrue(all((h['start'], h['end'], h['similarity']) == (2, 6, 1) for h in hits))
        self.assertEqual(self.matcher.match('ámbar'), [])

    def test_distinct_unicode_spellings(self):
        index = self.index.parent / 'unicode-index'
        build_index(index, '-L')
        db = QuickUMLS(index, spacy_component=True).cuisem_db
        self.assertCountEqual([(cui, pref) for cui, _, pref in db.get('café')],
                              [('C4', 0), ('C4', 1), ('C5', 1)])

    def test_custom_model(self):
        model = self.index.parent / 'model'
        spacy.blank('de').to_disk(model)
        matcher = QuickUMLS(self.index, spacy_model=model)
        self.assertEqual(matcher.nlp.lang, 'de')
        self.assertEqual(matcher.match('amber')[0][0]['cui'], 'C1')
        with self.assertRaisesRegex(OSError, 'quickumls_missing_model'):
            QuickUMLS(self.index, spacy_model='quickumls_missing_model')

    def test_server_filter(self):
        for args, cuis in [([], {'C4', 'C5'}), (['--accepted-semtypes', 'T047'], {'C4'})]:
            with patch.object(server, 'run_server') as serve:
                server.run_quickumls_server(server.parse_args([str(self.index)] + args))
            hits = serve.call_args.args[0].match('café')[0]
            self.assertEqual({h['cui'] for h in hits}, cuis)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            server.parse_args([str(self.index), '--accepted-semtypes', '047'])

    def test_spacy_entities_and_alternatives(self):
        for _ in range(2):  # Extensions are shared across independent pipelines.
            nlp = spacy.blank('en')
            with patch.object(spacy, 'load', side_effect=AssertionError('redundant model load')):
                nlp.add_pipe('quickumls', config={'quickumls_fp': str(self.index),
                             'options': {'best_match': False, 'threshold': 1.0}})
            doc = nlp.make_doc('amber stone café')
            doc.ents = [Span(doc, 0, 1, label='EXISTING')]
            nlp(doc)
            self.assertEqual([(e.text, e.label_) for e in doc.ents],
                             [('amber', 'EXISTING'), ('stone', 'C6'), ('café', 'C5')])
            self.assertEqual(doc.ents[-1]._.semtypes, {'T184'})
            self.assertEqual({h['cui'] for g in doc._.quickumls for h in g}, {'C1', 'C2', 'C4', 'C5', 'C6'})
            self.assertEqual([e.text for e in nlp('amber stone').ents], ['amber stone'])

    def test_fuzzy_overlap_policy(self):
        for policy, winner in [('score', 'amber'), ('length', 'amber stony')]:
            nlp = spacy.blank('en')
            nlp.add_pipe('quickumls', config={'quickumls_fp': str(self.index),
                         'options': {'overlapping_criteria': policy, 'threshold': 0.6}})
            self.assertEqual([e.text for e in nlp('amber stony').ents], [winner])


class SourceIndex(unittest.TestCase):
    def test_all_sampled_atoms_against_source(self):
        full = os.environ.get('QUICKUMLS_TEST_FULL') == '1'
        if full or os.environ.get('QUICKUMLS_TEST_LICENSED') == '1':
            root = SANDBOX / 'full' if full else SANDBOX
            index, meta, sample = root / 'index', root / 'META', SANDBOX / 'META'
        else:
            stack = ExitStack()
            self.addCleanup(stack.close)
            index = stack.enter_context(standin_index())
            meta = sample = FIXTURES / 'umls'
        matcher = QuickUMLS(index, accepted_semtypes=None, threshold=1)
        with (sample / 'MRCONSO.RRF').open(encoding='utf8') as rows:
            fields = (row.split('|', 15) for row in rows)
            spellings = {atom[14] for atom in fields if atom[1] == 'ENG'}
        probes = {unidecode(term.lower()) for term in spellings}
        expected = defaultdict(dict)
        with (meta / 'MRCONSO.RRF').open(encoding='utf8') as rows:
            for row in rows:
                fields = row.split('|', 15)
                if fields[1] == 'ENG':
                    term = unidecode(fields[14].lower())
                    if term in probes:
                        expected[term].setdefault(fields[0], int(fields[6] == 'Y'))
        self.assertEqual(set(expected), probes)
        wanted = {cui for cuis in expected.values() for cui in cuis}
        types = defaultdict(set)
        with (meta / 'MRSTY.RRF').open(encoding='utf8') as rows:
            for row in rows:
                cui, tui, _ = row.split('|', 2)
                if cui in wanted:
                    types[cui].add(tui)
        self.assertTrue(spellings)
        for term in sorted(spellings):
            with self.subTest(term=term):
                cuis = expected[unidecode(term.lower())]
                groups = matcher.match(term, best_match=False, ignore_syntax=True)
                hits = [h for g in groups for h in g if (h['start'], h['end']) == (0, len(term))]
                self.assertCountEqual([(h['cui'], h['semtypes'], h['preferred']) for h in hits],
                                      [(cui, types[cui], pref) for cui, pref in cuis.items()])
