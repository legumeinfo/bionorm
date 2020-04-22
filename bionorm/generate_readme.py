#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard library imports
import json as jsonlib
import sys
from pathlib import Path

# third-party imports
import click
from ruamel.yaml import YAML

# module imports
from . import cli
from .common import DataStorePath


def read_yaml(template):
    """Reads yaml file and checks for valid yaml"""
    yaml = YAML()
    target_yaml = yaml.load(open(template, "rt"))
    return yaml, target_yaml


@cli.command()
@click.option("--json", help="Write JSON to stdout.", is_flag=True, default=False)
@click.option("--pathonly", help="Write only path to output.", is_flag=True, default=False)
@click.option("--invalid", help="Write only invalid node info.", is_flag=True, default=False)
@click.option("--unrecognized", help="Write only unrecognized node info.", is_flag=True, default=False)
@click.option("--recurse", help="Recursively visit all files.", is_flag=True, default=False)
@click.argument("nodelist", nargs=-1)
def node_attributes(nodelist, json, invalid, pathonly, unrecognized, recurse):
    """Print attributes of nodes in data store.

    \b
    Example:
        bionorm node-attributes . # attributes of current directory
        bionorm node-attributes Medicago_truncatula/ # organism directory
        bionorm node-attributes  Medicago_truncatula/jemalong_A17.gnm5.FAKE/ # genome directory
        bionorm node-attributes Medicago_truncatula/jemalong_A17.gnm5.ann1.FAKE/ # annotation directory

    """
    n_invalid = 0
    if nodelist == ():  # empty list gets CWD
        nodelist = ["."]
    if recurse:
        filelist = []
        for node in nodelist:
            filelist += [f for f in Path(node).rglob("*") if f.is_file()]
        nodelist = filelist
    for node in nodelist:
        node = DataStorePath(node)
        if node.data_store_attributes.invalid_key is not None:
            n_invalid += 1
        else:
            if invalid:
                continue
        if unrecognized and not node.data_store_attributes.file_type == "unrecognized":
            continue
        if json:
            print(jsonlib.dumps(node.data_store_attributes))
        elif pathonly:
            print(node)
        else:
            logger.info(node.data_store_attributes.describe(node), end="")
            logger.info(node.data_store_attributes, end="")
    if n_invalid:
        print(f"ERROR--{n_invalid} invalid nodes were found.", file=sys.stderr)
        sys.exit(1)


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
        print(f"ERROR--target directory '{target_dir}' is not a recognized type.")
        sys.exit(1)
    print(attributes, end="")
    # yaml, my_yaml = read_yaml(template)
    # for key in ("identifier", "genotype", "scientific_name", "scientific_name_abbrev"):
    #    my_yaml[key] == attributes["key"]
    # with target_path / f"README.{key}.yaml" as readme_handle:
    #   yaml.dump(my_yaml, readme_handle)
