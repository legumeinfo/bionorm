# -*- coding: utf-8 -*-
"""Define global constants and common helper functions."""

# standard library imports
import locale
import os
from pathlib import Path
from pathlib import PosixPath

# third-party imports
import toml

# first-party imports
import click
from addict import Dict

#
# global constants
#
NAME = "bionorm"
__version__ = "0.7.6"
CONFIG_FILE_ENVVAR = NAME.upper() + "_CONFIG_FILE_PATH"
FASTA_TYPES = ["fna", "fasta", "fa", "faa"]
GFF_TYPES = ["gff", "gff3"]
COMPRESSED_TYPES = ["gz", "bgz", "bz", "xz"]
FAIDX_DICT = {"fai": "faidx", "gzi": "gzindex"}
ANNOTATION_SUBTYPES = {
    "cds": {"name": "cds", "ext": "fna", "modifiers": FAIDX_DICT},
    "mrna": {"name": "mrna", "ext": "fna", "modifiers": FAIDX_DICT},
    "protein": {"name": "protein", "ext": "faa", "modifiers": FAIDX_DICT},
    "protein_primaryTranscript": {
        "name": "primary",
        "ext": "faa",
        "modifiers": FAIDX_DICT,
    },
    "gene_models_main": {
        "name": "gff",
        "ext": "gff3",
        "modifiers": {"tbi": "tabix", "csi": "CSIindex"},
    },
}
GENOME_SUBTYPES = {
    "genome_main": {"name": "genome", "ext": "fna", "modifiers": FAIDX_DICT},
}
GENUS_CODE_LEN = 3
SPECIES_CODE_LEN = 2
KEY_LEN = 4
DIR_DESCRIPTORS = [
    "ann",
    "bac",
    "div",
    "expr",
    "esm",
    "fam",
    "genefam",
    "gnm",
    "map",
    "met",
    "mrk",
    "rpt",
    "samplesetN",
    "syn",
    "tcp",
    "trt",
]
# order in list will ultimately be order in tsv file
DATA_STORE_ATTRIBUTES = [
    "file_name",
    "dir_type",
    "file_type",
    "genus",
    "species",
    "scientific_name",
    "scientific_name_abbrev",
    "identifier",
    "genotype",
    "compressed",
    "invalid_key",
    "invalid_val",
    "about_dir",
    "annotation_dir",
    "applies_to",
] + DIR_DESCRIPTORS

COLLECTION_DIR = "." + NAME
COLLECTION_ATT_FILENAME = "collection_attributes.tsv"
METADATA_DIR_SUFFIX = "_metadata"
FILE_METADATA_SUFFIX = METADATA_DIR_SUFFIX + ".toml"
#
# set locale so grouping works
#
for localename in ["en_US", "en_US.utf8", "English_United_States"]:
    try:
        locale.setlocale(locale.LC_ALL, localename)
        break
    except BaseException:
        continue

#
# helper functions used in multiple places
#
def get_user_context_obj():
    """Return user context, containing logging and configuration data.

    :return: User context object (dict)
    """
    return click.get_current_context().obj


