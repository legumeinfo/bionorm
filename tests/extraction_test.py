# -*- coding: utf-8 -*-
# standard library imports
from pathlib import Path

# third-party imports
import pytest
import sh

# first-party imports
from tests.counters import fasta_count
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


def test_extraction(tmp_path):
    print("testing command prefix-gff")
    with dlmanager.data_to_working_directory(tmp_path, [GFF_FILE, FASTA_FILE]):
        try:
            sh.bionorm(
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
            sh.bionorm(
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
            output = sh.bionorm(
                [
                    "extract-fasta",
                    "Medicago_truncatula/jemalong_A17.gnm5.ann1.FAKE/medtr.jemalong_A17.gnm5.ann1.FAKE.gene_models_main.gff3",
                    "Medicago_truncatula/jemalong_A17.gnm5.FAKE/medtr.jemalong_A17.gnm5.FAKE.genome_main.fna",
                ]
            )
        except sh.ErrorReturnCode as e:
            print(e)
            pytest.fail(e)
        print(output)
        loglist = [fp.name for fp in (tmp_path / "logs").glob("*")]
        assert len(loglist) is 3
        assert "bionorm-extract-fasta.log" in loglist
        outdir_path = Path("Medicago_truncatula") / "jemalong_A17.gnm5.ann1.FAKE"
        outfilelist = [fp.name for fp in outdir_path.glob("*")]
        cdsfile = "medtr.jemalong_A17.gnm5.ann1.FAKE.cds.fna"
        proteinfile = "medtr.jemalong_A17.gnm5.ann1.FAKE.protein.faa"
        expectedlist = [
            cdsfile,
            proteinfile,
            "medtr.jemalong_A17.gnm5.ann1.FAKE.mrna.fna",
            "medtr.jemalong_A17.gnm5.ann1.FAKE.protein_primaryTranscript.faa",
        ]
        for filename in expectedlist:
            assert filename in outfilelist
        assert fasta_count(outdir_path / proteinfile) == fasta_count(outdir_path / cdsfile)
