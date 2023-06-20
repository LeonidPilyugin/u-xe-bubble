from edward2 import Simulation, SimulationData
import openmm
import openmm.unit as unit
import numpy as np
import itertools
from tqdm import tqdm

def get_positions(size, rho) -> np.ndarray:
    volume = np.prod(size)
    n_particles = np.floor(volume * rho)
    volume_per_particle = volume / n_particles
    grid_step = volume_per_particle ** (1/3)

    positions = np.empty(
        tuple(
            (np.ceil(
                    side_length / grid_step
                )
            ).astype(int) + 2 for side_length in size
        ) + (3,)
    )

    grid_step = np.array(size) / np.array(positions.shape[:3])
    for idx in itertools.product(*[range(l) for l in positions.shape[:3]]):
        positions[idx] = np.array(idx) * grid_step

    # positions += (np.random.rand(*positions.shape) - 0.5) * grid_step / 1.5
    positions = positions[1:-1, 1:-1, 1:-1].reshape(-1, 3)

    return positions

T = 0.4 / (8.314/1000) * unit.kelvin
box = np.array([500, 200, 10]) * unit.nanometer
rho = 0.3 * unit.nanometer ** -3
dt = 0.001 * unit.picosecond
vflow = 0.7 * unit.nanometer / unit.picosecond

m = 1 * unit.dalton
sigma = 1 * unit.nanometer
epsilon = 1 * unit.kilojoule_per_mole
cutoff = 2 ** (1/6) * unit.nanometer

data = SimulationData()
data.set_cell(np.diag(box))
data.set_pos(get_positions(box, rho))
data.set_mass(1 * unit.dalton)
data.set_temp(T)
data.set_integrator(openmm.VerletIntegrator(dt))
data.add_lj_force(sigma=sigma, epsilon=epsilon, cutoff=cutoff)
data.add_force(openmm.OpenBoundary(T, vflow, 'x', {0.92, 0.94, 0.96, 0.98}))
simulation = data.make_simulation("CUDA", {"Precision": "mixed"})

filename_mask = "test_dumps/dump{ind}.dump"

state = simulation.get_state()
for i in tqdm(range(100)):
    future = simulation.step_async(100)
    simulation.dump_ovito(state, filename_mask.format(ind=i))
    state = future.result()

simulation.dump_ovito(state, filename_mask.format(ind=i+1))
