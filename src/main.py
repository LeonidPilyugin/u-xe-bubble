import sys
from config import configs
import os
from datetime import timedelta
from config import Config
from createsystem import create_system
from simulation import run
from utils import create_logger, time_ns


def create_tree(config: Config):
    """Create tree of new simulation"""
    
    # make simulations directory if necessary
    if not os.path.exists(config.SIMULATIONS_DIR):
        os.mkdir(config.SIMULATIONS_DIR)
    
    # create new simulation directory
    # if directory exists, will raise an exception
    os.mkdir(config.SIMULATION_DIR)
    
    # Dump config file
    config.dump()
    
    # Create all directories
    for dir in [
        config.CONFIGURATION_DIR,
        config.CHECKPOINT_DIR,
        config.LOG_DIR,
        config.TRAJECTORY_DIR,
        config.ANALYSIS_DIR,
    ]: os.mkdir(dir)
    
    
def start(config: Config):
    """Starts simulation"""
    
    logger = create_logger(config, "main")
    
    logger.info("Starting simulation")
    
    logger.info("Starting creating system")
    t = time_ns(create_system, config, logger)[0]
    logger.info(f"System creation took {timedelta(seconds=t // 1e9)}")
    
    logger.info("Starting running simulation")
    t = time_ns(run, config, logger)[0]
    logger.info(f"Simulation running took {timedelta(seconds=t // 1e9)}")
    
    logger.info("Simulation finished")
    

if __name__ == "__main__":
    print("Script started")
    
    # get simulation to run
    config = configs[sys.argv[1]]
    
    # create file tree
    create_tree(config)
    
    # start
    start(config)
    
    print("Script finished")
