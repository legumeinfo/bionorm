# -*- coding: utf-8 -*-
"""Define global constants and common helper functions."""

# standard library imports
import locale
import logging
from pathlib import Path
from pathlib import PurePosixPath

# third-party imports
import click
from addict import Dict

#
# global constants
#
PROGRAM_NAME = "bionorm"
CONFIG_FILE_ENVVAR = "BIONORM_CONFIG_FILE_PATH"
FASTA_TYPES = ["fna", "fasta", "fa", "faa"]
GFF_TYPES = ["gff", "gff3"]
COMPRESSED_TYPES = ["gz", "bgz", "bz", "xz"]
FAIDX_DICT = {"fai": "faidx", "gzi": "gzindex"}
ANNOTATION_SUBTYPES = {
    "cds": {"name": "cds", "ext": "fna", "modifiers": FAIDX_DICT},
    "mrna": {"name": "mrna", "ext": "fna", "modifiers": FAIDX_DICT},
    "protein": {"name": "protein", "ext": "faa", "modifiers": FAIDX_DICT},
    "protein_primaryTranscript": {"name": "primary", "ext": "faa", "modifiers": FAIDX_DICT},
    "gene_models_main": {"name": "gff", "ext": "gff3", "modifiers": {"tbi": "tabix", "csi": "CSIindex"}},
}
GENOME_SUBTYPES = {
    "genome_main": {"name": "genome", "ext": "fna", "modifiers": FAIDX_DICT},
}
GENUS_CODE_LEN = 3
SPECIES_CODE_LEN = 2
KEY_LEN = 4
#
# global logger object
#
logger = logging.getLogger(PROGRAM_NAME)
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


class DataStorePath(PurePosixPath):

    """Pathlib path with Data Store attributes."""

    def __init__(self, path):
        """"Init with attributes."""
        super().__init__()
        self.data_store_attributes = PathToDataStoreAttributes(self)


class PathToDataStoreAttributes(Dict):

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
        self.file_type = None
        self.file_subtype = None
        self.dir_type = None
        self.invalid = False
        self.invalid_key = None
        self.invalid_val = None
        if path.is_file():
            self.file_type = "unknown"
            self.file_subtype = "unrecognized"
            self.modifies = None
            self.compressed = path.suffix[1:] in COMPRESSED_TYPES
            if self.annotation_dir(path.resolve().parent):
                self.file_type = "annotation"
                if not self.annotation_file(path):
                    self.invalid = True
            elif self.genome_dir(path.resolve().parent):
                self.file_type = "genomic"
                if not self.genome_file(path):
                    self.invalid = True
            elif self.organism_dir(path.parent):
                self.file_type = "organism"
                self.is_organism_file = True
            return
        elif path.is_dir():
            dir_types = (
                ("annotation", self.annotation_dir),
                ("genome", self.genome_dir),
                ("organism", self.organism_dir),
            )
            # Check more-restrictive rules first
            self.dir_type = "unrecognized"
            for name, dir_method in dir_types:
                if dir_method(path):
                    self.dir_type = name
                    break

    def organism_dir(self, path):
        """Check if path.name is of form Genus_species."""
        parts = path.resolve().name.split("_")
        if len(parts) != 2:
            return False
        if parts[0] != parts[0].capitalize():
            return False
        if parts[1] != parts[1].lower():
            return False
        self.genus = parts[0]
        self.species = parts[1]
        self.scientific_name = f"{parts[0]} {parts[1]}"
        self.scientific_name_abbrev = f"{parts[0][:GENUS_CODE_LEN]}{parts[1][:SPECIES_CODE_LEN]}".lower()
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
        parts = path.resolve().name.split(".")
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
                self.file_subtype = subtype_dict["name"]
            if parts[6] != subtype_dict["ext"]:
                self.invalid_key = "ext"
                self.invalid_val = parts[6]
                return False
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
        self.file_subtype = subtype_dict["modifiers"][endparts[mod_pos]]
        self.modifies = subtype_dict["name"]
        return True

    def genome_file(self, path):
        """Check if file is a valid genomic file."""
        parts = path.resolve().name.split(".")
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
                self.file_subtype = subtype_dict["name"]
            if parts[5] != subtype_dict["ext"]:
                self.invalid_key = "ext"
                self.invalid_val = parts[5]
                return False
        return True

    def identifier_val(self, string):
        """Return True if string is upper-case of length KEY_LEN."""
        code = "identifier"
        if len(string) != KEY_LEN:
            self.invalid_key = code + "_len"
            self.invalid_val = string
            return False
        if string != string.upper():
            self.invalid_key = code + "_case"
            self.invalid_val = string
            return False
        if code not in self:
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
        if not string[len(code) :].isnumeric():
            self.invalid_key = code + "_number"
            self.invalid_val = string[len(code) :]
            return False
        val = int(string[len(code) :])
        if code not in self:
            self[code] = val
        elif self[code] != val:
            self.invalid_key = code + "_number"
            self.invalid_val = val
            return False
        return True

    def genome_dir(self, path):
        """See if path is of form genotype.gnmX.KEYV"""
        parts = path.resolve().name.split(".")
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
        parts = path.resolve().name.split(".")
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

    def __repr__(self):
        """Print Data Store attributes."""
        node_text = "Node is "
        if self.dir_type is not None:
            node_text += f"{self.dir_type} directory with "
        elif self.file_type is not None:
            node_text += f"{self.file_type} {self.file_subtype} "
            if self.modifies is not None:
                node_text += f"of {self.modifies} "
        exclusionlist = ["invalid", "invalid_key", "invalid_val", "dir_type", "file_type", "file_subtype", "modifies"]
        keys = [k for k in self.keys() if k not in exclusionlist]
        if len(keys) and not self.invalid:
            node_text += f"file with {len(keys)} Data Store attributes:\n"
            for key in sorted(keys):
                node_text += f"   {key}: {self[key]}\n"
        elif self.invalid:
            node_text += f'invalid key "{self.invalid_key}" value "{self.invalid_val}"\n'
        else:
            node_text = "no Data Store attributes."
        return node_text
