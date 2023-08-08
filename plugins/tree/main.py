from pathlib import Path
from typing import List
import shutil
import wget
import os
import subprocess

def create_tree(wd: Path, structure: List, exist_ok: bool):
    # return if nothing to do
    if structure is None:
        return
    
    # iterate throw structure
    for file in structure:
        # create directory
        if isinstance(file, dict):
            # create directory
            dirname = list(file.keys())[0]
            current = wd.joinpath(dirname)
            current.mkdir(parents=True, exist_ok=exist_ok)
            # create tree in directory
            create_tree(current, file[dirname], exist_ok)
        # touch file
        elif isinstance(file, str):
            current = wd.joinpath(file)
            current.touch()
        # incorect object, throw exception
        else:
            raise ValueError(f"Incorect tree object: {file}")
    

def create(**data):
    create_tree(Path("/"), data["/"], data["exist_ok"])
    

def install(**data):
    for pair in data["pairs"]:
        # get source and destination
        src = list(pair.keys())[0]
        dst = pair[src]
        
        # copy file
        if src.startswith("/"):
            shutil.copy(Path(src), Path(dst))
        # download file
        else:
            wget.download(src, dst, None)
        
        
def chmod(**data):
    for pair in data["pairs"]:
        # get path and mod
        path = list(pair.keys())[0]
        mod = pair[path]
        
        # chmod
        subprocess.call(f"chmod {mod} {path}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
