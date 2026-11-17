from __future__ import unicode_literals, division, print_function

# built in modules
import argparse
import codecs
from contextlib import closing, contextmanager
import os
from six.moves import input
import shutil
import sqlite3
import sys
from tempfile import TemporaryDirectory
import time
try:
    from unidecode import unidecode
except ImportError:
    pass


# third party-dependencies
import spacy


# project modules
from .toolbox import countlines, CuiSemTypesDB, SimstringDBWriter, mkdir
from .constants import HEADERS_MRCONSO, HEADERS_MRSTY, LANGUAGES, SPACY_LANGUAGE_MAP


def get_semantic_types(path, headers):
    sem_types = {}
    with codecs.open(path, encoding='utf-8') as f:
        for i, ln in enumerate(f):
            content = dict(zip(headers, ln.strip().split('|')))

            sem_types.setdefault(content['cui'], []).append(content['sty'])

    return sem_types


def get_mrconso_iterator(path, headers, lang='ENG'):
    with codecs.open(path, encoding='utf-8') as f:
        for i, ln in enumerate(f):
            content = dict(zip(headers, ln.strip().split('|')))

            if content['lat'] != lang:
                continue

            yield content


def extract_from_mrconso(
        mrconso_path, mrsty_path, opts,
        mrconso_header=HEADERS_MRCONSO, mrsty_header=HEADERS_MRSTY):
    atoms = _iter_atoms(mrconso_path, mrsty_path, opts, mrconso_header, mrsty_header)
    with _seen_database(getattr(opts, 'destination_path', None)) as seen:
        for atom in atoms:
            term, cui = atom[:2]
            if _first_pair(seen, term, cui):
                yield atom


def _iter_atoms(mrconso_path, mrsty_path, opts,
                mrconso_header=HEADERS_MRCONSO, mrsty_header=HEADERS_MRSTY):
    start = time.time()
    print('loading semantic types...', end=' ')
    sys.stdout.flush()
    sem_types = get_semantic_types(mrsty_path, mrsty_header)
    print('done in {:.2f} s'.format(time.time() - start))

    start = time.time()

    mrconso_iterator = get_mrconso_iterator(
        mrconso_path, mrconso_header, opts.language
    )

    total = countlines(mrconso_path)

    i = 0

    for content in mrconso_iterator:
        i += 1

        if i % 100000 == 0:
            delta = time.time() - start
            status = (
                '{:,} in {:.2f} s ({:.2%}, {:.1e} s / term)'
                ''.format(i, delta, i / total, delta / i if i > 0 else 0)
            )
            print(status)

        concept_text = content['str'].strip()
        cui = content['cui']
        preferred = 1 if content['ispref'] == 'Y' else 0

        if opts.lowercase:
            concept_text = concept_text.lower()

        if opts.normalize_unicode:
            concept_text = unidecode(concept_text)

        yield (concept_text, cui, sem_types[cui], preferred)

    delta = time.time() - start
    status = (
        '\nCOMPLETED: {:,} in {:.2f} s ({:.1e} s / term)'
        ''.format(i, delta, i / total, delta / i if i > 0 else 0)
    )
    print(status)


@contextmanager
def _seen_database(directory):
    # Track original spellings. The permanent databases normalize their keys to
    # NFKD, which can merge distinct input terms with different preferred flags.
    with TemporaryDirectory(dir=directory) as temp:
        with closing(sqlite3.connect(os.path.join(temp, 'seen.sqlite'))) as db:
            # These keys can be discarded on any failure, including an interruption.
            db.execute('PRAGMA journal_mode = OFF')
            db.execute('CREATE TABLE seen (term TEXT, cui TEXT, '
                       'PRIMARY KEY (term, cui)) WITHOUT ROWID')
            yield db


def _first_pair(db, term, cui):
    return db.execute('INSERT OR IGNORE INTO seen VALUES (?, ?)', (term, cui)).rowcount == 1


