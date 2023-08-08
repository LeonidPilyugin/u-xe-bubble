import yaml
import os
import importlib.util as iu
from inspect import getmembers, isfunction


class ConfigException(Exception):
    pass

class YamlRepresentersFileException(ConfigException):
    pass


class State:
    """Stores state"""
    
    def __init__(self):
        self._dict = {}
    
    
    def load(self, path: str):
        """Loads config by path"""
        with open(path) as f:
            line = f.readline()
            if line[0] == "#":
                repr = line.split("#")[1].strip()
                try:
                    # load functions
                    spec = iu.spec_from_file_location("repr", repr)
                    module = iu.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    func = getmembers(module, isfunction)
                    
                    for name, obj in func:
                        if name.startswith("_"):
                            continue
                        yaml.add_constructor(f"!{name}", obj)
                except Exception:
                    raise YamlRepresentersFileException(f"Incorrect \"{repr}\" YAML representers file")
            
        try:
            # load config
            with open(path) as f:
                self._dict = yaml.load(f, Loader=yaml.loader.UnsafeLoader)
        except Exception:
            raise ConfigException(f"Incorrect config \"{path}\"")
        
    
    def __getitem__(self, key):
        try:
            d = self._dict
            
            for k in key.split("|"):
                d = d[k]
                
            return d
        
        except (KeyError, TypeError):
            raise KeyError(f"No such key \"{key}\"")
    
    
    def __setitem__(self, key, value):
        try:
            spl = key.split("|")
            d = self._dict
            
            for k in spl[:-1]:
                d = d[k]
                
            d[spl[-1]] = value
            
        except (KeyError, TypeError):
            raise KeyError(f"No such key \"{key}\"")
        
        
def join(loader, node):
    seq = loader.construct_sequence(node)
    return os.path.join(*[str(i) for i in seq])
