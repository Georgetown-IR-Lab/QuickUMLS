# future statements for Python 2 compatibility
from __future__ import absolute_import, division, print_function, unicode_literals

import datetime

# built in modules
import os
import sys

import nltk

# installed modules
import spacy
from six.moves import xrange
from unidecode import unidecode

# project modules
from . import constants, toolbox


class QuickUMLS(object):
    """The main class to interact with the matcher.
    """

    def __init__(
        self,
        quickumls_fp,
        overlapping_criteria="score",
        threshold=0.7,
        window=5,
        similarity_name="jaccard",
        min_match_length=3,
        accepted_semtypes=constants.ACCEPTED_SEMTYPES,
        verbose=False,
        keep_uppercase=False,
        spacy_component=False,
    ):
        """Instantiate QuickUMLS object

            This is the main interface through which text can be processed.

        Args:
            quickumls_fp (str): Path to which QuickUMLS was installed
            overlapping_criteria (str, optional):
                    One of "score" or "length". Choose how results are ranked.
                    Choose "score" for best matching score first or "length" for longest match first.. Defaults to 'score'.
            threshold (float, optional): Minimum similarity between strings. Defaults to 0.7.
            window (int, optional): Maximum amount of tokens to consider for matching. Defaults to 5.
            similarity_name (str, optional): One of "dice", "jaccard", "cosine", or "overlap".
                    Similarity measure to be used. Defaults to 'jaccard'.
            min_match_length (int, optional): TODO: ??. Defaults to 3.
            accepted_semtypes (List[str], optional): Set of UMLS semantic types concepts should belong to.
                Semantic types are identified by the letter "T" followed by three numbers
                (e.g., "T131", which identifies the type "Hazardous or Poisonous Substance").
                Defaults to constants.ACCEPTED_SEMTYPES.
            verbose (bool, optional): TODO:??. Defaults to False.
            keep_uppercase (bool, optional): By default QuickUMLS converts all
                    uppercase strings to lowercase. This option disables that
                    functionality, which makes QuickUMLS useful for
                    distinguishing acronyms from normal words. For this the
                    database should be installed without the -L option.
                    Defaults to False.

        Raises:
            ValueError: Raises a ValueError if QuickUMLS was installed for a language that is not currently supported TODO: verify this?
            OSError: Raises an OSError if the required Spacy model was not installed.
        """

        self.verbose = verbose

        valid_criteria = {"length", "score"}
        err_msg = (
            '"{}" is not a valid overlapping_criteria. Choose '
            "between {}".format(overlapping_criteria, ", ".join(valid_criteria))
        )
        assert overlapping_criteria in valid_criteria, err_msg
        self.overlapping_criteria = overlapping_criteria

        valid_similarities = {"dice", "jaccard", "cosine", "overlap"}
        err_msg = '"{}" is not a valid similarity name. Choose between ' "{}".format(
            similarity_name, ", ".join(valid_similarities)
        )
        assert not (valid_similarities in valid_similarities), err_msg
        self.similarity_name = similarity_name

        simstring_fp = os.path.join(quickumls_fp, "umls-simstring.db")
        cuisem_fp = os.path.join(quickumls_fp, "cui-semtypes.db")

        self.valid_punct = constants.UNICODE_DASHES
        self.negations = constants.NEGATIONS

        self.window = window
        self.ngram_length = 3
        self.threshold = threshold
        self.min_match_length = min_match_length
        self.to_lowercase_flag = os.path.exists(
            os.path.join(quickumls_fp, "lowercase.flag")
        )
        self.normalize_unicode_flag = os.path.exists(
            os.path.join(quickumls_fp, "normalize-unicode.flag")
        )
        self.keep_uppercase = keep_uppercase

        # Check whether data is installed with lowercase flag and QuickUMLS initiated with keeping uppercase words
        if self.to_lowercase_flag and self.keep_uppercase:
            raise ValueError(
                "Database is installed with lowercase flag and QuickUMLS is initiated with "
                "keep_uppercase flag. This would prevent identifying concepts that contain all uppercase"
                "characters. Please reinstall data without --lowercase or run QuickUMLS without"
                "--keep_uppercase."
            )

        language_fp = os.path.join(quickumls_fp, "language.flag")

        # download stopwords if necessary
        try:
            nltk.corpus.stopwords.words()
        except LookupError:
            nltk.download("stopwords")

        if os.path.exists(language_fp):
            with open(language_fp) as f:
                self.language_flag = f.read().strip()
        else:
            self.language_flag = "ENG"

        if self.language_flag not in constants.LANGUAGES:
            raise ValueError('Language "{}" not supported'.format(self.language_flag))
        elif constants.LANGUAGES[self.language_flag] is None:
            self._stopwords = set()
            spacy_lang = "XXX"
        else:
            self._stopwords = set(
                nltk.corpus.stopwords.words(constants.LANGUAGES[self.language_flag])
            )
            spacy_lang = constants.SPACY_LANGUAGE_MAP[self.language_flag]

        database_backend_fp = os.path.join(quickumls_fp, "database_backend.flag")
        if os.path.exists(database_backend_fp):
            with open(database_backend_fp) as f:
                self._database_backend = f.read().strip()
        else:
            print(
                "[WARNING] This installation was created with QuickUMLS v.1.3 or earlier, "
                "which does not support multiple database backends. For now, I'll "
                "assume that leveldb was used as default, implicit assumption will "
                "change in future versions of QuickUMLS. More info here: "
                "https://github.com/Georgetown-IR-Lab/QuickUMLS/wiki/Migration-QuickUMLS-1.3-to-1.4",
                file=sys.stderr,
            )
            self._database_backend = "leveldb"

        # domain specific stopwords
        self._stopwords = self._stopwords.union(constants.DOMAIN_SPECIFIC_STOPWORDS)

        self._info = None

        self.accepted_semtypes = accepted_semtypes

        # if this is not being executed as as spacy component, then it must be standalone
        if spacy_component:
            # In this case, the pipeline is external to this current class
            self.nlp = None
        else:
            try:
                self.nlp = spacy.load(spacy_lang)
            except OSError:
                msg = (
                    'Model for language "{}" is not downloaded. Please '
                    'run "python -m spacy download {}" before launching '
                    "QuickUMLS"
                ).format(
                    self.language_flag,
                    constants.SPACY_LANGUAGE_MAP.get(self.language_flag, "xx"),
                )
                raise OSError(msg)

        self.ss_db = toolbox.SimstringDBReader(simstring_fp, similarity_name, threshold)
        self.cuisem_db = toolbox.CuiSemTypesDB(
            cuisem_fp, database_backend=self._database_backend
        )
        self.cuipref_db = toolbox.CuiPrefDB(
            cuisem_fp, database_backend=self._database_backend
        )

    def get_info(self):
        """Computes a summary of the matcher options.

        Returns:
            Dict: Dictionary containing information on the QuicUMLS instance.
        """
        return self.info

    def get_accepted_semtypes(self):
        return self.accepted_semtypes

    @property
    def info(self):
        """Computes a summary of the matcher options.

        Returns:
            Dict: Dictionary containing information on the QuicUMLS instance.
        """
        # useful for caching of respnses

        if self._info is None:
            self._info = {
                "threshold": self.threshold,
                "similarity_name": self.similarity_name,
                "window": self.window,
                "ngram_length": self.ngram_length,
                "min_match_length": self.min_match_length,
                "accepted_semtypes": sorted(self.accepted_semtypes),
                "negations": sorted(self.negations),
                "valid_punct": sorted(self.valid_punct),
            }
        return self._info

    def _is_valid_token(self, tok):
        return not (
            tok.is_punct
            or tok.is_space
            or tok.pos_ == "ADP"
            or tok.pos_ == "DET"
            or tok.pos_ == "CONJ"
        )

    def _is_valid_start_token(self, tok):
        return not (
            tok.like_num
            or (self._is_stop_term(tok) and tok.lemma_ not in self.negations)
            or tok.pos_ == "ADP"
            or tok.pos_ == "DET"
            or tok.pos_ == "CONJ"
        )

    def _is_stop_term(self, tok):
        return tok.text in self._stopwords

    def _is_valid_end_token(self, tok):
        return not (
            tok.is_punct
            or tok.is_space
            or self._is_stop_term(tok)
            or tok.pos_ == "ADP"
            or tok.pos_ == "DET"
            or tok.pos_ == "CONJ"
        )

    def _is_valid_middle_token(self, tok):
        return (
            not (tok.is_punct or tok.is_space)
            or tok.is_bracket
            or tok.text in self.valid_punct
        )

    def _is_ok_semtype(self, target_semtypes):
        if self.accepted_semtypes is None:
            ok = True
        else:
            ok = any(sem in self.accepted_semtypes for sem in target_semtypes)
        return ok

    def _is_longer_than_min(self, span):
        return (span.end_char - span.start_char) >= self.min_match_length

    def _make_ngrams(self, sent):
        sent_length = len(sent)

        # do not include determiners inside a span
        skip_in_span = {token.i for token in sent if token.pos_ == "DET"}

        # invalidate a span if it includes any on these symbols
        invalid_mid_tokens = {
            token.i for token in sent if not self._is_valid_middle_token(token)
        }

        for i in xrange(sent_length):
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
            if (
                i + 1 == sent_length
                and self._is_valid_end_token(tok)  # it's the last token
                and len(tok)  # it's a valid end token
                >= self.min_match_length  # it's of miminum length
            ):
                yield (tok.idx, tok.idx + len(tok), tok.text)

            for j in xrange(i + 1, span_end):
                if compensate:
                    compensate = False
                    continue

                if sent[j - 1] in invalid_mid_tokens:
                    break

                if not self._is_valid_end_token(sent[j - 1]):
                    continue

                span = sent[i:j]

                if not self._is_longer_than_min(span):
                    continue

                yield (
                    span.start_char,
                    span.end_char,
                    "".join(
                        token.text_with_ws
                        for token in span
                        if token.i not in skip_in_span
                    ).strip(),
                )

    def get_preferred_term(self, cui):
        return self.cuipref_db.get(cui)

    def _get_all_matches(self, ngrams):
        matches = []
        for start, end, ngram in ngrams:
            ngram_normalized = ngram

            if self.normalize_unicode_flag:
                ngram_normalized = unidecode(ngram_normalized)

            # make it lowercase
            if self.to_lowercase_flag:
                ngram_normalized = ngram_normalized.lower()

            # If the term is all uppercase, it might be the case that
            # no match is found; so we convert to lowercase;
            # however, this is never needed if the string is lowercased
            # in the step above
            if (
                not self.to_lowercase_flag
                and ngram_normalized.isupper()
                and not self.keep_uppercase
            ):
                ngram_normalized = ngram_normalized.lower()

            prev_cui = None
            ngram_cands = list(set(self.ss_db.get(ngram_normalized)))

            ngram_matches = []

            for match in ngram_cands:
                cuisem_match = sorted(self.cuisem_db.get(match))

                match_similarity = toolbox.get_similarity(
                    x=ngram_normalized,
                    y=match,
                    n=self.ngram_length,
                    similarity_name=self.similarity_name,
                )

                if match_similarity == 0:
                    continue

                for cui, semtypes, preferred in cuisem_match:

                    if not self._is_ok_semtype(semtypes):
                        continue

                    if prev_cui is not None and prev_cui == cui:
                        if match_similarity > ngram_matches[-1]["similarity"]:
                            ngram_matches.pop(-1)
                        else:
                            continue

                    prev_cui = cui
                    preferred_term = self.cuipref_db.get(cui)

                    ngram_matches.append(
                        {
                            "start": start,
                            "end": end,
                            "ngram": ngram,
                            "term": toolbox.safe_unicode(match),
                            "cui": cui,
                            "similarity": match_similarity,
                            "semtypes": semtypes,
                            "preferred": preferred,
                            "preferred_term": preferred_term,
                        }
                    )

            if len(ngram_matches) > 0:
                matches.append(
                    sorted(
                        ngram_matches,
                        key=lambda m: m["similarity"] + m["preferred"],
                        reverse=True,
                    )
                )
        return matches

    @staticmethod
    def _select_score(match):
        return (match[0]["similarity"], (match[0]["end"] - match[0]["start"]))

    @staticmethod
    def _select_longest(match):
        return ((match[0]["end"] - match[0]["start"]), match[0]["similarity"])

    def _select_terms(self, matches):
        sort_func = (
            self._select_longest
            if self.overlapping_criteria == "length"
            else self._select_score
        )

        matches = sorted(matches, key=sort_func, reverse=True)

        intervals = toolbox.Intervals()
        final_matches_subset = []

        for match in matches:
            match_interval = (match[0]["start"], match[0]["end"])
            if match_interval not in intervals:
                final_matches_subset.append(match)
                intervals.append(match_interval)

        return final_matches_subset

    def _make_token_sequences(self, parsed):
        for i in range(len(parsed)):
            for j in xrange(i + 1, min(i + self.window, len(parsed)) + 1):
                span = parsed[i:j]

                if not self._is_longer_than_min(span):
                    continue

                yield (span.start_char, span.end_char, span.text)

    def _print_verbose_status(self, parsed, matches):
        if not self.verbose:
            return False

        print(
            "[{}] {:,} extracted from {:,} tokens".format(
                datetime.datetime.now().isoformat(),
                sum(len(match_group) for match_group in matches),
                len(parsed),
            ),
            file=sys.stderr,
        )
        return True

    def match(self, text, best_match=True, ignore_syntax=False):
        """Perform UMLS concept resolution for the given string.

        [extended_summary]

        Args:
            text (str): Text on which to run the algorithm

            best_match (bool, optional): Whether to return only the top match or all overlapping candidates. Defaults to True.
            ignore_syntax (bool, optional): Wether to use the heuristcs introduced in the paper (Soldaini and Goharian, 2016). TODO: clarify,. Defaults to False.

        Returns:
            List: List of all matches in the text
            TODO: Describe format
        """

        parsed = self.nlp("{}".format(text))

        # pass in parsed spacy doc to get concept matches
        matches = self._match(parsed, best_match, ignore_syntax)

        return matches

    def _match(self, doc, best_match=True, ignore_syntax=False):
        """Gathers ngram matches given a spaCy document object.

        [extended_summary]

        Args:
            text (Document): spaCy Document object to be used for extracting ngrams

            best_match (bool, optional): Whether to return only the top match or all overlapping candidates. Defaults to True.
            ignore_syntax (bool, optional): Wether to use the heuristcs introduced in the paper (Soldaini and Goharian, 2016). TODO: clarify,. Defaults to False

        Returns:
            List: List of all matches in the text
            TODO: Describe format
        """

        ngrams = None
        if ignore_syntax:
            ngrams = self._make_token_sequences(doc)
        else:
            ngrams = self._make_ngrams(doc)

        matches = self._get_all_matches(ngrams)

        if best_match:
            matches = self._select_terms(matches)

        self._print_verbose_status(doc, matches)

        return matches
