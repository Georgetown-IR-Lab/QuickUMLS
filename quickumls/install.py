from __future__ import division, print_function, unicode_literals

# built in modules
import argparse
import codecs
import os
import shutil
import sys
import time

import spacy
import tqdm
from six.moves import input

try:
    from unidecode import unidecode
except ImportError:
    pass

from .constants import HEADERS_MRCONSO, HEADERS_MRSTY, LANGUAGES, SPACY_LANGUAGE_MAP
from .toolbox import CuiPrefDB, CuiSemTypesDB, SimstringDBWriter, countlines, mkdir


def get_semantic_types(path, headers):
    sem_types = {}
    with codecs.open(path, encoding="utf-8") as f:
        for line in tqdm.tqdm(f, total=countlines(path)):
            content = dict(zip(headers, line.strip().split("|")))
            sem_types.setdefault(content["cui"], []).append(content["sty"])

    return sem_types


def get_mrconso_iterator(path, headers, lang="ENG"):
    with codecs.open(path, encoding="utf-8") as f:
        for ln in f:
            content = dict(zip(headers, ln.strip().split("|")))

            if content["lat"] != lang:
                continue

            yield content


def extract_from_mrconso(
    mrconso_path,
    mrsty_path,
    opts,
    mrconso_header=HEADERS_MRCONSO,
    mrsty_header=HEADERS_MRSTY,
):

    start = time.time()
    print("loading semantic types...", end=" ")
    sys.stdout.flush()
    sem_types = get_semantic_types(mrsty_path, mrsty_header)
    print("done in {:.2f} s".format(time.time() - start))

    start = time.time()

    mrconso_iterator = get_mrconso_iterator(mrconso_path, mrconso_header, opts.language)

    total = countlines(mrconso_path)

    for content in tqdm.tqdm(mrconso_iterator, total=total):
        concept_text = content["str"].strip()
        cui = content["cui"]
        preferred = 1 if content["ispref"] == "Y" else 0
        preferred_term = 1 if content["ts"] == "P" else 0
        preferred_string = 1 if content["stt"] == "PF" else 0

        if opts.lowercase:
            concept_text = concept_text.lower()

        if opts.normalize_unicode:
            concept_text = unidecode(concept_text)

        yield (
            concept_text,
            cui,
            sem_types[cui],
            preferred,
            preferred_term,
            preferred_string,
        )


def parse_and_encode_ngrams(extracted_it, simstring_dir, cuisty_dir, database_backend):
    # Create destination directories for the two databases
    mkdir(simstring_dir)
    mkdir(cuisty_dir)

    ss_db = SimstringDBWriter(simstring_dir)
    cuisty_db = CuiSemTypesDB(cuisty_dir, database_backend=database_backend)
    cuipref_db = CuiPrefDB(cuisty_dir, database_backend=database_backend)

    prev_cui = None
    pref_term = False
    prev_term = None
    cui_terms = set()
    for term, cui, stys, preferred, preferred_term, preferred_string in extracted_it:
        if cui != prev_cui:
            if prev_cui is not None:
                if not pref_term:
                    raise RuntimeError(
                        f"did not find preferred term for cui {prev_cui}"
                    )
            prev_cui = cui
            pref_term = False
            cui_terms = set()

        if prev_term != term and term not in cui_terms:
            ss_db.insert(term)
        prev_term = term
        cui_terms.add(term)

        cuisty_db.insert(term, cui, stys, preferred)
        if preferred_term and preferred and preferred_string:
            cuipref_db.insert(term, cui)
            pref_term = True


def install_spacy(lang):
    """Tries to create a spacy object; if it fails, downloads the dataset"""

    print(f'Determining if SpaCy for language "{lang}" is installed...')

    if lang in SPACY_LANGUAGE_MAP:
        try:
            spacy.load(SPACY_LANGUAGE_MAP[lang])
            print(f"SpaCy is installed and avaliable for {lang}!")
        except OSError:
            print(f"SpaCy is not available! Attempting to download and install...")
            spacy.cli.download(SPACY_LANGUAGE_MAP[lang])


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "umls_installation_path",
        help=(
            "Location of UMLS installation files (`MRCONSO.RRF` and "
            "`MRSTY.RRF` files)"
        ),
    )
    ap.add_argument(
        "destination_path",
        help="Location where the necessary QuickUMLS files are installed",
    )
    ap.add_argument(
        "-L",
        "--lowercase",
        action="store_true",
        help="Consider only lowercase version of tokens",
    )
    ap.add_argument(
        "-U",
        "--normalize-unicode",
        action="store_true",
        help="Normalize unicode strings to their closest ASCII representation",
    )
    ap.add_argument(
        "-d",
        "--database-backend",
        choices=("leveldb", "unqlite"),
        default="unqlite",
        help="KV database to use to store CUIs and semantic types",
    )
    ap.add_argument(
        "-E",
        "--language",
        default="ENG",
        choices=LANGUAGES,
        help="Extract concepts of the specified language",
    )
    opts = ap.parse_args()
    return opts


def main():
    opts = parse_args()

    install_spacy(opts.language)

    if not os.path.exists(opts.destination_path):
        msg = 'Directory "{}" does not exists; should I create it? [y/N] ' "".format(
            opts.destination_path
        )
        create = input(msg).lower().strip() == "y"

        if create:
            os.makedirs(opts.destination_path)
        else:
            print("Aborting.")
            exit(1)

    if len(os.listdir(opts.destination_path)) > 0:
        msg = 'Directory "{}" is not empty; should I empty it? [y/N] ' "".format(
            opts.destination_path
        )
        empty = input(msg).lower().strip() == "y"
        if empty:
            shutil.rmtree(opts.destination_path)
            os.mkdir(opts.destination_path)
        else:
            print("Aborting.")
            exit(1)

    if opts.normalize_unicode:
        try:
            unidecode
        except NameError:
            err = (
                "`unidecode` is needed for unicode normalization"
                "please install it via the `[sudo] pip install "
                "unidecode` command."
            )
            print(err, file=sys.stderr)
            exit(1)

        flag_fp = os.path.join(opts.destination_path, "normalize-unicode.flag")
        open(flag_fp, "w").close()

    if opts.lowercase:
        flag_fp = os.path.join(opts.destination_path, "lowercase.flag")
        open(flag_fp, "w").close()

    flag_fp = os.path.join(opts.destination_path, "language.flag")
    with open(flag_fp, "w") as f:
        f.write(opts.language)

    flag_fp = os.path.join(opts.destination_path, "database_backend.flag")
    with open(flag_fp, "w") as f:
        f.write(opts.database_backend)

    mrconso_path = os.path.join(opts.umls_installation_path, "MRCONSO.RRF")
    mrsty_path = os.path.join(opts.umls_installation_path, "MRSTY.RRF")

    mrconso_iterator = extract_from_mrconso(mrconso_path, mrsty_path, opts)

    simstring_dir = os.path.join(opts.destination_path, "umls-simstring.db")
    cuisty_dir = os.path.join(opts.destination_path, "cui-semtypes.db")

    parse_and_encode_ngrams(
        mrconso_iterator,
        simstring_dir,
        cuisty_dir,
        database_backend=opts.database_backend,
    )


if __name__ == "__main__":
    main()
