import os
import pandas as pd
import numpy as np
import openmm as mm
from tqdm import tqdm
import subprocess
from openmm import unit as un
from ovito import data as odata
from ovito import io as oio
from edward2 import SimulationData
from edward2 import Simulation
import importlib.util as iu

_types: np.ndarray = None
_simulation: Simulation = None


def init(**data):
    global _types, _simulation
    
    # simulation data
    simulation_data = SimulationData()
    
    # load configuration
    simulation_data.read_ovito(data["configuration"])
    
    # load integrator
    openmm_module = __import__("openmm")
    integrator_class = getattr(openmm_module, data["integrator"]["type"])
    # create integrator
    integrator = integrator_class(*data["integrator"]["arguments"])
    # set integrator
    simulation_data.set_integrator(integrator)
    
    # create forces
    for force in data["forces"]:
        force_type = list(force.keys())[0]
        parameters = force[force_type]
        
        if force_type == "Potential":
            # load force
            with open(parameters["potential_path"], "r") as file_force:
                force = mm.XmlSerializer.deserialize(file_force.read())
            # add particles
            for i in range(simulation_data.count):
                force.addParticle([parameters["particle_types"][simulation_data.types[i]]])
        else:
            # create force
            force_class = getattr(openmm_module, force_type)
            force = force_class(**parameters)
        
        simulation_data.add_force(force)
    
    # modify HIP properties
    if data["platform_name"] == "HIP":
        os.environ["HIP_VISIBLE_DEVICES"] = data["platform_properties"]["DeviceIndex"]
        data["platform_properties"]["DeviceIndex"] = "0"
    
    # save types
    _types = simulation_data.types
    # save simulation
    _simulation = simulation_data.make_simulation(data["platform_name"], data["platform_properties"])
    
    # load checkpoint if necessary
    if data["checkpoint"] is not None:
        with open(data["checkpoint"], "b+r") as f:
            _simulation.context.loadCheckpoint(f.read())
            

def dump(therm,
         positions: np.ndarray,
         velocities: np.ndarray,
         u: float,
         t: float,
         P: float,
         T: float,
         step: int,
         cell,
         **data):
    """Writes dumps of energies and positions"""
    
    therm.write(f"{step},{u},{t},{P},{T}\n")
    therm.flush()
    
    data_collection = odata.DataCollection()
    
    # get cell
    data_cell = odata.SimulationCell(pbc=(True, True, True))
    data_cell[:, :3] = cell

    # set cell
    data_collection.objects.append(data_cell)

    # set positions, velocities and types
    particles = odata.Particles()
    particles.create_property("Position", data=positions)
    particles.create_property("Velocity", data=velocities)
    particles.create_property("Particle Type", data=_types)
    
    # add data to data object
    data_collection.objects.append(particles)

    # export
    oio.export_file(
        data_collection,
        data["trajectory_template"].format(i=step),
        "lammps/dump",
        columns=[
            "Particle Identifier",
            "Particle Type",
            "Position.X",
            "Position.Y",
            "Position.Z",
            "Velocity.X",
            "Velocity.Y",
            "Velocity.Z",
        ]
    )
    
    return data_collection
    
    
def load_analyzing_script(path, function):
    # load module
    spec = iu.spec_from_file_location(
        "analysis", path
    )
    module = iu.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # get entry points
    return getattr(module, function)
    
    
def simulate(**data):
    # helping variables
    saved_checkpoints = 0
    iter_steps = data["average_steps"] + data["skip_steps"]
    
    if not data["analyzing_script"] is None:
        log = open(data["logfile"], "w")
        analize = subprocess.Popen(f"python {data['analyzing_script']}", shell=True, stdout=log, stderr=log)
    
    with open(data["thermo"], "w") as f:
        f.write("step,u,t,P,T\n")
        for i in tqdm(range(0, data["run_steps"] // iter_steps)):
            # get data
            result = _simulation.mean_next(data["average_steps"])
            
            # split result
            u, t, P, T, p, v, s = result
            # dump
            dump(f, p, v, u, t, P, T, i * iter_steps, s.getPeriodicBoxVectors(asNumpy=True).value_in_unit(un.angstrom), **data)
            
            # skip dumps
            if data["skip_steps"] > 0:
                _simulation.step(data["skip_steps"])
            
            # save checkpoint
            if data["checkpoint_steps"] > 0 and (i + 1) * iter_steps // data["checkpoint_steps"] >= saved_checkpoints:
                with open(data["checkpoint_template"].format(i=(i + 1) * iter_steps), "wb") as ff:
                    ff.write(_simulation.context.createCheckpoint())
                saved_checkpoints += 1

    with open(data["checkpoint_template"].format(i=(i + 1) * iter_steps), "wb") as f:
        f.write(_simulation.context.createCheckpoint())
        
    if not data["analyzing_script"] is None:
        with open(data["trajectory_template"].format(i=data["run_steps"]), "w") as f:
            f.write("")

        analize.wait()
        log.close()
    
