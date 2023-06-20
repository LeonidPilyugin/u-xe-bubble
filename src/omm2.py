#!/usr/bin/python3

import time
import numpy as np
t0 = time.time()

import simtk.openmm as openmm
import simtk.openmm.app as app
import simtk.unit as unit

import ovito.io
import ovito.data
import ovito.pipeline

################################# PROPERTIES INITIALIZATION #######################################
FILE_INPUT = "testing/lattices_generated/Fe_8000k.lmp"
FILE_FORCE = "testing/potentials_generated/Fe_gb.xml"

# current implementation only allows for dumping into separate files
DUMP_ENABLED = False
DUMP_PREFIX = "gigadump4/omm."
DUMP_POSTFIX = ".custom"

TIME_STEP = 0.001 * unit.picoseconds
STEPS_BETWEEN_OUTPUTS = 1
OUTPUTS_AMOUNT = 1

PLATFORM_NAME = "CUDA"
PLATFORM_PROPERTIES = {"Precision" : "mixed"}

# particle masses and velocities may or may not be provided in input
# and in case of the latter we need some default values to roll back to
DEFAULT_PARTICLE_MASSES = [55.85]
DEFAULT_TEMPERATURE = 300 * unit.kelvins

# multi-type systems require particle type to be loaded as a per-particle parameter
LOAD_TYPES = False

# usually, angstroms are used as length units and picoseconds as time units
# but that might very well not be the case in input files
INPUT_LENGTH_UNITS = unit.angstroms
INPUT_TIME_UNITS = unit.picoseconds
INPUT_VELOCITY_UNITS = INPUT_LENGTH_UNITS / INPUT_TIME_UNITS

################################# OVITO IMPORT ####################################################
print("Importing system from " + FILE_INPUT)
# we use ovito to read the starting configuration
data = ovito.io.import_file(FILE_INPUT, sort_particles=True).compute()

cell = data.cell[0:3, 0:3] * INPUT_LENGTH_UNITS
positions = data.particles.positions[...] * INPUT_LENGTH_UNITS

count = data.particles.count
types = data.particles.particle_types
 
# system needs to know particle masses,
# so if those aren't provided in input, we have to set them manually
for particle_type in data.particles_.particle_types_.types:
    if particle_type.mass == 0:
        particle_type.mass = DEFAULT_PARTICLE_MASSES[particle_type.id - 1]
        print(
            "WARNING: No mass loaded for element \"" + str(particle_type.id) +
            "\". Defaulting to \"" + str(particle_type.mass) + "\".")

print("System imported")

################################# XML INPORT & SYSTEM GENERATION #############################################
print("Importing force from " + FILE_FORCE)
with open(FILE_FORCE, "r") as file_force:
    force = openmm.XmlSerializer.deserialize(file_force.read())
print("Force imported")

print("Adding particles..")
system = openmm.System()
system.setDefaultPeriodicBoxVectors(cell[0], cell[1], cell[2])

#force.addParticles(data.particles.particle_types[...])
#force.addParticles(np.array([[1],[1],[1]]))
#system.addParticles(data.particles.masses[...])

#pregenerating masses to save time
masses = [
    types.type_by_id(i + 1).mass
    for i in range(len(types.types))
]
if LOAD_TYPES:
    for i in range(count):
        system.addParticle(masses[types[i] - 1])
        force.addParticle([types[i] - 1])
else:
    for i in range(count):
        system.addParticle(masses[types[i] - 1])
        force.addParticle()

print("Particles added")

system.addForce(force)
print("Force added to system")

################################# CONTEXT INITIALIZATION ########################################
print("Creating context..")
integrator = openmm.VerletIntegrator(TIME_STEP)
platform = openmm.Platform.getPlatformByName(PLATFORM_NAME)
context = openmm.Context(system, integrator, platform, PLATFORM_PROPERTIES)

print("Setting positions..")
context.setPositions(positions)

print("Setting velocities..")
if "Velocity" in data.particles:
    context.setVelocities(
        data.particles.velocities[...] * INPUT_VELOCITY_UNITS)
else:
    print("WARNING: No velocities loaded. Defaulting to " + str(DEFAULT_TEMPERATURE))
    context.setVelocitiesToTemperature(DEFAULT_TEMPERATURE)

# now the simulation is ready to go
print("Simulation set up")
print("Initialization took " + "{:.3f}".format(time.time() - t0) + "s")

################################# FORCES DUMP #####################################################
forces=context.getState(getForces=True).getForces() / unit.AVOGADRO_CONSTANT_NA
forces=forces.value_in_unit(unit.elementary_charge * unit.volt / unit.angstrom)
print("Forces calculated")

if not "Force" in data.particles:
    data.particles_.create_property("Force", data=forces)
else:
    data.particles_.forces_[...] = forces

ovito.io.export_file(
    data,
    "omm.force",
    "lammps/dump",
    columns=[
        "Particle Identifier",
        "Force.X",
        "Force.Y",
        "Force.Z"
    ]
)
################################# SIMULATION ######################################################

if DUMP_ENABLED:
    state = context.getState(getPositions=True, getVelocities=True, getEnergy=True)

    # to be able to export velocity we need to ensure its PropertyContainer exists
    if not "Velocity" in data.particles:
        data.particles_.create_property(
            "Velocity",
            data=state.getVelocities().value_in_unit(INPUT_VELOCITY_UNITS))

    def dump(i):
        data.particles_.positions_[...] = state.getPositions().value_in_unit(INPUT_LENGTH_UNITS)
        # data.particles_.velocities_[...] = state.getVelocities().value_in_unit(INPUT_VELOCITY_UNITS)
        ovito.io.export_file(
            data,
            DUMP_PREFIX + str(i) + DUMP_POSTFIX,
            "lammps/dump",
            columns=[
                "Particle Identifier",
                "Particle Type",
                "Position.X",
                "Position.Y",
                "Position.Z"])

for i in range(OUTPUTS_AMOUNT):
    t1 = time.time()
    integrator.step(STEPS_BETWEEN_OUTPUTS)

    if DUMP_ENABLED:
        dump(i)
        t2 = time.time()
        state = context.getState(getPositions=True, getVelocities=True, getEnergy=True)
        print("sync: " + "{:.3f}".format(time.time() - t2) + "s")
    else:
        state = context.getState(getEnergy=True)

    energy = (state.getKineticEnergy() + state.getPotentialEnergy()) / unit.AVOGADRO_CONSTANT_NA
    print(
        "time: " + "{:.3f}".format(time.time() - t1) + "s " +
        "step: " + str(i + 1) + " " +
        "energy: " + "{:.1f}".format(energy.value_in_unit(unit.elementary_charge * unit.volt)) + "EV ")

if DUMP_ENABLED:
    dump(OUTPUTS_AMOUNT)
