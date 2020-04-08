# -*- coding: utf-8 -*-
# standard library imports
from pathlib import Path

# third-party imports
import pytest
import sh

# first-party imports
from tests.common import FASTA_PATH
from tests.common import GFF_PATH
from tests.common import fasta_count
from tests.common import line_count

DOWNLOAD_URL = "http://generisbio.com/ncgr/"
RAW_FASTA_FILE = "example_jemalong.fna"
RAW_GFF_FILE = "example_jemalong.gff3"


def test_prefix_gff(datadir_mgr):
    print("testing command prefix-gff")
    datadir_mgr.download(
        download_url=DOWNLOAD_URL,
        files=[RAW_GFF_FILE],
        scope="function",
        md5_check=True,
        gunzip=True,
        progressbar=False,
    )
    with datadir_mgr.in_tmp_dir(inpathlist=[RAW_GFF_FILE], save_outputs=True, excludepattern="*.log"):
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
                    RAW_GFF_FILE,
                ]
            )
        except sh.ErrorReturnCode as e:
            print(e)
            pytest.fail(e)
        print(output)
        loglist = list((Path.cwd() / "logs").glob("*"))
        assert len(loglist) is 1
        assert str(loglist[0].name) == "bionorm-prefix-gff.log"
        outdir_path = Path(GFF_PATH.parts[0])
        subdirname = list(outdir_path.glob("*"))[0].parts[-1]
        assert subdirname == GFF_PATH.parts[1]
        subdir_path = outdir_path / subdirname
        outfilename = list(subdir_path.glob("*"))[0].name
        assert outfilename == GFF_PATH.parts[2]
        assert line_count(Path(RAW_GFF_FILE)) == line_count(subdir_path / outfilename)


def test_prefix_fasta(datadir_mgr):
    print("testing command prefix-fasta")
    datadir_mgr.download(
        download_url=DOWNLOAD_URL,
        files=[RAW_FASTA_FILE],
        scope="function",
        md5_check=True,
        gunzip=True,
        progressbar=False,
    )
    with datadir_mgr.in_tmp_dir(inpathlist=[RAW_FASTA_FILE], save_outputs=True, excludepattern="*.log"):
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
                    RAW_FASTA_FILE,
                ]
            )
        except sh.ErrorReturnCode as e:
            print(e)
            pytest.fail(e)
        print(output)
        loglist = list((Path.cwd() / "logs").glob("*"))
        assert len(loglist) is 1
        assert str(loglist[0].name) == "bionorm-prefix-fasta.log"
        outdir_path = Path(FASTA_PATH.parts[0])
        subdirname = list(outdir_path.glob("*"))[0].parts[-1]
        assert subdirname == FASTA_PATH.parts[1]
        subdir_path = outdir_path / subdirname
        outfilename = list(subdir_path.glob("*"))[0].name
        assert outfilename == FASTA_PATH.parts[2]
        assert fasta_count(Path(RAW_FASTA_FILE)) == fasta_count(subdir_path / outfilename)