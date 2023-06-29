import subprocess as sp
import openmm.unit as un
import subprocess as sp
from config import Config
from logging import Logger

logger_: Logger = None
config_: Config = None


def create_system(config: Config, logger: Logger):
    """Creates config_uration file and reference file"""
    
    # set global logger and config
    global logger_, config_
    logger_= logger
    config_ = config
    
    logger_.info("Creating system")
    
    logger_.info(f"Saving script to \"{config_.LAMMPS_SCRIPT_PATH}\"")
    
    with open(config_.LAMMPS_SCRIPT_PATH, "w") as f:
        f.write(config_.LAMMPS_SCRIPT)
        
    logger_.info("Generating system")
    
    sp.call(f"{config_.LAMMPS_EXECUTABLE_PATH} -in {config_.LAMMPS_SCRIPT_PATH} -log {config_.LAMMPS_LOG_PATH} -screen none".split())
    
    logger_.info(f"System saved to \"{config_.CONFIGURATION_PATH}\"")


