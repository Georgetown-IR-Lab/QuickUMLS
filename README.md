**We recommend to download the latest tested version from the [releases section](https://github.com/Georgetown-IR-Lab/QuickUMLS/releases)**.

**NEW: v.1.2 now includes client/server support!** Start a QuickUMLS server once, avoid loading QuickUMLS each time your experiments run! See <a href="#client_server">below</a> for more info.

# QuickUMLS

QuickUMLS (Soldaini and Goharian, 2016) is a tool for fast, unsupervised  biomedical concept extraction from medical text.
It takes advantage of [Simstring](http://www.chokkan.org/software/simstring/) (Okazaki and Tsujii, 2010) for approximate string matching.
For more details on how QuickUMLS works, we remand to our paper.

This project should be compatible with both Python 2 and 3 and run on any UNIX system (support for Windows is experimental, please report bugs!). **If you find any bugs, please file an issue on GitHub or email the author at luca@ir.cs.georgetown.edu**.

## Installation

#### Before Starting

1. Make sure that your Python installation include C headers (e.g., on Ubuntu, make sure `python3-dev` or `python-dev` are installed).
2. This software requires all packages listed in the `requirements.txt` file. You can install all of them by running `pip install -r requirements.txt`.
3. Note that, in order to use `spacy`, you are required to download its corpus. You can do that by running `python -m spacy download en`.
4. This system requires you to have a valid UMLS installation on disk. To install UMLS, you must first obtain a [license](https://uts.nlm.nih.gov/license.html) from the National Library of Medicine; then you should download all UMLS files from [this page](https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html); finally, you can install UMLS using the [MetamorphoSys](https://www.nlm.nih.gov/pubs/factsheets/umlsmetamorph.html) tool as [explained in this guide](https://www.nlm.nih.gov/research/umls/implementation_resources/metamorphosys/help.html).  The installation can be removed once the system has been initialized.

#### How To get the System Initialized

1. Download and compile Simstring by running `bash setup_simstring.sh <python_version>`, where `<python_version>` is either "`2`" or "`3`".
2. Initialize the system by running `python install.py <umls_installation_path> <destination_path>`, where `<umls_installation_path>` is where the installation files are (in particular, we need `MRCONSO.RRF` and `MRSTY.RRF`) and `<destination_path>` is the directory where the QuickUmls data files should be installed. This process will take between 5 and 30 minutes depending how fast the CPU and the drive where UMLS and QuickUMLS files are stored are (on a system with a Intel i7 6700K CPU and a 7200RPM hard drive, initialization takes 8.5 minutes).

`install.py` supports the following optional arguments:
- `-L` / `--lowercase`: if used, all concept terms are folded to lowercase before being processed. This option typically increases recall, but it might reduce precision;
- `-U` / `--normalize-unicode`: if used, expressions with non-ASCII characters are converted to the closest combination of ASCII characters.
- `-E` / `--language`: Specify the language to consider for UMLS concepts; by default, English is used. For a complete list of languages, please see [this table provided by NLM](https://www.nlm.nih.gov/research/umls/knowledge_sources/metathesaurus/release/abbreviations.html#LAT).

## APIs

A QuickUMLS object can be instantiated as follows:

```python
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


<h2 id="client_server">[NEW] Server / Client Support</h2>

Starting with v.1.2, QuickUMLS includes a support for being used in a client-server configuration. That is, you can start one QuickUMLS server, and query it from multiple scripts using a client.

To start the server, run `server.py`:

```bash
python server.py /path/to/quickumls/files {-P QuickUMLS port} {-H QuickUMLS host} {QuickUMLS options}
```

Host and port are optional; by default, QuickUMLS runs on `localhost:4645`. You can also pass any QuickUMLS option mentioned above to the server. To obtain a list of options for the server, run `python server.py -h`.

To load the client, import `get_quickumls_client` from `client.py`:

```bash
from client import get_quickumls_client
matcher = get_quickumls_client()
text = "The ulna has dislocated posteriorly from the trochlea of the humerus."
matcher.match(text, best_match=True, ignore_syntax=False)
```

The API of the client is the same of a QuickUMLS object.


In case you wish to run the server in the background, you can do so as follows:

```bash
nohup python server.py /path/to/QuickUMLS {server options} > /dev/null 2>&1 & echo $! > nohup.pid

```

When you are done, don't forget to stop the server by running.
```bash
kill -9 `cat nohup.pid`
rm nohup.pid
```

## References

- Okazaki, Naoaki, and Jun'ichi Tsujii. "*Simple and efficient algorithm for approximate dictionary matching.*" COLING 2010.
- Luca Soldaini and Nazli Goharian. "*QuickUMLS: a fast, unsupervised approach for medical concept extraction.*" MedIR Workshop, SIGIR 2016.
