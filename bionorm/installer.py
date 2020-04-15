# -*- coding: utf-8 -*-
"""Install binary dependencies."""
# standard library imports
import os
import shutil
import sys
import tempfile
from pathlib import Path

# third-party imports
import click
import sh
from packaging import version
from progressbar import DataTransferBar
from requests_download import ProgressTracker
from requests_download import download as request_download

# module imports
from . import cli

INSTALL_ENVIRON_VAR = "BIONORM_INSTALL_DIR"  # installs go into "/bin" and other subdirs of this directory
if INSTALL_ENVIRON_VAR in os.environ:
    INSTALL_PATH = Path(os.environ[INSTALL_ENVIRON_VAR])
else:
    INSTALL_PATH = Path(sys.executable).parent.parent
BIN_PATH = INSTALL_PATH / "bin"
SAMTOOLS_VER = "1.10"
GFFREAD_VER = "0.11.8"
GT_VER = "1.6.1"
HTSLIB_DIR = "htslib-" + SAMTOOLS_VER

DEPENDENCY_DICT = {
    "gffread": {
        "binaries": ["gffread"],
        "git_list": ["https://github.com/gpertea/gffread.git", "https://github.com/gpertea/gclib"],
        "dir": "gffread",
        "version": version.parse(GFFREAD_VER),
        "version_command": ["--version"],
        "make": ["release"],
        "copy_binaries": ["gffread"],
    },
    "samtools": {
        "binaries": ["samtools", "tabix", "bgzip"],
        "tarball": (
            "https://github.com/samtools/samtools/releases/download/"
            + SAMTOOLS_VER
            + "/samtools-"
            + SAMTOOLS_VER
            + ".tar.bz2"
        ),
        "dir": "samtools-" + SAMTOOLS_VER,
        "version": version.parse(SAMTOOLS_VER),
        "version_command": ["--version"],
        "make": [],
        "make_extra_dirs": [HTSLIB_DIR],
        "configure": [],
        "configure_extra_dirs": [HTSLIB_DIR],
        "copy_binaries": ["samtools", HTSLIB_DIR + "/bgzip", HTSLIB_DIR + "/tabix", HTSLIB_DIR + "/htsfile"],
    },
    "genometools": {
        "binaries": ["gt"],
        "tarball": ("https://github.com/genometools/genometools/archive/v" + GT_VER + ".tar.gz"),
        "dir": "genometools-" + GT_VER,
        "version": version.parse(GT_VER),
        "version_command": ["--version"],
        "make": ["install", "prefix=" + str(INSTALL_PATH), "cairo=no", "useshared=no"],
    },
}


