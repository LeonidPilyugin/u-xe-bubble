import yaml
import os

class State:
    """Stores state"""
    
    def __init__(self):
        self._dict = {}
    
    
    def load(self, path: str):
        """Loads config by path"""
        yaml.add_constructor('!join', join)
            
        # load config
        with open(path) as f:
            self._dict = yaml.load(f, Loader=yaml.loader.UnsafeLoader)
        
    
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
