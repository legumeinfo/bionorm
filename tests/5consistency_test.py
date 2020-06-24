# -*- coding: utf-8 -*-
# standard library imports
from pathlib import Path

# first-party imports
import sh

# module imports
from . import CDS_PATH
from . import FASTA_PATH
from . import GFF_PATH
from . import MRNA_PATH
from . import TRANSCRIPT_PATH


def test_install_genometools(datadir_mgr):
    """Test install genometools"""
    with datadir_mgr.in_tmp_dir():
        print("installing gffread")
        output = sh.bionorm(["install", "genometools",])
        print(output)


def test_consistency(datadir_mgr):
    """Test consistency"""
    datadir_mgr.add_scope("prefix", module="1prefixing_test")
    datadir_mgr.add_scope("extract", module="2extraction_test")
    with datadir_mgr.in_tmp_dir(
        inpathlist=[
            CDS_PATH,
            GFF_PATH,
            FASTA_PATH,
            MRNA_PATH,
            TRANSCRIPT_PATH,
        ],
        save_outputs=True,
        excludepatterns=["*.log"],
    ):
        output = sh.bionorm(["consistency", "--help"])
        print(output)
