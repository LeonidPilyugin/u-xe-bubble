import sys
from config import configs
from main_utils import create_tree
from main_utils import start_analysis
from main_utils import create_process
from main_utils import create_analysis_bar


if __name__ == "__main__":
    print("Script started")
    
    # get name of simulation to run
    name = sys.argv[1]
    config = configs[name]
    
    # create file tree
    create_tree(config)
    
    # create analysis bar
    analysis_bar = create_analysis_bar([config])
    
    # create process
    process, event = create_process(config, name)
    
    # start process
    process.start()
    
    # start analysis
    start_analysis([(process, event, config)], analysis_bar)
    
    # join simulation process
    process.join()
    
    print("Script finished")
