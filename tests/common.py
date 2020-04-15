# -*- coding: utf-8 -*-

# standard library imports
from pathlib import Path

# global constants
FASTA_PATH = Path("Medicago_truncatula") / "jemalong_A17.gnm5.FAKE" / "medtr.jemalong_A17.gnm5.FAKE.genome_main.fna"
ANN_PATH = Path("Medicago_truncatula") / "jemalong_A17.gnm5.ann1.FAKE"
GFF_PATH = ANN_PATH / "medtr.jemalong_A17.gnm5.ann1.FAKE.gene_models_main.gff3"
PROTEIN_PATH = ANN_PATH / "medtr.jemalong_A17.gnm5.ann1.FAKE.protein.faa"
CDS_PATH = ANN_PATH / "medtr.jemalong_A17.gnm5.ann1.FAKE.cds.fna"
MRNA_PATH = ANN_PATH / "medtr.jemalong_A17.gnm5.ann1.FAKE.mrna.fna"
TRANSCRIPT_PATH = ANN_PATH / "medtr.jemalong_A17.gnm5.ann1.FAKE.protein_primaryTranscript.faa"


def line_count(filepath):
    """Count the number of lines in a file"""
    lines = 0
    buf_size = 1024 * 1024
    with filepath.open("rb") as fh:
        read_f = fh.raw.read
        buf = read_f(buf_size)
        while buf:
            lines += buf.count(b"\n")
            buf = read_f(buf_size)
    return lines


def fasta_count(filepath):
    """Count the number of lines in a file"""
    lines = 0
    buf_size = 1024 * 1024
    with filepath.open("rb") as fh:
        read_f = fh.raw.read
        buf = read_f(buf_size)
        while buf:
            lines += buf.count(b">")
            buf = read_f(buf_size)
    return lines
