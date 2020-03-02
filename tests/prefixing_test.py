# -*- coding: utf-8 -*-
# standard library imports
from pathlib import Path

# third-party imports
import pytest
import sh

# first-party imports
from tests.counters import fasta_count
from tests.counters import line_count
from tests.download_files import DownloadTestFiles

# global constants
FASTA_FILE = "example_jemalong.fna"
GFF_FILE = "example_jemalong.gff3"

dlmanager = DownloadTestFiles(
    download_url="http://generisbio.com/ncgr/",
    files=[FASTA_FILE, GFF_FILE],
    md5_check=True,
    gzipped=True,
    progressbar=False,
)


def test_prefix_gff(tmp_path):
    print("testing command prefix-gff")
    with dlmanager.data_to_working_directory(tmp_path, [GFF_FILE]):
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
        assert line_count(Path(GFF_FILE)) == line_count(subdir_path / outfilename)


def test_prefix_fasta(tmp_path):
    print("testing command prefix-fasta")
    with dlmanager.data_to_working_directory(tmp_path, [FASTA_FILE]):
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
