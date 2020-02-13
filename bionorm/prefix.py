# -*- coding: utf-8 -*-

# standard library imports
import os
import re
import sys

# third-party imports
import click

# module imports
from . import cli
from .common import logger
from .helper import check_file
from .helper import create_directories
from .helper import return_filehandle


@cli.command()
@click.option("--target", help="""TARGETS can be files or directories or both""")
@click.option("--gnm", help="""Genome Version for Normalizer.""")
@click.option("--genus", metavar="<STRING>", help="""Genus of organism input file""")
@click.option("--species", metavar="<STRING>", help="""Species of organism input file""")
@click.option(
    "--infra_id", metavar="<STRING>", help="""Line or infraspecific identifier.  ex. A17_HM341""",
)
@click.option(
    "--key", metavar="<STRING, len=4>", help="""4-character unique identifier""",
)
def prefix_fasta(target, gnm, genus, species, infra_id, key):
    """Prefix FASTA files for data store standard.

    \b
    Example:
        bionorm prefix-fasta --gnm 5 --genus medicago \\
                --species truncatula --infra_id jemalong_A17 --key FAKE \\
                --target example_jemalong.fna
    """
    if not (target and gnm and genus and species and infra_id and key):
        logger.error("--target, --species, --genus, --gnm, --infra_id, and --key are required")
        sys.exit(1)
    target = os.path.abspath(target)
    gnm = "gnm{}".format(gnm)  # format user provided argument for gnm
    re_header = re.compile(r"^>(\S+)\s*(.*)")  # match header
    prefix = "{}{}".format(genus[:3].lower(), species[:2].lower())  # gensp
    new_file_raw = "{}.{}.{}.{}.genome_main.fna".format(prefix, infra_id, gnm, key)
    species_dir = "./{}_{}".format(genus.capitalize(), species)
    new_file_dir = "{}/{}.{}.{}".format(species_dir, infra_id, gnm, key)  # setup for ds
    create_directories(new_file_dir)  # make genus species dir for output
    fasta_file_path = os.path.abspath("{}/{}".format(new_file_dir, new_file_raw))
    new_fasta = open(fasta_file_path, "w")
    name_prefix = "{}.{}.{}".format(prefix, infra_id, gnm)
    fh = return_filehandle(target)
    n_headers = 0
    with fh as gopen:
        for line in gopen:
            line = line.rstrip()
            if re_header.match(line):  # header line
                parsed_header = re_header.search(line).groups()
                logger.debug(line)
                logger.debug(parsed_header)
                if isinstance(parsed_header, str):  # check tuple
                    hid = parsed_header
                    new_header = ">{}.{}".format(name_prefix, hid)
                    n_headers += 1
                    logger.debug(hid)
                else:
                    if len(parsed_header) == 2:  # header and description
                        hid = parsed_header[0]  # header
                        desc = parsed_header[1]  # description
                        new_header = ">{}.{} {}".format(name_prefix, hid, desc)
                        n_headers += 1
                        logger.debug(hid)
                        logger.debug(desc)
                        logger.debug(new_header)
                    else:
                        logger.error("header {} looks odd...".format(line))
                        sys.exit(1)
                new_fasta.write(new_header + "\n")  # write new header
            else:  # sequence lines
                new_fasta.write(line + "\n")
    new_fasta.close()
    if not n_headers:
        logger.error("file %s contains no headers, are you sure it is a FASTA?", target)
        os.remove(fasta_file_path)
        sys.exit(1)
    if not check_file(fasta_file_path):
        logger.error("Output file {} not found for normalize fasta".format(fasta_file_path))
        sys.exit(1)  # new file not found return False
    logger.info("Prefixing FASTA done, final file: {}".format(fasta_file_path))
    return fasta_file_path


def type_rank(hierarchy, feature_type):
    if feature_type in hierarchy:
        return hierarchy[feature_type]["rank"]
    else:
        return 1000  # no feature id, no children, no order


