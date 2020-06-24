# -*- coding: utf-8 -*-
# standard library imports
from pathlib import Path

# first-party imports
import sh

# module imports
from . import FASTA_PATH
from . import GFF_PATH


def test_install_samtools(datadir_mgr):
    """Test install samtools"""
    with datadir_mgr.in_tmp_dir():
        print("installing samtools")
        output = sh.bionorm(["install", "samtools",])
        print(output)


def test_index_fasta(datadir_mgr):
    """Test index_fasta."""
    datadir_mgr.add_scope("prefix", module="1prefixing_test")
    with datadir_mgr.in_tmp_dir(
        inpathlist=[FASTA_PATH], save_outputs=True, excludepatterns=["*.log"],
    ):
        output = sh.bionorm(["index-fasta", str(FASTA_PATH)])
        print(output)


def test_index_gff(datadir_mgr):
    """Test index_gff."""
    datadir_mgr.add_scope("prefix", module="1prefixing_test")
    with datadir_mgr.in_tmp_dir(
        inpathlist=[GFF_PATH], save_outputs=True, excludepatterns=["*.log"],
    ):
        output = sh.bionorm(["index-gff", str(GFF_PATH)])
        print(output)
