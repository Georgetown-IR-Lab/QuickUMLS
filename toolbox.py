from __future__ import unicode_literals, division, print_function

# build-in modules
import re
import os
import six
import unicodedata
from string import punctuation
from itertools import takewhile, repeat
from six.moves import xrange

# installed modules
import numpy
import leveldb

# project imports
try:
    from simstring import simstring
except ImportError:
    from .simstring import simstring

# Python version specific imports
if six.PY2:
    import cPickle as pickle
else:
    import pickle


def pickle_loading(data):
    pass


def pickle_dumping(data):
    pass


def mkdir(path):
    try:
        os.makedirs(path)
        return True
    except OSError:
        return False


def count_ngrams(s, n):
    return len(s) + n - 1


def safe_unicode(s):
    if six.PY2:
        # in python 3, there no ambiguity on whether
        # a string is encoded in bytes format or not
        try:
            s = u'%s' % s
        except UnicodeDecodeError:
            s = u'%s' % s.decode('utf-8')

    return u'{}'.format(unicodedata.normalize('NFKD', s))


def prepare_string_for_db_input(s):
    if six.PY2:
        return s.encode('utf-8')
    else:
        return s


def make_ngrams(s, n):
    # s = u'{t}{s}{t}'.format(s=safe_unicode(s), t=('$' * (n - 1)))
    n = len(s) if len(s) < n else n
    return (s[i:i + n] for i in xrange(len(s) - n + 1))


def get_similarity(x, y, n, similarity_name):
    if len(x) == 0 or len(y) == 0:
        # we define similarity between two strings
        # to be 0 if any of the two is empty.
        return 0.

    X, Y = set(make_ngrams(x, n)), set(make_ngrams(y, n))
    intersec = len(X.intersection(Y))

    if similarity_name == 'dice':
        return 2 * intersec / (len(X) + len(Y))
    elif similarity_name == 'jaccard':
        return intersec / (len(X) + len(Y) - intersec)
    elif similarity_name == 'cosine':
        return intersec / numpy.sqrt(len(X) * len(Y))
    elif similarity_name == 'overlap':
        return intersec
    else:
        msg = 'Similarity {} not recognized'.format(similarity_name)
        raise TypeError(msg)


class SimpleTokenizer(object):
    def __init__(self, stopwords=None, min_length=1, split_sym=None):
        if stopwords == 'default':
            stopwords = [
                'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for',
                'from', 'has', 'he', 'in', 'is', 'its', 'of', 'on', 'or',
                'that', 'the', 'to', 'was ', 'were', 'will', 'with'
            ]
        elif stopwords is None:
            stopwords = []

        self.stopwords = set(stopwords)

        if split_sym is None:
            split_sym = []

        split_sym = punctuation + ''.join(split_sym)

        self.min_length = min_length
        self.re_tokenize = re.compile(r'&\w+;|\W+|_')

    def tokenize(self, text, lower=True):
        """Tokenize text"""
        if lower:
            text = text.lower()
        for tok in self.re_tokenize.split(text):
            if len(tok) >= self.min_length and tok not in self.stopwords:
                yield tok

    def tokenize_list(self, text, lower=True):
        if lower:
            text = text.lower()
        return [
            tok for tok in self.re_tokenize.split(text)
            if len(tok) >= self.min_length and tok not in self.stopwords
        ]


def db_key_encode(term):
    if six.PY2:
        return term
    else:
        return term.encode('utf-8')


def countlines(fn):
    """Count lines in fn. Slightly modified version of
    http://stackoverflow.com/a/27518377"""
    with open(fn, 'rb') as f:
        bufgen = takewhile(
            lambda x: x, (f.read(1024 * 1024) for _ in repeat(None)))
        ln = sum(buf.count(b'\n') for buf in bufgen)
    return ln


class SimstringDBWriter(object):
    def __init__(self, path):

        if not(os.path.exists(path)) or not(os.path.isdir(path)):
            err_msg = (
                '"{}" does not exists or it is not a directory.'
            ).format(path)
            raise IOError(err_msg)
        else:
            try:
                os.makedirs(path)
            except OSError:
                pass

        self.db = simstring.writer(
            prepare_string_for_db_input(
                os.path.join(path, 'umls-terms.simstring')
            ),
            3, False, True
        )

    def insert(self, term):
        term = prepare_string_for_db_input(safe_unicode(term))
        self.db.insert(term)


class SimstringDBReader(object):
    def __init__(self, path, similarity_name, threshold):
        if not(os.path.exists(path)) or not(os.path.isdir(path)):
            err_msg = (
                '"{}" does not exists or it is not a directory.'
            ).format(path)
            raise IOError(err_msg)

        self.db = simstring.reader(
            prepare_string_for_db_input(
                os.path.join(path, 'umls-terms.simstring')
            )
        )
        self.db.measure = getattr(simstring, similarity_name)
        self.db.threshold = threshold

    def get(self, term):
        term = prepare_string_for_db_input(safe_unicode(term))
        return self.db.retrieve(term)


class Intervals(object):
    def __init__(self):
        self.intervals = []

    def _is_overlapping_intervals(self, a, b):
        if b[0] < a[1] and b[1] > a[0]:
            return True
        elif a[0] < b[1] and a[1] > b[0]:
            return True
        else:
            return False

    def __contains__(self, interval):
        return any(
            self._is_overlapping_intervals(interval, other)
            for other in self.intervals
        )

    def append(self, interval):
        self.intervals.append(interval)


class CuiSemTypesDB(object):
    def __init__(self, path):
        if not (os.path.exists(path) or os.path.isdir(path)):
            err_msg = (
                '"{}" is not a valid directory').format(path)
            raise IOError(err_msg)

        self.cui_db = leveldb.LevelDB(
            os.path.join(path, 'cui.leveldb'))
        self.semtypes_db = leveldb.LevelDB(
            os.path.join(path, 'semtypes.leveldb'))

    def has_term(self, term):
        term = prepare_string_for_db_input(safe_unicode(term))
        try:
            self.cui_db.Get(db_key_encode(term))
            return True
        except KeyError:
            return

    def insert(self, term, cui, semtypes, is_preferred):
        term = prepare_string_for_db_input(safe_unicode(term))
        cui = prepare_string_for_db_input(safe_unicode(cui))

        # some terms have multiple cuis associated with them,
        # so we store them all
        try:
            cuis = pickle.loads(self.cui_db.Get(db_key_encode(term)))
        except KeyError:
            cuis = set()

        cuis.add((cui, is_preferred))
        self.cui_db.Put(db_key_encode(term), pickle.dumps(cuis))

        try:
            self.semtypes_db.Get(db_key_encode(cui))
        except KeyError:
            self.semtypes_db.Put(
                db_key_encode(cui), pickle.dumps(set(semtypes))
            )

    def get(self, term):
        term = prepare_string_for_db_input(safe_unicode(term))

        cuis = pickle.loads(self.cui_db.Get(db_key_encode(term)))
        matches = (
            (
                cui,
                pickle.loads(self.semtypes_db.Get(db_key_encode(cui))),
                is_preferred
            )
            for cui, is_preferred in cuis
        )
        return matches
