# -*- coding: utf-8 -*-
# standard library imports
import json
import os
import re
import sys
import subprocess
from glob import glob
from pathlib import Path

# first-party imports
import click
from loguru import logger
from sequencetools.tools.basic_fasta_stats import basic_fasta_stats
from sequencetools.helpers.file_helpers import return_filehandle

# module imports
from . import cli
from . import click_loguru
from . import specification_checks

# global defs
DOMAIN = "https://legumeinfo.org/data/public"
FASTA_TYPES = ("fna", "faa", "fasta", "frn")
GFF_TYPES = ("gff", "gff3")


def count_gff_features(gff):
    counts = {}
    with return_filehandle(Path(gff)) as fopen:
        for line in fopen:
            if (
                not line or line.isspace() or line.startswith("#")
            ):  # skip comments
                continue
            line = line.rstrip()
            f = line.split("\t")  # get fields
            if f[2] not in counts:  # feature type
                counts[f[2]] = 1
                continue
            counts[f[2]] += 1
    return counts


class Detector:

    """Detect datastore file inconsistencies."""

    def __init__(
        self,
        target,
        busco,
        nodes,
        genome_main,
        gene_models_main,
        genometools,
        fasta_headers,
        disable_all
    ):
        """Check for check for gt"""
        self.checks = {}  # object that determines which checks are skipped
        self.checks["genome_main"] = genome_main
        self.checks["gene_models_main"] = gene_models_main
        self.checks["perform_gt"] = genometools
        self.checks["fasta_headers"] = fasta_headers
        self.nodes = nodes
        self.busco = busco
        self.disable_all = disable_all
        self.options = {}
        self.canonical_types = [
            "genome_main",
            "protein_primaryTranscript",
            "protein",
            "gene_models_main",
            "gwas",
            "mrk",
            "phen"
        ]
        self.canonical_parents = {
            "genome_main": None,
            "gene_models_main": "genome_main",
            "mrk": "genome_main",
            "protein_primaryTranscript": "gene_models_main",
            "protein": "gene_models_main",
            "gwas": "mrk",
            "phen": "gwas",
            "qtl": "genome_main"
        }
        self.rank = {
            "genome_main": 0,
            "gene_models_main": 1,
            "mrk": 1,
            "qtl": 1,
            "protein": 2,
            "protein_primaryTranscript": 2,
            "gwas": 2,
            "phen": 3
        }
        self.write_me = {}
        self.passed = {}  # dictionary of passing names
        self.target_objects = {}  # store all target pairings self.get_targets
        self.fasta_ids = {}
        self.reporting = {}
        self.node_data = {}  # nodes for DSCensor
        self.target = Path(target)
        self.target_readme = ""
        self.target_name = os.path.basename(self.target)
        self.target_type = self.get_target_type()
        if (
            self.target_type is None
        ):  # target type returned False not recognized
            logger.error(f"Target type not recognized for {self.target}")
            sys.exit(1)
        logger.info(f"Target type looks like {self.target_type}")
        self.get_targets()
        logger.info("Performing Checks for the Following:\n")
        for t in self.target_objects:  # for each object set validate
            logger.info(f"Parent {t}:")
            logger.debug(f"{self.target_objects[t]}")
            count = 0
            set_primary = ""
            primary = False
            for c in self.target_objects[t]["children"]:
                logger.info(f"Child {c}")
                if (
                    self.target_objects[t]["children"][c]["type"]
                    == "protein_primaryTranscript"
                ):
                    primary = True
                if self.target_objects[t]["children"][c]["type"] == "protein":
                    count += 1
                    set_primary = c
            if count == 1 and not primary:
                self.target_objects[t]["children"][set_primary][
                    "type"
                ] = "protein_primaryTranscript"
                self.target_objects[t]["children"][set_primary]["node_data"][
                    "canonical_type"
                ] = "protein_primaryTranscript"
            if count > 1 and not primary:
                logger.error(
                    f"Multiple protein files found for {t}, one must be"
                    " renamed to primary."
                )
                sys.exit(1)
        logger.info("Initialized Detector\n")

    def get_target_type(self):
        """Determine whether target is file, organism directory, or data directory."""
        if self.target.is_file():
            target_type = "file"
        elif (
            len(self.target_name.split("_")) == 2
            and len(self.target_name.split(".")) < 3
        ):
            target_type = "organism_dir"  # will always be Genus_species
        elif len(self.target_name.split(".")) >= 3:  # standard naming minimum
            target_type = "data_dir"
        else:
            target_type = None
            logger.warning(f"Unrecognized directory type {self.target}")
        return target_type

    def get_targets(self):
        """Gets and discovers target files relation to other files.

        If the target is a directory, the program will discover
        all related files that can be checked.
        """
        if self.target_type == "file":  # starting with a file
            self.add_target_object()
            return
        elif (
            self.target_type == "data_dir"
            or self.target_type == "organism_dir"
        ):
            self.get_all_files()  # works for both data and organism
            return

    def get_all_files(self):
        """Walk filetree and return all files."""
        for root, directories, filenames in os.walk(self.target):
            for filename in filenames:  # we only care about the files
                my_target = f"{root}/{filename}"
                logger.debug(f"Checking file {my_target}")
                self.target = my_target
                self.target_name = filename
                self.add_target_object()  # add target if canonical

    def get_target_file_type(self, target_file):
        """Determines if file is fasta, gff3, vcf, etc"""
        file_type = target_file.split(".")[-2].lower()
        if file_type in FASTA_TYPES:
            file_type = "fasta"
        elif file_type in GFF_TYPES:
            file_type = "gff3"
        else:
            return False
        return file_type

    def add_target_object(self):
        """Create a structure for file objects."""
        target_attributes = self.target_name.split(".")
        if len(target_attributes) < 3 or self.target_name[0] == "_":
            logger.info(f"File {self.target} does not seem to have attributes")
            return
        canonical_type = target_attributes[-3]  # check content type
        if canonical_type not in self.canonical_types:  # check for known file types
            if len(target_attributes) < 5:
                logger.info(f"No type for {self.target}. skipping")
                return
            canonical_type = target_attributes[-5]
            if canonical_type not in self.canonical_types: # check for mrk identifier
                logger.info(
                    f"Type {canonical_type} not recognized in"
                    f" {self.canonical_types}.  Skipping"
                )
                return
        organism_dir_path = os.path.dirname(
            os.path.dirname(self.target)
        )  # org dir
        organism_dir = os.path.basename(
            os.path.dirname(os.path.dirname(self.target))
        )  # org dir
        target_dir = os.path.basename(os.path.dirname(self.target))
        print(target_dir, organism_dir)
        if len(organism_dir.split("_")) != 2:
            return
        genus = organism_dir.split("_")[0].lower()
        species = organism_dir.split("_")[1].lower()
        target_ref_type = self.canonical_parents[canonical_type]
        logger.debug("Getting target files reference if necessary...")
        file_type = self.get_target_file_type(self.target_name)
        file_url = f"{DOMAIN}/{organism_dir}/{target_dir}/{self.target_name}"
        target_node_object = {
            "filename": self.target_name,
            "filetype": file_type,
            "canonical_type": canonical_type,
            "url": file_url,
            "counts": "",
            "genus": genus,
            "species": species,
            "origin": "LIS",
            "infraspecies": target_attributes[1],
            "derived_from": [],
            "child_of": [],
        }
        if len(target_attributes) > 7 and target_ref_type:  # check parent
            logger.debug("Target Derived from Some Reference Searching...")
            ref_glob = f"{organism_dir_path}/{ '.'.join(target_attributes[1:3])}*/*{target_ref_type}.*.gz"
            if self.rank[canonical_type] > 1:  # feature has a subtype
                ref_glob = f"{organism_dir_path}/{'.'.join(target_attributes[1:4])}*/*{target_ref_type}.*.gz"
                if canonical_type == 'gwas':  # mrk is parent and needs be read from PlatformName in gwas file
                    cmd = f'zgrep PlatformName {self.target}'
                    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                    platformname = proc.communicate()[0].decode('utf-8').rstrip().split('\t')[1]
                    ref_glob = f"{organism_dir_path}/*.mrk.*/*mrk.*.{platformname}.gff3.gz"
                elif canonical_type == 'phen':  # gwas is parent

                    ref_glob = 'gwas'.join(str(self.target).rsplit('phen', 1))
            my_reference = self.get_reference(ref_glob)
            logger.info(my_reference)
            if my_reference not in self.target_objects:  # new parent
                parent_name = os.path.basename(my_reference)
                file_type = self.get_target_file_type(parent_name)
                organism_dir = os.path.basename(
                    os.path.dirname(os.path.dirname(my_reference))
                )
                ref_dir = os.path.basename(os.path.dirname(my_reference))
                file_url = f"{DOMAIN}/{organism_dir}/{ref_dir}/{parent_name}"
                ref_node_object = {
                    "filename": parent_name,
                    "filetype": file_type,
                    "canonical_type": target_ref_type,
                    "url": file_url,
                    "counts": "",
                    "genus": genus,
                    "species": species,
                    "origin": "LIS",
                    "infraspecies": target_attributes[1],
                    "derived_from": [],
                    "child_of": [],
                }
                target_node_object["child_of"].append(parent_name)
                target_node_object["derived_from"].append(parent_name)
                self.target_objects[my_reference] = {
                    "type": target_ref_type,
                    "node_data": ref_node_object,
                    "readme": "",
                    "children": {},
                }
                self.target_objects[my_reference]["children"][self.target] = {
                    "node_data": target_node_object,
                    "type": canonical_type,
                }
                if self.rank[target_ref_type] > 0:
                    self.target = my_reference
                    self.target_name = os.path.basename(my_reference)
                    self.add_target_object()  # add target if canonical
            else:  # the parent is already in the data structure add child
                if self.target not in self.target_objects[my_reference]["children"]:
                    parent_name = os.path.basename(my_reference)
                    target_node_object["child_of"].append(parent_name)
                    target_node_object["derived_from"].append(parent_name)
                    self.target_objects[my_reference]["children"][
                        self.target
                    ] = {
                        "node_data": target_node_object,
                        "type": canonical_type,
                    }
        else:  # target is a reference
            if target_ref_type:
                logger.error("Reference was not found or file has <=7 fields")
                sys.exit(1)
            logger.debug("Target has no Parent, it is a Reference")
            if self.target not in self.target_objects:
                self.target_objects[self.target] = {
                    "type": canonical_type,
                    "node_data": target_node_object,
                    "children": {},
                }

    def get_reference(self, glob_target):
        """Finds the FASTA reference for some prefix"""
        if len(glob(glob_target)) > 1:  # too many references....?
            logger.error(f"Multiple references found {glob(glob_target)}")            
