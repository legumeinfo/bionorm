#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard library imports
import sys
from pathlib import Path

# first-party imports
import click
from ruamel.yaml import YAML

# module imports
from . import cli


@cli.command()
@click.option(
    "--force/--no-force",
    help="Force overwrites of existing binaries.",
    default=False,
)
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
        target_dir = Path(target_dir[0])
    else:
        print(f"ERROR--unrecognized extra argument '{target_dir}'. ")
        sys.error(1)
    attributes = PathToDataStoreAttributes(target_dir)
    if attributes.is_annotation_dir:
        print("annotation dir")
    elif attributes.is_genome_dir:
        print("genome dir")
    elif attributes.is_organism_dir:
        print("organism dir")
    else:
        print(
            f"ERROR--target directory '{target_dir}' is not a recognized type."
        )
        sys.exit(1)
    print(attributes, end="")
    yaml = YAML()
    # target_yaml = yaml.load(open(template, "rt"))
    # for key in ("identifier", "genotype", "scientific_name", "scientific_name_abbrev"):
    #    my_yaml[key] == attributes["key"]
    # with target_path / f"README.{key}.yaml" as readme_handle:
    #   yaml.dump(my_yaml, readme_handle)