def parse_and_encode_ngrams(extracted_it, simstring_dir, cuisty_dir, database_backend,
                            deduplicate_pairs=False):
    # Create destination directories for the two databases
    mkdir(simstring_dir)
    mkdir(cuisty_dir)

    ss_db = SimstringDBWriter(simstring_dir)
    cuisty_db = CuiSemTypesDB(cuisty_dir, database_backend=database_backend)

    with _seen_database(cuisty_dir) as seen:
        for term, cui, stys, preferred in extracted_it:
            first_pair = _first_pair(seen, term, cui)
            if first_pair:
                # The (term, cui) primary key also indexes the term by itself.
                other = seen.execute('SELECT 1 FROM seen WHERE term = ? LIMIT 1 OFFSET 1',
                                     (term,)).fetchone()
                if other is None:
                    ss_db.insert(term)
            if first_pair or not deduplicate_pairs:
                cuisty_db.insert(term, cui, stys, preferred)


def install_spacy(lang):
    """Tries to create a spacy object; if it fails, downloads the dataset"""

    print(f'Determining if SpaCy for language "{lang}" is installed...')

    if lang in SPACY_LANGUAGE_MAP:
        try:
            spacy.load(SPACY_LANGUAGE_MAP[lang])
            print(f'SpaCy is installed and avaliable for {lang}!')
        except OSError:
            print(f'SpaCy is not available! Attempting to download and install...')
            spacy.cli.download(SPACY_LANGUAGE_MAP[lang])


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        'umls_installation_path',
        help=('Location of UMLS installation files (`MRCONSO.RRF` and '
              '`MRSTY.RRF` files)')
    )
    ap.add_argument(
        'destination_path',
        help='Location where the necessary QuickUMLS files are installed'
    )
    ap.add_argument(
        '-L', '--lowercase', action='store_true',
        help='Consider only lowercase version of tokens'
    )
    ap.add_argument(
        '-U', '--normalize-unicode', action='store_true',
        help='Normalize unicode strings to their closest ASCII representation'
    )
    ap.add_argument(
        '-d', '--database-backend', choices=('leveldb', 'unqlite'), default='unqlite',
        help='KV database to use to store CUIs and semantic types'
    )
    ap.add_argument(
        '-E', '--language', default='ENG', choices=LANGUAGES,
        help='Extract concepts of the specified language'
    )
    ap.add_argument('--skip-spacy', action='store_true',
                    help='Build the index without loading or downloading a spaCy model')
    opts = ap.parse_args()
    return opts


def main():
    opts = parse_args()

    if not opts.skip_spacy:
        install_spacy(opts.language)

    if not os.path.exists(opts.destination_path):
        msg = ('Directory "{}" does not exists; should I create it? [y/N] '
               ''.format(opts.destination_path))
        create = input(msg).lower().strip() == 'y'

        if create:
            os.makedirs(opts.destination_path)
        else:
            print('Aborting.')
            exit(1)

    if len(os.listdir(opts.destination_path)) > 0:
        msg = ('Directory "{}" is not empty; should I empty it? [y/N] '
               ''.format(opts.destination_path))
        empty = input(msg).lower().strip() == 'y'
        if empty:
            shutil.rmtree(opts.destination_path)
            os.mkdir(opts.destination_path)
        else:
            print('Aborting.')
            exit(1)

    if opts.normalize_unicode:
        try:
            unidecode
        except NameError:
            err = ('`unidecode` is needed for unicode normalization'
                   'please install it via the `[sudo] pip install '
                   'unidecode` command.')
            print(err, file=sys.stderr)
            exit(1)

        flag_fp = os.path.join(opts.destination_path, 'normalize-unicode.flag')
        open(flag_fp, 'w').close()

    if opts.lowercase:
        flag_fp = os.path.join(opts.destination_path, 'lowercase.flag')
        open(flag_fp, 'w').close()

    flag_fp = os.path.join(opts.destination_path, 'language.flag')
    with open(flag_fp, 'w') as f:
        f.write(opts.language)

    flag_fp = os.path.join(opts.destination_path, 'database_backend.flag')
    with open(flag_fp, 'w') as f:
        f.write(opts.database_backend)

    mrconso_path = os.path.join(opts.umls_installation_path, 'MRCONSO.RRF')
    mrsty_path = os.path.join(opts.umls_installation_path, 'MRSTY.RRF')

    mrconso_iterator = _iter_atoms(mrconso_path, mrsty_path, opts)

    simstring_dir = os.path.join(opts.destination_path, 'umls-simstring.db')
    cuisty_dir = os.path.join(opts.destination_path, 'cui-semtypes.db')

    parse_and_encode_ngrams(mrconso_iterator, simstring_dir, cuisty_dir,
                            database_backend=opts.database_backend, deduplicate_pairs=True)


if __name__ == '__main__':
    main()
