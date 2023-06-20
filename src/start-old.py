# 0) сделать то же самое для 1400, 500 нс
# 1) поменять часть создания системы
# 2) поменять логику симуляции (поэкспериментировать с числом шагов в дамп) (дампер из главного потока)
# 3) обработку ovito перенести в питон


from simtk.openmm import app
import simtk.openmm as mm
import openmmtools as mmtools
from simtk import unit
from sys import stdout
#import read as rd
import pandas as pd
import numpy as np 
import  subprocess
import sys
import time

import ovito.io
import ovito.data
import ovito.pipeline

DevInd = str(sys.argv[1])
# dump_file = str(sys.argv[2])
T = 1400

CUTOFF_DISTANCE = 0.619610 * unit.nanometers
FILE_FORCE_FIELD = "./UMo.xml"
DEFAULT_PARTICLE_TYPES = ["U", "Xe"]
FILE_INPUT = sys.argv[2]

timestepint = 1 * unit.femtoseconds

runSteps = 500000000
stepsPDBTrj = 200000
stepsForParams = 200000

pathToSave = './'
#nameToRead = 'data.UO2-5x5x5'
nameToSaveTrj = sys.argv[3]
# nameToSaveParams = 'params_'+str(T)
saveCheckPoint = nameToSaveTrj+'.checkpoint'
file_output=open(nameToSaveTrj+".output", 'w')

platform = mm.Platform.getPlatformByName('HIP')
properties = {'DeviceIndex': DevInd, 'Precision': 'mixed'}

################################# OVITO IMPORT ####################################################
print("Importing system from " + FILE_INPUT)
# we use ovito to read the starting configuration
data = ovito.io.import_file(FILE_INPUT, sort_particles=True).compute()

cell = data.cell[0:3, 0:3] * unit.angstrom

positions = data.particles.positions[...] * unit.angstrom

print(positions)

count = data.particles.count
types = data.particles.particle_types
print("particles count:", count)
print ("particle types:", data.particles_.particle_types_.types)
# topology NEEDS to know particle elements,
# so if those aren't provided in input, we have to set them manually
for particle_type in data.particles_.particle_types_.types:
    if particle_type.name == "":
        particle_type.name = DEFAULT_PARTICLE_TYPES[particle_type.id - 1]
        print(
            "No name loaded for element \"" + str(particle_type.id) +
            "\". Defaulting to \"" + particle_type.name + "\".")

print("System imported")

################################# TOPOLOGY GENERATION #############################################
print("Generating topology..")
topology = app.Topology()
topology.setPeriodicBoxVectors(cell)

#pregenerating elements and names to save time
names = [
    types.type_by_id(i + 1).name
    for i in range(len(types.types))
]
elements = [
    app.element.get_by_symbol(names[i])
    for i in range(len(types.types))
]

#topology consists of chains, chains consist of residues, residues consist of atoms
chain = topology.addChain()
for i in range(count):
    # for each atom, a new residue is created
    # this terribleness is the price to pay for using the handy xml format
    topology.addAtom(
        names[types[i] - 1],
        elements[types[i] - 1],
        topology.addResidue(names[types[i] - 1], chain))

# the state can now be exported as PDB just like that:
# app.PDBFile.writeFile(topology, positions, open("omm.pdb", "w"), True)

print("Topology generated")

################################# XML IMPORT & Forces & APPLICATION ########################################
print("Importing force field from " + FILE_FORCE_FIELD)
force_field = app.ForceField(FILE_FORCE_FIELD)
print("Force field imported")

################################  APPLICATION1 ########################################
print("Creating system..")
# this is why cutoff distance needs to be set separately:
# it's not a property of a force field, it's apparently a property of a system
system = force_field.createSystem(topology, app.CutoffPeriodic, CUTOFF_DISTANCE)
# system = force_field.createSystem(topology, nonbondedMethod=app.CutoffPeriodic, nonbondedCutoff=CUTOFF_DISTANCE, rigidWater=False, ewaldErrorTolerence=1e-5,removeCMMotion=False)

nvt = mm.LangevinIntegrator(T*unit.kelvin, 0.1/unit.picosecond, timestepint)
nve = mm.VerletIntegrator(timestepint)

################################  APPLICATION2 ########################################

system.addForce(mm.CMMotionRemover())

print("Setting up simulation..")
simulation = app.Simulation(
    topology,
    system,
    nve,
    platform)
    #,properties)

print("Setting positions..")
simulation.context.setPositions(positions)

print("Setting velocities..")
simulation.context.setVelocitiesToTemperature(T*unit.kelvin)


# now the simulation is ready to go
print("Simulation set up")  

#forces = (simulation.context.getState(getForces=True).getForces(asNumpy=True) / unit.AVOGADRO_CONSTANT_NA).value_in_unit(unit.elementary_charge * unit.volt / unit.angstrom)
#pd.DataFrame({'xs': forces[:, 0], 'ys': forces[:, 1], 'zs': forces[:, 2]}).to_csv("forces15.csv", index=False)


# exit(0)

####################################  SIMULATION ##############################################################

print("Simulation 1 ...")
simulation.reporters.append(app.StateDataReporter(file_output, stepsForParams, step=True, kineticEnergy=True, potentialEnergy=True, totalEnergy=True, volume=False, density=True, temperature=True, time=False, speed=True, separator=' | '))

simulation.reporters.append(app.PDBReporter(nameToSaveTrj, stepsPDBTrj))

t1 = time.time()
simulation.step(runSteps)
#print(simulation.context.getState().getPositions())
print(runSteps, 'steps')
print('calculation time:', time.time() - t1)
file_output.close()

simulation.saveState(saveCheckPoint)