#            sys.exit(1)
        reference = glob(glob_target)
        if not reference:  # if the objects parent could not be found
            logger.error(f"Could not find ref glob: {glob_target}")
            sys.exit(1)
        reference = glob(glob_target)[0]
        if not os.path.isfile(reference):  # if cannot find reference file
            logger.error(f"Could not find main target {reference}")
            sys.exit(1)
        logger.debug(f"Found reference {reference}")
        return reference

    def write_node_object(self):
        """Write DSCensor object node."""
        my_name = self.write_me["filename"]
        if self.write_me["canonical_type"] == "genome_main":
            return
            self.write_me["counts"] = basic_fasta_stats(self.target, 10, False)
        elif self.write_me["canonical_type"] == "gene_models_main":
            self.write_me["counts"] = count_gff_features(self.target)
        my_file = open(f"./{my_name}.json", "w")
        my_file.write(json.dumps(self.write_me))
        my_file.close()

    def check_busco(self):
        """Runs BUSCO using BUSCO_ENV_FILE envvar and outputs to file_name."""
        target = self.target
        node_data = self.node_data  # get current targets nodes
        busco_parse = re.compile(
            r"C:(.+)\%\[S:(.+)\%,D:(.+)\%\],F:(.+)\%,M:(.+)\%,n:(\d+)"
        )
