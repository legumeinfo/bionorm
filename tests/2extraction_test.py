# -*- coding: utf-8 -*-
# standard library imports
from pathlib import Path

# third-party imports
import pytest
import sh

from tests.common import FASTA_PATH
from tests.common import GFF_PATH
from tests.common import fasta_count


def test_install_gffread(datadir_mgr):
    print("testing command prefix-gff")
    with datadir_mgr.in_tmp_dir():
        print("installing gffread")
        output = sh.bionorm(["install", "gffread",])
        print(output)


def test_extraction(datadir_mgr):
    print("testing command prefix-gff")
    datadir_mgr.add_scope("prefix", module="prefixing_test")
    with datadir_mgr.in_tmp_dir(inpathlist=[GFF_PATH, FASTA_PATH], save_outputs=True, excludepattern="*.log"):
        print("extracting fasta")
        output = sh.bionorm(["extract-fasta", str(GFF_PATH), str(FASTA_PATH)])
        print(output)
        loglist = [fp.name for fp in (Path.cwd() / "logs").glob("*")]
        assert len(loglist) is 1
        assert "bionorm-extract-fasta.log" in loglist
        outdir_path = Path(GFF_PATH.parts[0]) / GFF_PATH.parts[1]
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
