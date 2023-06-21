import openmm.unit as un
from lammps import lammps
from logging import Logger
from config import Config
from logging import Logger

logger_: Logger = None
config_: Config = None


def create_system(config: Config, logger: Logger):
    """Creates config_uration file and reference file"""
    
    # set global logger and config
    global logger_, config_
    logger_= logger
    config_ = config
    
    logger_.info("Creating system")
    
    script = \
f"""
units metal
dimension 3
boundary p p p

variable A equal {config_.LATTICE_PARAMETER.value_in_unit(un.angstrom)}
variable L equal {config_.BOX_SIZE.value_in_unit(un.angstrom)}
variable T equal {config_.TEMPERATURE.value_in_unit(un.kelvin)}
variable F equal {1.0 - config_.OCCUPANCY}
variable r equal {config_.RADIUS.value_in_unit(un.angstrom)}
variable N equal {config_.ADDITIONAL_ATOMS}

region SIMULATION_BOX block 0 $L 0 $L 0 $L units box

create_box 2 SIMULATION_BOX

region DEFFECT_IN  sphere $(lx/2) $(lx/2) $(lx/2) $r side in  units box
region DEFFECT_OUT sphere $(lx/2) $(lx/2) $(lx/2) $r side out units box

group U  type 1
group Xe type 2

lattice bcc $A
create_atoms 1 region SIMULATION_BOX
write_dump all atom \'{config_.REFERENCE_PATH}\'
delete_atoms region SIMULATION_BOX

create_atoms 2 region DEFFECT_IN
delete_atoms random fraction $F no all NULL {config_.RANDOM_SEED}

create_atoms 1 region DEFFECT_OUT
delete_atoms random count $N no U NULL {config_.RANDOM_SEED}
create_atoms 1 random $N {config_.RANDOM_SEED} DEFFECT_OUT

pair_style eam/alloy
pair_coeff * * \"{config_.EAM_POTENTIAL_PATH}\" U Xe

minimize 1.0e-4 1.0e-6 1000 10000

velocity all create {config_.TEMPERATURE.value_in_unit(un.kelvin)} {config_.RANDOM_SEED}

write_dump all custom \"{config_.CONFIGURATION_PATH}\" id type mass x y z vx vy vz
"""
    
    lmp = lammps(cmdargs=["-log", config_.LAMMPS_LOG_PATH, "-screen", "none"])
    logger_.debug(f"LAMMPS version: {lmp.version()}")
    lmp.commands_string(script)
    logger_.info(f"System saved to \"{config_.CONFIGURATION_PATH}\"")
    lmp.close()