#        output = f"{'.'.join(file_name.split('.')[:-2])}.busco"
        #cmd = f"run_BUSCO.py --mode {mode} --lineage {'lineage'}"
        #outdir = f"./run_{output}"  # output from BUSCO
        name = f'{os.path.basename(target)}_busco'
        if node_data.get("canonical_type") == "gene_models_main":
            name = "*.protein_primaryTranscript.*_busco"
        print(node_data.get("canonical_type"))
        print(f"{os.path.dirname(target)}/busco/{name}/short_summary*_busco.txt")
        short_summary = glob(f'{os.path.dirname(target)}/busco/{name}/short_summary*_busco.txt')
        if not short_summary:
            logger.debug(f"BUSCO short summary not found for {target}")
            return
        short_summary = short_summary[0]
        node_data["busco"] = {}
        with open(short_summary) as fopen:
            for line in fopen:
                line = line.rstrip()
                if line.startswith("#") or not line or len(line.split("\t")) < 3:
                    continue
                fields = line.split("\t")
                if fields[2].startswith("Complete BUSCOs"):
                    node_data["busco"]["complete_buscos"] = fields[1]
                elif fields[2].startswith("Complete and single"):
                    node_data["busco"]["single_copy_buscos"] = fields[1]
                elif fields[2].startswith("Complete and dupli"):
                    node_data["busco"]["duplicate_buscos"] = fields[1]
                elif fields[2].startswith("Fragmented"):
                    node_data["busco"]["fragmented_buscos"] = fields[1]
                elif fields[2].startswith("Missing"):
                    node_data["busco"]["missing_buscos"] = fields[1]
                elif fields[2].startswith("Total"):
                    node_data["busco"]["total_buscos"] = fields[1]

    def detect_incongruencies(self):
        """Check consistencies in all objects."""
        targets = self.target_objects  # get objects from class init
        busco = self.busco  # if true, run BUSCO
        nodes = self.nodes  # if true, generate nodes for DSCensor
        for reference in sorted(targets, key=lambda k: self.rank[targets[k]["type"]]):
            #            logger.info('HERE {}'.format(reference))
            if reference not in self.passed:
                self.passed[reference] = 0
                self.target = reference
                ref_method = getattr(
                    specification_checks,
                    targets[reference]["type"],  # reads checks from spec
                )  # type ex genome_main
                if (
                    not ref_method
                ):  # if the target isnt in the hierarchy continue
                    logger.debug(
                        f"Check for {targets[reference]['type']} does not"
                        " exist"
                    )
                    continue
                logger.debug(ref_method)
                my_detector = ref_method(self, **self.options)
                passed = True
                if not self.disable_all:
                    passed = my_detector.run()
                if (
                    passed
                ):  # validation passed writing object node for DSCensor
                    self.passed[reference] = 1
                    self.node_data = targets[reference]["node_data"]
                    if nodes:
                        logger.info(f"Writing node object for {reference}")
                        # dscensor node
                        self.check_busco()
                        self.write_me = targets[reference]["node_data"]
                        self.write_node_object()  # write node for dscensor loading
                logger.debug(f"{targets[reference]}")
            if self.target_objects[reference]["children"]:  # process children
                self.parent = reference
                children = self.target_objects[reference]["children"]
                for c in children:
                    if c in self.passed:
                        logger.debug(f"Child {c} Already Passed")
                        continue

                    self.passed[c] = 0
                    #                    logger.info('HERE child {}'.format(c))
                    logger.info(f"Performing Checks for {c}")
                    self.target = c
                    child_method = getattr(
                        specification_checks,
                        children[c]["type"],  # check for spec
                    )  # exgene_models_main
                    if not child_method:
                        logger.warning(
                            f"Check for {children[c]['type']} does not exist"
                        )
                        continue
                    logger.debug(child_method)
                    my_detector = child_method(self, **self.options)
                    passed = True
                    if not self.disable_all:
                        passed = my_detector.run()
                    if (
                        passed
                    ):  # validation passed writing object node for DSCensor
                        self.passed[c] = 1
                        self.node_data = children[c]["node_data"]
                        if nodes:
                            logger.info(f"Writing node object for {c}")
                            self.check_busco()
                            self.write_me = children[c]["node_data"]
                            self.write_node_object()
                    logger.debug(f"{c}")


