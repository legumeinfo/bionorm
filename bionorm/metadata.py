#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard library imports
import datetime
import hashlib
import sys
from pathlib import Path

# third-party imports
import toml

# first-party imports
import click
import pandas as pd
import pygit2
from addict import Dict
from loguru import logger

# module imports
from . import cli
from . import click_loguru
from .__version__ import __version__
from .common import COLLECTION_ATT_FILENAME
from .common import COLLECTION_DIR
from .common import COLLECTION_HOME
from .common import COLLECTION_TITLE
from .common import DATA_PATH
from .common import FILE_METADATA_SUFFIX
from .common import METADATA_DIR_SUFFIX
from .common import METADATA_HOME
from .common import REPOSITORY_URL
from .common import CollectionPath
from .common import args_to_pathlist


@cli.command()
@click_loguru.init_logger(logfile=False)
def show_collection():
    """Show collection info."""
    if COLLECTION_HOME is not None:
        logger.info(f'Collection "{COLLECTION_TITLE}" info:')
        logger.info(f"  directory: {COLLECTION_HOME}")
        if METADATA_HOME is not None:
            logger.info(f'  metadata repository: "{METADATA_HOME}"')
        else:
            logger.warn("   metadata repository is not set.")
    else:
        logger.error("No collection found.")
        sys.exit(1)


@cli.command()
@click_loguru.init_logger()
@click.argument("data_path")
@click.argument("title")
@click.argument("repo_url")
def init_collection(data_path, title, repo_url):
    """Initialize collection of metadata.

    Initialize a metadata collection in the current working directory.
    \b
    Example:
        bionorm init-collection legumeinfo_public "Legume Information System Public Database" \\
                https://github.com/legumeinfo/public_bionorm_metadata.git
    """
    data_path = Path(data_path)
    if not data_path.exists():
        logger.info(f"Creating directory {data_path}.")
        data_path.mkdir(parents=True, exist_ok=True)
    dir_name = data_path.name
    parent_path = Path.cwd()
    collection_path = parent_path / COLLECTION_DIR
    metadata_path = collection_path / (dir_name + METADATA_DIR_SUFFIX)
    toml_path = collection_path / (dir_name + ".toml")
    if data_path == COLLECTION_HOME:
        logger.warning(f'Using existing "{data_path}" as collection home.')
    else:
        logger.info(f"Creating collection home {data_path}.")
        data_path.mkdir(parents=True, exist_ok=True)
    if not metadata_path.exists():
        logger.info(f"Cloning repository at {repo_url} into {metadata_path}.")
        pygit2.clone_repository(repo_url, str(metadata_path))
    else:
        logger.warning(
            f"Metadata repository already exists at {METADATA_HOME}."
        )
    if not toml_path.exists():
        logger.debug(f'Initializing collection path file ".{toml_path}".')
        with toml_path.open("w") as toml_fh:
            collection_dict = Dict()
            if not data_path.is_absolute():
                data_path = Path("..") / data_path
            collection_dict["installation"] = {
                "metadata_path": metadata_path.name,
                "metadata_url": repo_url,
                "data_path": str(data_path),
                "title": title,
                "version": __version__,
            }
            toml.dump(collection_dict, toml_fh)


def calculate_file_metadata(filepath, filetype=None):
    """Calculates expensive file metadata."""
    relative_path = filepath.parent.resolve().relative_to(DATA_PATH)
    md5sum = hashlib.md5(filepath.open("rb").read()).hexdigest()
    file_metadata = {
        "download_url": REPOSITORY_URL
        + "/"
        + str(relative_path)
        + "/"
        + filepath.name,
        "mod_time": datetime.datetime.fromtimestamp(filepath.stat().st_mtime),
        "MD5": md5sum,
    }
    return file_metadata


@cli.command()
@click_loguru.init_logger()
@click.argument("nodelist", nargs=-1)
def write_metadata(datadirlist):
    """Write attributes of nodes to collection metadata.

    \b
    Example:
        bionorm write-metadata . # attributes of current directory
        bionorm write-metadata Medicago_truncatula/ # organism directory
        bionorm write-metadata  Medicago_truncatula/jemalong_A17.gnm5.FAKE/ # genome directory
        bionorm write-metadata Medicago_truncatula/jemalong_A17.gnm5.ann1.FAKE/ # annotation directory

    """
    if METADATA_HOME is None:
        logger.error("Collection has not been initialized.")
        sys.exit(1)
    n_nodes = 0
    n_invalid = 0
    att_dict_list = []
    pathlist = args_to_pathlist(datadirlist, directory=False, recurse=False)
    relative_path = pathlist[0].parent.resolve().relative_to(DATA_PATH)
    metadata_dirpath = METADATA_HOME / relative_path
    collection_path = metadata_dirpath / COLLECTION_ATT_FILENAME
    if not len(pathlist):
        logger.error("No files to consider.")
        sys.exit(1)
    if not metadata_dirpath.exists():
        metadata_dirpath.mkdir(parents=True)
    for node in pathlist:
        n_nodes += 1
        node = CollectionPath(node)
        if node.collection_attributes.invalid_key is not None:
            n_invalid += 1
            logger.error(f"File {node} has invalid attributes.")
        att_dict_list.append(dict(node.collection_attributes))
        file_metadata = calculate_file_metadata(node)
        file_metadata_path = metadata_dirpath / (
            node.name + FILE_METADATA_SUFFIX
        )
        with file_metadata_path.open("w") as file_metadata_fh:
            logger.debug(f'Writing file metadata to "{file_metadata_path}".')
            toml.dump(file_metadata, file_metadata_fh)
    att_frame = pd.DataFrame(att_dict_list)
    att_frame.to_csv(collection_path, sep="\t")
    logger.info(
        f"{len(att_frame)} attribute records written to {collection_path}"
    )
    if n_invalid:
        logger.error(f"{n_invalid} invalid nodes were found.", file=sys.stderr)
        sys.exit(1)
