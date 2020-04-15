# -*- coding: utf-8 -*-
# standard library imports
from pathlib import Path

# third-party imports
import sh

from tests.common import CDS_PATH
from tests.common import GFF_PATH
from tests.common import MRNA_PATH
from tests.common import TRANSCRIPT_PATH


def test_install_genometools(datadir_mgr):
    """Test install genometools"""
    with datadir_mgr.in_tmp_dir():
        print("installing gffread")
        output = sh.bionorm(["install", "gffread",])
        print(output)


def test_consistency(datadir_mgr):
    """Test consistency"""
    datadir_mgr.add_scope("prefix", module="1prefixing_test")
    datadir_mgr.add_scope("extract", module="2extraction_test")
    with datadir_mgr.in_tmp_dir(
        inpathlist=[CDS_PATH, GFF_PATH, MRNA_PATH, TRANSCRIPT_PATH], save_outputs=True, excludepattern="*.log"
    ):
        output = sh.bionorm(["consistency"])
        print(output)
