# -*- coding: utf-8 -*-

import contextlib
import os
from pathlib import Path

from tests.download_files import DownloadDataFiles

# global constants
FASTA_FILE = "example_jemalong.fna"
GFF_FILE = "example_jemalong.gff3"

dlmanager = DownloadDataFiles(
    download_url="http://generisbio.com/ncgr/",
    files=[FASTA_FILE, GFF_FILE],
    # subdir="prefixing_test",
    md5_check=True,
    gzipped=True,
    progressbar=False,
)


def line_count(filepath):
    """Count the number of lines in a file"""
    lines = 0
    buf_size = 1024 * 1024
    with filepath.open("rb") as fh:
        read_f = fh.raw.read
        buf = read_f(buf_size)
        while buf:
            lines += buf.count(b"\n")
            buf = read_f(buf_size)
    return lines


def fasta_count(filepath):
    """Count the number of lines in a file"""
    lines = 0
    buf_size = 1024 * 1024
    with filepath.open("rb") as fh:
        read_f = fh.raw.read
        buf = read_f(buf_size)
        while buf:
            lines += buf.count(b">")
            buf = read_f(buf_size)
    return lines


@contextlib.contextmanager
def in_tmp_dir(tmp_path, datadir_copy, infilelist=[], outpathlist=[]):
    """Copy data and change context to tmp_path directory."""
    cwd = Path.cwd()
    for filename in infilelist:
        datadir_copy[filename]

    os.chdir(tmp_path)
    try:
        yield
    finally:
        for filepath in outpathlist:
            shutil.copy2(filepath, Path(__file__).parent / "data" / filepath.name)
        os.chdir(cwd)
