import os
import sys
import logging
from inspect import isfunction
from dataclasses import dataclass, field
from typing import Dict, Any
from simtk import unit
from os.path import abspath, join

@dataclass
class Config:
    
    # platform
    PLATFORM_NAME: str = "CPU"
    PLATFORM_PROPERTIES: Dict[str, Any] = field(default_factory=lambda:{})
    
    # configuration
    RANDOM_SEED: int = 10
    TEMPERATURE: unit.Quantity = 1400 * unit.kelvin
    LATTICE_PARAMETER: unit.Quantity = 3.5449 * unit.angstroms
    BOX_SIZE: unit.Quantity = 20 * LATTICE_PARAMETER
    RADIUS: unit.Quantity = 2.2 * LATTICE_PARAMETER
    ADDITIONAL_ATOMS: int = 0
    OCCUPANCY: float = 10/27
    TIME_STEP: unit.Quantity = 1 * unit.femtoseconds
    PARTICLE_TYPE_DICT: Dict[int, int] = field(default_factory=lambda: {1: 1, 2: 3})
    
    # simulation
    RUN_STEPS: int = 100 # 500 * 1e6
    AVERAGE_STEPS: int = 1 # 1000
    CHECKPOINT_STEPS: int = 10
    
    # Absolute path of directory with this program
    ROOT: str = join("/", *abspath(__file__).split("/")[:-2])
    
    # Absolute path of directory with simulations
    SIMULATIONS_DIR: str = join(ROOT, "result")
    
    # Name of subdirectory with current simulation results
    SIMULATION_NAME: str = ""
    
    @property
    def SIMULATION_DIR(self) -> str:
        """Absolute path of directory with current simulation"""
        return join(self.SIMULATIONS_DIR, self.SIMULATION_NAME)
    
    # Directory with potentials
    POTENTIAL_DIR: str = join(ROOT, "potentials")
    # Potential file for OpenMM
    POTENTIAL_PATH: str = join(POTENTIAL_DIR, "output-gb.xml")
    # Potential file for LAMMPS
    EAM_POTENTIAL_PATH: str = join(POTENTIAL_DIR, "U_Mo_Xe.2013.eam.alloy")
    
    # Name of configuration file
    CONFIG_NAME: str = "config"
    # Extention of 
    CONFIG_EXT: str = ".txt"
    
    @property
    def CONFIG_PATH(self) -> str:
        """Absolute path of file with configs of simulation"""
        return join(self.SIMULATION_DIR, self.CONFIG_NAME + self.CONFIG_EXT)
    
    
    @property
    def CONFIGURATION_DIR(self) -> str:
        """Absolute path of directory with configuration system"""
        return join(self.SIMULATION_DIR, "configuration")
    
    # Extention of configuration system
    CONFIGURATION_EXT: str = ".atom"
    # Extention of reference system
    REFERENCE_EXT: str = ".atom"
    
    @property
    def CONFIGURATION_PATH(self) -> str:
        return join(self.CONFIGURATION_DIR, "configuration" + self.CONFIGURATION_EXT)
    
    @property
    def REFERENCE_PATH(self) -> str:
        return join(self.CONFIGURATION_DIR, "reference" + self.REFERENCE_EXT)
    
    
    @property
    def CHECKPOINT_DIR(self) -> str:
        """Absolute path of directory with checkpoints"""
        return join(self.SIMULATION_DIR, "checkpoints")
    
    # Extention of checkpoint file
    CHECKPOINT_EXT: str = ".checkpoint"
    
    def CHECKPOINT_PATH(self, n: int) -> str:
        """Absolute path of n step of checkpoint file"""
        return join(self.CHECKPOINT_DIR, str(n) + self.CHECKPOINT_EXT)
    
    
    @property
    def THERMO_DIR(self) -> str:
        """Absolute path of directory with thermo info"""
        return join(self.SIMULATION_DIR, "thermo")
    
    # Name of energy file
    ENERGY_NAME: str = "energy"
    # Extention of energy file
    ENERGY_EXT: str = ".csv"
    
    @property
    def ENERGY_PATH(self) -> str:
        """Absolute path of file with energies"""
        return join(self.THERMO_DIR, self.ENERGY_NAME + self.ENERGY_EXT)
    
    
    @property
    def LOG_DIR(self) -> str:
        """Absolute path of directory with logs"""
        return join(self.SIMULATION_DIR, "log")
    
    # Name of file with common logs
    COMMON_LOG_NAME: str = "common"
    # Name of file with LAMMPS logs
    LAMMPS_LOG_NAME: str = "lammps"
    # Extention of logs files
    LOG_EXT: str = ".log"
    
    @property
    def COMMON_LOG_PATH(self) -> str:
        """Absolute path of file with common logs"""
        return join(self.LOG_DIR, self.COMMON_LOG_NAME + self.LOG_EXT)
    
    @property
    def LAMMPS_LOG_PATH(self) -> str:
        """Absolute path of file with LAMPS logs"""
        return join(self.LOG_DIR, self.LAMMPS_LOG_NAME + self.LOG_EXT)
    
    
    @property
    def TRAJECTORY_DIR(self) -> str:
        """Absolute path of directory with trajectories"""
        return join(self.SIMULATION_DIR, "trajectory")
    
    # Extention of trajectory file
    TRAJECTORY_EXT: str = ".trj"
    
    def TRAJECTORY_PATH(self, n: int) -> str:
        """Absolute path of n step of trajectory file"""
        return join(self.TRAJECTORY_DIR, str(n) + self.TRAJECTORY_EXT)
    
    
    
    
    
    # log mode
    LOG_MODE: int = logging.INFO
    LOG_STREAM = sys.stdout
    LOG_FORMAT: str = "%(name)s -- %(levelname)s : %(message)s"
    
    
    
    def dump(self):
        """Dumps this config to CONFIG_FILE_PATH file"""
        with open(self.CONFIG_PATH, "w") as f:
            for attr, value in self.__dict__.items():
                if not attr.startswith("_"):
                    f.write(f"{attr} = {value}\n")
                
        
    

configs = {
    "CPU1": Config(SIMULATION_NAME="cpu1"),
    "CPU2": Config(SIMULATION_NAME="cpu2", TEMPERATURE=1000 * unit.kelvins),
    # "HIP": Config(PLATFORM_NAME = "HIP", PLATFORM_PROPERTIES = {"HIP": {"DeviceIndex": 0}})
}

# configuration
# config: Config = configs["CPU"]
    
if __name__ == "__main__":
    for config in configs:
        print(f"Config: {config}")
        for attr, value in configs[config].__dict__.items():
            if not attr.startswith("_"):
                print(f"{attr} = {value}")
        print()