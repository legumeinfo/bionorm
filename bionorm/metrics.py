#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard library imports
from pathlib import Path


def count_gff_features(gff):
    counts = {}
    with Path(gff).open("r") as fopen:
        for line in fopen:
            if not line or line.isspace() or line.startswith("#"):  # skip comments
                continue
            line = line.rstrip()
            f = line.split("\t")  # get fields
            if f[2] not in counts:  # feature type
                counts[f[2]] = 1
                continue
            counts[f[2]] += 1
    return counts
