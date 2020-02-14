# -*- coding: utf-8 -*-

# standard library imports
import os
import subprocess
import sys

# third-party imports
import click
from sequencetools.helpers import sequence_helpers

# module imports
from . import cli
from .common import logger
from .helper import check_subprocess_dependencies


def primary_transcript_check(peptides, logger):
    """If the file is not of primary transcripts, selects the longest isoforms.
    """
    seq_handle = open(peptides, "rt")
    longest = {}
    count = 0
    primary = "{}.protein_primaryTranscript.faa".format(".".join(peptides.split(".")[:-2]))
    for record in sequence_helpers.get_seqio_fasta_record(seq_handle):
        count += 1
        my_record = ">{}\n{}".format(record.id, record.seq)
        my_obj = {"record": my_record, "length": len(record.seq)}
        gene_id = ".".join(record.id.split(".")[:-1])
        if gene_id not in longest:
            longest[gene_id] = my_obj
        else:
            if len(record.seq) > longest[gene_id]["length"]:
                longest[gene_id] = my_obj
    if len(longest) == count:
        logger.info("Protein file is already primary transcripts")
        return  # protein file is already primary
    primary_handle = open(primary, "w")
    for r in longest:
        primary_handle.write(longest[r]["record"] + "\n")
    primary_handle.close()
    return primary


def run_gffread(gff, reference):
    """Reads gff3 file and writes mRNA, CDS and Peptides"""
    gff_dir = os.path.dirname(gff)
    gff_attributes = os.path.basename(gff).split(".")
    mrna = "{}/{}.mrna.fna".format(gff_dir, ".".join(gff_attributes[:5]))
    cds = "{}/{}.cds.fna".format(gff_dir, ".".join(gff_attributes[:5]))
    pep = "{}/{}.protein.faa".format(gff_dir, ".".join(gff_attributes[:5]))
    cmd = "gffread {} -g {} -w {} -x {} -y {} -W".format(gff, reference, mrna, cds, pep)
    subprocess.check_call(cmd, shell=True)
    primary_transcript_check(pep)


@cli.command()
@click.option(
    "--target", type=str, help="""GFF file from prefix_gff.""",
)
@click.option(
    "--reference", type=str, help="""FASTA file from prefix_fasta.""",
)
def extract_fasta(target, reference):
    """Determines what type of index to apply to input target

    \b
    Example:
        bionorm extract_fasta --target example_jemalong.gff3 --reference
    """
    check_subprocess_dependencies()
    if not (target and reference):
        logger.error("--target and --reference arguments are required")
        sys.exit(1)
    target = os.path.abspath(target)  # get full path
    target_attributes = os.path.basename(target).split(".")
    if os.path.basename(reference).split(".")[-1] == "gz":
        logger.error("GFFREAD cannot process compressed fasta as reference")
        sys.exit(1)
    if len(target_attributes) < 7:
        logger.error("Target file {} is not delimited correctly".format(target))
        sys.exit(1)
    run_gffread(target, reference)  # write readme template
