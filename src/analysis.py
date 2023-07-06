import os.path as path
from logging import Logger
from ovito import io as oio
from ovito import modifiers as mod
from ovito import pipeline as pln
from config import Config

config_: Config = None
pipeline_: pln.Pipeline = None

def set_modifiers():
    """Sets modifiers to pipeline"""
    global pipeline_
    
    # 
    logger_.info("Setting WignerSeitzAnalysisModifier modifier")
    modifier = mod.WignerSeitzAnalysisModifier()
    modifier.reference = pln.FileSource()
    modifier.reference.load(config_.REFERENCE_PATH)
    modifier.affine_mapping = pln.ReferenceConfigurationModifier.AffineMapping.ToReference
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
    

def analize(config: Config, logger: Logger, filepath: str):
    """Processes frame"""
    global pipeline_, logger_, config_
    logger_ = logger
    config_ = config
    
    # create pipeline or load data if pipeline exists
    if pipeline_ is None:
        create_pipeline(filepath)
    else:
        pipeline_.source.load(filepath)
    
    count = pipeline_.compute().attributes["ExpressionSelection.count"]
    
    with open(path.join(config_.ANALYSIS_DIR, "count"), "a") as f:
        f.write(f"{count}\n")
        
