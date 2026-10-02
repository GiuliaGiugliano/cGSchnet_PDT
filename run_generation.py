import os
import subprocess

base_dir = "/data/horse/ws/gigi895h-QM9_gen_alpha/generative_project_less"

# Supponendo che le cartelle siano nomi generation_1, generation_2, ..., generation_N
n_jobs = 24  # sostituisci col numero esatto di cartelle

for i in range(1, n_jobs + 1):
    job_dir = os.path.join(base_dir, f"generation_{i}")
    slurm_script = os.path.join(job_dir, f"generation.slurm")
    if os.path.exists(slurm_script):
        print(f"Submitting job {i} from {slurm_script}")
        subprocess.run(["sbatch", slurm_script], cwd=job_dir)
    else:
        print(f"Warning: {slurm_script} not found!")

