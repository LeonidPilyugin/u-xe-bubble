#from time import sleep
import sys
import os
from logging import Logger
from multiprocessing import Process, Value
from typing import List, Tuple
from datetime import timedelta
import ovito.io
import ovito.data
import ovito.pipeline
import openmm
from tqdm import tqdm
from createsystem import create_system
from simulation import run
from utils import create_logger, time_ns
from config import configs, Config
from random import random
 

def create_tree(config: Config):
    """Create tree of new simulation"""
    
    # Make simulations directory if necessary
    if not os.path.exists(config.SIMULATIONS_DIR):
        os.mkdir(config.SIMULATIONS_DIR)
    
    # Create new simulation directory
    # If directory exists, will raise an exception
    os.mkdir(config.SIMULATION_DIR)
    
    # Dump config file
    config.dump()
    
    # Create all directories
    for dir in [
        config.CONFIGURATION_DIR,
        config.CHECKPOINT_DIR,
        config.THERMO_DIR,
        config.LOG_DIR,
        config.TRAJECTORY_DIR,
    ]: os.mkdir(dir)
    
    
def start(config: Config, sim_bar: tqdm, proc_bar: tqdm):
    """Runs simulation"""
    
    logger = create_logger(config)
    
    logger.info("Starting simulation")
    
    if config.PLATFORM_NAME == "HIP":
        logger.info(f"Setting HIP_VISIBLE_DEVICES = {config.PLATFORM_PROPERTIES['HIP']['DeviceIndex']}")
        os.environ["HIP_VISIBLE_DEVICES"] = config.PLATFORM_PROPERTIES["HIP"]["DeviceIndex"]
    
    logger.info("Starting creating system")
    t = time_ns(create_system, config, logger)[0]
    logger.info(f"System creation took {timedelta(seconds=t // 1e9)}")
    
    logger.info("Starting running simulation")
    t = time_ns(run, config, logger, sim_bar, proc_bar)[0]
    logger.info(f"Simulation running took {timedelta(seconds=t // 1e9)}")
    
    logger.info("Simulation finished")
        

if __name__ == "__main__":
    print("Script started")
    
    processes = []
    
    for config in configs.values():
        create_tree(config)
        
    for name, config in configs.items():
        sim_bar = tqdm(total=config.RUN_STEPS // config.AVERAGE_STEPS)
        sim_bar.set_description(f"{name} simulation progress")
        proc_bar = tqdm(total=config.RUN_STEPS // config.AVERAGE_STEPS)
        proc_bar.set_description(f"{name} processing progress")
        process = Process(target=start,
                          args=(config,
                                sim_bar,
                                proc_bar, ),
                          name=name)
        
        processes.append(process)
        
    for p in processes:
        p.start()
        
    for p in processes:
        p.join()
        
    print("Script finished")

