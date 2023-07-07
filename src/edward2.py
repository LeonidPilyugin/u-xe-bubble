from concurrent.futures import ThreadPoolExecutor

import openmm
import openmm.unit as unit

import ovito.io
import ovito.data

import os

import numpy as np

class SimulationData:
    def __init__(self):
        self.forces = []

    def read_ovito(self, filename, length_units=unit.angstroms, time_units=unit.picoseconds, mass_units=unit.atom_mass_units):
        velocity_units = length_units / time_units

        data = ovito.io.import_file(filename, sort_particles=True).compute()

        self.set_cell(data.cell[:, :3] * length_units)
        self.set_pos(data.particles.positions[...] * length_units)
        self.set_vel(data.particles.velocities[...] * velocity_units)

        self.masses = data.particles.masses[...] * mass_units
        self.types = data.particles.particle_types[...]

    def set_cell(self, cell):
        self.cell = cell
    
    def set_pos(self, pos):
        if hasattr(self, "count"):
            assert self.count == len(pos)

        self.positions = pos
        self.count = len(pos)

    def set_vel(self, vel):
        if hasattr(self, "count"):
            assert self.count == len(vel)

        self.velocities = vel
        self.count = len(vel)

    def set_temp(self, temp):
        self.temperature = temp

    def set_mass(self, mass):
        assert not hasattr(self, "masses")

        self.mass = mass

    def set_integrator(self, integrator):
        assert not hasattr(self, "integrator")

        self.integrator = integrator

    def add_force(self, force):
        self.forces.append(force)

    def add_lj_force(self, sigma, epsilon, cutoff):
        force = openmm.CustomNonbondedForce(
            "4*{epsilon}*(({sigma}/r)^12-({sigma}/r)^6)".format(
                epsilon=epsilon.value_in_unit(unit.kilojoule_per_mole),
                sigma=sigma.value_in_unit(unit.nanometer)
            )
        )
        force.setNonbondedMethod(openmm.CustomNonbondedForce.CutoffPeriodic)
        force.setCutoffDistance(cutoff)
        for _ in range(self.count):
            force.addParticle([])
        self.add_force(force)

    def make_simulation(self, platform, properties):
        try:
            loaded_platform = openmm.Platform.getPlatformByName(platform)
        except openmm.OpenMMException:
            print("Loaded plugins: ", openmm.pluginLoadedLibNames)
            print("Loading errors: ", openmm.Platform.getPluginLoadFailures())
            raise

        system = openmm.System()
        system.setDefaultPeriodicBoxVectors(self.cell[0], self.cell[1], self.cell[2])
        if hasattr(self, "mass"):
            for _ in range(self.count):
                system.addParticle(self.mass)
        else:
            assert hasattr(self, "masses")
            for mass in self.masses:
                system.addParticle(mass)

        for force in self.forces:
            system.addForce(force)
                
        context = openmm.Context(system, self.integrator, loaded_platform, properties)
        
        context.setPositions(self.positions)
        if hasattr(self, 'velocities'):
            context.setVelocities(self.velocities)
        else:
            assert hasattr(self, 'temperature')
            context.setVelocitiesToTemperature(self.temperature)

        simulation = Simulation(context=context, integrator=self.integrator)
        self.set_tainted(True)
        return simulation

    def set_tainted(self, tainted):
        self.tainted = tainted

    def __getattribute__(self, name):
        try:
            if super().__getattribute__('tainted') and name != 'set_tainted':
                raise RuntimeError("Access to a tainted SimulationData")
        except AttributeError:
            pass
        return super().__getattribute__(name)


class Simulation:
    def __init__(self, context, integrator):
        self.context = context
        self.integrator = integrator
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.running = False

        self.get_state_flags = {'getPositions': True,
                                'getVelocities': True,
                                'enforcePeriodicBox': True,
                                'getForces': True,
                                'getEnergy': True,
                               }

    def get_state(self) -> openmm.State:
        assert not self.running
        return self.context.getState(**self.get_state_flags)

    def step(self, steps):
        assert not self.running
        self.running = True
        self.integrator.step(steps)
        self.running = False
        return self.get_state()

    def step_async(self, steps):
        return self.executor.submit(self.step, (steps))
    
    def dump_ovito(self, state, filename):
        data = ovito.data.DataCollection()

        cell = state.getPeriodicBoxVectors(asNumpy=True).value_in_unit(unit.angstrom)
        positions = state.getPositions(asNumpy=True).value_in_unit(unit.angstrom)
        velocities = state.getVelocities(asNumpy=True).value_in_unit(unit.angstrom / unit.picosecond)

        data_cell = ovito.data.SimulationCell(pbc=(True, True, True))
        data_cell[:, :3] = cell

        data.objects.append(data_cell)

        particles = ovito.data.Particles()
        particles.create_property('Position', data=positions)
        particles.create_property('Velocity', data=velocities)
        particles.create_property('Particle Type', data=types)

        data.objects.append(particles)

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        ovito.io.export_file(
            data,
            filename,
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
        
        
    def mean_next(self, steps, create_checkpoint = False):
        """Means"""
        
        state = self.get_state()
        
        p = state.getPositions(asNumpy=True)
        v = state.getVelocities(asNumpy=True)
        u = t = 0
        positions = np.zeros_like(p)
        velocities = np.zeros_like(v)

        for _ in range(steps):
            # run 1 step
            state = self.step(1)
            p = state.getPositions(asNumpy=True)
            v = state.getVelocities(asNumpy=True)
            # add parameters to created variables
            positions = np.add(positions, p.value_in_unit(unit.angstrom))
            velocities = np.add(velocities, v.value_in_unit(unit.angstrom / unit.picosecond))
            u += state.getPotentialEnergy().value_in_unit(unit.elementary_charge * unit.volt / unit.mole)
            t += state.getKineticEnergy().value_in_unit(unit.elementary_charge * unit.volt / unit.mole)
        
        # mean parameters
        positions /= steps
        velocities /= steps
        u /= steps
        t /= steps
        
        checkpoint = self.context.createCheckpoint() if create_checkpoint else None
        
        return u, t, positions, velocities, state, checkpoint


    def mean_next_async(self, steps, checkpoint = False):
        return self.executor.submit(self.mean_next, steps, checkpoint)
    
    