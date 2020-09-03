[**NEW: v.1.4 supports starting multiple QuickUMLS matchers concurrently!**](https://giphy.com/embed/BlVnrxJgTGsUw) I've finally added support for [unqlite](https://github.com/coleifer/unqlite-python) as an alternative to leveldb for storage of CUIs and Semantic Types (see [here](https://github.com/Georgetown-IR-Lab/QuickUMLS/wiki/Migration-QuickUMLS-1.3-to-1.4) for more details). unqlite-backed QuickUMLS installation support multiple matchers running at the same time. Other than better multi-processing support, unqlite should have better support for unicode.

# QuickUMLS

QuickUMLS (Soldaini and Goharian, 2016) is a tool for fast, unsupervised  biomedical concept extraction from medical text.
It takes advantage of [Simstring](http://www.chokkan.org/software/simstring/) (Okazaki and Tsujii, 2010) for approximate string matching.
For more details on how QuickUMLS works, we remand to our paper.

This project should be compatible with Python 3 (Python 2 is [no longer supported](https://pythonclock.org/)) and run on any UNIX system (support for Windows is experimental, please report bugs!). **If you find any bugs, please file an issue on GitHub or email the author at luca@ir.cs.georgetown.edu**.

## Installation

1. **Obtain a UMLS installation** This tool requires you to have a valid UMLS installation on disk. To install UMLS, you must first obtain a [license](https://uts.nlm.nih.gov/license.html) from the National Library of Medicine; then you should download all UMLS files from [this page](https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html); finally, you can install UMLS using the [MetamorphoSys](https://www.nlm.nih.gov/pubs/factsheets/umlsmetamorph.html) tool as [explained in this guide](https://www.nlm.nih.gov/research/umls/implementation_resources/metamorphosys/help.html).  The installation can be removed once the system has been initialized.
2. **Install QuickUMLS**: You can do so by either running `pip install quickumls` or `python setup.py install`. On macOS, using anaconda is **strongly recommended**<sup>†</sup>.
3. **Create a QuickUMLS installation** Initialize the system by running `python -m quickumls.install <umls_installation_path> <destination_path>`, where `<umls_installation_path>` is where the installation files are (in particular, we need `MRCONSO.RRF` and `MRSTY.RRF`) and `<destination_path>` is the directory where the QuickUmls data files should be installed. This process will take between 5 and 30 minutes depending how fast the CPU and the drive where UMLS and QuickUMLS files are stored are (on a system with a Intel i7 6700K CPU and a 7200 RPM hard drive, initialization takes 8.5 minutes). `python -m quickumls.install` supports the following optional arguments:
    - `-L` / `--lowercase`: if used, all concept terms are folded to lowercase before being processed. This option typically increases recall, but it might reduce precision;
    - `-U` / `--normalize-unicode`: if used, expressions with non-ASCII characters are converted to the closest combination of ASCII characters.
    - `-E` / `--language`: Specify the language to consider for UMLS concepts; by default, English is used. For a complete list of languages, please see [this table provided by NLM](https://www.nlm.nih.gov/research/umls/knowledge_sources/metathesaurus/release/abbreviations.html#LAT).
    - `-d` / `--database-backend`: Specify which database backend to use for QuickUMLS. The two options are `leveldb` and `unqlite`. The latter supports multi-process reading and has better unicode compatibility, and it used as default for all new 1.4 installations; the former is still used as default when instantiating a QuickUMLS client. More info about differences between the two databases and migration info are available [here](https://github.com/Georgetown-IR-Lab/QuickUMLS/wiki/Migration-QuickUMLS-1.3-to-1.4).


**†**: If the installation fails on macOS when using Anaconda, install `leveldb` first by running `conda install -c conda-forge python-leveldb`.

## APIs

A QuickUMLS object can be instantiated as follows:

```python
from quickumls import QuickUMLS

matcher = QuickUMLS(quickumls_fp, overlapping_criteria, threshold,
                    similarity_name, window, accepted_semtypes)
```

Where:

- `quickumls_fp` is the directory where the QuickUMLS data files are installed.
- `overlapping_criteria` (optional, default: "score") is the criteria used to deal with overlapping concepts; choose "score" if the matching score of the concepts should be consider first, "length" if the longest should be considered first instead.
- `threshold` (optional, default: 0.7) is the minimum similarity value between strings.
- `similarity_name` (optional, default: "jaccard") is the name of similarity to use. Choose between "dice", "jaccard", "cosine", or "overlap".
- `window` (optional, default: 5) is the maximum number of tokens to consider for matching.
- `accepted_semtypes` (optional, default: see `constants.py`) is the set of UMLS semantic types concepts should belong to. Semantic types are identified by the letter "T" followed by three numbers (e.g., "T131", which identifies the type *"Hazardous or Poisonous Substance"*). See [here](https://metamap.nlm.nih.gov/Docs/SemanticTypes_2013AA.txt) for the full list.

To use the matcher, simply call

```python
text = "The ulna has dislocated posteriorly from the trochlea of the humerus."
matcher.match(text, best_match=True, ignore_syntax=False)
```

Set `best_match` to `False` if you want to return overlapping candidates, `ignore_syntax` to `True` to disable all heuristics introduced in (Soldaini and Goharian, 2016).

If the matcher throws a warning during initialization, read [this page](https://github.com/Georgetown-IR-Lab/QuickUMLS/wiki/Migration-QuickUMLS-1.3-to-1.4) to learn why and how to stop it from doing so.

## spaCy pipeline component

QuickUMLS can be used for standalone processing but it can also be use as a component in a modular spaCy pipeline.  This follows traditional spaCy handling of concepts to be entity objects added to the Document object.  These entity objects contain the CUI, similarity score and Semantic Types in the spacy "underscore" object.

Adding QuickUMLS as a component in a pipeline can be done as follows:

```python
from quickumls.spacy_component import SpacyQuickUMLS

# common English pipeline
nlp = spacy.load('en_core_web_sm')

quickumls_component = SpacyQuickUMLS(nlp, 'PATH_TO_QUICKUMLS_DATA')
nlp.add_pipe(quickumls_component)

doc = nlp('Pt c/o shortness of breath, chest pain, nausea, vomiting, diarrrhea')

for ent in doc.ents:
    print('Entity text : {}'.format(ent.text))
    print('Label (UMLS CUI) : {}'.format(ent.label_))
    print('Similarity : {}'.format(ent._.similarity))
    print('Semtypes : {}'.format(ent._.semtypes))
```

## Server / Client Support

Starting with v.1.2, QuickUMLS includes a support for being used in a client-server configuration. That is, you can start one QuickUMLS server, and query it from multiple scripts using a client.

To start the server, run `python -m quickumls.server`:

```bash
python -m quickumls.server /path/to/quickumls/files {-P QuickUMLS port} {-H QuickUMLS host} {QuickUMLS options}
```

Host and port are optional; by default, QuickUMLS runs on `localhost:4645`. You can also pass any QuickUMLS option mentioned above to the server. To obtain a list of options for the server, run `python -m quickumls.server -h`.

To load the client, import `get_quickumls_client` from `quickumls`:

```bash
from quickumls import get_quickumls_client
matcher = get_quickumls_client()
text = "The ulna has dislocated posteriorly from the trochlea of the humerus."
matcher.match(text, best_match=True, ignore_syntax=False)
```

The API of the client is the same of a QuickUMLS object.


In case you wish to run the server in the background, you can do so as follows:

```bash
nohup python -m quickumls.server /path/to/QuickUMLS {server options} > /dev/null 2>&1 & echo $! > nohup.pid

```

When you are done, don't forget to stop the server by running.
```bash
kill -9 `cat nohup.pid`
rm nohup.pid
```

## References

- Okazaki, Naoaki, and Jun'ichi Tsujii. "*Simple and efficient algorithm for approximate dictionary matching.*" COLING 2010.
- Luca Soldaini and Nazli Goharian. "*QuickUMLS: a fast, unsupervised approach for medical concept extraction.*" MedIR Workshop, SIGIR 2016.
