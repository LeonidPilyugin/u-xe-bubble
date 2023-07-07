import logging
import os.path as path
from dataclasses import dataclass
from dataclasses import field
from typing import Dict
from typing import Any
from typing import List
from openmm import unit as un

@dataclass
class Config:
    
    # platform
    PLATFORM_NAME: str = "CPU"
    PLATFORM_PROPERTIES: Dict[str, str] = field(default_factory=lambda:{})
    
    # configuration
    RANDOM_SEED: int = 10
    TEMPERATURE: un.Quantity = 1400 * un.kelvin
    LATTICE_PARAMETER: un.Quantity = 3.5449 * un.angstroms
    BOX_SIZE: un.Quantity = 20 * LATTICE_PARAMETER
    RADIUS: un.Quantity = 2.2 * LATTICE_PARAMETER
    ADDITIONAL_ATOMS: int = 0
    OCCUPANCY: float = 10/27
    TIME_STEP: un.Quantity = 1 * un.femtoseconds
    PARTICLE_TYPE_DICT: Dict[int, int] = field(default_factory=lambda: {1: 1, 2: 3})
    
    # simulation
    RUN_STEPS: int = 1000
    AVERAGE_STEPS: int = 10
    CHECKPOINT_STEPS: int = 10
    
    # absolute path of directory with this program
    ROOT: str = path.join("/", *path.abspath(__file__).split("/")[:-2])
    
    # absolute path of directory with simulations
    SIMULATIONS_DIR: str = path.join(ROOT, "result")
    
    # name of subdirectory with current simulation results
    SIMULATION_NAME: str = ""
    
    @property
    def SIMULATION_DIR(self) -> str:
        """Absolute path of directory with current simulation"""
        return path.join(self.SIMULATIONS_DIR, self.SIMULATION_NAME)
    
    # directory with potentials
    POTENTIAL_DIR: str = path.join(ROOT, "potentials")
    # potential file for OpenMM
    POTENTIAL_PATH: str = path.join(POTENTIAL_DIR, "output-gb.xml")
    # potential file for LAMMPS
    EAM_POTENTIAL_PATH: str = path.join(POTENTIAL_DIR, "U_Mo_Xe.2013.eam.alloy")
    
    # name of configuration file
    CONFIG_NAME: str = "config"
    # extention of configuration file
    CONFIG_EXT: str = ".txt"
    
    @property
    def CONFIG_PATH(self) -> str:
        """Absolute path of file with configs of simulation"""
        return path.join(self.SIMULATION_DIR, self.CONFIG_NAME + self.CONFIG_EXT)
    
    
    @property
    def CONFIGURATION_DIR(self) -> str:
        """Absolute path of directory with configuration system"""
        return path.join(self.SIMULATION_DIR, "configuration")
    
    # extention of configuration system
    CONFIGURATION_EXT: str = ".atom"
    # extention of reference system
    REFERENCE_EXT: str = ".atom"
    
    @property
    def CONFIGURATION_PATH(self) -> str:
        """Absolute path of configuration file"""
        return path.join(self.CONFIGURATION_DIR, "configuration" + self.CONFIGURATION_EXT)
    
    @property
    def REFERENCE_PATH(self) -> str:
        """Absolute path of reference file"""
        return path.join(self.CONFIGURATION_DIR, "reference" + self.REFERENCE_EXT)
    
    
    @property
    def CHECKPOINT_DIR(self) -> str:
        """Absolute path of directory with checkpoints"""
        return path.join(self.SIMULATION_DIR, "checkpoints")
    
    # extention of checkpoint file
    CHECKPOINT_EXT: str = ".checkpoint"
    
    def CHECKPOINT_PATH(self, n: int) -> str:
        """Absolute path of n step of checkpoint file"""
        return path.join(self.CHECKPOINT_DIR, str(n) + self.CHECKPOINT_EXT)
    
    
    @property
    def THERMO_DIR(self) -> str:
        """Absolute path of directory with thermo info"""
        return path.join(self.SIMULATION_DIR, "thermo")
    
    # name of energy file
    ENERGY_NAME: str = "energy"
    # extention of energy file
    ENERGY_EXT: str = ".csv"
    
    @property
    def ENERGY_PATH(self) -> str:
        """Absolute path of file with energies"""
        return path.join(self.THERMO_DIR, self.ENERGY_NAME + self.ENERGY_EXT)
    
    
    @property
    def LOG_DIR(self) -> str:
        """Absolute path of directory with logs"""
        return path.join(self.SIMULATION_DIR, "log")
    
    # name of file with main logs
    MAIN_LOG_NAME: str = "main"
    # name of file with main logs
    ANALYSIS_LOG_NAME: str = "analysis"
    # name of file with LAMMPS logs
    LAMMPS_LOG_NAME: str = "lammps"
    # extention of logs files
    LOG_EXT: str = ".log"
    
    @property
    def ANALYSIS_LOG_PATH(self) -> str:
        """Absolute path of file with main logs"""
        return path.join(self.LOG_DIR, self.ANALYSIS_LOG_NAME + self.LOG_EXT)
    
    @property
    def MAIN_LOG_PATH(self) -> str:
        """Absolute path of file with analysis logs"""
        return path.join(self.LOG_DIR, self.MAIN_LOG_NAME + self.LOG_EXT)
    
    @property
    def LAMMPS_LOG_PATH(self) -> str:
        """Absolute path of file with LAMPS logs"""
        return path.join(self.LOG_DIR, self.LAMMPS_LOG_NAME + self.LOG_EXT)
    
    # path to LAMMPS executable
    LAMMPS_EXECUTABLE_PATH: str = "/home/leonid/github.com/other/lammps/build/lmp"
    # name of LAMMPS script
    LAMMPS_SCRIPT_NAME: str = "script"
    # extention of LAMMPS script
    LAMMPS_SCRIPT_EXT: str = ".lmp"
    
    @property
    def LAMMPS_SCRIPT_PATH(self) -> str:
        """Path to LAMMPS generating script"""
        return path.join(self.CONFIGURATION_DIR, self.LAMMPS_SCRIPT_NAME + self.LAMMPS_SCRIPT_EXT)
    
    
    @property
    def TRAJECTORY_DIR(self) -> str:
        """Absolute path of directory with trajectories"""
        return path.join(self.SIMULATION_DIR, "trajectory")
    
    # extention of trajectory file
    TRAJECTORY_EXT: str = ".trj"
    
    
    @property
    def ANALYSIS_DIR(self) -> str:
        """Absolute path of directory with analysis results"""
        return path.join(self.SIMULATION_DIR, "analysis")
    
    def TRAJECTORY_PATH(self, n: int) -> str:
        """Absolute path of n step of trajectory file"""
        return path.join(self.TRAJECTORY_DIR, str(n) + self.TRAJECTORY_EXT)
    
    # columns in trajectory file
    TRAJECTORY_COLUMNS: List[str] = field(default_factory=lambda: [
        "Particle Identifier",
        "Particle Type",
        "Position.X",
        "Position.Y",
        "Position.Z",
        "Velocity.X",
        "Velocity.Y",
        "Velocity.Z",
    ])
    
    
    # log mode
    LOG_MODE: int = logging.INFO
    # log format
    LOG_FORMAT: str = "%(name)s -- %(levelname)s : %(message)s"
    
    
    def dump(self):
        """Dumps this config to CONFIG_FILE_PATH file"""
        with open(self.CONFIG_PATH, "w") as f:
            for attr, value in self.__dict__.items():
                if not attr.startswith("_"):
                    f.write(f"{attr} = {value}\n")
                    
    @property
    def LAMMPS_SCRIPT(self) -> str:
        """Returns LAMMPS script"""
        return \
