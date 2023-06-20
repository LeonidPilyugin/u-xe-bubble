import sys
import os
import logging
import lammps
import openmm.unit as unit
from config import Config
from logging import Logger

logger_: Logger = None

# logger
def create_system(config: Config, logger: logging.Logger):
    global logger_
    logger_ = logger
    
    logger_.info("Creating system")
    
    script = \
f"""
units metal
dimension 3
boundary p p p

variable A equal {config.LATTICE_PARAMETER.value_in_unit(unit.angstrom)}
variable L equal {config.BOX_SIZE.value_in_unit(unit.angstrom)}
variable T equal {config.TEMPERATURE.value_in_unit(unit.kelvin)}
variable F equal {1.0 - config.OCCUPANCY}
variable r equal {config.RADIUS.value_in_unit(unit.angstrom)}
variable N equal {config.ADDITIONAL_ATOMS}

region SIMULATION_BOX block 0 $L 0 $L 0 $L units box

create_box 2 SIMULATION_BOX

region DEFFECT_IN  sphere $(lx/2) $(lx/2) $(lx/2) $r side in  units box
region DEFFECT_OUT sphere $(lx/2) $(lx/2) $(lx/2) $r side out units box

group U  type 1
group Xe type 2

lattice bcc $A
create_atoms 1 region SIMULATION_BOX
write_dump all atom \'{config.REFERENCE_PATH}\'
delete_atoms region SIMULATION_BOX

create_atoms 2 region DEFFECT_IN
delete_atoms random fraction $F no all NULL {config.RANDOM_SEED}

create_atoms 1 region DEFFECT_OUT
delete_atoms random count $N no U NULL {config.RANDOM_SEED}
create_atoms 1 random $N {config.RANDOM_SEED} DEFFECT_OUT

pair_style eam/alloy
pair_coeff * * \"{config.EAM_POTENTIAL_PATH}\" U Xe

minimize 1.0e-4 1.0e-6 1000 10000

velocity all create {config.TEMPERATURE.value_in_unit(unit.kelvin)} {config.RANDOM_SEED}

write_dump all custom \"{config.CONFIGURATION_PATH}\" id type mass x y z vx vy vz
"""
    
    lmp = lammps.lammps(cmdargs=["-log", config.LAMMPS_LOG_PATH, "-screen", "none"])
    logger_.debug(f"LAMMPS version: {lmp.version()}")
    lmp.commands_string(script)
    logger_.info(f"System saved to \"{config.CONFIGURATION_PATH}\"")
    lmp.close()


