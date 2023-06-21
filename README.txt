# u-xe-bubble
Simulation of a xenon nanobubble in uranium lattice

Running this file starts all simulations from config list and their analysis.

Example:
    $ python3 main.py

This creates directory result in project root if it not exists
The structure of result directory is:

result
├── config1
│   ├── analysis
│   │   ├── analysis_result_0
│   │   :
│   │
│   ├── checkpoints
│   │   ├── 0.checkpoint
│   │   :
│   │
│   ├── configuration
│   │   ├── configuration.atom
│   │   └── reference.atom
│   │
│   ├── log
│   │   ├── analysis.log
│   │   ├── lammps.log
│   │   └── main.log
│   │
│   ├── thermo
│   │   └── energy.csv
│   │
│   ├── trajectory
│   │   ├── 0.trj
│   │   :
│   │
│   └── config.txt
│
├── config2
:   :

Every simulation has it's own subdirectory in result.

In this directory there is config.txt file and some directories:

1) analysis directory contains analysis results

2) checkpoints directory contains OpenMM checkpoints

3) configuration directory contains two files:
  3.1) configuration.atom file is initial configuration system
  3.2) creference.atom file is reference system for Wigner-Seitz analysis

4) log directory contains three files:
  4.1) analysis.log file contains logs of analysis process
  4.2) lammps.log file contains LAMMPS logs
  4.3) main.log file contains logs of simualtion and system creation processes

5) thermo directory contains one file:
  5.1) energy.csv is a csv file of energies.
       It's header:
       step,u,t,e

       where:
       step -- number of md step
       u    -- potential energy
       t    -- kinetic energy
       e    -- total energy

       Energies are given in eV/mole units

6) trajectory directory contains


