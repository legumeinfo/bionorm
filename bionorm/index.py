#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard library imports
import sys
from pathlib import Path

# first-party imports
import click
from loguru import logger

# module imports
from . import cli
from .common import COMPRESSED_TYPES
from .common import FASTA_TYPES
from .common import GFF_TYPES


@cli.command()
@click.option(
    "--compress",
    is_flag=True,
    default=True,
    help="Compress with bgzip before indexing.",
)
@click.argument("fasta", type=click.Path(exists=True, readable=True))
def index_fasta(fasta, compress=True):
    """Index and optionally compress a fasta file.


        \b
    Examples:
        bionorm index_fasta Medicago_truncatula/jemalong_A17.gnm5.ann1.FAKE/medtr.jemalong_A17.gnm5.FAKE.genome_main.fna
    """
    from sh import bgzip  # isort:skip
    from sh import samtools  # isort:skip

    target = Path(fasta)
    if len(target.suffixes) < 1:
        error_message = f"Target {target} does not have a file extension."
        logger.error(error_message)
        sys.exit(1)
    if target.suffix.lstrip(".") in COMPRESSED_TYPES:
        logger.error(f"Uncompress {target} befor indexing.")
        sys.exit(1)
    if target.suffix.lstrip(".") not in FASTA_TYPES:
        logger.error(
            f"File {target} does not have a recognized FASTA extension."
        )
        sys.exit(1)
    if compress:
        output = bgzip(["-f", "--index", str(target)])
        print(output)
        target = Path(target.parent) / f"{target.name}.gz"
    output = samtools(["faidx", str(target)])
    print(output)
    return target


@cli.command()
@click.option(
    "--compress",
    is_flag=True,
    default=True,
    help="Compress with bgzip before indexing.",
)
@click.argument("gff", type=click.Path(exists=True, readable=True))
def index_gff(gff, compress=True):
    """Index and optionally compress a GFF file.

        \b
    Examples:
        bionorm index_gff Medicago_truncatula/jemalong_A17.gnm5.ann1.FAKE/medtr.jemalong_A17.gnm5.ann1.FAKE.gene_models_main.gff3
    """
    from sh import bgzip  # isort:skip
    from sh import tabix  # isort:skip

    target = Path(gff)
    if len(target.suffixes) < 1:
        error_message = f"Target {target} does not have a file extension."
        logger.error(error_message)
        sys.exit(1)
    if target.suffix.lstrip(".") in COMPRESSED_TYPES:
        logger.error(f"Uncompress {target} befor indexing.")
        sys.exit(1)
    if target.suffix.lstrip(".") not in GFF_TYPES:
        logger.error(
            f"File {target} does not have a recognized GFF extension."
        )
        sys.exit(1)
    if compress:
        output = bgzip(["-f", str(target)])
        print(output)
        target = Path(target.parent) / f"{target.name}.gz"
    output = tabix(["-p", "gff", str(target)])
    print(output)
    output = tabix(["--csi", "-p", "gff", str(target)])
    print(output)
    return target
