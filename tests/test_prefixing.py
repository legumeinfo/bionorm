# stdlib imports
# standard library imports
import contextlib
import os
import shutil
from pathlib import Path

# third-party imports
import pytest
import sh

# global constants
FASTA_FILE = "example_jemalong.fna"
GFF_FILE = "example_jemalong.gff3"


@contextlib.contextmanager
def data_to_working_directory(tmp_path, copy_fasta=False, copy_gff=False):
    """Copy data and change context to tmp_path directory."""
    cwd = Path.cwd()
    test_path = Path(__file__).parent
    if copy_fasta:
        shutil.copy2(test_path / FASTA_FILE, tmp_path / FASTA_FILE)
    if copy_gff:
        shutil.copy2(test_path / GFF_FILE, tmp_path / GFF_FILE)
    os.chdir(tmp_path)
    try:
        yield
    finally:
        os.chdir(cwd)


def linecount(filepath):
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


def test_prefix_gff(tmp_path):
    print("testing command prefix-gff")
    with data_to_working_directory(tmp_path, copy_gff=True):
        try:
            output = sh.bionorm(
                [
                    "prefix-gff",
                    "--gnm",
                    "5",
                    "--ann",
                    "1",
                    "--genus",
                    "medicago",
                    "--species",
                    "truncatula",
                    "--infra_id",
                    "jemalong_A17",
                    "--key",
                    "FAKE",
                    "example_jemalong.gff3",
                ]
            )
        except sh.ErrorReturnCode as e:
            print(e)
            pytest.fail(e)
        print(output)
        loglist = list((tmp_path / "logs").glob("*"))
        assert len(loglist) is 1
        assert str(loglist[0].name) == "bionorm-prefix-gff.log"
        outdir_path = Path("Medicago_truncatula")
        subdirname = list(outdir_path.glob("*"))[0].parts[-1]
        assert subdirname == "jemalong_A17.gnm5.ann1.FAKE"
        subdir_path = outdir_path / subdirname
        outfilename = list(subdir_path.glob("*"))[0].name
        assert outfilename == "medtr.jemalong_A17.gnm5.ann1.FAKE.gene_models_main.gff3"
        assert linecount(Path(GFF_FILE)) == linecount(subdir_path / outfilename)


def test_prefix_fasta(tmp_path):
    print("testing command prefix-fasta")
    with data_to_working_directory(tmp_path, copy_fasta=True):
        try:
            output = sh.bionorm(
                [
                    "prefix-fasta",
                    "--genver",
                    "5",
                    "--genus",
                    "medicago",
                    "--species",
                    "truncatula",
                    "--infra_id",
                    "jemalong_A17",
                    "--key",
                    "FAKE",
                    "example_jemalong.fna",
                ]
            )
        except sh.ErrorReturnCode as e:
            print(e)
            pytest.fail(e)
        print(output)
        loglist = list((tmp_path / "logs").glob("*"))
        assert len(loglist) is 1
        assert str(loglist[0].name) == "bionorm-prefix-fasta.log"
        outdir_path = Path("Medicago_truncatula")
        subdirname = list(outdir_path.glob("*"))[0].parts[-1]
        assert subdirname == "jemalong_A17.gnm5.FAKE"
        subdir_path = outdir_path / subdirname
        outfilename = list(subdir_path.glob("*"))[0].name
        assert outfilename == "medtr.jemalong_A17.gnm5.FAKE.genome_main.fna"
        assert fasta_count(Path(FASTA_FILE)) == fasta_count(subdir_path / outfilename)