@cli.command()
@click_loguru.init_logger()
@click.option(
    "--busco", 
    is_flag=True, 
    default=False, 
    help="""Parse BUSCO for node object."""
)
@click.option(
    "--nodes",
    is_flag=True,
    default=False,
    help="""Generate DSCensor stats and node.""",
)
@click.option(
    "--genome_main",
    is_flag=True,
    default=True,
    help="""Verify genomic DNA files.""",
)
@click.option(
    "--gene_models_main",
    is_flag=True,
    default=True,
    help="""Verify gene model FASTA files.""",
)
@click.option(
    "--genometools",
    is_flag=True,
    help="""Run genometools checks on GFF files.""",
)
@click.option(
    "--fasta_headers",
    is_flag=True,
    help="""Check consistency of FASTA headers and GFF.""",
)
@click.option(
    "--disable_all",
    is_flag=True,
    help="""Disables all consistency checking.""",
)
@click.argument("target", nargs=1)
def consistency(
    target,
    busco,
    nodes,
    genome_main,
    gene_models_main,
    genometools,
    fasta_headers,
    disable_all
):
    """Perform consistency checks on target directory."""
    detector = Detector(
        target,
        busco=busco,
        nodes=nodes,
        genome_main=genome_main,
        gene_models_main=gene_models_main,
        genometools=genometools,
        fasta_headers=fasta_headers,
        disable_all=disable_all
    )  # initialize class
    detector.detect_incongruencies()  # run all detection methods
