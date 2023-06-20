import os
import numpy as np
from typing import Tuple
from tqdm import tqdm
from logging import Logger
import openmm
from openmm import unit
import ovito.io
import ovito.data
from edward2 import SimulationData, Simulation
from config import Config

logger_: Logger = None
config_: Config = None

def create_simulation() -> Tuple[Simulation, np.ndarray]:
    logger_.info(f"Creating simulation data")
    data = SimulationData()
    
    logger_.info(f"Importing configuration from \"{config_.CONFIGURATION_PATH}\"")
    data.read_ovito(config_.CONFIGURATION_PATH)
    
    data.set_integrator(openmm.VerletIntegrator(config_.TIME_STEP))
    
    logger_.info(f"Importing force from \"{config_.POTENTIAL_PATH}\"")
    with open(config_.POTENTIAL_PATH, "r") as file_force:
        force = openmm.XmlSerializer.deserialize(file_force.read())
        
    logger_.info(f"Adding particles")
    for i in range(data.count):
        force.addParticle([config_.PARTICLE_TYPE_DICT[data.types[i]]])
        
    data.add_force(force)
    data.add_force(openmm.CMMotionRemover())
    
    logger_.info(f"Creating simulation")
    types = data.types
    simulation = data.make_simulation(config_.PLATFORM_NAME, config_.PLATFORM_PROPERTIES)
    
    logger_.info("Simulation created")
    
    return simulation, types
    
    

def mean_next(simulation: Simulation, steps: int) -> Tuple[np.ndarray, np.ndarray]:
    state = simulation.get_state()
    p = state.getPositions(asNumpy=True)
    v = state.getVelocities(asNumpy=True)
    u = t = 0
    positions = np.zeros_like(p)
    velocities = np.zeros_like(v)
    
    for _ in range(steps):
        state = simulation.step(1)
        positions = np.add(positions, p.value_in_unit(unit.angstrom))
        velocities = np.add(velocities, v.value_in_unit(unit.angstrom / unit.picosecond))
        u += state.getPotentialEnergy().value_in_unit(unit.elementary_charge * unit.volt / unit.mole)
        t += state.getKineticEnergy().value_in_unit(unit.elementary_charge * unit.volt / unit.mole)
        
    positions /= steps
    velocities /= steps
    u /= steps
    t /= steps
    
    return u, t, positions, velocities


def dump(u: float,
         t: float,
         positions: np.ndarray,
         velocities: np.ndarray,
         types: np.ndarray,
         cell,
         step: int):
    data = ovito.data.DataCollection()
    
    data_cell = ovito.data.SimulationCell(pbc=(True, True, True))
    data_cell[:, :3] = cell
    
    data.objects.append(data_cell)

    particles = ovito.data.Particles()
    particles.create_property("Position", data=positions)
    particles.create_property("Velocity", data=velocities)
    particles.create_property("Particle Type", data=types)
    
    data.objects.append(particles)

    ovito.io.export_file(
        data,
        config_.TRAJECTORY_PATH(step),
        "lammps/dump",
        columns=[
            "Particle Identifier",
            "Particle Type",
            "Position.X",
            "Position.Y",
            "Position.Z",
            "Velocity.X",
            "Velocity.Y",
            "Velocity.Z"
        ]
    )
    
    if not os.path.exists(config_.ENERGY_PATH):
        with open(config_.ENERGY_PATH, "w") as f:
            f.write("step,u,t,e\n")
            
    with open(config_.ENERGY_PATH, "a") as f:
        f.write(f"{step},{u},{t},{u+t}\n")


def run(config: Config, logger: Logger, sim_bar: tqdm, proc_bar: tqdm):
    global logger_, config_
    logger_= logger
    config_ = config
    
    simulation, types = create_simulation()
    
    saved_checkpoints = 0
    
    logger_.info("Starting simulation")
    for i in range(0, config_.RUN_STEPS, config_.AVERAGE_STEPS):
        # run
        u, t, positions, velocities = mean_next(simulation, config_.AVERAGE_STEPS)
        dump(u,
             t,
             positions,
             velocities,
             types,
             simulation.get_state().getPeriodicBoxVectors(asNumpy=True).value_in_unit(openmm.unit.angstrom),
             i)
        
        sim_bar.update(1)
        
        if i // config_.CHECKPOINT_STEPS >= saved_checkpoints:
            saved_checkpoints += 1
            with open(config_.CHECKPOINT_PATH(i), "wb") as f:
                f.write(simulation.context.createCheckpoint())
        
    sim_bar.close()
    proc_bar.close()
        
        # process
        
        # dump
        
        
        
        
    
"""
system = make_openmm_system(snap, forces=[force, obstacle, gravity])
integrator, context = make_openmm_context(snap, system, time_step=0.001*unit.picoseconds)

dump_enabled = True
steps_between_outputs = 1000
num_outputs = 1000
state = context.getState(getPositions=True, getVelocities=True, getEnergy=True)
for i in range(num_outputs):
    t1 = time.time()
    thr = threading.Thread(target=integrator.step, args=(steps_between_outputs,))
    thr.start()

    openmm_print_logs(i, snap.count, state)

    if dump_enabled:
        openmm_dump(i, snap.data, state, "data/dump{}.dump")
        t2 = time.time()
        print("dumping: " + "{:.3f}".format(t2 - t1) + "s")
        thr.join()
        state = context.getState(getPositions=True, getVelocities=True, getEnergy=True)
        t3 = time.time()
        print("syncing: " + "{:.3f}".format(t3 - t2) + "s")
        if (t2 - t1) > (t3 - t2):
            print("WARNING: Risky timing! Maybe, increase step?")
    else:
        thr.join()
        state = context.getState(getEnergy=True)
"""
