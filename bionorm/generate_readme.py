#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard library imports
import sys
from collections import UserDict
from pathlib import Path

# third-party imports
import click
from ruamel.yaml import YAML

# module imports
from . import cli
from .common import logger
from .common import GENUS_CODE_LEN
from .common import SPECIES_CODE_LEN
from .common import KEY_LEN


def read_yaml(template):
    """Reads yaml file and checks for valid yaml"""
    yaml = YAML()
    target_yaml = yaml.load(open(template, "rt"))
    return yaml, target_yaml


class PathToAttributes(UserDict):

    """Decide whether path is to an organism, genome, or annotation directory."""

    def __init__(self, path=None):
        super().__init__()
        if path is None:
            self.path = Path.cwd()
        else:
            self.path = Path(path).resolve()
        self.is_organism_dir = False
        self.is_genome_dir = False
        self.is_annotation_dir = False
        if not self.path.is_dir():
            return
        #
        # Check more-restrictive rules first.
        #
        if self.annotation_dir():
            self.is_annotation_dir = True
        elif self.genome_dir():
            self.is_genome_dir = True
        elif self.organism_dir(self.path):
            self.is_organism_dir = True

    def organism_dir(self, path):
        """Check if path.name is of form Genus_species."""
        parts = path.name.split("_")
        if len(parts) != 2:
            return False
        if parts[0] != parts[0].capitalize():
            return False
        if parts[1] != parts[1].lower():
            return False
        self["genus"] = parts[0]
        self["species"] = parts[1]
        self["scientific_name"] = f"{parts[0]} {parts[1]}"
        self["scientific_name_abbrev"] = f"{parts[0][:GENUS_CODE_LEN]}{parts[1][:SPECIES_CODE_LEN]}".lower()
        return True

    def key_val(self, string):
        """Return True if string is upper-case of length KEY_LEN."""
        if len(string) != KEY_LEN:
            return False
        if string != string.upper():
            return False
        self["identifier"] = string
        return True

    def genome_val(self, string):
        """Return True if string is of form gnmN."""
        if not string.startswith("gnm"):
            return False
        if not string[3:].isnumeric():
            return False
        self["gnm"] = int(string[3:])
        return True

    def annotation_val(self, string):
        """Return True if string is of form annN."""
        if not string.startswith("ann"):
            return False
        if not string[3:].isnumeric():
            return False
        self["ann"] = int(string[3:])
        return True

    def genome_dir(self):
        """See if path is of form genotype.gnmX.KEYV"""
        parts = self.path.name.split(".")
        if len(parts) != 3:
            return False
        if not self.genome_val(parts[1]):
            return False
        if not self.key_val(parts[2]):
            return False
        if not self.organism_dir(self.path.parent):
            return False
        self["genotype"] = parts[0]
        return True

    def annotation_dir(self):
        """See if path is of form strain.gnmX.annY.KEYV"""
        parts = self.path.name.split(".")
        if len(parts) != 4:
            return False
        if not self.genome_val(parts[1]):
            return False
        if not self.annotation_val(parts[2]):
            return False
        if not self.key_val(parts[3]):
            return False
        if not self.organism_dir(Path(self.path.parent)):
            return False
        self["genotype"] = parts[0]
        return True


@cli.command()
@click.option("--force/--no-force", help="Force overwrites of existing binaries.", default=False)
@click.argument("target_dir", nargs=-1)
def generate_readme(target_dir, force):
    """Write context-appropriate templated qREADME YAML file to target_dir.

    \b
    Example:
        bionorm generate-readme # generates README in current directory
        bionorm generate-readme Medicago_truncatula/ # organism directory
        bionorm generate-readme  Medicago_truncatula/jemalong_A17.gnm5.FAKE/ # genome directory
        bionorm generate_readme Medicago_truncatula/jemalong_A17.gnm5.ann1.FAKE/ # annotation directory

    """
    if target_dir == ():
        target_dir = None
    elif len(target_dir) == 1:
        target_dir = target_dir[0]
    else:
        print(f"ERROR--unrecognized extra argument '{target_dir}'. ")
        sys.error(1)
    attributes = PathToAttributes(target_dir)
    if attributes.is_annotation_dir:
        print("annotation dir")
    elif attributes.is_genome_dir:
        print("genome dir")
    elif attributes.is_organism_dir:
        print("organism dir")
    else:
        print(f"ERROR--target directory '{target_dir}' is not a recognized type.")
        sys.exit(1)
    print(attributes)
    # yaml, my_yaml = read_yaml(template)
    # for key in ("identifier", "genotype", "scientific_name", "scientific_name_abbrev"):
    #    my_yaml[key] == attributes["key"]
    # with target_path / f"README.{key}.yaml" as readme_handle:
    #   yaml.dump(my_yaml, readme_handle)
