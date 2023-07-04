import os
import numpy as np
import os.path as path
import openmm as mm
from typing import Tuple
from tqdm import tqdm
from logging import Logger
from threading import Event
from numpy import ndarray
from openmm import unit as un
from ovito import data as odata
from ovito import io as oio
from edward2 import SimulationData
from edward2 import Simulation
from config import Config

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
    
    

def mean_next(simulation: Simulation, steps: int) -> Tuple[float, float, np.ndarray, np.ndarray]:
    """Does next steps iterations and returns mean parameters
    (potential energy, kinetic energy, positions, velocities)"""
    
    # create parameters to mean
    state = simulation.get_state()
    p = state.getPositions(asNumpy=True)
    v = state.getVelocities(asNumpy=True)
    u = t = 0
    positions = np.zeros_like(p)
    velocities = np.zeros_like(v)
    
    for _ in range(steps):
        # run 1 step
        state = simulation.step(1)
        # add parameters to created variables
        positions = np.add(positions, p.value_in_unit(un.angstrom))
        velocities = np.add(velocities, v.value_in_unit(un.angstrom / un.picosecond))
        u += state.getPotentialEnergy().value_in_unit(un.elementary_charge * un.volt / un.mole)
        t += state.getKineticEnergy().value_in_unit(un.elementary_charge * un.volt / un.mole)
        
    # mean parameters
    positions /= steps
    velocities /= steps
    u /= steps
    t /= steps
    
    return u, t, positions, velocities


def dump(u: float,
         t: float,
         positions: ndarray,
         velocities: ndarray,
         types: ndarray,
         cell,
         step: int):
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


def run(config: Config, logger: Logger, sim_bar: tqdm, event: Event):
    """Runs simulation and data processing"""
    
    # set global logger and config
    global logger_, config_
    logger_= logger
    config_ = config
    
    # create simulation
    simulation, types = create_simulation()
    
    # variable to count saved checkpoints
    saved_checkpoints = 0
    
    logger_.info("Starting simulation")
    for i in range(0, config_.RUN_STEPS, config_.AVERAGE_STEPS):
        # get next mean values
        u, t, positions, velocities = mean_next(simulation, config_.AVERAGE_STEPS)
        
        # dump mean values
        dump(u,
             t,
             positions,
             velocities,
             types,
             simulation.get_state().getPeriodicBoxVectors(asNumpy=True).value_in_unit(un.angstrom),
             i)
        
        # save new checkpoint if necessary
        if i // config_.CHECKPOINT_STEPS >= saved_checkpoints:
            saved_checkpoints += 1
            with open(config_.CHECKPOINT_PATH(i), "wb") as f:
                f.write(simulation.context.createCheckpoint())
        
        # update progress bar
        sim_bar.update(1)
    else:
        # save last checkpoint
        with open(config_.CHECKPOINT_PATH(config_.RUN_STEPS - 1), "wb") as f:
                f.write(simulation.context.createCheckpoint())
        
    # close simulation bar
    sim_bar.close()
    
    event.set()
    
    logger.info("Simulation finished")
    