def update_hierarchy(hierarchy, feature_type, parent_types):
    """Breaks input gff3 line into attributes.

       Determines feature type hierarchy using type and attributes fields
    """
    if not parent_types:  # this feature must be a root
        if feature_type not in hierarchy:  # add to hierarchy
            hierarchy[feature_type] = {"children": [], "parents": [], "rank": 0}
        hierarchy[feature_type]["rank"] = 1  # rank is 1 because no parents
    else:  # feature has parents
        if feature_type not in hierarchy:
            hierarchy[feature_type] = {"children": [], "parents": [], "rank": 0}
        hierarchy[feature_type]["parents"] = parent_types
        for p in parent_types:  # set children and aprents for all p
            if hierarchy.get(p):
                if feature_type not in hierarchy[p]["children"]:
                    hierarchy[p]["children"].append(feature_type)
            else:
                hierarchy[p] = {"children": [feature_type], "parents": [], "rank": 0}


@cli.command()
@click.option("--target", help="""TARGETS can be files or directories or both""")
@click.option("--gnm", help="""Genome Version for Normalizer.""")
@click.option("--ann", help="""Annotation Version for Normalizer.""")
@click.option("--genus", metavar="<STRING>", help="""Genus of organism input file""")
@click.option("--species", metavar="<STRING>", help="""Species of organism input file""")
@click.option(
    "--infra_id", metavar="<STRING>", help="""Line or infraspecific identifier.  ex. A17_HM341""",
)
@click.option(
    "--key", metavar="<STRING, len=4>", help="""4 Character unique idenfier (get from spreadsheet)""",
)
@click.option(
    "--sort_only", is_flag=True, help="""Performing sorting only.""",
)
def prefix_gff(target, gnm, ann, genus, species, infra_id, key, sort_only):
    """Prefix and sort GFF3 file for data store standard.

    \b
    Example:
        bionorm prefix-gff --gnm 5 --ann 1 --species truncatula --genus medicago \\
                --infra_id jemalong_A17 --key FAKE --target example_jemalong.fna
    """
    if not (target and gnm and genus and species and infra_id and key and ann):
        logger.error("--target, --species, --genus, --gnm, -ann, --infra_id, and --key are required")
        sys.exit(1)
    target = os.path.abspath(target)
    gnm = "gnm{}".format(gnm)  # format user provided argument for gnm
    ann = "ann{}".format(ann)  # format user provided argument for ann
    if sort_only:
        logger.info("sorting ONLY...")
    else:
        logger.info("prefixing and sorting...")
    prefix = "{}{}".format(genus[:3].lower(), species[:2].lower())  # gensp
    target = os.path.abspath(target)
    new_file_raw = "{}.{}.{}.{}.{}.gene_models_main.gff3".format(prefix, infra_id, gnm, ann, key)
    species_dir = "./{}_{}".format(genus.capitalize(), species)
    new_file_dir = "{}/{}.{}.{}.{}".format(species_dir, infra_id, gnm, ann, key)  # setup for ds
    create_directories(new_file_dir)  # make genus species dir for output
    gff_file_path = os.path.abspath("{}/{}".format(new_file_dir, new_file_raw))
    new_gff = open(gff_file_path, "w")
    get_id = re.compile("ID=([^;]+)")  # gff3 get id string
    get_name = re.compile("Name=([^;]+)")  # get name string
    get_parents = re.compile("Parent=([^;]+)")  # get parents
    gff3_lines = []  # will be sorted after loading and hierarchy
    sub_tree = {}  # feature hierarchy sub tree
    type_hierarchy = {}  # type hierarchy for features, will be ranked
    prefix_name = False
    fh = return_filehandle(target)  # get filehandle for target
    n_lines = 0
    with fh as gopen:
        for line in gopen:
            line = line.rstrip()
            if not line:
                continue
            n_lines += 1
            if n_lines == 1:
                if not line.split() == ["##gff-version", "3"]:
                    logger.error("File does not start with GFF3 magic, are you sure is is a GFF3?")
                    new_gff.close()
                    os.remove(gff_file_path)
                    sys.exit(1)
            if line.startswith("#"):  # header
                if sort_only:  # do not prefix
                    new_gff.write("{}\n".format(line))
                    continue
                if line.startswith("##sequence-region"):  # replace header
                    fields = re.split(r"\s+", line)
                    ref_name = "{}.{}.{}.{}".format(prefix, infra_id, gnm, fields[1])
                    line = re.sub(fields[1], ref_name, line)
                new_gff.write("{}\n".format(line))
                continue
            fields = line.split("\t")
            gff3_lines.append(fields)
            feature_id = get_id.search(fields[-1])
            parent_ids = get_parents.search(fields[-1])
            if parent_ids:
                parent_ids = parent_ids.group(1).split(",")
            else:
                parent_ids = []
            if not feature_id:
                continue
            feature_id = feature_id.group(1)
            sub_tree[feature_id] = {
                "type": fields[2],  # parent child
                "parent_ids": parent_ids,
            }
    for f in sub_tree:
        feature_type = sub_tree[f]["type"]
        parent_types = []
        for p in sub_tree[f]["parent_ids"]:
            parent_type = sub_tree[p]["type"]
            if not parent_type:  # must have type
                logger.error("could not find type for parent {}".format(parent_type))
                sys.exit(1)  # error no type
            parent_types.append(parent_type)
        update_hierarchy(type_hierarchy, feature_type, parent_types)
    ranking = 1  # switch to stop ranking in while below
    while ranking:  # this is over-engineered for tabix indexing, but tis cool
        check = 0  # switch to indicate no features unranked
        for t in sorted(type_hierarchy, key=lambda k: type_hierarchy[k]["rank"], reverse=True):
            if type_hierarchy[t]["rank"]:  # rank !=0
                for c in type_hierarchy[t]["children"]:
                    if not type_hierarchy[c]["rank"]:
                        type_hierarchy[c]["rank"] = type_hierarchy[t]["rank"] + 1
            else:  # rank == 0
                check = 1
        if not check:  # escape loop when all features are ranked
            ranking = 0
    feature_prefix = "{}.{}.{}.{}".format(prefix, infra_id, gnm, ann)
    for l in sorted(
        gff3_lines, key=lambda x: (x[0], int(x[3]), type_rank(type_hierarchy, x[2]))
    ):  # rank by chromosome, start, type_rank and stop
        if sort_only:  # do not prefix or change IDs
            l = "\t".join(l)
            new_gff.write("{}\n".format(l))
            continue
        l[0] = "{}.{}.{}.{}".format(prefix, infra_id, gnm, l[0])  # rename
        l = "\t".join(l)
        feature_id = get_id.search(l)
        feature_name = get_name.search(l)
        feature_parents = get_parents.search(l)
        if feature_id:  # if id set new id
            new_id = "{}.{}".format(feature_prefix, feature_id.group(1))
            l = get_id.sub("ID={}".format(new_id), l)
        if feature_name and prefix_name:  # if name and flag set new name
            new_name = "{}.{}".format(feature_prefix, feature_name.group(1))
            l = get_name.sub("Name={}".format(new_name), l)
        if feature_parents:  # parents set new parent ids
            parent_ids = feature_parents.group(1).split(",")
            new_ids = []
            for p in parent_ids:  # for all parents
                new_id = "{}.{}".format(feature_prefix, p)
                new_ids.append(new_id)
            new_ids = ",".join(new_ids)  # set delimiter for multiple parents
            l = get_parents.sub("Parent={}".format(new_ids), l)
        new_gff.write("{}\n".format(l))
    new_gff.close()
    if not check_file(gff_file_path):  # check for output error if not found
        logger.error("Output file {} not found for normalize gff".format(gff_file_path))
        sys.exit(1)  # new file not found return False
    logger.info("{} lines in output file {}".format(n_lines, gff_file_path))
    return gff_file_path  # return path to new gff file
