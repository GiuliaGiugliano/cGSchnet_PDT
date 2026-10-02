import os

excitation_energy_vals = [1.8, 2.1, 2.5]
gap_vals = [2.0, 3.0]
fosc_vals = [0.5, 1.0]
soc_vals = [0.00006, 0.0001]  # valori in notazione decimale fissa
relative_atomic_energy_val = -0.005

template_slurm = """#!/bin/bash
#SBATCH --job-name=xmace_gpu
#SBATCH --partition=capella
#SBATCH --account=p_brighten
#SBATCH --time=48:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=6
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --licenses horse

module purge
module load release/24.10
module load GCC/13.2.0 OpenMPI/4.1.6
module load Anaconda3
source $EBROOTANACONDA3/etc/profile.d/conda.sh
conda activate /home/gigi895h/gschnet2-env

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OPENBLAS_NUM_THREADS=$SLURM_CPUS_PER_TASK

mkdir -p /data/horse/ws/gigi895h-QM9_gen_alpha/generative_project_less/generation_{counter}/generated_molecules

gschnet_generate modeldir=/data/horse/ws/gigi895h-QM9_gen_alpha/generative_project/models/multicond_experiment/2035167_i8035 n_molecules=1000 batch_size=500 max_n_atoms=280 ++conditions.excitation_energy={excitation_energy} ++conditions.gap={gap} ++conditions.fosc={fosc} ++conditions.soc={soc} ++conditions.relative_atomic_energy={relative_atomic_energy} outputfile=/data/horse/ws/gigi895h-QM9_gen_alpha/generative_project_less/generation_{counter}/generated_molecules/structures_{counter}.db
"""

counter = 1
for exc in excitation_energy_vals:
    for gap in gap_vals:
        for fosc in fosc_vals:
            for soc in soc_vals:
                dirname = f"generation_{counter}"
                os.makedirs(dirname, exist_ok=True)
                with open(os.path.join(dirname, "values.txt"), "w") as f:
                    f.write(f"excitation_energy={exc}, gap={gap}, fosc={fosc}, soc={soc}, relative_atomic_energy={relative_atomic_energy_val}\n")
                slurm_content = template_slurm.format(
                    excitation_energy=exc,
                    gap=gap,
                    fosc=fosc,
                    soc=f"{soc:.5f}",
                    relative_atomic_energy=relative_atomic_energy_val,
                    counter=counter
                )
                with open(os.path.join(dirname, "generation.slurm"), "w") as f:
                    f.write(slurm_content)
                counter += 1

print(f"Create {counter-1} generation folders with slurm scripts and values.txt files.")

