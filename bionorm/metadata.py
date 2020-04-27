#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard library imports
import datetime
import hashlib
import sys
from pathlib import Path

# third-party imports
import click
import pandas as pd
import pygit2
import toml
from addict import Dict

# module imports
from . import cli
from .common import COLLECTION_ATT_FILENAME
from .common import COLLECTION_DIR
from .common import COLLECTION_HOME
from .common import DATA_PATH
from .common import DOWNLOAD_URL
from .common import FILE_METADATA_SUFFIX
from .common import METADATA_DIR_SUFFIX
from .common import METADATA_HOME
from .common import CollectionPath
from .common import args_to_pathlist


@cli.command()
def show_collection():
    """Show collection info."""
    if COLLECTION_HOME is not None:
        print(f'COLLECTION_HOME is "{COLLECTION_HOME}"')
        if METADATA_HOME is not None:
            print(f'METADATA_HOME is "{METADATA_HOME}"')
        else:
            print("METADATA HOME is not set.")
    else:
        print("No collection found.")


@cli.command()
@click.argument("data_path")
@click.argument("repo_url")
def init_collection(data_path, repo_url):
    """Initialize collection of metadata.

    Initialize a metadata collection in the current working directory.
    \b
    Example:
        bionorm init-collection legumeinfo_public https://github.com/legumeinfo/public_bionorm_metadata.git
    """
    data_path = Path(data_path)
    if not data_path.exists():
        print(f"Creating directory {data_path}.")
        data_path.mkdir(parents=True, exist_ok=True)
    dir_name = data_path.name
    parent_path = Path.cwd()
    collection_path = parent_path / COLLECTION_DIR
    metadata_path = collection_path / (dir_name + METADATA_DIR_SUFFIX)
    toml_path = collection_path / (dir_name + ".toml")
    if data_path == COLLECTION_HOME:
        print(f'Using existing "{data_path}" as collection home.')
    else:
        print(f"Creating collection home {data_path}.")
        data_path.mkdir(parents=True, exist_ok=True)
    if not metadata_path.exists():
        print(f"Cloning repository at {repo_url} into {metadata_path}.")
        pygit2.clone_repository(repo_url, str(metadata_path))
    else:
        print(f"Metadata repository already exists at {METADATA_HOME}.")
    if not toml_path.exists():
        print(f'Initializing collection path file ".{toml_path}".')
        with toml_path.open("w") as toml_fh:
            collection_dict = Dict()
            if not data_path.is_absolute():
                data_path = Path("..") / data_path
            collection_dict["installation"] = {
                "metadata_path": metadata_path.name,
                "metadata_url": repo_url,
                "data_path": str(data_path),
                "verified": False,
            }
            toml.dump(collection_dict, toml_fh)


def calculate_file_metadata(filepath, filetype=None):
    """Calculates expensive file metadata."""
    relative_path = filepath.parent.resolve().relative_to(DATA_PATH)
    md5sum = hashlib.md5(filepath.open("rb").read()).hexdigest()
    file_metadata = {
        "download_url": DOWNLOAD_URL + "/" + str(relative_path) + "/" + filepath.name,
        "mod_time": datetime.datetime.fromtimestamp(filepath.stat().st_mtime),
        "MD5": md5sum,
    }
    return file_metadata


@cli.command()
@click.argument("nodelist", nargs=-1)
def write_metadata(nodelist):
    """Write attributes of nodes to collection metadata.

    \b
    Example:
        bionorm write-metadata . # attributes of current directory
        bionorm write-metadata Medicago_truncatula/ # organism directory
        bionorm write-metadata  Medicago_truncatula/jemalong_A17.gnm5.FAKE/ # genome directory
        bionorm write-metadata Medicago_truncatula/jemalong_A17.gnm5.ann1.FAKE/ # annotation directory

    """
    if METADATA_HOME is None:
        print("""ERROR--collection has not been initialized.""")
        sys.exit(1)
    n_nodes = 0
    n_invalid = 0
    att_dict_list = []
    pathlist = args_to_pathlist(nodelist, directory=False, recurse=False)
    relative_path = pathlist[0].parent.resolve().relative_to(DATA_PATH)
    metadata_dirpath = METADATA_HOME / relative_path
    collection_path = metadata_dirpath / COLLECTION_ATT_FILENAME
    if not len(pathlist):
        print("ERROR--no files to consider.")
        sys.exit(1)
    if not metadata_dirpath.exists():
        metadata_dirpath.mkdir(parents=True)
    for node in pathlist:
        n_nodes += 1
        node = CollectionPath(node)
        if node.collection_attributes.invalid_key is not None:
            n_invalid += 1
            print(f"File {node} has invalid attributes.")
        att_dict_list.append(dict(node.collection_attributes))
        file_metadata = calculate_file_metadata(node)
        file_metadata_path = metadata_dirpath / (node.name + FILE_METADATA_SUFFIX)
        with file_metadata_path.open("w") as file_metadata_fh:
            print(f'Writing file metadata to "{file_metadata_path}".')
            toml.dump(file_metadata, file_metadata_fh)
    att_frame = pd.DataFrame(att_dict_list)
    att_frame.to_csv(collection_path, sep="\t")
    print(f"{len(att_frame)} attribute records written to {collection_path}")
    if n_invalid:
        print(f"ERROR--{n_invalid} invalid nodes were found.", file=sys.stderr)
