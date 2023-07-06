import os
import os.path as path
import openmm as mm
from typing import Tuple
from tqdm import tqdm
from logging import Logger
from numpy import ndarray
from openmm import unit as un
from ovito import data as odata
from ovito import io as oio
from edward2 import SimulationData
from edward2 import Simulation
from config import Config
from analysis import analize

logger_: Logger = None
config_: Config = None

def create_simulation() -> Tuple[Simulation, ndarray]:
    """Creates a simulation object"""
    
    logger_.info(f"Creating simulation data")
    data = SimulationData()
    
    logger_.info(f"Importing configuration from \"{config_.CONFIGURATION_PATH}\"")
    data.read_ovito(config_.CONFIGURATION_PATH)
    
    data.set_integrator(mm.VerletIntegrator(config_.TIME_STEP))
    
    logger_.info(f"Importing force from \"{config_.POTENTIAL_PATH}\"")
    with open(config_.POTENTIAL_PATH, "r") as file_force:
        force = mm.XmlSerializer.deserialize(file_force.read())
        
    logger_.info(f"Adding particles")
    for i in range(data.count):
        force.addParticle([config_.PARTICLE_TYPE_DICT[data.types[i]]])
        
    data.add_force(force)
    data.add_force(mm.CMMotionRemover())
    
    logger_.info(f"Creating simulation")
    types = data.types
    
    if config_.PLATFORM_NAME == "HIP":
        logger_.info(f"Setting HIP_VISIBLE_DEVICES = {config_.PLATFORM_PROPERTIES['DeviceIndex']}")
        os.environ["HIP_VISIBLE_DEVICES"] = config_.PLATFORM_PROPERTIES["DeviceIndex"]
    
    simulation = data.make_simulation(config_.PLATFORM_NAME, config_.PLATFORM_PROPERTIES)
    
    logger_.info("Simulation created")
    
    return simulation, types


def dump(u: float,
         t: float,
         positions: ndarray,
         velocities: ndarray,
         types: ndarray,
         step: int,
         cell):
    """Writes dumps of energies and positions"""
    
    data = odata.DataCollection()
    
    # get cell
    data_cell = odata.SimulationCell(pbc=(True, True, True))
    data_cell[:, :3] = cell

    # set cell
    data.objects.append(data_cell)

    # set positions, velocities and types
    particles = odata.Particles()
    particles.create_property("Position", data=positions)
    particles.create_property("Velocity", data=velocities)
    particles.create_property("Particle Type", data=types)
    
    # add data to data object
    data.objects.append(particles)

    # export
    oio.export_file(
        data,
        config_.TRAJECTORY_PATH(step),
        "lammps/dump",
        columns=config_.TRAJECTORY_COLUMNS
    )
    
    # create energy dump file on first dump
    if not path.exists(config_.ENERGY_PATH):
        with open(config_.ENERGY_PATH, "w") as f:
            f.write("step,u,t,e\n")
    
    # append new line to energy dump file
    with open(config_.ENERGY_PATH, "a") as f:
        f.write(f"{step},{u},{t},{u+t}\n")
        
        
def save_checkpoint(step, checkpoint):
    with open(config_.CHECKPOINT_PATH(step), "wb") as f:
        f.write(checkpoint)
        
        
def process(step: int, u: ndarray, t: ndarray, p: ndarray,
            v: ndarray, types: ndarray, checkpoint, cell):
    
    # dump
    dump(u, t, p, v, types, step, cell)
    
    # save checkpoint if necessary
    if checkpoint is not None:
        save_checkpoint(step, checkpoint)
        
    # analyze
    analize(config_, logger_, config_.TRAJECTORY_PATH(step))
    


def run(config: Config, logger: Logger):
    """Runs simulation and data processing"""
    
    # set global logger and config
    global logger_, config_
    logger_= logger
    config_ = config
    
    # create simulation
    simulation, types = create_simulation()
    
    saved_checkpoints = 0
    need_checkpoint = False
    
    logger_.info("Starting simulation")
    # get first data
    result = simulation.mean_next(config_.AVERAGE_STEPS)
    
    for i in tqdm(range(0, config_.RUN_STEPS, config_.AVERAGE_STEPS)):
        # start getting next data
        future = simulation.mean_next_async(config_.AVERAGE_STEPS, need_checkpoint)
        if need_checkpoint: need_checkpoint = False
        
        # process data
        u, t, p, v, s, c = result
        process(i, u, t, p, v, types, c,
                s.getPeriodicBoxVectors(asNumpy=True).value_in_unit(un.angstrom))
        
        # decide to generate or not checkpoint
        if i // config_.CHECKPOINT_STEPS >= saved_checkpoints:
            need_checkpoint = True
            saved_checkpoints += 1
        
        # get result
        result = future.result()
    
    logger.info("Simulation finished")
    
