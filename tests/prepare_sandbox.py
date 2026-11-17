"""Build .sandbox/META from the user's UMLS Metathesaurus full-release ZIP."""

import argparse
import io
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from zipfile import ZipFile


SANDBOX = Path(__file__).resolve().parents[1] / ".sandbox"
# Ordinary search inputs exercise overlapping mentions, drugs, symptoms, and Unicode.
TERMS = {
    "aspirin", "chest pain", "pain", "headache", "heart", "heart failure",
    "congestive heart failure", "diabetes mellitus", "type 2 diabetes mellitus",
    "vitamin a", "sjögren syndrome", "sjögren's syndrome", "ménière disease",
    "ménière's disease",
}


def prepare(archive_path):
    SANDBOX.mkdir(exist_ok=True)
    with ZipFile(archive_path) as archive, TemporaryDirectory(dir=SANDBOX) as temp:
        inputs = [PurePosixPath(name) for name in archive.namelist()
                  if PurePosixPath(name).name == "MRCONSO.RRF"]
        if len(inputs) != 1:
            raise ValueError("Expected one MRCONSO.RRF in the Metathesaurus ZIP")
        conso = inputs[0]
        sty = conso.with_name("MRSTY.RRF")
        archive.getinfo(str(sty))  # Both files must come from the same release.

        stage = Path(temp)
        cuis = set()
        found_terms = set()
        atom_count = 0
        with archive.open(str(conso)) as member, (stage / conso.name).open("wb") as out:
            for row in io.BufferedReader(member, buffer_size=1024 * 1024):
                fields = row.split(b"|", 15)
                if fields[1] == b"ENG":
                    term = fields[14].decode("utf-8").casefold()
                    if term in TERMS:
                        out.write(row)
                        cuis.add(fields[0])
                        found_terms.add(term)
                        atom_count += 1
        missing = {"aspirin", "chest pain", "pain", "headache"} - found_terms
        if missing:
            raise ValueError(f"Missing core sandbox terms: {', '.join(sorted(missing))}")

        typed_cuis = set()
        type_count = 0
        with archive.open(str(sty)) as member, (stage / sty.name).open("wb") as out:
            for row in io.BufferedReader(member, buffer_size=1024 * 1024):
                cui = row.partition(b"|")[0]
                if cui in cuis:
                    out.write(row)
                    typed_cuis.add(cui)
                    type_count += 1
        if typed_cuis != cuis:
            raise ValueError(f"Missing MRSTY rows for {len(cuis - typed_cuis)} CUIs")

        destination = SANDBOX / "META"
        destination.mkdir(exist_ok=True)
        for name in (conso.name, sty.name):
            (stage / name).replace(destination / name)
        print(f"Wrote {atom_count} English atoms and {type_count} semantic type rows "
              f"for {len(cuis)} CUIs to {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Path to the licensed UMLS full-release ZIP")
    args = parser.parse_args()
    prepare(args.archive)
