import os
from state import State
from plugin import Plugin


class Kernel:
    
    def __init__(self, config: str):
        self.PLUGIN_DIR = "./plugins"
        self.state = State()
        self.state.load(config)
        self.plugins = {}
        self.sequence = self.state["sequence"]
    
    
    def load(self):
        for plugin_name in self.state["plugins"]:
            self.plugins[plugin_name] = Plugin(os.path.join(self.PLUGIN_DIR, plugin_name))
    
    
    def run(self):
        for command in self.sequence:
            key, value = list(command.items())[0]
            plugin, entry = key.split(".")
            self.plugins[plugin].execute(entry, value)
    