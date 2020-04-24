# -*- coding: utf-8 -*-
# standard library imports\
import json
from pathlib import Path

# third-party imports
import sh

from tests.common import ANN_PATH
from tests.common import GENOME_PATH

FASTA_NAME = "medtr.jemalong_A17.gnm5.FAKE.genome_main.fna"
GFF_PATH = "medtr.jemalong_A17.gnm5.ann1.FAKE.gene_models_main.gff3"
ORGANISM_DIR = str(ANN_PATH.parent)
UNREC_PATH = ANN_PATH / "medtr.jemalong_A17.gnm5.ann1.FAKE.badname.fna"
ANN_INVALID_LIST = [
    ("bad.jemalong_A17.gnm5.ann1.FAKE.genome_name.fna", "scientific_name_abbrev"),
    ("medtr.jemalong_A17.gnm1.ann1.FAKE.genome_name.fna", "gnm_verify"),
    ("medtr.jemalong_A17.gnm5.ann2.FAKE.genome_name.fna", "ann_verify"),
    ("medtr.jemalong_A17.gnm5.ann1.BADD.genome_name.fna", "identifier"),
]


def test_ls(datadir_mgr):
    """Test ls command. """
    test_file_paths = []
    test_file_paths += datadir_mgr.paths_from_scope(module="1prefixing_test")
    test_file_paths += datadir_mgr.paths_from_scope(module="2extraction_test")
    test_file_paths += datadir_mgr.paths_from_scope(module="3indexing_test")
    datadir_mgr.add_scope("prefix", module="1prefixing_test")
    datadir_mgr.add_scope("extract", module="2extraction_test")
    datadir_mgr.add_scope("index", module="3indexing_test")
    with datadir_mgr.in_tmp_dir(
        inpathlist=test_file_paths, save_outputs=True, excludepatterns=["*.log"],
    ):
        output = sh.bionorm(["ls", "--recurse", ORGANISM_DIR])
        lines_out = output.count("\n")
        assert lines_out == len(test_file_paths)
        assert not sh.bionorm(["ls", "-r", "--invalid", ORGANISM_DIR]).count("\n")  # no invalid filename
        assert not sh.bionorm(["ls", "-r", "--unrecognized", ORGANISM_DIR]).count("\n")  # no unrecognized filenames
        UNREC_PATH.touch()
        assert 1 == sh.bionorm(["ls", "-ru", ORGANISM_DIR]).count("\n")  # now 1 unrecognized filename
        UNREC_PATH.unlink()
        for badname, reason in ANN_INVALID_LIST:
            badpath = ANN_PATH / badname
            badpath.touch()
            print(f"testing {reason}")
            jsondict = sh.bionorm(["ls", "-rji", ORGANISM_DIR])
            result_dict = json.loads(str(jsondict))
            assert "invalid_key" in result_dict
            assert result_dict["invalid_key"] == reason
            badpath.unlink()
