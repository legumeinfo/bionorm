# -*- coding: utf-8 -*-
# standard library imports
from pathlib import Path

# first-party imports
import sh

# module imports
from . import ANN_PATH
from . import CDS_PATH
from . import EXTRACTION_LIST
from . import FASTA_PATH
from . import GFF_PATH
from . import PREFIXING_LIST
from . import PROTEIN_COUNT
from . import PROTEIN_PATH
from . import fasta_count


def test_install_gffread(datadir_mgr):
    """Test install gffread."""
    with datadir_mgr.in_tmp_dir():
        output = sh.bionorm(["install", "gffread",])
        print(output)


def test_extraction(datadir_mgr):
    """Test command extract-fasta."""
    datadir_mgr.add_scope("prefix", module="1prefixing_test")
    with datadir_mgr.in_tmp_dir(
        inpathlist=PREFIXING_LIST, save_outputs=True, excludepatterns=["*.log"]
    ):
        output = sh.bionorm(["extract-fasta", str(GFF_PATH), str(FASTA_PATH)])
        print(output)
        loglist = [fp.name for fp in (Path.cwd() / "logs").glob("*")]
        assert len(loglist) is 1
        assert "bionorm-extract-fasta_0.log" in loglist
        outfilelist = [fp.name for fp in ANN_PATH.glob("*")]
        expectedlist = [p.name for p in EXTRACTION_LIST]
        for filename in expectedlist:
            assert filename in outfilelist
        assert fasta_count(PROTEIN_PATH) == PROTEIN_COUNT
        assert fasta_count(CDS_PATH) == PROTEIN_COUNT
