import subprocess


def main(**data):
    # save file
    with open(data["script_save"], "w") as write, open(data["script"]) as read:
        write.write(read.read().format(**data["variables"]))
         
    # run LAMMPS
    subprocess.call(f"{data['executable']} -in {data['script_save']} -log {data['log']} -screen none".split())
    
    