import os
import os.path as path
from multiprocessing.connection import Connection
from tqdm import tqdm
from logging import Logger
from ovito import io as oio
from ovito import modifiers as mod
from ovito import pipeline as pln
from config import Config

config_: Config = None
pipeline_: pln.Pipeline = None

def files(connection: Connection):
    """Iterates throw files with trajectory in increasing order"""
    
    last_returned = -1
    flag = False
    finish_flag = False
    
    while not finish_flag:
        for iteration in sorted(list(map(lambda x: int(path.basename(x).split(".")[0]), 
                        os.listdir(config_.TRAJECTORY_DIR))))[:None if flag else -1]:
            if iteration > last_returned:
                last_returned = iteration
                yield path.join("/", config_.TRAJECTORY_PATH(iteration))
        
        if flag:
            finish_flag = True
            
        # if there is signal to stop, run one more iteration
        flag = connection.poll(timeout=1)
        
    return StopIteration

def set_modifiers():
    """Sets modifiers to pipeline"""
    global pipeline_
    
    # 
    logger_.info("Setting WignerSeitzAnalysisModifier modifier")
    modifier = mod.WignerSeitzAnalysisModifier()
    modifier.reference = pln.FileSource()
    modifier.reference.load(config_.REFERENCE_PATH)
    #modifier.reference.load("/home/leonid/github.com/LeonidPilyugin/u-xe-bubble/result/cpu1/configuration/reference.atom")
    modifier.affine_mapping = mod.ReferenceConfigurationModifier.AffineMapping.ToReference
    modifier.per_type_occupancies = True
    pipeline_.modifiers.append(modifier)
    
    # 
    logger_.info("Setting ExpressionSelection modifier")
    modifier = mod.ExpressionSelectionModifier(expression="Occupancy.1>1")
    pipeline_.modifiers.append(modifier)
    
    

def create_pipeline(filepath):
    """Creates pipeline"""
    global pipeline_
    
    logger_.info("Creating pipeline")
    pipeline_ = oio.import_file(filepath,
                                columns=config_.TRAJECTORY_COLUMNS)
    logger_.info("Setting modifiers")
    set_modifiers()
    

def process(filepath: str):
    """Processes frame"""
    global pipeline_
    
    # create pipeline or load data if pipeline exists
    if pipeline_ is None:
        create_pipeline(filepath)
    else:
        pipeline_.source.load(filepath)
    
    count = pipeline_.compute().attributes["ExpressionSelection.count"]
    
    with open(path.join(config_.ANALYSIS_DIR, "count"), "a") as f:
        f.write(f"{count}\n")
    

def start_analyze(config: Config, logger: Logger, connection: Connection, progressbar: tqdm):
    """Starts analysing simulation"""
    
    # set global logger and config
    global logger_, config_
    logger_= logger
    config_ = config
    
    # process each file
    for filepath in files(connection):
        process(filepath)
        progressbar.update(1)
        
