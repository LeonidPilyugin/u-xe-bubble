import os.path as path
from logging import Logger
from ovito import io as oio
from ovito import modifiers as mod
from ovito import pipeline as pln
from config import Config
import parameter

config_: Config = None
pipeline_: pln.Pipeline = None
logger_: Logger = None

modifiers_ = [ ]

def set_modifiers():
    """Sets modifiers to pipeline"""
    global pipeline_
    
    for m in modifiers_:
        m.setup(config_)
        pipeline_.modifiers.append(m.modify)
    

def create_pipeline(source):
    """Creates pipeline"""
    global pipeline_
    
    logger_.info("Creating pipeline")
    pipeline_ = pln.Pipeline(source=source)
    logger_.info("Setting modifiers")
    set_modifiers()
    

def analize(config: Config, logger: Logger, data, u, t):
    """Processes frame"""
    global pipeline_, logger_, config_, modifiers_
    logger_ = logger
    config_ = config
    
    modifiers_ = [
        parameter.MyWeignerSeitz,
        parameter.MyClusterAnalysis,
    ]
    
    #print(dir(mod.WignerSeitzAnalysisModifier))
    #exit(0)
    # create pipeline or load data if pipeline exists
    if pipeline_ is None:
        create_pipeline(pln.StaticSource(data=data))
    else:
        pipeline_.source = pln.StaticSource(data=data)
        
    data = pipeline_.compute()
    # print(data.attributes["WignerSeitz.vacancy_count"])
        

def final_analyze():
    
    for m in modifiers_:
        m.save()
        
    for m in modifiers_:
        m.plot()
        
