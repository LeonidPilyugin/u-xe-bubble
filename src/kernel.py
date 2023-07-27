import os
from state import State
from plugin import Plugin

class KernelException(Exception):
    pass

class InvalidConfig(KernelException):
    pass


class Kernel:
    
    def __init__(self, config: str):
        self.state = State()
        self.state.load(config)
        self.plugins = {}
        try:
            self.sequence = self.state["sequence"]
        except KeyError:
            raise InvalidConfig("Cannot find sequence")
    
    
    def load(self):
        try:
            for plugin_name in self.state["plugins"]:
                self.plugins[plugin_name] = Plugin(os.path.join(os.path.dirname(__file__), "../plugins", plugin_name))
        except KeyError:
            raise InvalidConfig("Cannot find plugins")
    
    
    def run(self):
        for command in self.sequence:
            key, value = list(command.items())[0]
            plugin, entry = key.split(".")
            self.plugins[plugin].execute(entry, value)
    