import os
from typing import List
from typing import Tuple
from multiprocessing import Process
from multiprocessing import Pipe
from multiprocessing.connection import Connection
from datetime import timedelta
from tqdm import tqdm
from config import Config
from createsystem import create_system
from simulation import run
from analysis import start_analyze
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
        config.THERMO_DIR,
        config.LOG_DIR,
        config.TRAJECTORY_DIR,
        config.ANALYSIS_DIR,
    ]: os.mkdir(dir)
    
def create_process(config: Config, name: str) -> Tuple[Process, Connection]:
    sim_bar = tqdm(total=config.RUN_STEPS // config.AVERAGE_STEPS)
    sim_bar.set_description(f"{name} simulation progress")
    
    parent_connection, child_connection = Pipe()
    process = Process(target=start,
                        args=(config,
                              sim_bar,
                              child_connection),
                        name=name)
    
    return process, parent_connection
    
    
    
def start(config: Config, sim_bar: tqdm, analyze_bar: tqdm):
    """Runs simulation"""
    
    logger = create_logger(config, "main")
    
    logger.info("Starting simulation")
    
    if config.PLATFORM_NAME == "HIP":
        logger.info(f"Setting HIP_VISIBLE_DEVICES = {config.PLATFORM_PROPERTIES['HIP']['DeviceIndex']}")
        os.environ["HIP_VISIBLE_DEVICES"] = config.PLATFORM_PROPERTIES["HIP"]["DeviceIndex"]
    
    logger.info("Starting creating system")
    t = time_ns(create_system, config, logger)[0]
    logger.info(f"System creation took {timedelta(seconds=t // 1e9)}")
    
    logger.info("Starting running simulation")
    t = time_ns(run, config, logger, sim_bar, analyze_bar)[0]
    logger.info(f"Simulation running took {timedelta(seconds=t // 1e9)}")
    
    logger.info("Simulation finished")
    
    
def start_analysis(processes: List[Tuple[Process, Connection, Config]], progressbar: tqdm):
    # analyzing each process
    for process, connection, config in processes:
        logger = create_logger(config, "analysis")
        
        logger.info(f"Analysing started")
        t = time_ns(start_analyze, config, logger, connection, progressbar)[0]
        logger.info(f"Analysing took {timedelta(seconds=t // 1e9)}")
        
        logger.info(f"Analysing finished")
    
    progressbar.close()
    

def create_analysis_bar(configs: List[Config]) -> tqdm:
    analyze_bar = tqdm(total=sum([config.RUN_STEPS // config.AVERAGE_STEPS for config in configs]))
    analyze_bar.set_description(f"Analyzing progress")
    
    return analyze_bar
    
