# -*- coding: utf-8 -*-
# standard library imports
from pathlib import Path

# third-party imports
import pytest
import sh

# first-party imports
from tests.common import fasta_count
from tests.common import in_tmp_dir
from tests.common import GFF_FILE
from tests.common import FASTA_FILE


@pytest.mark.dependency()
def test_extraction(tmp_path, datadir_copy):
    print("testing command prefix-gff")
    with in_tmp_dir(tmp_path, datadir_copy, [GFF_FILE, FASTA_FILE]):
        print("installing gffread")
        output = sh.bionorm(["install", "gffread",])
        print(output)
        print("prefixing gff")
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
        print(output)


#        print("Prefixing fasta")
#        output = sh.bionorm(
#            [
#                "prefix-fasta",
#                "--genver",
#                "5",
#                "--genus",
#                "medicago",
#                "--species",
#                "truncatula",
#                "--infra_id",
#                "jemalong_A17",
#                "--key",
#                "FAKE",
#                "example_jemalong.fna",
#            ]
#        )
#        print(output)
#        print("extracting fasta")
#       output = sh.bionorm(
#            [
#                "extract-fasta",
#                "Medicago_truncatula/jemalong_A17.gnm5.ann1.FAKE/medtr.jemalong_A17.gnm5.ann1.FAKE.gene_models_main.gff3",
#                "Medicago_truncatula/jemalong_A17.gnm5.FAKE/medtr.jemalong_A17.gnm5.FAKE.genome_main.fna",
#            ]
#        )
#        print(output)
#        loglist = [fp.name for fp in (tmp_path / "logs").glob("*")]
#        assert len(loglist) is 4
#        assert "bionorm-extract-fasta.log" in loglist
#        outdir_path = Path("Medicago_truncatula") / "jemalong_A17.gnm5.ann1.FAKE"
#        outfilelist = [fp.name for fp in outdir_path.glob("*")]
#        cdsfile = "medtr.jemalong_A17.gnm5.ann1.FAKE.cds.fna"
#        proteinfile = "medtr.jemalong_A17.gnm5.ann1.FAKE.protein.faa"
#        expectedlist = [
#            cdsfile,
#            proteinfile,
#            "medtr.jemalong_A17.gnm5.ann1.FAKE.mrna.fna",
#            "medtr.jemalong_A17.gnm5.ann1.FAKE.protein_primaryTranscript.faa",
#        ]
#        for filename in expectedlist:
#            assert filename in outfilelist
#        assert fasta_count(outdir_path / proteinfile) == fasta_count(outdir_path / cdsfile)
