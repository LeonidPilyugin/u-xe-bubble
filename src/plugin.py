import os
import sys
import yaml
import importlib.util as iu

class Plugin:
    
    def __init__(self, path: str):
        sys.path.append(path)
        self.path = path
        self.load()
    
    
    def load(self):
        # load manifest
        with open(os.path.join(self.path, "manifest.yaml")) as f:
            self.manifest = yaml.load(f, Loader=yaml.UnsafeLoader)
        
        # get name
        self.name = self.manifest["name"]
        # get description
        self.description = self.manifest["description"]
        # entry points
        self.entries = {}
        
        # load module
        self.spec = iu.spec_from_file_location(
            self.name, os.path.join(self.path, "main.py")
        )
        self.module = iu.module_from_spec(self.spec)
        self.spec.loader.exec_module(self.module)
        
        # get entry points
        for key in self.manifest["entries"]:
            self.entries[key] = getattr(self.module, key)
        
    
    def execute(self, entry: str, kwargs):
        self.entries[entry](**kwargs)
    
    
    
    