class DependencyInstaller(object):
    """Install and check binary dependencies."""

    def __init__(self, dependency_dict, force=False):
        """Initialize dictionary of dependencies."""
        self.dependency_dict = dependency_dict
        self.force = force
        self.dependencies = tuple(dependency_dict.keys())
        self.versions_checked = False
        self.bin_path = BIN_PATH
        self.bin_path_exists = self.bin_path.exists()
        self.bin_path_writable = os.access(self.bin_path, os.W_OK)
        self.bin_path_in_path = str(self.bin_path) in os.environ["PATH"].split(":")

    def check_all(self, verbose=True):
        """Check all depenencies for existence and version."""
        for dep in self.dependencies:
            target_version = self.dependency_dict[dep]["version"]
            version_command = self.dependency_dict[dep]["version_command"]
            self.dependency_dict[dep]["installed"] = not self.force
            for bin in self.dependency_dict[dep]["binaries"]:
                if sh.which(bin) == None:
                    if verbose:
                        print(f"Binary {bin} of dependency {dep} is not installed")
                    self.dependency_dict[dep]["installed"] = False
                else:
                    exe = sh.Command(bin)
                    ver_out = exe(*version_command, _err_to_out=True)
                    installed_version = version.parse((ver_out.split("\n")[0]).split()[-1])
                    if installed_version == target_version:
                        ver_str = f"{bin} version at recommended version {installed_version}."
                    elif installed_version < target_version:
                        ver_str = f"{bin} installed {installed_version} <  target {target_version}."
                        self.dependency_dict[dep]["installed"] = False
                    elif installed_version > target_version:
                        ver_str = f"installed {installed_version} exceeds target {target_version}."
                    if verbose:
                        print(f"{dep}: {exe} {ver_str}")
        self.versions_checked = True
        # Check that bin directory exists and is writable.
        if self.bin_path_exists:
            bin_path_state = "exists, "
        else:
            bin_path_state = "doesn't exist, "
        if self.bin_path_writable:
            bin_path_state += "writable, "
        else:
            bin_path_state += "not writable, "
        if self.bin_path_in_path:
            bin_path_state += "in path."
        else:
            bin_path_state += "not in path."
        if verbose:
            print(f"Bin dir '{self.bin_path}' {bin_path_state}")

    def install_list(self, deplist):
        """Install needed dependencies from a list."""
        self.check_all(verbose=False)
        if deplist == ("all",):
            deplist = self.dependencies
        install_list = [dep for dep in deplist if not self.dependency_dict[dep]["installed"]]
        if len(install_list):
            if not self.bin_path_exists:
                print(f"ERROR--Installation directory {self.bin_path} does not exist.")
                sys.exit(1)
            if not self.bin_path_writable:
                print(f"ERROR--Installation directory {self.bin_path} is not writable.")
                sys.exit(1)
            if not self.bin_path_in_path:
                print(f"ERROR--Installation directory {self.bin_path} is not in PATH.")
                sys.exit(1)
        for dep in install_list:
            self.install(dep)

    def _git(self, dep, dep_dict, verbose):
        """Git clone from list."""
        from sh import git  # isort:skip

        for repo in dep_dict["git_list"]:
            if verbose:
                print(f"   cloning {dep} repo {repo}")
            git.clone(repo)

    def _download_untar(self, dep, dep_dict, verbose, progressbar=True):
        """Download and untar tarball."""
        from sh import tar  # isort:skip

        download_url = dep_dict["tarball"]
        dlname = download_url.split("/")[-1]
        download_path = Path(".") / dlname
        if verbose:
            print(f"downloading {download_url} to {dlname}")
        tmp_path = download_path / (dlname + ".tmp")
        if progressbar:
            trackers = (ProgressTracker(DataTransferBar()),)
        else:
            trackers = None
        request_download(download_url, download_path, trackers=trackers)
        if verbose:
            print(f"downloaded file {download_path}, size {download_path.stat().st_size}")
        tar_output = tar("xvf", download_path)
        if verbose:
            print(tar_output)
            print("untar done")

    def _configure(self, dep, dep_dict, verbose):
        """Run make to build package."""
        if verbose:
            print(f"   configuring {dep} in {Path.cwd()}")
        configure = sh.Command("./configure")
        try:
            configure_out = configure()
        except:
            print("ERROR--configure failed.")
            sys.exit(1)
        if verbose:
            print(configure_out)

    def _make(self, dep, dep_dict, verbose):
        """Run make to build package."""
        from sh import make  # isort:skip

        if verbose:
            print(f"   making {dep} in {Path.cwd()}")
        try:
            make_out = make(dep_dict["make"])
        except:
            print("ERROR--make failed.")
            sys.exit(1)
        if verbose:
            print(make_out)

    def _make_install(self, dep, dep_dict, verbose):
        """Run make install to install a package."""
        print(f"   installing {dep} into {self.bin_path}")
        install_out = make.install(dep_dict["make_install"])
        if verbose:
            print(install_out)

    def _copy_binaries(self, dep, dep_dict, verbose):
        """Copy the named binary to the bin directory."""
        print(f"   copying {dep} into {self.bin_path}")
        for bin in dep_dict["copy_binaries"]:
            binpath = Path(bin)
            shutil.copy2(binpath, self.bin_path / binpath.name)

    def install(self, dep, verbose=True):
        """Install a particular dependency."""
        print(f"installing {dep}")
        dep_dict = self.dependency_dict[dep]
        with tempfile.TemporaryDirectory() as tmp:
            tmppath = Path(tmp)
            if verbose:
                print(f'build directory: "{tmppath}"')
            os.chdir(tmppath)
            #
            # Get the sources.  Alternatives are git or download
            #
            if "git_list" in dep_dict:
                self._git(dep, dep_dict, verbose)
            elif "tarball" in dep_dict:
                self._download_untar(dep, dep_dict, verbose)
            #
            # Change to the work directory.
            #
            if verbose:
                print(f'building in directory {dep_dict["dir"]}')
            dirpath = Path(".") / dep_dict["dir"]
            if not dirpath.exists():
                raise ValueError(f'directory "{dirpath}" does not exist.')
            if not dirpath.is_dir():
                raise ValueError(f'directory "{dirpath}" is not a directory.')
            os.chdir(dirpath)
            workpath = Path.cwd()
            #
            # Build the executables.
            #
            if "configure" in dep_dict:
                self._configure(dep, dep_dict, verbose)
            if "configure_extra_dirs" in dep_dict:
                for newdir in dep_dict["configure_extra_dirs"]:
                    os.chdir(workpath / newdir)
                    self._configure(dep, dep_dict, verbose)
                    os.chdir(workpath)
            if "make" in dep_dict:
                self._make(dep, dep_dict, verbose)
            if "make_extra_dirs" in dep_dict:
                for newdir in dep_dict["make_extra_dirs"]:
                    os.chdir(workpath / newdir)
                    self._make(dep, dep_dict, verbose)
                    os.chdir(workpath)
            #
            # Install the executables.
            #
            if "make_install" in dep_dict:
                self._make_install(dep, dep_dict, verbose)
            elif "copy_binaries" in dep_dict:
                self._copy_binaries(dep, dep_dict, verbose)


@cli.command()
@click.option("--force/--no-force", help="Force overwrites of existing binaries.", default=False)
@click.argument("dependencies", nargs=-1)
def install(dependencies, force):
    """Check for/install binary dependencies.

    \b
    Example:
        bionorm install all

    """
    installer = DependencyInstaller(DEPENDENCY_DICT, force=force)
    if dependencies == ():
        installer.check_all()
        return
    installer.install_list(dependencies)
    print("installer done")
