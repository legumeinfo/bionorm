# -*- coding: utf-8 -*-
# standard library imports
import contextlib
import gzip
import hashlib
import os
import shutil
from pathlib import Path

# third-party imports
from progressbar import DataTransferBar
from requests_download import HashTracker
from requests_download import ProgressTracker
from requests_download import download


class DownloadTestFiles(object):
    """Download, verify, cache, and optionally gzip test files from a specified URL"""

    def __init__(
        self,
        download_url="https://example.com/dldir/",
        files=[],
        download_dir=None,
        gzipped=False,
        md5_check=False,
        progressbar=False,
    ):
        if download_url.endswith("/"):
            self.download_url = download_url
        else:
            self.download_url = download_url + "/"
        if download_dir is None:  # default download is test directory
            download_dir = Path(__file__).parent
        self.download_path = Path(download_dir)
        if not self.download_path.exists():
            self.download_path.mkdir(exist_ok=True, parents=True)
        self.progressbar = progressbar
        self.file_dict = {}
        self.gzipped = gzipped
        for filename in files:
            self.file_dict[filename] = {}
            self.file_dict[filename]["path"] = self.download_path / filename
            if gzipped:
                self.file_dict[filename]["dlname"] = filename + ".gz"
            else:
                self.file_dict[filename]["dlname"] = filename
            if md5_check:
                self.file_dict[filename]["md5"] = self.file_dict[filename]["dlname"] + ".md5"
            if not self.file_dict[filename]["path"].exists():
                self.download_file(self.file_dict[filename])

    def download_file(self, filedict):
        """Download file from URL with optional MD5 check and gunzip"""
        if "md5" in filedict:
            check_type = "MD5 checked"
            print(f'downloading {self.download_url}{filedict["dlname"]} with MD5 check')
            md5_path = self.download_path / filedict["md5"]
            if not md5_path.exists():
                download(self.download_url + filedict["md5"], md5_path)
            md5_val = md5_path.read_text().split()[0]
            md5_path.unlink()
        else:
            check_type = ""
            print(f'downloading {self.download_url}{filedict["dlname"]}')
        tmp_path = self.download_path / (filedict["dlname"] + ".tmp")
        hasher = HashTracker(hashlib.md5())
        if self.progressbar:
            trackers = (hasher, ProgressTracker(DataTransferBar()))
        else:
            trackers = (hasher,)
        download(self.download_url + filedict["dlname"], tmp_path, trackers=trackers)
        filedict["hash"] = hasher.hashobj.hexdigest()
        if (not "md5" in filedict) or (md5_val == filedict["hash"]):
            if self.gzipped:
                with gzip.open(tmp_path, "rb") as f_in:
                    with filedict["path"].open("wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                tmp_path.unlink()
                print(f'ungzipped {check_type} file to {filedict["path"]}')
            else:
                tmp_path.rename(filedict["path"])
                print(f'downloaded {check_type} file to {filedict["path"]}')
        else:
            raise ValueError(f'\nhash of {filedict["dlname"]}={hashval}, expected {md5_val}')

    @contextlib.contextmanager
    def data_to_working_directory(self, tmp_path, filelist=[]):
        """Copy data and change context to tmp_path directory."""
        cwd = Path.cwd()
        for filename in filelist:
            shutil.copy2(self.file_dict[filename]["path"], tmp_path / filename)
        os.chdir(tmp_path)
        try:
            yield
        finally:
            os.chdir(cwd)
