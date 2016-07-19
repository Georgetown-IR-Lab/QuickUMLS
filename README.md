# QuickUMLS

QuickUMLS (Soldaini and Goharian, 2015) is a tool for fast, unsupervised  biomedical concept extraction from medical text.
It takes advantage of [Simstring](http://www.chokkan.org/software/simstring/) (Okazaki and Tsujii, 2010) for approximate string matching.
For more details on how QuickUMLS works, we remand to our paper.

This project should be compatible with both Python 2 and 3. **If you find any bugs, please file an issue here on GitHub or email the author at `luca@ir.cs.georgetown.edu`**

## Installation

Before starting:

1. This software requires all packages listed in the requirements.txt file. You can install all of them by running `pip install -r requirements.txt`.
2. Note that, in order to use `spacy`, you are required to download its corpus. You can do that by running `python -m spacy.en.download`.
3. This system requires you to have a valid UMLS installation on disk. The installation can be remove once the system has been initialized.

To get the system running:

1. Download and compile Simstring by running `sh setup_simstring.sh <python_version>`, where `<python_version>` is either "`2`" or "`3`".
2. Initialize the system by running `python install.py <umls_installation_path> <destination_path>`, where `<umls_installation_path>` is where the installation files are (in particular, we need `MRCONSO.RRF` and `MRSTY.RRF`) and `<destination_path>` is the directory where the

## References

- Okazaki, Naoaki, and Jun'ichi Tsujii. "*Simple and efficient algorithm for approximate dictionary matching.*" COLING 2010.
- Luca Soldaini and Nazli Goharian. "*QuickUMLS: a fast, unsupervised approach for medical concept extraction.*" MedIR Workshop, SIGIR 2016.
