import os
import sys
import yaml
import importlib.util as iu


class PluginException(Exception):
    pass

class PluginNotFoundException(PluginException):
    pass

class ManifestNotFoundException(PluginException):
    pass

class InvalidManifestException(PluginException):
    pass

class MainScriptNotFoundException(PluginException):
    pass

class EntryNotFoundException(PluginException):
    pass


class Plugin:
    def __init__(self, path: str):
        sys.path.append(path)
        self.path = path
        self.name = os.path.basename(path)
        self.load()
    
    
    def load(self):
        if not os.path.exists(self.path):
            raise PluginNotFoundException(f"Cannot find plugin in \"{self.name}\" plugin")
        
        try:
            # load manifest
            with open(os.path.join(self.path, "manifest.yaml")) as f:
                self.manifest = yaml.load(f, Loader=yaml.UnsafeLoader)
        except FileNotFoundError:
            raise ManifestNotFoundException(f"Cannot find manifest for plugin \"{self.name}\"")
        
        try:
            # get description
            self.description = self.manifest["description"]
        except KeyError:
            raise InvalidManifestException(f"Invalid manifest for plugin \"{self.name}\"")
        
        # entry points
        self.entries = {}
        
        if not os.path.exists(os.path.join(self.path, "main.py")):
            raise MainScriptNotFoundException(f"Cannot find main script in \"{self.name}\" plugin")
        
        try:
            # load module
            self.spec = iu.spec_from_file_location(
                self.name, os.path.join(self.path, "main.py")
            )
            self.module = iu.module_from_spec(self.spec)
            self.spec.loader.exec_module(self.module)
        except Exception:
            raise PluginException(f"Plugin \"{self.name}\" error")
        
        try:
            # get entry points
            for key in self.manifest["entries"]:
                self.entries[key] = getattr(self.module, key)
        except KeyError:
            raise InvalidManifestException(f"Entry list not found in \"{self.name}\" plugin")
        except AttributeError:
            raise EntryNotFoundException(f"Entry \"{key}\" not found for plugin \"{self.name}\"")
        
    
    def execute(self, entry: str, kwargs):
        try:
            self.entries[entry](**kwargs)
        except KeyError:
            raise EntryNotFoundException(f"Entry \"{entry}\" not found for plugin \"{self.name}\"")
        except Exception:
            if kwargs.get("strict", True):
                raise 
    
    
    
    