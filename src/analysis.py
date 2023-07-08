from os import path
from logging import Logger
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from ovito import modifiers as mod
from ovito import pipeline as pln
from ovito import data
from config import Config

config_: Config = None
logger_: Logger = None

pb_: mod.WrapPeriodicImagesModifier = None
ws_: mod.WignerSeitzAnalysisModifier = None
es1_: mod.ExpressionSelectionModifier = None
es2_: mod.ExpressionSelectionModifier = None
ca_: mod.ClusterAnalysisModifier = None
vacancy_counts_ = []
interstitial_counts_ = []
clusters_ = []
potential_energies_ = []
kinetic_energies_ = []
steps_ = []
defects_: pd.DataFrame = None
thermo_: pd.DataFrame = None

def compute(data: data.DataCollection):
    # run pipeline
    data.apply(pb_)
    data.apply(ws_)
    data.apply(es1_)
    data.apply(ca_)
    data.apply(es2_)
    
    # save cluster data
    cluster_table = data.tables["clusters"]
    clusters_.append(tuple(zip(
        cluster_table["Cluster Identifier"][...],
        cluster_table["Cluster Size"][...],
        cluster_table["Center of Mass"][...],
    )))
    
    # save defects data
    vacancy_counts_.append(data.attributes["ExpressionSelection.count"])
    interstitial_counts_.append(data.attributes["ExpressionSelection.count.2"])


def setup():
    # set config
    global pb_, ws_, es1_, es2_, ca_
    
    # set periodic bounds wrapper modifier
    pb_ = mod.WrapPeriodicImagesModifier()
    
    # set Weigner-Seitz modifier
    ws_ = mod.WignerSeitzAnalysisModifier()
    ws_.reference = pln.FileSource()
    ws_.reference.load(config_.REFERENCE_PATH)
    ws_.affine_mapping = pln.ReferenceConfigurationModifier.AffineMapping.ToReference
    ws_.per_type_occupancies = True

    # set cluster analysis modifier
    es1_ = mod.ExpressionSelectionModifier(expression="Occupancy.1 < 1")
    es2_ = mod.ExpressionSelectionModifier(expression="Occupancy.1 > 1")
    ca_ = mod.ClusterAnalysisModifier(
        compute_com=True,
        only_selected=True,
        sort_by_size=True,
    )
    
    
def save():
    global defects_, thermo_, clusters_
    
    # save defects
    defects_ = pd.DataFrame(
        zip(steps_, vacancy_counts_, interstitial_counts_),
        columns=["step", "vacancies", "interstitials"]
    )
    
    defects_.to_csv(path.join(config_.ANALYSIS_DIR, "defects.csv"))
    
    # save clusters
    temp = []
    for s, c in zip(steps_, clusters_):
        for cl in c:
            temp.append((s, cl[0], cl[1], *tuple(cl[2])))
            
    clusters_ = pd.DataFrame(
        temp,
        columns=["step", "cluster id", "size", "x", "y", "z"]
    )
    
    clusters_.to_csv(path.join(config_.ANALYSIS_DIR, "clusters.csv"))
    
    # save thermo
    thermo_ = pd.DataFrame(
        zip(steps_, potential_energies_, kinetic_energies_),
        columns=["step", "potential energy", "kinetic energy"]
    )
    thermo_["total energy"] = thermo_["potential energy"] + thermo_["kinetic energy"]
    
    thermo_.to_csv(path.join(config_.ANALYSIS_DIR, "thermo.csv"))


def plot():
    # aply style
    matplotlib.use('Agg')
    plt.style.use("https://raw.githubusercontent.com/LeonidPilyugin/mpl-style/main/simple.mplstyle")
    
    # plot all vacancies
    plt.plot(steps_, vacancy_counts_)
    plt.xlabel("Step")
    plt.ylabel("Vacancies")
    plt.title("Vacancies")
    plt.savefig(path.join(config_.ANALYSIS_DIR, "vacancies.png"))
    plt.cla()
    
    # plot all interstitials
    plt.plot(steps_, interstitial_counts_)
    plt.xlabel("Step")
    plt.ylabel("Interstitials")
    plt.title("Interstitials")
    plt.savefig(path.join(config_.ANALYSIS_DIR, "interstitials.png"))
    plt.cla()
    
    # plot energies
    plt.plot(steps_, thermo_["potential energy"], label="potential")
    plt.plot(steps_, thermo_["kinetic energy"], label="kinetic")
    plt.plot(steps_, thermo_["total energy"], label="total")
    plt.xlabel("Step")
    plt.ylabel("Energy, eV/mole")
    plt.title("Energy")
    plt.legend()
    plt.savefig(path.join(config_.ANALYSIS_DIR, "energy.png"))
    plt.cla()
    
    # choose largest cluster
    cluster = clusters_[clusters_["cluster id"] == 1]
    cluster.index = range(len(cluster.index))
    
    # plot vacancies outside bubble
    plt.plot(steps_, defects_["vacancies"] - cluster["size"])
    plt.xlabel("Step")
    plt.ylabel("Non-bubble vacancie")
    plt.title("Non-bubble vacancies")
    plt.savefig(path.join(config_.ANALYSIS_DIR, "nonbubblevacancies.png"))
    plt.cla()
    
    # plot bubble size
    plt.plot(steps_, cluster["size"])
    plt.xlabel("Step")
    plt.ylabel("Size")
    plt.title("Size of cluster")
    plt.savefig(path.join(config_.ANALYSIS_DIR, "size.png"))
    plt.cla()
    
    # plot x coordinate
    plt.plot(steps_, cluster["x"])
    plt.xlabel("Step")
    plt.ylabel("x")
    plt.title("x")
    plt.savefig(path.join(config_.ANALYSIS_DIR, "x.png"))
    plt.cla()
    
    # plot y coordinate
    plt.plot(steps_, cluster["y"])
    plt.xlabel("Step")
    plt.ylabel("y")
    plt.title("y")
    plt.savefig(path.join(config_.ANALYSIS_DIR, "y.png"))
    plt.cla()
    
    # plot z coordinate
    plt.plot(steps_, cluster["z"])
    plt.xlabel("Step")
    plt.ylabel("z")
    plt.title("z")
    plt.savefig(path.join(config_.ANALYSIS_DIR, "z.png"))
    plt.cla()


def analize(config: Config, logger: Logger, data, u, t, step):
    """Processes frame"""
    global logger_, config_
    logger_ = logger
    config_ = config
    
    potential_energies_.append(u)
    kinetic_energies_.append(t)
    steps_.append(step)
    
    if ws_ is None:
        setup()
    
    compute(data)
        

def final_analyze():
    save()
    plot()
