from config import configs
from main_utils import create_tree
from main_utils import start_analysis
from main_utils import create_process
from main_utils import create_analysis_bar


if __name__ == "__main__":
    print("Script started")
    
    # create file tree for each simulation
    for config in configs.values():
        create_tree(config)
    
    # create analysis bar
    analysis_bar = create_analysis_bar(configs.values())
    
    # create processes
    processes = []
    for name, config in configs.items():
        processes.append((*create_process(config, name), config))
        
    # start processes
    for p, _, _ in processes:
        p.start()
        
    # start analyzing
    start_analysis(processes, analysis_bar)
    
    # join all processes
    for p, _, _ in processes:
        p.join()
        
    print("Script finished")

