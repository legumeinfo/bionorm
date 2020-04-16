# -*- coding: utf-8 -*-

# standard library imports
import os
import subprocess
import sys

# third-party imports
import click

# module imports
from .common import logger


def create_directories(dirpath):
    """make directory path"""
    try:
        os.makedirs(dirpath)
    except OSError as e:
        if e.errno != errno.EEXIST:  # ignore if error is exists else raise
            raise


def check_busco_dependencies():
    """attempts to run samtools, tabix and bgzip"""
    subprocess.check_call("which run_BUSCO.py", shell=True)  # check in env
    subprocess.check_call("which augustus", shell=True)  # check in env
    return True


def change_directories(dirpath):
    """cd to path, does not modify calling process CWD"""
    try:
        os.chdir(dirpath)
    except OSError as e:
        raise


def return_filehandle(open_me):
    """return file handle for gz compressed or text file"""
    magic_dict = {  # headers for compression
        b"\x1f\x8b\x08": "gz",
        #                 '\x42\x5a\x68': 'bz2',
        #                 '\x50\x4b\x03\x04': 'zip'
    }
    max_bytes = max(len(t) for t in magic_dict)
    with open(open_me, "rb") as f:
        s = f.read(max_bytes)
    for m in magic_dict:
        if s.startswith(m):  # check file header for match with m
            t = magic_dict[m]
            if t == "gz":
                return gzip.open(open_me, "rt")
    return open(open_me)


def preprocess_input(target):
    """Creates a temporary file for BUSCO to act on and sets temp and output"""
    name = os.path.basename(target)
    target_dir = os.path.dirname(target)
    busco_dir = f"{target_dir}/busco"
    create_directories(busco_dir)  # make runtime dir
    change_directories(busco_dir)  # go to runtime dir cause busco cannot path
    temp_file = f"./{name}_buscoready.fa"
    temp_file_handle = open(temp_file, "w")
    temp_target = return_filehandle(target)
    temp_file_handle.writelines(temp_target)
    temp_file_handle.close()
    return temp_file


def run_busco(busco_target, output, temp_dir, threads, mode, lineage):
    """takes busco_target and performs BUSCO using lineage and mode"""
    cmd = """run_BUSCO.py -f -m {} -c {} -i {} -l {} -t {} -o {}""".format(
        mode, threads, busco_target, lineage, temp_dir, output
    )
    subprocess.check_call(cmd, shell=True)
    return output


@click.command()
@click.option("--target", type=str, help="""TARGETS can be files or directories or both""")
@click.option("--lineage", type=str, help="""BUSCO lineage to compare target against""")
@click.option("--mode", type=str, help="""BUSCO mode (genome, protein, transcript)""")
@click.option("--threads", type=int, default=4, help="""Threads for BUSCO""")
def cli(target, lineage, mode, threads):
    """Determines what type of index to apply to input target"""
    check_busco_dependencies()
    if not (target and lineage):
        logger.error("--target, --lineage and arguments required")
        sys.exit(1)
    target = os.path.abspath(target)
    lineage = os.path.abspath(lineage)
    file_types = ["fna", "fasta", "fa", "faa", "ADD MORE"]
    canonical_types = {
        "genome_main": "genome",
        "mrna": "transcriptome",
        "protein": "proteins",
        "protein_primaryTranscript": "proteins",
    }
    fasta = ["fna", "fasta", "fa", "faa"]
    file_attributes = target.split(".")
    output = False
    if len(file_attributes) < 2:
        error_message = """Target {} does not have a type or attributes.  File must end in either gz, bgz, fasta, fna, fa.""".format(
            target
        )
        logger.error(error_message)
        sys.exit(1)
    if (
        not (file_attributes[-2].lower() in canonical_types or file_attributes[-3].lower() in canonical_types)
        and not mode
    ):
        logger.info(
            "file {} was not recognized as a canonical type and mode cannot be assigned please specify --mode for BUSCO to run anyway".format(
                target
            )
        )
        sys.exit(1)
    if file_attributes[-2].lower() in canonical_types and not mode:
        mode = canonical_types[file_attributes[-2].lower()]
    elif file_attributes[-3].lower() in canonical_types and not mode:
        mode = canonical_types[file_attributes[-3].lower()]
    if not mode:
        logger.info("Mode was not assigned and could not be autodetected, please specify BUSCO mode with --mode")
        sys.exit(1)
    logger.info("Setting up output and making temp input...")
    busco_me = preprocess_input(target)
    name = os.path.basename(target)
    output = f"{name}_busco"
    temp_dir = f"{name}_temp"
    logger.info(f"Runnig BUSCO on {target} with mode {mode} and lineage {lineage}...")
    output = run_busco(busco_me, output, temp_dir, threads, mode, lineage)
    logger.info(f"BUSCO done output: {output}")
