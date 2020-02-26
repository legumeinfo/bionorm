#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard library imports
import os
import sys


def cli():
    """Normalizer -- Normalize Files to Data Store Standards

           The normalizer will detect the input file type.
           Currently recognizes case independent fasta, fna, fa, gff3, gff
           START WITH THE PREFIX COMMAND UNLESS YOU JUST WANT TO INDEX!
               This stages the canonical directory structure

       USAGE: normalizer <mode> [options]

       Current Modes:

           prefix        (will sort GFF3 Files)
           index         (Canonical indexing for datastore)
           readme        (Generates README files for directories)
           extract_fasta (extracts mRNA, CDS and Peptides from GFF3)
           busco         (Runs BUSCO on the target)
           checksums     (Generate md5s for all files in target dir)

       Please run `normalizer <TOOL> --help` for individual usage
    """
    if not len(sys.argv) > 1:
        print(cli.__doc__)
        sys.exit(1)
    mode = sys.argv[1].lower()  # get mode
    sys.argv = [mode] + sys.argv[2:]  # makes usage for application correct
    if mode == "--help" or mode == "-h":
        print(cli.__doc__)
        sys.exit(1)
    if mode == "index":  # determine file type and index
        from . import index

        index.cli()
    if mode == "prefix":  # determine file type and prefix, sorts gff3
        from . import prefix

        prefix.cli()
    if mode == "readme":  # generate readmes from template and target
        from . import generate_readme

        generate_readme.cli()
    if mode == "extract_fasta":  # Extract FASTA features from GFF3
        from . import extract_fasta

        extract_fasta.cli()
    if mode == "busco":  # Run BUSCO with mode and lineage on target
        from . import busco_normalizer

        busco_normalizer.cli()


if __name__ == "__main__":
    cli()