class PathToAttributes(Dict):

    """Dictionary/attributes of Data Store nodes."""

    def __init__(self, path=None):
        """Init addict, can query as dict or as attributes."""
        super().__init__()
        if path is None:
            path = Path.cwd()
        elif isinstance(path, Path):
            path = path
        else:
            path = Path(path)
        dir_types = (
            ("annotation", self.annotation_dir, self.annotation_file),
            ("genome", self.genome_dir, self.genome_file),
            ("about", self.about_dir, self.about_file),
            ("organism", self.organism_dir, self.organism_file),
        )
        for att in DATA_STORE_ATTRIBUTES:
            self[att] = None
        if path.is_file():
            for name, dir_method, file_method in dir_types:
                if dir_method(path.resolve().parent):
                    self.dir_type = name
                    self.file_name = path.name
                    self.compressed = path.suffix[1:] in COMPRESSED_TYPES
                    if not file_method(path):
                        self.file_type = "invalid"
                    break
        elif path.is_dir():
            # Check more-restrictive rules first
            for name, dir_method, file_method in dir_types:
                if dir_method(path):
                    self.dir_type = name
                    break

    def organism_dir(self, path):
        """Check if path.name is of form Genus_species."""
        name = path.resolve().name
        parts = name.split("_")
        if len(parts) != 2:
            return False
        if parts[0] != parts[0].capitalize():
            return False
        if parts[1] != parts[1].lower():
            return False
        self.genus = parts[0]
        self.species = parts[1]
        self.scientific_name = f"{parts[0]} {parts[1]}"
        self.scientific_name_abbrev = (
            f"{parts[0][:GENUS_CODE_LEN]}{parts[1][:SPECIES_CODE_LEN]}".lower()
        )
        return True

    def check_filename_part(self, namepart, key):
        """Check if part of filename agrees with directory info."""
        if namepart != self[key]:
            self.invalid_key = key
            self.invalid_val = namepart
            return False
        else:
            return True

    def annotation_file(self, path):
        """Check if annotation file is of known type."""
        name = path.resolve().name
        parts = name.split(".")
        if parts[-1] == "yml":
            return self.YAML_name_checker(name)
        elif parts[-1] == "md5":
            return self.MD5_name_checker(name)
        elif parts[-1] == "txt":
            return self.text_name_checker(name)
        if len(parts) < 7:
            self.invalid_key = "dots_in_name"
            self.invalid_val = len(parts)
            return False
        if not self.check_filename_part(parts[0], "scientific_name_abbrev"):
            return False
        if not self.check_filename_part(parts[1], "genotype"):
            return False
        if not self.versioned_val(parts[2], "gnm"):
            return False
        if not self.versioned_val(parts[3], "ann"):
            return False
        if not self.identifier_val(parts[4]):
            return False
        if parts[5] in ANNOTATION_SUBTYPES:
            subtype_dict = ANNOTATION_SUBTYPES[parts[5]]
            if not self.is_modified(parts[6:], subtype_dict):
                self.file_type = subtype_dict["name"]
            if parts[6] != subtype_dict["ext"]:
                self.invalid_key = "ext"
                self.invalid_val = parts[6]
                return False
        else:
            self.file_type = "unrecognized"
        return True

    def genome_file(self, path):
        """Check if file is a valid genomic file."""
        name = path.resolve().name
        parts = name.split(".")
        if parts[-1] == "yml":
            return self.YAML_name_checker(name)
        elif parts[-1] == "md5":
            return self.MD5_name_checker(name)
        elif parts[-1] == "txt":
            return self.text_name_checker(name)
        if len(parts) < 6:
            self.invalid_key = "dots_in_name"
            self.invalid_val = len(parts)
            return False
        if not self.check_filename_part(parts[0], "scientific_name_abbrev"):
            return False
        if not self.check_filename_part(parts[1], "genotype"):
            return False
        if not self.versioned_val(parts[2], "gnm"):
            return False
        if not self.identifier_val(parts[3]):
            return False
        if parts[4] in GENOME_SUBTYPES:
            subtype_dict = GENOME_SUBTYPES[parts[4]]
            if not self.is_modified(parts[5:], subtype_dict):
                self.file_type = subtype_dict["name"]
            if parts[5] != subtype_dict["ext"]:
                self.invalid_key = "ext"
                self.invalid_val = parts[5]
                return False
        else:
            self.file_type = "unrecognized"
        return True

    def about_file(self, path):
        """Check if file is a valid about_this_collection file."""
        name = path.resolve().name
        parts = name.split(".")
        if parts[-1] == "yml":
            return self.YAML_name_checker(name)
        else:
            self.file_type = "unrecognized"
        return True

    def organism_file(self, path):
        """Check if file is a valid organismic file."""
        self.file_type = "unrecognized"  # no organismic files
        return True

    def is_modified(self, endparts, subtype_dict):
        """Check if file has modifiers."""
        if len(endparts) < 2:
            return False
        if "modifiers" not in subtype_dict:
            return False
        if endparts[1] in COMPRESSED_TYPES:
            if len(endparts) < 3:
                return False
            mod_pos = 2
        else:
            mod_pos = 1
        if endparts[mod_pos] not in subtype_dict["modifiers"]:
            return False
        self.file_type = subtype_dict["modifiers"][endparts[mod_pos]]
        self.applies_to = subtype_dict["name"]
        return True

    def identifier_val(self, string):
        """Return True if string is upper-case of length KEY_LEN."""
        code = "identifier"
        if len(string) != KEY_LEN:
            self.invalid_key = code + "_len"
            self.invalid_val = string
            return False
        # decided that upppercase is not a strict rule for now
        # if string != string.upper():
        #    self.invalid_key = code + "_case"
        #    self.invalid_val = string
        #    return False
        if self[code] is None:
            self[code] = string
        elif self[code] != string:
            self.invalid_key = code
            self.invalid_val = string
            return False
        return True

    def versioned_val(self, string, code):
        """Return True if string is of form gnmN."""
        if not string.startswith(code):
            self.invalid_key = code
            self.invalid_val = string
            return False
        if len(code) == len(string):
            val = 0  # no number
        else:
            if not string[len(code) :].isnumeric():
                self.invalid_key = code + "_number"
                self.invalid_val = string[len(code) :]
                return False
            val = int(string[len(code) :])
        if self[code] is None:
            self[code] = val
        elif self[code] != val:
            self.invalid_key = code + "_verify"
            self.invalid_val = val
            return False
        return True

    def YAML_name_checker(self, filename):
        """Check for consistency of YAML filenames."""
        parts = filename.split(".")
        underscore_parts = parts[0].split("_")
        if parts[0] == "README":
            if len(parts) != 3:
                self.invalid_key = "length"
                self.invalid_val = len(parts)
                return False
            if not self.identifier_val(parts[1]):
                return False
            self.file_type = "readme"
        elif parts[0] == "MANIFEST":
            if len(parts) != 4:
                self.invalid_key = "length"
                self.invalid_val = len(parts)
                return False
            if not self.identifier_val(parts[1]):
                return False
            if parts[2] not in ["correspondence", "descriptions"]:
                self.invalid_key = "type"
                self.invalid_val = parts[2]
                return False
            self.file_type = parts[2]
        elif underscore_parts[0] in ["strains", "description"]:
            if len(underscore_parts) != 3:
                self.invalid_key = "length"
                self.invalid_val = len(underscore_parts)
                return False
            if underscore_parts[1] != self.genus:
                self.invalid_key = "genus"
                self.invalid_val = underscore_parts[1]
                return False
            if underscore_parts[2] != self.species:
                self.invalid_key = "species"
                self.invalid_val = underscore_parts[2]
                return False
            self.file_type = underscore_parts[0]
        else:
            self.invalid_key = "unknown_YAML"
            self.invalid_value = filename
            return False
        return True

    def MD5_name_checker(self, filename):
        """Check for consistency of YAML filenames."""
        parts = filename.split(".")
        if parts[0] == "CHECKSUM":
            if len(parts) != 3:
                self.invalid_key = "length"
                self.invalid_val = len(parts)
                return False
            if not self.identifier_val(parts[1]):
                return False
            self.file_type = "checksum"
        else:
            self.invalid_key = "name"
            self.invalid_val = parts[0]
            return False
        return True

    def text_name_checker(self, filename):
        """Check for consistency of text filenames."""
        if filename.startswith("original"):
            self.file_type = "original_text"
        else:
            self.file_type = "unrecognized"
        return True

    def genome_dir(self, path):
        """See if path is of form genotype.gnmX.KEYV"""
        name = path.resolve().name
        parts = name.split(".")
        if len(parts) != 3:
            return False
        if not self.versioned_val(parts[1], "gnm"):
            return False
        if not self.identifier_val(parts[2]):
            return False
        if not self.organism_dir(path.parent):
            return False
        self.genotype = parts[0]
        return True

    def annotation_dir(self, path):
        """See if path is of form strain.gnmX.annY.KEYV"""
        name = path.resolve().name
        parts = name.split(".")
        if len(parts) != 4:
            return False
        if not self.versioned_val(parts[1], "gnm"):
            return False
        if not self.versioned_val(parts[2], "ann"):
            return False
        if not self.identifier_val(parts[3]):
            return False
        if not self.organism_dir(Path(path.resolve().parent)):
            return False
        self.genotype = parts[0]
        return True

    def about_dir(self, path):
        """See if path is of form genotype.gnmX.KEYV"""
        name = path.resolve().name
        if name != "about_this_collection":
            return False
        if not self.organism_dir(path.parent):
            return False
        return True

    def describe(self, name):
        """Return human-readable summary of attributes."""
        node_text = f"Node {name} is "
        if self.file_name is not None:
            if self.file_type is not None:
                node_text += f"{self.file_type} file "
            else:
                node_text += "unknown file "
            if self.applies_to is not None:
                node_text += f"that applies to {self.applies_to} file "
            node_text += "in "
        if self.dir_type is not None:
            node_text += f"{self.dir_type} directory with "
        else:
            node_text += "in non-Data-Store directory with"
        n_keys = len([k for k in self.keys() if self[k] is not None])
        if n_keys and self.invalid_key is None:
            node_text += f"{n_keys} non-null Data Store attributes.\n"
        elif self.invalid_key is not None:
            node_text += f'invalid key "{self.invalid_key}" value "{self.invalid_val}"\n'
        else:
            node_text = "No Data Store attributes.\n"
        return node_text

    def __repr__(self):
        """Print Data Store attributes."""
        node_text = ""
        keys = [k for k in self.keys() if self[k] is not None]
        for key in sorted(keys):
            node_text += f"   {key}: {self[key]}\n"
        return node_text