f"""# Script generated in u-xe-bubble program

units metal
dimension 3
boundary p p p

variable A equal {self.LATTICE_PARAMETER.value_in_unit(un.angstrom)}
variable L equal {self.BOX_SIZE.value_in_unit(un.angstrom)}
variable T equal {self.TEMPERATURE.value_in_unit(un.kelvin)}
variable F equal {1.0 - self.OCCUPANCY}
variable r equal {self.RADIUS.value_in_unit(un.angstrom)}
variable N equal {self.ADDITIONAL_ATOMS}

region SIMULATION_BOX block 0 $L 0 $L 0 $L units box

create_box 2 SIMULATION_BOX

region DEFFECT_IN  sphere $(lx/2) $(lx/2) $(lx/2) $r side in  units box
region DEFFECT_OUT sphere $(lx/2) $(lx/2) $(lx/2) $r side out units box

group U  type 1
group Xe type 2

lattice bcc $A
create_atoms 1 region SIMULATION_BOX
write_dump all atom \"{self.REFERENCE_PATH}\"
delete_atoms region SIMULATION_BOX

create_atoms 2 region DEFFECT_IN
delete_atoms random fraction $F no all NULL {self.RANDOM_SEED}

create_atoms 1 region DEFFECT_OUT
delete_atoms random count $N no U NULL {self.RANDOM_SEED}
create_atoms 1 random $N {self.RANDOM_SEED} DEFFECT_OUT

pair_style eam/alloy
pair_coeff * * \"{self.EAM_POTENTIAL_PATH}\" U Xe

minimize 1.0e-4 1.0e-6 1000 10000

velocity all create {self.TEMPERATURE.value_in_unit(un.kelvin)} {self.RANDOM_SEED}

write_dump all custom \"{self.CONFIGURATION_PATH}\" id type mass x y z vx vy vz
"""
                
        
    

configs = {
    "CPU1": Config(SIMULATION_NAME="cpu1"),
    "CPU2": Config(SIMULATION_NAME="cpu2", TEMPERATURE=1000 * un.kelvins),
    "HIP": Config(SIMULATION_NAME="HIP", PLATFORM_NAME = "HIP", PLATFORM_PROPERTIES = {"DeviceIndex": "0"}),
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