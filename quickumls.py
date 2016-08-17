# future statements for Python 2 compatibility
from __future__ import unicode_literals, division, print_function, absolute_import

# built in modules
import os

# installed modules
import spacy

# project modules
try:
    import toolbox
    import constants
except ImportError:
    from . import toolbox
    from . import constants

class QuickUMLS(object):
    def __init__(
            self, quickumls_fp,
            overlapping_criteria='score', threshold=0.7, window=5,
            similarity_name='jaccard', accepted_semtypes=constants.ACCEPTED_SEMTYPES):

        valid_criteria = {'length', 'score'}
        err_msg = ('"{}" is not a valid overlapping_criteria. Choose '
                   'between {}'.format(
                        overlapping_criteria, ', '.join(valid_criteria)))
        assert overlapping_criteria in valid_criteria, err_msg
        self.overlapping_criteria = overlapping_criteria

        valid_similarities = {'dice', 'jaccard', 'cosine', 'overlap'}
        err_msg = ('"{}" is not a valid similarity name. Choose between '
                   '{}'.format(similarity_name, ', '.join(valid_similarities)))
        assert not(valid_similarities in valid_similarities), err_msg
        self.similarity_name = similarity_name

        simstring_fp = os.path.join(quickumls_fp, 'umls-simstring.db')
        cuisem_fp = os.path.join(quickumls_fp, 'cui-semtypes.db')

        self.valid_punct = constants.UNICODE_DASHES

        self.window = window
        self.ngram_length = 3
        self.threshold = threshold
        self._info = None

        self.accepted_semtypes = accepted_semtypes

        self.ss_db =\
            toolbox.SimstringDBReader(simstring_fp, similarity_name, threshold)
        self.cuisem_db = toolbox.CuiSemTypesDB(cuisem_fp)
        self.nlp = spacy.load('en')

    @property
    def info(self):
        # useful for caching of respnses

        if self._info is None:
            self._info = {
                'threshold': self.threshold,
                'similarity_name': self.similarity_name,
                'window': self.window,
                'ngram_length': self.ngram_length,
                'accepted_semtypes': sorted(self.accepted_semtypes),
                'negations': sorted(self.negations),
                'valid_punct': sorted(self.valid_punct)
            }
        return self._info

    def _is_valid_token(self, tok):
        return not(
            tok.is_punct or tok.is_space or
            tok.pos_ == 'ADP' or tok.pos_ == 'DET' or tok.pos_ == 'CONJ'
        )

    def _is_valid_start_token(self, tok):
        return not(
            tok.like_num or
            (self._is_stop_term(tok) and tok.lemma_ not in self.negations) or
            tok.pos_ == 'ADP' or tok.pos_ == 'DET' or tok.pos_ == 'CONJ'
        )

    def _is_stop_term(self, tok):
        return tok.is_stop or tok.lemma_ == 'time'

    def _is_valid_end_token(self, tok):
        return not(
            tok.is_punct or tok.is_space or self._is_stop_term(tok) or
            tok.pos_ == 'ADP' or tok.pos_ == 'DET' or tok.pos_ == 'CONJ'
        )

    def _is_valid_middle_token(self, tok):
        return (
            not(tok.is_punct or tok.is_space) or
            tok.is_bracket or
            tok.text in self.valid_punct
        )

    def _is_ok_semtype(self, target_semtypes):
        if self.accepted_semtypes is None:
            ok = True
        else:
            ok = any(sem in self.accepted_semtypes for sem in target_semtypes)
        return ok

    def _make_ngrams(self, sent):
        sent_length = len(sent)

        # do not include teterminers inside a span
        skip_in_span = {token.i for token in sent if token.pos_ == 'DET'}

        # invalidate a span if it includes any on these  symbols
        invalid_mid_tokens = {
            token.i for token in sent if not self._is_valid_middle_token(token)
        }

        for i in toolbox.xrange3(sent_length):
            tok = sent[i]

            if not self._is_valid_token(tok):
                continue

            # do not consider this token by itself if it is
            # a number or a stopword.
            if self._is_valid_start_token(tok):
                compensate = False
            else:
                compensate = True

            span_end = min(sent_length, i + self.window) + 1

            # we take a shortcut if the token is the last one
            # in the sentence
            if i + 1 == sent_length and self._is_valid_end_token(tok):
                yield(tok.idx, tok.idx + len(tok), tok.text)


            for j in toolbox.xrange3(i + 1, span_end):
                if compensate:
                    compensate = False
                    continue

                if sent[j - 1] in invalid_mid_tokens:
                    break

                valid_span = self._is_valid_end_token(sent[j - 1])

                if valid_span:
                    span = sent[i:j]

                    yield (
                        span.start_char, span.end_char,
                        ''.join(token.text_with_ws for token in span
                                if token.i not in skip_in_span).strip()
                    )


    def _get_all_matches(self, ngrams):
        matches = []
        for start, end, ngram in ngrams:
            prev_cui = None
            ngram_cands = list(self.ss_db.get(ngram))

            if ngram.isupper():
                ngram_normalized = ngram.lower()
                ngram_cands = list(self.ss_db.get(ngram_normalized))
            else:
                ngram_normalized = ngram

            ngram_matches = []

            for match in ngram_cands:
                cuisem_match = sorted(self.cuisem_db.get(match))

                for cui, semtypes in cuisem_match:
                    match_similarity = toolbox.get_similarity(
                        x=ngram_normalized.lower(),
                        y=match.lower(),
                        n=self.ngram_length,
                        similarity_name=self.similarity_name
                    )

                    if not self._is_ok_semtype(semtypes):
                        continue

                    if prev_cui is not None and prev_cui == cui:
                        if match_similarity > ngram_matches[-1]['similarity']:
                            ngram_matches.pop(-1)
                        else:
                            continue

                    prev_cui = cui

                    ngram_matches.append(
                        {
                            'start': start,
                            'end': end,
                            'ngram': ngram,
                            'term': toolbox.safe_unicode(match),
                            'cui': cui,
                            'similarity': match_similarity,
                            'semtypes': semtypes
                        }
                    )

            if len(ngram_matches) > 0:
                matches.append(
                    sorted(
                        ngram_matches,
                        key=lambda m: m['similarity'],
                        reverse=True
                    )
                )
        return matches

    @staticmethod
    def _select_score(match):
        return (match[0]['similarity'], (match[0]['end'] - match[0]['start']))

    @staticmethod
    def _select_longest(match):
        return (match[0]['similarity'], (match[0]['end'] - match[0]['start']))

    def _select_terms(self, matches):
        sort_func = (
            self._select_longest if self.overlapping_criteria == 'length'
            else self._select_score
        )

        matches = sorted(matches, key=sort_func, reverse=True)

        intervals = toolbox.Intervals()
        final_matches_subset = []

        for match in matches:
            match_interval = (match[0]['start'], match[0]['end'])
            if match_interval not in intervals:
                final_matches_subset.append(match)
                intervals.append(match_interval)

        return final_matches_subset

    def _make_token_sequences(self, parsed):
        for i in range(len(parsed)):
            for j in xrange3(i + 1, min(i + self.window, len(parsed)) + 1):
                span = parsed[i:j]
                yield (span.start_char, span.end_char, span.text)

    def match(self, text, best_match=True, ignore_syntax=False):
        parsed = self.nlp(u'{}'.format(text))

        if ignore_syntax:
            ngrams = self._make_token_sequences(parsed)
        else:
            ngrams = self._make_ngrams(parsed)

        matches = self._get_all_matches(ngrams)

        if best_match:
            final_matches_subset = self._select_terms(matches)
            return final_matches_subset
        else:
            return matches