def recursive_check_for_collection(path):
    "Check for access to COLLECTION_DIR in parents of path."
    if not os.access(path, os.R_OK):
        return None
    potential_path = path / COLLECTION_DIR
    if potential_path.exists():
        if potential_path.is_dir():
            return potential_path
        else:
            print(
                f"WARNING--{COLLECTION_DIR} exists in {path} but is not a"
                " directory."
            )
            return None
    else:
        if path == Path("/"):
            return None
        else:
            return recursive_check_for_collection(path.parent)


def find_collection_home(path=None):
    "Set path defaults then check for COLLECTION_DIR."
    if path is None:
        path = Path.cwd()
    if not path.is_absolute():
        path = path.absolute()
    return recursive_check_for_collection(path)


COLLECTION_HOME = find_collection_home()
METADATA_HOME = None
INSTALLATION_DICT = None
DATA_PATH = None
REPOSITORY_DICT = None
REPOSITORY_URL = None
COLLECTION_TITLE = None
if COLLECTION_HOME is not None:
    metadata_paths = list(COLLECTION_HOME.glob("*" + METADATA_DIR_SUFFIX))
    if len(metadata_paths) and metadata_paths[0].is_dir():
        METADATA_HOME = metadata_paths[0]
        collection_name = METADATA_HOME.name[: -len(METADATA_DIR_SUFFIX)]
        installation_data_path = COLLECTION_HOME / (collection_name + ".toml")
        if installation_data_path.exists():
            with installation_data_path.open("r") as inst_fh:
                INSTALLATION_DICT = toml.load(inst_fh)
                DATA_PATH = Path(
                    INSTALLATION_DICT["installation"]["data_path"]
                )
                if not DATA_PATH.is_absolute():
                    DATA_PATH = (COLLECTION_HOME / DATA_PATH).resolve()
        repository_path = METADATA_HOME / ("repository" + FILE_METADATA_SUFFIX)
        if repository_path.exists():
            with repository_path.open("r") as repo_fh:
                REPOSITORY_DICT = toml.load(repo_fh)
                REPOSITORY_URL = REPOSITORY_DICT["repository"]["download_url"]
                COLLECTION_TITLE = REPOSITORY_DICT["repository"]["title"]


class CollectionPath(PosixPath):

    """Pathlib path with Data Store attributes."""

    def __init__(self, path):
        """"Init with attributes."""
        super().__init__()
        self.collection_attributes = PathToAttributes(self)
        self.file_attributes = None

    def n_files(self):
        if self.is_dir:
            return len([f for f in self.glob("*") if f.is_file()])
        else:
            return None


def args_to_pathlist(nodelist, directory, recurse):
    """Process optional list of files."""
    if nodelist == ():  # empty nodelist
        if directory:
            pathlist = [Path(".")]
        else:
            pathlist = [p for p in Path(".").glob("*") if p.is_file()]
    else:
        pathlist = [n for n in Path(nodelist[0]).glob("*") if n.is_file()]
    if recurse:
        filelist = []
        for node in nodelist:
            filelist += [f for f in Path(node).rglob("*") if f.is_file()]
        pathlist = filelist
    return pathlist
