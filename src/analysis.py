from config import Config
from logging import Logger
from ovito.io import import_file
from ovito.pipeline import Pipeline, FileSource
from ovito.pipeline import ReferenceConfigurationModifier
from ovito.modifiers import WignerSeitzAnalysisModifier
from ovito.modifiers import ExpressionSelectionModifier
from ovito.modifiers import DeleteSelectedModifier
from config import Config
from multiprocessing.connection import Connection
import os
from tqdm import tqdm

config_: Config = None
pipeline_: Pipeline = None

def files(connection: Connection):
    """Iterates throw files with trajectory in increasing order"""
    
    last_returned = -1
    flag = False
    finish_flag = False
    
    while not finish_flag:
        for iteration in sorted(list(map(lambda x: int(os.path.basename(x).split(".")[0]), 
                        os.listdir(config_.TRAJECTORY_DIR))))[:None if flag else -1]:
            if iteration > last_returned:
                last_returned = iteration
                yield os.path.join("/", config_.TRAJECTORY_PATH(iteration))
        
        if flag:
            finish_flag = True
            
        # If there is signal to stop, run one more iteration
        flag = connection.poll(timeout=1)
        
    return StopIteration

def set_modifiers():
    """Sets modifiers to pipeline"""
    global pipeline_
    
    # 
    logger_.info("Setting WignerSeitzAnalysisModifier modifier")
    modifier = WignerSeitzAnalysisModifier()
    modifier.reference = FileSource()
    modifier.reference.load(config_.REFERENCE_PATH)
    #modifier.reference.load("/home/leonid/github.com/LeonidPilyugin/u-xe-bubble/result/cpu1/configuration/reference.atom")
    modifier.affine_mapping = ReferenceConfigurationModifier.AffineMapping.ToReference
    modifier.per_type_occupancies = True
    pipeline_.modifiers.append(modifier)
    
    # 
    logger_.info("Setting ExpressionSelection modifier")
    modifier = ExpressionSelectionModifier(expression="Occupancy.1>1")
    pipeline_.modifiers.append(modifier)
    
    

def create_pipeline(filepath):
    """Creates pipeline"""
    global pipeline_
    
    logger_.info("Creating pipeline")
    pipeline_ = import_file(filepath,
                            columns=config_.TRAJECTORY_COLUMNS)
    logger_.info("Setting modifiers")
    set_modifiers()
    

def process(filepath: str):
    """Processes frame"""
    global pipeline_
    
    # Create pipeline or load data if pipeline exists
    if pipeline_ is None:
        create_pipeline(filepath)
    else:
        pipeline_.source.load(filepath)
    
    count = pipeline_.compute().attributes["ExpressionSelection.count"]
    
    with open(os.path.join(config_.ANALYSIS_DIR, "count"), "a") as f:
        f.write(f"{count}\n")
    

def start_analyze(config: Config, logger: Logger, connection: Connection, progressbar: tqdm):
    """Starts analysing simulation"""
    
    # Set global logger and config
    global logger_, config_
    logger_= logger
    config_ = config
    
    # Process each file
    for filepath in files(connection):
        process(filepath)
        progressbar.update(1)
        
    
    
if __name__ == "__main__":
    #config_.__setattr__("REFERENCE_PATH", "/home/leonid/github.com/LeonidPilyugin/u-xe-bubble/result/cpu1/configuration/reference.atom")
    pipeline = create_pipeline("/home/leonid/github.com/LeonidPilyugin/u-xe-bubble/result/cpu1/trajectory/0.trj")
    count = pipeline.compute().attributes["ExpressionSelection.count"]
    print(count)
