# QuickUMLS fix and test plan

The November 15 review covered all 30 [open GitHub issues](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues?q=is%3Aissue%20is%3Aopen) against [b8fed22](https://github.com/Georgetown-IR-Lab/QuickUMLS/tree/b8fed224c125b245176ea250b0f056701c156219). The issue tables below retain the acceptance criteria. The November 17 results describe this checkout.

## Implementation order and checks

| Order | Work | Evidence or next test |
| --- | --- | --- |
| 1 | Matcher flags (#74, #102), model selection (#69) and server semantic types (#91) | Implemented. Exercise all flag combinations, model paths and CLI filtering. A loopback client and a direct matcher returned the same results against the real index. |
| 2 | spaCy factory, extension registration and overlapping entities (#79, #94, #60) | Implemented. Reuse a pipeline on successive documents, construct a second pipeline, and verify simultaneous CUIs, upstream entities, and score-versus-length ranking on a fuzzy match. |
| 3 | Installer memory (#64, #95) | The new indexer uses one temporary SQLite table for term and CUI deduplication. Record time, peak RSS, and output parity. Repeat under a measured WSL memory limit before resolving #95. The semantic-type map and native SimString writer still consume memory. |
| 4 | Default storage and native installations (#98, #73, #101 and related packaging reports) | UnQLite works without installing LevelDB. An unmarked LevelDB index built with the prior code reopened with the optional binding. The Python 3.12 SimString import and native Windows builds still need upstream work. Add those platforms to CI once a released binding installs and round-trips the fixture. |
| 5 | Remaining platform, performance and terminology requests | Use the small fixture to isolate Windows retrieval (#82), then reproduce external-volume locking (#58). Extend the English NER benchmark (#77) to other supported models before changing the default. For #78, prototype a source-specific ICD lookup and verify zero, one and multiple codes. |

The published 1.4.2 wheel loaded the English model and produced entities with a directly constructed component on the real index (#65, #68, #81). The wheel and source distribution built from this checkout each passed the synthetic suite outside the source tree. A clean Colab restart, native Windows, and a constrained WSL build still need their own runs.

For #77, excluding NER from `en_core_web_sm` 3.8.0 improved warm throughput 1.77× on four short texts and 1.62× on two 116-token texts against the small index. Match outputs agreed under all four combinations of flags. To try this with the model override, save a pipeline loaded with `exclude=["ner"]` using spaCy's `to_disk` and pass that directory as `spacy_model`.

## Running the tests

In a Python 3.11 environment, install QuickUMLS from the checkout and use the stand-in vocabulary for daily development.

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python tests/standin.py "amber stone"
```

The [fictional RRF files](../tests/fixtures/umls) supply seven concepts, including overlapping phrases, repeated spellings, accented text and a non-English row. The tests use the real indexer and matcher with a temporary index, a blank English spaCy pipeline, and a two-word stopword list. After package installation, both commands work offline. The example returns `C2` at offsets 0–11.

### Optional licensed release checks

For release validation, provision the English model and stopwords, then prepare a subset from a full-release ZIP and enable the licensed source comparison explicitly.

```sh
python -m spacy download en_core_web_sm
export NLTK_DATA="$PWD/.sandbox/nltk_data"
python -m nltk.downloader -d "$NLTK_DATA" stopwords
python tests/prepare_sandbox.py "$HOME/Downloads/umls-2026AB-metathesaurus-full.zip"
mkdir -p .sandbox/index
python -m quickumls.install --skip-spacy -L -U .sandbox/META .sandbox/index
QUICKUMLS_TEST_LICENSED=1 python -m unittest discover -s tests -v
```

The existing 2026AB subset contains 434 atoms across 24 CUIs. To check the probe terms against all English rows in the prepared full index, use `QUICKUMLS_TEST_FULL=1` in place of `QUICKUMLS_TEST_LICENSED=1`. To rebuild that index, extract `*/META/MRCONSO.RRF` and `*/META/MRSTY.RRF` into `.sandbox/full/META` and run the same installer with `.sandbox/full/index` as the destination.

## Installer measurements

The comparison used native UnQLite and SimString on Apple Silicon with Python 3.11. For the 1M-row check, both builds processed the same first 1,000,000 MRCONSO rows and corresponding MRSTY rows with English selection and lowercasing. All 165,296 stored terms had the same CUIs, semantic types and preferred flags as the source. All native SimString files matched byte for byte. Timings and peak RSS below are medians of three runs per revision for that sample.

| MRCONSO input | Original peak RSS / time | This checkout peak RSS / time |
| --- | --- | --- |
| 100,000 rows | 183.92 MiB / 0.780 s | 183.88 MiB / 0.816 s |
| 1,000,000 rows | 327.53 MiB / 4.290 s | 295.77 MiB / 4.701 s |
| Full 2026AB release (18,302,757 rows) | 12.02 GiB / 233.6 s | 9.26 GiB / 263.3 s |

The full-build row is a single run per revision on the same Mac, with lowercasing, Unicode folding and the model check skipped for both. The indexer processed 10,906,659 English atoms. Peak memory fell 23% and the build took 30 seconds longer. All 1,078 native SimString files matched the original build byte for byte. The licensed test also reopened the new index and verified the probe CUIs, semantic types and preferred flags against the full RRF inputs.

## Matcher and server

| Issues | Plan | Ready to close when |
| --- | --- | --- |
| [#74](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/74), [#102](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/102) · Public match flags ignored | In [core.py](../quickumls/core.py), `match()` calls `_match(parsed)` without either argument. Adapt [PR #75](https://github.com/Georgetown-IR-Lab/QuickUMLS/pull/75) to forward both by name and keep the existing defaults. The spaCy component already forwards them. | On the public API, `best_match=False` retains overlapping spans and `ignore_syntax=True` admits a term normally removed by syntax heuristics. Exercise all four flag combinations and the no-argument default. Resolve both reports with the same patch. |
| [#91](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/91) · Server cannot select semantic types | Add `--accepted-semtypes T047 T184` to [server.py](../quickumls/server.py), validate the TUI format, and pass the set to the matcher. When omitted, retain the constructor default; passing `None` would turn off filtering. | A local client and a direct matcher return the same results with defaults and with a custom subset. A malformed ID fails at argument parsing; the option appears in help. |
| [#82](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/82) · Windows returns no matches | The reporter isolated the difference to SimString retrieval on Windows versus Ubuntu. Build the same small index **on each OS** and check writer finalization, exact and fuzzy retrieval, then CUI lookup and semantic filtering. Fix the first layer that differs. | Both platforms retrieve the inserted term after reopening the index, and the public matcher returns its expected CUI. If the fixture already passes, collect the reporter's index flags and binding build before attributing the failure. |

## Native packages and release verification

| Issues | Plan | Ready to close when |
| --- | --- | --- |
| [#98](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/98), [#73](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/73), [#101](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/101) · LevelDB blocks Python 3.12 and native Windows installs | New indexes use UnQLite, but [requirements.txt](../requirements.txt) and [toolbox.py](../quickumls/toolbox.py) require LevelDB unconditionally. Make legacy LevelDB an optional dependency loaded only for that backend, including old indexes without a backend flag. Evaluate [PR #99](https://github.com/Georgetown-IR-Lab/QuickUMLS/pull/99) for that path: [Plyvel](https://plyvel.readthedocs.io/en/latest/api.html#plyvel.DB.get) returns a default on a missing key; the current adapter expects `KeyError`. Also update the [SimString loader](https://github.com/Georgetown-IR-Lab/simstring/blob/master/quickumls_simstring/simstring.py), which imports [`imp`, removed in Python 3.12](https://docs.python.org/3/library/imp.html). | Install and query an UnQLite index with no LevelDB on Ubuntu 24.04/Python 3.12 and native Windows. Separately read a pre-change LevelDB index, exercise misses, inserts and duplicates, and check that a missing legacy dependency gives an actionable error. |
| [#76](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/76), [#83](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/83), [#84](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/84), [#51](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/51) · SimString packaging on Windows | The first three traces fail while reading package metadata under GBK or CP1252; pip's resolver message in #83 is downstream. #51 also gets as far as missing MSVC/iconv headers. Compare [SimString's setup](https://github.com/Georgetown-IR-Lab/simstring/blob/master/setup.py) with its [published source distribution](https://pypi.org/project/quickumls-simstring/). Package the UTF-8 read and working iconv discovery, build native wheels, and update QuickUMLS's dependency floor only after those artifacts are available. Replace the README's legacy `setup.py install` path with `python -m pip install .`. | On native Windows, build metadata under both locales with UTF-8 mode off; test a source build with the documented compiler and iconv paths. A fresh wheel install must import the binding and round-trip a Unicode term without a compiler or local source edits. |
| [#62](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/62) · Linux extension cannot resolve `libiconv` | The error occurs on importing `_simstring.so`, before either RRF file is opened. Inspect linkage in clean Conda and system-Python environments; fix the binding's build or packaged runtime library in the environment that fails. | A fresh Linux process imports the release artifact and writes/reads a Unicode term without `LD_PRELOAD`. Document the affected build and interpreter so notebook users can select the repaired environment. |
| [#63](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/63) · SimString has no `writer` | The report used 1.3's top-level `simstring` and was resolved locally by installing the binding. Verify the current packaged import, `from quickumls_simstring import simstring`, and document the distinction from unrelated packages of the same name. | In a clean Linux/WSL environment both reader and writer work through the installed package. If not, capture the imported module path and fix the artifact at fault. |
| [#70](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/70) · macOS UnQLite build | The reporter confirmed an isolated Conda environment returned CUIs on an Intel Mac after the system-Python build failed. Document a verified macOS installation path and distinguish Intel from Apple Silicon when listing support. | A clean environment on an advertised architecture installs and matches the fixture. Record the working versions and close the original report with its confirmed workaround. |
| [#65](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/65), [#81](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/81) · PyPI package missing component or constructor flag | Both reports predate [release 1.4.2](https://pypi.org/project/quickumls/1.4.2/#files). Inspection of its published wheel confirmed that it ships both the component module and the constructor flag. Test the wheel and source distribution outside the checkout, then add that check to future releases. | Each artifact can import and construct `SpacyQuickUMLS` with the fixture without a constructor error or a second model load. Record the working version; cut another release only if the published artifacts fail this check and need a change. |

## spaCy integration and performance

| Issues | Plan | Ready to close when |
| --- | --- | --- |
| [#79](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/79), [#94](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/94) · Pipeline setup and duplicate extensions | Register a spaCy 3 factory in [spacy_component.py](../quickumls/spacy_component.py) and change the README to `nlp.add_pipe("quickumls", config={...})`. Construct the matcher once per pipeline. Make registration of `Span` extensions idempotent and handle a conflicting third-party extension without overwriting it. | Run the example verbatim on two documents and build a second pipeline in the same process without E966 or E090. A pre-existing incompatible extension is preserved and the conflict is reported clearly. |
| [#60](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/60) · Overlapping entities crash | Reconcile [PR #61](https://github.com/Georgetown-IR-Lab/QuickUMLS/pull/61) and [PR #88](https://github.com/Georgetown-IR-Lab/QuickUMLS/pull/88). Preserve candidate CUIs, scores and semantic types in a QuickUMLS-specific collection, including separate metadata for CUIs at identical offsets. Add only deterministic non-overlapping winners to `doc.ents`, honoring the configured score/length policy and preserving existing entities. | Two CUIs for one span, nested spans, and an overlap with an upstream NER entity all return usable candidates without an exception or lost metadata. Test both ranking policies. |
| [#68](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/68), [#86](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/86) · Obsolete model name and TLS download failure | The English mapping from [PR #72](https://github.com/Georgetown-IR-Lab/QuickUMLS/pull/72) is present in the [1.4.2 wheel](https://pypi.org/project/quickumls/1.4.2/#files). Verify at runtime that it loads a preinstalled `en_core_web_sm`. For restricted networks, document preinstalling the model and NLTK stopwords; offer an offline path that names missing assets without downloading. Keep certificate verification enabled. | With both resources present and networking disabled, build and query the index. With the model absent, the offline error names the full model and how to supply it. Treat any remaining certificate failure separately from the old `en` shortcut. |
| [#69](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/69) · Custom model | Add an optional standalone model name or path that overrides the language mapping. Keep the existing default; the pipeline component should reuse its caller's pipeline. Use the selected name/path in load errors. | The default model and a custom installed model both produce results; a missing override identifies the correct model. Component mode does not load an extra pipeline. |
| [#77](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/77) · Faster short-text matching | Benchmark standalone matching with NER excluded; it does not consume NER entities. After the flag fix, also compare tokenizer-only processing for `ignore_syntax=True`. Keep syntax annotations in the default path and leave caller-owned pipelines untouched. | Record warm throughput on short and long inputs with model/version specified. Adopt only changes that improve measured performance while preserving CUIs, offsets and scores; the reported 2× is a hypothesis. |

## Index construction

| Issues | Plan | Ready to close when |
| --- | --- | --- |
| [#64](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/64), [#95](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/95) · Memory usage and interrupted builds | [install.py](../quickumls/install.py) retains the semantic-type map, all seen CUI/term pairs, and all unique SimString terms. Profile each phase; use disk-backed membership for exact deduplication and move semantic types to disk if needed. Isolate the memory work in [PR #67](https://github.com/Georgetown-IR-Lab/QuickUMLS/pull/67) from its preferred-term API change, and check its duplicate-insertion tradeoff. #95's WSL process was killed near 5.5M rows; check exit status, WSL memory limit, OOM logs and disk space before declaring it the same defect. | Compare peak RSS, time, disk usage and query output on increasing synthetic inputs. Finish a full licensed build under a recorded memory limit; preserve duplicate handling, shared CUIs and preferred flags. Close #95 against this fix only if its failure is reproduced or confirmed. |
| [#58](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/58) · UnQLite lock on external macOS volume | Identify the filesystem and whether another process holds a lock. Compare a single writer on internal and external volumes with intentional writer contention. Explicitly close database handles on success and failure; report the locked path and document building locally and copying the closed index if needed. | A completed index can be reopened after moving it; a competing writer fails clearly and retry succeeds after release. Do not classify the external-volume failure as a deadlock without reproducing it. |

## Setup guidance and terminology requests

| Issues | Plan | Ready to close when |
| --- | --- | --- |
| [#90](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/90) · Broken license link | Replace the obsolete README URL with [NLM's licensing and access instructions](https://www.nlm.nih.gov/databases/umls.html). | From the README, a new user can reach the UTS account and license-request steps. |
| [#92](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/92) · Missing index on Colab | Show three distinct locations in a notebook example: the installed Python package, the user's licensed RRF input, and a persistent generated index. Run the installer on the input, then point the matcher at its **output**, not `site-packages`. Improve the missing-index error to name the required directory and command. | A fresh runtime builds a small index, and another runtime reopens the saved index and returns the known CUI without rebuilding. |
| [#89](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/89) · Only SNOMED or RxNorm | Turn the maintainer's answer into a README recipe: select the desired sources when creating the [MetamorphoSys subset](https://www.nlm.nih.gov/research/umls/implementation_resources/metamorphosys/help.html), then index its RRF output. Explain that source filtering and semantic-type filtering are different. | In a subset, verify the `MRCONSO.SAB` source inventory, match a retained term and exclude a source-only term from the omitted vocabulary. No matcher change is needed. |
| [#78](https://github.com/Georgetown-IR-Lab/QuickUMLS/issues/78) · CUI to ICD code | Document a lookup over the user's release of [MRCONSO](https://www.ncbi.nlm.nih.gov/books/NBK9685/table/ch03.T.concept_names_and_sources_file_mr/): filter by matched CUI and requested `SAB`, then return distinct `CODE` values. Distinguish ICD10 from ICD10CM and specify handling of suppressed rows. Offer an optional indexed lookup if in-process results are wanted. | An example reports zero, one, or multiple codes for the requested source without inferring a code where none exists. Existing indexes and default match output stay compatible. |
