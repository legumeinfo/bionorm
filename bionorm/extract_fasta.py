# -*- coding: utf-8 -*-
"""Extract rRNA, CDS, and protein sequences defined in GFF from genome sequence."""
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


def primary_transcript_check(peptides):
    """Select the longest isoforms as the primary transcripts."""
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


def run_gffread(gff, fastapath):
    """Read gff3 file and write mRNA, CDS and peptides."""
    gff_dir = os.path.dirname(gff)
    gff_attributes = os.path.basename(gff).split(".")
    mrna = "{}/{}.mrna.fna".format(gff_dir, ".".join(gff_attributes[:5]))
    cds = "{}/{}.cds.fna".format(gff_dir, ".".join(gff_attributes[:5]))
    pep = "{}/{}.protein.faa".format(gff_dir, ".".join(gff_attributes[:5]))
    cmd = "gffread {} -g {} -w {} -x {} -y {} -W".format(gff, fastapath, mrna, cds, pep)
    # print("cmd=", cmd)
    subprocess.check_call(cmd, shell=True)
    primary_transcript_check(pep)


@cli.command()
@click.argument("gffpath", type=click.Path(exists=True, readable=True, dir_okay=False))
@click.argument("fastapath", type=click.Path(exists=True, readable=True, dir_okay=False))
def extract_fasta(gffpath, fastapath):
    """Extract CDS, mrna, protein, and primary transcript files from gff and genome.

    \b
    Example:
        bionorm extract-fasta \\
          Medicago_truncatula/jemalong_A17.gnm5.ann1.FAKE/medtr.jemalong_A17.gnm5.ann1.FAKE.gene_models_main.gff3 \\
          Medicago_truncatula/jemalong_A17.gnm5.FAKE/medtr.jemalong_A17.gnm5.FAKE.genome_main.fna

    """
    # gffpath = os.path.abspath(gffpath)  # get full path
    gffpath_attributes = os.path.basename(gffpath).split(".")
    if os.path.basename(fastapath).split(".")[-1] == "gz":
        logger.error("GFFREAD cannot process compressed fasta as fastapath")
        sys.exit(1)
    if len(gffpath_attributes) < 7:
        logger.error("Target file {} is not delimited correctly".format(gffpath))
        sys.exit(1)
    run_gffread(gffpath, fastapath)  # write readme template
