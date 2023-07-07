import numpy as np
from os import path
from abc import ABC, abstractmethod
import matplotlib
import matplotlib.pyplot as plt
from ovito import modifiers as mod
from ovito import pipeline as pln
from ovito import data
from openmm import unit as un
from config import Config

matplotlib.use('Agg')
plt.style.use("https://raw.githubusercontent.com/LeonidPilyugin/mpl-style/main/simple.mplstyle")

class Parameter():
    """Describes an abstract parameter which should be detected, saved and ploted"""
    
    def setup(config: Config):
        pass
    
    def modify(frame: int, data: data.DataCollection):
        pass
        
    def save():
        pass
    
    def plot():
        pass
    
    
class MyWeignerSeitz(Parameter):
    
    def setup(config: Config):
        MyWeignerSeitz.config = config
        
        MyWeignerSeitz.ws = mod.WignerSeitzAnalysisModifier()
        MyWeignerSeitz.ws.reference = pln.FileSource()
        MyWeignerSeitz.ws.reference.load(MyWeignerSeitz.config.REFERENCE_PATH)
        MyWeignerSeitz.ws.affine_mapping = pln.ReferenceConfigurationModifier.AffineMapping.ToReference
        MyWeignerSeitz.ws.per_type_occupancies = True
        
        MyWeignerSeitz.vacancy_counts = []
        MyWeignerSeitz.interstitial_counts = []
        
    
    def modify(frame: int, data: data.DataCollection):
        data.apply(MyWeignerSeitz.ws)
        MyWeignerSeitz.vacancy_counts.append(data.attributes["WignerSeitz.vacancy_count"])
        MyWeignerSeitz.interstitial_counts.append(data.attributes["WignerSeitz.interstitial_count"])
        
        
    def save():
        filepath = path.join(MyWeignerSeitz.config.ANALYSIS_DIR, "deffects.csv")
        
        with open(filepath, "w") as f:
            f.write(f"step,vacancies,interstitials\n")
            
            for step, (v, i) in enumerate(zip(MyWeignerSeitz.vacancy_counts, MyWeignerSeitz.interstitial_counts)):
                f.write(f"{step * (MyWeignerSeitz.config.AVERAGE_STEPS + MyWeignerSeitz.config.SKIP_STEPS)},{v},{i}\n")
    
    
    def plot():
        steps = [i * (MyWeignerSeitz.config.AVERAGE_STEPS + MyWeignerSeitz.config.SKIP_STEPS) for i in range(len(MyWeignerSeitz.vacancy_counts))]
        
        plt.plot(steps, MyWeignerSeitz.vacancy_counts)
        plt.xlabel("Step")
        plt.ylabel("Vacancies")
        plt.title("Vacancies")
        plt.savefig(path.join(MyWeignerSeitz.config.ANALYSIS_DIR, "vacancies.png"))
        plt.cla()
        
        plt.plot(steps, MyWeignerSeitz.interstitial_counts)
        plt.xlabel("Step")
        plt.ylabel("Interstitials")
        plt.title("Interstitials")
        plt.savefig(path.join(MyWeignerSeitz.config.ANALYSIS_DIR, "interstitials.png"))
        plt.cla()
    
    
class MyClusterAnalysis(Parameter):
    
    def setup(config: Config):
        MyClusterAnalysis.config = config
        
        MyClusterAnalysis.es = mod.ExpressionSelectionModifier(expression="Occupancy.1 < 1")
        MyClusterAnalysis.ca = mod.ClusterAnalysisModifier(
            compute_com=True,
            only_selected=True,
            sort_by_size=True,
        )
        
        MyClusterAnalysis.clusters = []
        
        
        
    def modify(frame: int, data: data.DataCollection):
        data.apply(MyClusterAnalysis.es)
        data.apply(MyClusterAnalysis.ca)
        
        cluster_table = data.tables["clusters"]
        
        MyClusterAnalysis.clusters.append((tuple(zip(
            cluster_table["Cluster Identifier"][...],
            cluster_table["Cluster Size"][...],
            cluster_table["Center of Mass"][...],
        ))))
        
        
    def save():
        filepath = path.join(MyClusterAnalysis.config.ANALYSIS_DIR, "clusters.csv")
        
        with open(filepath, "w") as f:
            f.write(f"step,cluster,size,x,y,z\n")
            
            for step, clusters in enumerate(MyClusterAnalysis.clusters):
                for c in clusters:
                    f.write(f"{step * (MyClusterAnalysis.config.AVERAGE_STEPS + MyClusterAnalysis.config.SKIP_STEPS)},{c[0]},{c[1]},{c[2][0]},{c[2][1]},{c[2][2]}\n")
                    
                    
    def plot():
        steps = [i * (MyClusterAnalysis.config.AVERAGE_STEPS + MyClusterAnalysis.config.SKIP_STEPS) for i in range(len(MyClusterAnalysis.clusters))]

        sizes = [c[0][1] for c in MyClusterAnalysis.clusters]
        x = [c[0][2][0] for c in MyClusterAnalysis.clusters]
        y = [c[0][2][1] for c in MyClusterAnalysis.clusters]
        z = [c[0][2][2] for c in MyClusterAnalysis.clusters]
        
        plt.plot(steps, sizes)
        plt.xlabel("Step")
        plt.ylabel("Size")
        plt.title("Size of cluster")
        plt.savefig(path.join(MyClusterAnalysis.config.ANALYSIS_DIR, "size.png"))
        plt.cla()
        
        plt.plot(steps, x)
        plt.xlabel("Step")
        plt.ylabel("x")
        plt.title("x")
        plt.savefig(path.join(MyClusterAnalysis.config.ANALYSIS_DIR, "x.png"))
        plt.cla()
        
        plt.plot(steps, y)
        plt.xlabel("Step")
        plt.ylabel("y")
        plt.title("y")
        plt.savefig(path.join(MyClusterAnalysis.config.ANALYSIS_DIR, "y.png"))
        plt.cla()
        
        plt.plot(steps, z)
        plt.xlabel("Step")
        plt.ylabel("z")
        plt.title("z")
        plt.savefig(path.join(MyClusterAnalysis.config.ANALYSIS_DIR, "z.png"))
        plt.cla()
        