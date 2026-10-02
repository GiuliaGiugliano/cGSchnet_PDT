# cGSchnet_PDT

## Conditional 3D molecular generation for the inverse design of photosensitizers

This repository contains the implementation, configuration files, generated molecular libraries, and quantum-mechanically screened candidates obtained by adapting **conditional G-SchNet (cG-SchNet)** to the inverse design of novel molecular photosensitizers for **photodynamic therapy (PDT)**.

The model is based on the cG-SchNet framework developed by **Gebauer et al.** for conditional generation of three-dimensional molecular structures and on its SchNetPack 2.0 implementation, **`schnetpack-gschnet`**.

The core cG-SchNet architecture was not modified. Instead, the model was adapted to photosensitizer discovery through dedicated **Hydra/YAML configurations** defining different training datasets and combinations of quantum-mechanical, photophysical, energetic, and chemical-space conditioning variables.

The workflow combines:

- direct molecular generation in 3D Cartesian space;
- multi-property conditional generation;
- excitation-energy targeting;
- oscillator-strength targeting;
- HOMO-LUMO gap targeting;
- spin-orbit-coupling targeting;
- relative atomic energy conditioning;
- PCA-guided exploration of chemical space;
- physicochemical and structural filtering;
- quantum-mechanical validation;
- PDT-oriented photophysical screening.

---

# Background

Photodynamic therapy relies on the interaction of a **photosensitizer (PS)**, light, and molecular oxygen to generate reactive oxygen species.

The design of potential photosensitizers requires the simultaneous optimization of several molecular and excited-state properties. Important characteristics include:

- absorption in the visible spectral region;
- sufficiently intense electronic transitions;
- efficient population of triplet excited states;
- significant spin-orbit coupling;
- suitable singlet-triplet energetics;
- adequate electronic and thermodynamic stability.

Conventional screening approaches search existing molecular libraries and therefore remain restricted to previously explored chemical space.

Conditional generative models provide an alternative strategy by performing **inverse molecular design**, generating new structures directly toward predefined target properties.

---

# cG-SchNet

cG-SchNet is an autoregressive generative neural network that generates molecules directly in **three-dimensional Cartesian space**.

Instead of first constructing a molecular graph or SMILES representation, the model sequentially generates:

1. atomic identities;
2. atomic positions.

The conditional model samples molecular structures according to:

```text
p(R, Z | Λ)
```

where:

- `R` represents atomic coordinates;
- `Z` represents atomic types;
- `Λ` represents a vector of user-defined target molecular properties.

A SchNet-based representation is used to describe the chemical and geometrical environment of the partially generated structure, while dedicated conditioning modules introduce information about the requested target properties.

This repository uses the **SchNetPack 2.0 implementation of G-SchNet/cG-SchNet**, available through `schnetpack-gschnet`.

---

# Repository structure

The main components of the repository are organized as follows:

```text
cGSchnet_PDT/
│
├── schnetpack-gschnet/
│   └── SchNetPack 2.0 implementation of G-SchNet/cG-SchNet
│
├── my_gschnet_multimod_configs/
│   └── experiment/
│       ├── multicond_experiment_gen1.yaml
│       ├── multicond_experiment_gen2.yaml
│       ├── multicond_experiment_gen3.yaml
│       └── multicond_experiment_gen4.yaml
│
├── generation_1.csv
├── generation_2.csv
├── generation_3.csv
├── generation_4.csv
│
├── foto_gen1_smiles.csv
├── foto_gen2_smiles.csv
├── foto_gen3_smiles.csv
├── foto_gen4_smiles.csv
│
└── README.md
```

---

# Configuration files

The directory

```text
my_gschnet_multimod_configs/experiment/
```

contains the Hydra configurations used for the four molecular-generation campaigns:

```text
multicond_experiment_gen1.yaml
multicond_experiment_gen2.yaml
multicond_experiment_gen3.yaml
multicond_experiment_gen4.yaml
```

Each YAML file defines the corresponding experiment, including the relevant:

- dataset;
- model configuration;
- training parameters;
- conditioning variables;
- scalar conditioning modules;
- property ranges;
- generation settings.

These files define the four different strategies used to explore the molecular space of potential photosensitizers.

---

# Training dataset

The conditional generative models were trained using a heterogeneous quantum-annotated molecular dataset containing approximately **5,000 chemically diverse molecules**.

The dataset includes molecular classes such as:

- known photosensitizers;
- chromophores;
- natural compounds;
- drugs;
- photocatalysts.

After considering the relevant protonation states, the training dataset contained more than **10,000 three-dimensional molecular geometries**.

Ground-state structures were optimized using **GFN2-xTB** in implicit aqueous solvent and annotated with quantum-mechanical and photophysical properties used as conditioning variables.

---

# Conditioning properties

The properties used to guide molecular generation include:

| Property | Description | Unit |
|---|---|---|
| `E_exc` | First vertical excitation energy, S0 → S1 | eV |
| `f_osc` | Oscillator strength of the S0 → S1 transition | dimensionless |
| `E_gap` | HOMO-LUMO energy gap | eV |
| `SOC` | Spin-orbit coupling associated with S1 → T1 | eV |
| `E_rel` | Relative atomic energy | Hartree/atom |
| `PC1` | First PCA chemical-space coordinate | dimensionless |
| `PC2` | Second PCA chemical-space coordinate | dimensionless |

The first excitation energy can be related approximately to the corresponding wavelength through:

```text
λmax [nm] = 1240 / E_exc [eV]
```

This allows excitation-energy conditioning to steer generated molecules toward the visible spectral region relevant for PDT.

---

# Relative atomic energy

The relative atomic energy was used as an energetic conditioning variable.

For a molecule with zero-Kelvin energy `E_U0` and `N_atoms` atoms, the energy per atom is first calculated as:

```text
E_U0 / N_atoms
```

Molecules are grouped according to molecular formula, and the relative atomic energy is defined with respect to the mean energy per atom for molecules having the same elemental composition:

```text
E_rel =
E_U0 / N_atoms
-
< E_U0 / N_atoms >_formula
```

Negative values therefore correspond to structures with an energy per atom lower than the average value for their molecular formula.

The target value used during generation was:

```text
E_rel = -0.005 Hartree/atom
```

---

# Conditioning architecture

Continuous target properties are handled using the `ScalarConditionEmbedding` framework implemented in `schnetpack-gschnet`.

Each scalar property is expanded using a Gaussian radial basis representation and subsequently processed by a property-specific multilayer perceptron.

For the models used here, each scalar embedding network contains:

```text
64 features
3 fully connected layers
```

The individual property embeddings are concatenated and passed to the final conditioning module:

```text
property embeddings
        │
        ▼
 concatenation
        │
        ▼
ConditioningModule
        │
        ▼
conditional representation y
```

The final conditioning module contains:

```text
128 features
5 fully connected layers
```

The resulting conditional representation is integrated into the autoregressive generation process and biases the selection of atomic identities and spatial coordinates toward the requested target values.

---

# Scalar conditioning grids

The continuous properties are embedded using Gaussian radial-basis grids.

| Property | Minimum | Maximum | Grid spacing |
|---|---:|---:|---:|
| E_exc | 0.0 eV | 11.0 eV | 10 eV |
| f_osc | 0.0 | 7.0 | 0.5 |
| E_gap | 0.0 eV | 13.0 eV | 1.0 eV |
| SOC(S1 → T1) | 0.0 eV | 0.05 eV | 0.005 eV |
| E_rel | -1.0 Hartree/atom | 1.0 Hartree/atom | 0.2 Hartree/atom |
| PC1 | -4.5 | 4.5 | 0.1 |
| PC2 | -3.5 | 3.5 | 0.1 |

The same scalar-conditioning machinery is used for both quantum-mechanical properties and PCA-derived chemical-space coordinates.

---

# Generation campaigns

Four complementary generation strategies were used to explore different regions of molecular space.

---

## Generation 1 — Multi-property conditioning

Generation 1 performs simultaneous conditioning on several photophysical and energetic properties.

The model was trained on the complete molecular dataset and conditioned on:

```text
E_exc
f_osc
E_gap
SOC
E_rel
```

Target values:

| Property | Target values |
|---|---|
| E_exc (S0 → S1) | 1.8, 2.1, 2.5 eV |
| f_osc (S0 → S1) | 0.5, 1.0 |
| HOMO-LUMO gap | 2.0, 3.0 eV |
| SOC (S1 → T1) | 0.00006, 0.0001 eV |
| E_rel | -0.005 Hartree/atom |

Configuration:

```text
my_gschnet_multimod_configs/experiment/multicond_experiment_gen1.yaml
```

Final unique molecules:

```text
312
```

Generated molecular library:

```text
generation_1.csv
```

---

## Generation 2 — Reduced conditioning

Generation 2 uses fewer explicit conditioning properties in order to provide greater structural freedom while retaining control over the target absorption region and relative molecular energy.

The model was conditioned on:

```text
E_exc
E_rel
```

Target values:

| Property | Target values |
|---|---|
| E_exc (S0 → S1) | 1.8, 2.1, 2.5 eV |
| E_rel | -0.005 Hartree/atom |

Configuration:

```text
my_gschnet_multimod_configs/experiment/multicond_experiment_gen2.yaml
```

Final unique molecules:

```text
44
```

Generated molecular library:

```text
generation_2.csv
```

---

## Generation 3 — Photosensitizer-focused generation

Generation 3 explores a more localized region of photosensitizer-like chemical space.

The model was trained on a restricted subset containing **172 known photosensitizer structures**, introducing a data-level bias toward molecular environments characteristic of PDT-relevant compounds.

Direct conditioning was applied using:

```text
E_rel
```

with:

```text
E_rel = -0.005 Hartree/atom
```

Configuration:

```text
my_gschnet_multimod_configs/experiment/multicond_experiment_gen3.yaml
```

Final unique molecules:

```text
151
```

Generated molecular library:

```text
generation_3.csv
```

---

## Generation 4 — PCA-guided chemical-space exploration

Generation 4 was developed to explicitly explore regions of chemical space that were poorly populated in the reference molecular dataset.

Molecular structures were represented using Morgan fingerprints and projected onto a lower-dimensional space using principal component analysis.

The resulting continuous coordinates `PC1` and `PC2` were added to the molecular database and used directly as additional scalar conditioning properties.

The model was conditioned on:

```text
E_exc
f_osc
E_gap
SOC
E_rel
PC1
PC2
```

Target values:

| Property | Target values |
|---|---|
| E_exc (S0 → S1) | 1.8, 2.1, 2.5 eV |
| f_osc (S0 → S1) | 0.5, 1.0 |
| HOMO-LUMO gap | 2.0, 3.0 eV |
| SOC (S1 → T1) | 0.00006, 0.0001 eV |
| E_rel | -0.005 Hartree/atom |
| PC1, PC2 | (-1.5, 1.5), (3.0, 2.0) |

Configuration:

```text
my_gschnet_multimod_configs/experiment/multicond_experiment_gen4.yaml
```

Final unique molecules:

```text
324
```

Generated molecular library:

```text
generation_4.csv
```

---

# Generated molecular library

After molecular validation and SMILES-based deduplication, the four generation campaigns yielded:

| Generation | Unique molecules |
|---|---:|
| Generation 1 | 312 |
| Generation 2 | 44 |
| Generation 3 | 151 |
| Generation 4 | 324 |
| **Total** | **831** |

The four generation sets contain distinct molecular structures and together define the complete generated molecular library.

The corresponding files are:

```text
generation_1.csv
generation_2.csv
generation_3.csv
generation_4.csv
```

These CSV files contain the generated molecules and their corresponding SMILES representations.

---

# Installation

The generative model implementation used in this repository is contained in:

```text
schnetpack-gschnet/
```

A Python virtual environment is recommended.

From the root of this repository:

```bash
python -m venv .venv
source .venv/bin/activate
```

Upgrade `pip`:

```bash
python -m pip install --upgrade pip
```

Install the local `schnetpack-gschnet` implementation:

```bash
pip install ./schnetpack-gschnet
```

A CUDA-compatible GPU is strongly recommended for model training and large-scale molecular generation.

The installation provides the main command-line interfaces:

```text
gschnet_train
gschnet_generate
```

---

# Training

`schnetpack-gschnet` uses **Hydra** for experiment configuration.

The experiment YAML files included in this repository define the four generation strategies.

## Generation 1

```bash
gschnet_train \
    --config-dir=./my_gschnet_multimod_configs \
    experiment=multicond_experiment_gen1
```

## Generation 2

```bash
gschnet_train \
    --config-dir=./my_gschnet_multimod_configs \
    experiment=multicond_experiment_gen2
```

## Generation 3

```bash
gschnet_train \
    --config-dir=./my_gschnet_multimod_configs \
    experiment=multicond_experiment_gen3
```

## Generation 4

```bash
gschnet_train \
    --config-dir=./my_gschnet_multimod_configs \
    experiment=multicond_experiment_gen4
```

Before starting a training run, verify dataset paths and machine-specific settings inside the corresponding YAML configuration.

---

# Molecular generation

Once a model has been trained, molecular generation can be performed using:

```bash
gschnet_generate
```

A general generation command has the form:

```bash
gschnet_generate \
    modeldir=<path/to/trained/model> \
    n_molecules=1000 \
    batch_size=500 \
    max_n_atoms=280
```

For a conditional model, target values must also be provided for every conditioning variable expected by the trained network.

General syntax:

```bash
gschnet_generate \
    modeldir=<path/to/trained/model> \
    n_molecules=1000 \
    batch_size=500 \
    max_n_atoms=280 \
    ++conditions.<property_1>=<target_value_1> \
    ++conditions.<property_2>=<target_value_2>
```

For example, a relative atomic energy target can be specified as:

```bash
++conditions.relative_atomic_energy=-0.005
```

The exact property names must correspond to the `condition_name` values defined in the YAML configuration used to train the model.

For the generation campaigns reported in this repository, every combination of selected conditioning values was sampled independently.

For each target-value combination, up to:

```text
1000 molecules
```

were requested.

The maximum molecular size was set to:

```text
280 atoms
```

to allow the generation of relatively large molecular scaffolds.

---

# Generation workflow

The general workflow is:

```text
Training database
       │
       ▼
Quantum / photophysical properties
       │
       ▼
Hydra/YAML experiment configuration
       │
       ▼
cG-SchNet training
       │
       ▼
Conditional molecular generation
       │
       ▼
3D molecular structures
       │
       ▼
Chemical validity check
       │
       ▼
SMILES conversion
       │
       ▼
Deduplication
       │
       ▼
Final generation library
```

---

# Molecular validation and deduplication

Generated structures were chemically validated before duplicate removal.

Duplicate structures were identified at the **molecular-graph level** through their corresponding SMILES representations.

Therefore, structures with the same molecular graph were considered duplicates even if the generated three-dimensional coordinates were different.

Only one representative structure for each unique molecular graph was retained.

This avoids counting alternative generated conformations of the same compound as independent molecules.

The `schnetpack-gschnet` implementation also provides tools for evaluating generated structures with respect to:

- chemical validity;
- valence consistency;
- molecular uniqueness;
- novelty with respect to the training set.

---

# Quantum-mechanical validation

The **831 generated molecules** were subsequently subjected to quantum-mechanical validation.

Because protonation state can strongly influence the photophysical behavior of a potential photosensitizer, possible protomers relevant under physiological conditions were generated in the approximate range:

```text
pH 7–8
```

Protomer generation was performed using **Dimorphite-DL**.

The resulting structures underwent conformational sampling using:

```text
CREST
GFN2-xTB
GBSA water
300 K
5 fs integration time step
```

The lowest-energy CREST conformer was subsequently re-optimized at the xTB level.

---

# Electronic-structure calculations

Quantum-mechanical calculations were performed using:

```text
ORCA 6.0.1
```

Ground-state energies were evaluated using:

```text
B3LYP_G/def2-TZVP
CPCM water
```

TD-DFT calculations were performed on the xTB-refined structures using:

```text
B3LYP/def2-TZVP
TDA
CPCM water
```

The calculations provided the main quantities required for PDT-oriented screening:

- vertical excitation energies;
- UV-Vis absorption wavelengths;
- oscillator strengths;
- HOMO-LUMO gaps;
- transition dipole moments;
- spin-orbit coupling matrix elements;
- singlet and triplet excited-state energies.

Triplet-state geometries were additionally optimized and their electronic energies evaluated.

---

# PDT screening

The generated molecular library was filtered according to photophysical criteria associated with potential photosensitizer activity.

The main criteria were:

| Property | Criterion |
|---|---:|
| Absorption wavelength | λmax(S0 → S1) > 400 nm |
| HOMO-LUMO gap | 1.5–3.5 eV |
| Transition dipole moment | μ(S0 → Sn) > 0 |
| Oscillator strength | fosc > 0.03 |
| Spin-orbit coupling | SOC > 0.14 cm⁻¹ |
| Triplet-ground-state gap | ΔE(T1−S0) > 0.88 eV |

The triplet-state criterion was used to evaluate the energetic accessibility of a **Type II photodynamic pathway**, involving energy transfer from the photosensitizer triplet state to molecular oxygen.

---

# QM-screened PDT candidates

The molecules retained after quantum-mechanical screening are provided in:

```text
foto_gen1_smiles.csv
foto_gen2_smiles.csv
foto_gen3_smiles.csv
foto_gen4_smiles.csv
```

The number of candidates retained from each generation is:

| Generation | QM-screened molecules |
|---|---:|
| Generation 1 | 50 |
| Generation 2 | 10 |
| Generation 3 | 37 |
| Generation 4 | 21 |
| **Total** | **118** |

The repository therefore contains **118 unique generated molecules** whose physiologically relevant protomers satisfy the complete set of PDT-oriented quantum-mechanical screening criteria.

---

# Complete workflow

```text
Heterogeneous molecular dataset
          │
          ▼
   >10,000 3D structures
          │
          ▼
Quantum-property annotation
          │
          ▼
       cG-SchNet
          │
          │
   ┌──────┼───────┬────────┐
   │      │       │        │
   ▼      ▼       ▼        ▼
 Gen 1   Gen 2   Gen 3    Gen 4
   │      │       │        │
multi-  reduced  PS-      PCA-
target  target   focused  guided
   │      │       │        │
   ▼      ▼       ▼        ▼
  312     44      151      324
   │      │       │        │
   └──────┴───────┴────────┘
          │
          ▼
    831 unique molecules
          │
          ▼
Physiological protomer generation
        pH 7–8
          │
          ▼
 CREST / GFN2-xTB sampling
          │
          ▼
   QM / TD-DFT validation
          │
          ▼
PDT photophysical screening
          │
          ▼
  118 selected candidates
```

---

# Upstream implementation

This repository builds on the conditional G-SchNet methodology developed by **Gebauer and co-workers**.

The original cG-SchNet framework introduced property-conditioned inverse design of molecular structures directly in three-dimensional Cartesian space.

The implementation used here is based on:

```text
atomistic-machine-learning/schnetpack-gschnet
```

which provides G-SchNet and cG-SchNet within the **SchNetPack 2.0** ecosystem.

The original cG-SchNet repository is available at:

```text
https://github.com/atomistic-machine-learning/cG-SchNet
```

The SchNetPack implementation is available at:

```text
https://github.com/atomistic-machine-learning/schnetpack-gschnet
```

---

# Citation

If you use the cG-SchNet methodology, please cite:

**Niklas W. A. Gebauer, Michael Gastegger, Stefaan S. P. Hessmann, Klaus-Robert Müller, and Kristof T. Schütt.**

*Inverse design of 3d molecular structures with conditional generative neural networks.*

**Nature Communications 13, 973 (2022).**

DOI: `10.1038/s41467-022-28526-y`

```bibtex
@article{gebauer2022inverse,
    author = {Gebauer, Niklas W. A. and
              Gastegger, Michael and
              Hessmann, Stefaan S. P. and
              M{\"u}ller, Klaus-Robert and
              Sch{\"u}tt, Kristof T.},
    title = {Inverse design of 3d molecular structures with conditional generative neural networks},
    journal = {Nature Communications},
    volume = {13},
    pages = {973},
    year = {2022},
    doi = {10.1038/s41467-022-28526-y}
}
```

The original G-SchNet architecture can be cited as:

**Niklas Gebauer, Michael Gastegger, and Kristof Schütt.**

*Symmetry-adapted generation of 3D point sets for the targeted discovery of molecules.*

**Advances in Neural Information Processing Systems 32 (2019).**

The SchNetPack 2.0 implementation can be cited as:

**Kristof T. Schütt, Stefaan S. P. Hessmann, Niklas W. A. Gebauer, Jonas Lederer, and Michael Gastegger.**

*SchNetPack 2.0: A neural network toolbox for atomistic machine learning.*

**The Journal of Chemical Physics 158, 144801 (2023).**

DOI: `10.1063/5.0138367`

---

# Software attribution

The G-SchNet/cG-SchNet implementation contained in:

```text
schnetpack-gschnet/
```

originates from the `atomistic-machine-learning/schnetpack-gschnet` project.

Please retain the upstream copyright notices and license information when redistributing or modifying the original implementation.

---

# Disclaimer

The molecules contained in this repository are **computationally generated candidates**.

Their potential suitability for photodynamic therapy is based on conditional molecular generation and quantum-chemical screening.

The presence of a molecule in the final screened dataset does not imply experimentally demonstrated:

- photosensitizing activity;
- biological activity;
- pharmacological activity;
- safety;
- synthetic accessibility;
- clinical efficacy.

Experimental synthesis, photophysical characterization, biological testing, and toxicological validation are required before any practical or therapeutic application.

# Reproducing the cG-SchNet PDT workflow

The molecular-generation workflow used in this repository follows three consecutive steps:

```text
1. cG-SchNet training
        ↓
2. Conditional molecular generation
        ↓
3. Validity, uniqueness and novelty filtering
```

The core training, generation, and filtering routines are those provided by the `schnetpack-gschnet` implementation. Additional Python scripts included in this project were used to automate the creation and submission of multiple SLURM jobs corresponding to the different combinations of conditioning target values.

The examples below reproduce the workflow used on the HPC system.

---

## 1. Model training

Training is performed using the `gschnet_train` command provided by `schnetpack-gschnet`.

For **Generation 1**, the model was trained with:

```bash
gschnet_train \
    --config-dir=/data/horse/ws/gigi895h-QM9_gen_alpha/my_gschnet_multimod_configs \
    experiment=multicond_experiment_gen1 \
    data.datapath=/data/horse/ws/gigi895h-QM9_gen_alpha/generative_project/dataset2.db \
    trainer.accelerator=gpu
```

The corresponding Hydra configuration is:

```text
my_gschnet_multimod_configs/experiment/multicond_experiment_gen1.yaml
```

The same procedure was used for the other generation campaigns by changing the experiment configuration:

```bash
gschnet_train \
    --config-dir=/data/horse/ws/gigi895h-QM9_gen_alpha/my_gschnet_multimod_configs \
    experiment=multicond_experiment_gen2 \
    data.datapath=/data/horse/ws/gigi895h-QM9_gen_alpha/generative_project/dataset2.db \
    trainer.accelerator=gpu
```

```bash
gschnet_train \
    --config-dir=/data/horse/ws/gigi895h-QM9_gen_alpha/my_gschnet_multimod_configs \
    experiment=multicond_experiment_gen3 \
    data.datapath=<path-to-generation-3-training-database> \
    trainer.accelerator=gpu
```

```bash
gschnet_train \
    --config-dir=/data/horse/ws/gigi895h-QM9_gen_alpha/my_gschnet_multimod_configs \
    experiment=multicond_experiment_gen4 \
    data.datapath=<path-to-generation-4-training-database> \
    trainer.accelerator=gpu
```

Generation 3 uses the photosensitizer-restricted training set, whereas Generation 4 uses the database augmented with the PCA-derived conditioning coordinates.

Therefore, the exact database specified through:

```text
data.datapath=
```

must correspond to the dataset associated with the selected experiment configuration.

Training output is written to a model directory containing the trained network, Hydra configuration, checkpoints, and the corresponding dataset split.

For example:

```text
/data/horse/ws/gigi895h-QM9_gen_alpha/generative_project/models/
└── multicond_experiment/
    └── 2035167_i8035/
        ├── ...
        └── split.npz
```

The `split.npz` file is subsequently used during the filtering stage to determine whether generated molecules correspond to structures contained in the training, validation, or test subsets.

---

# 2. Conditional molecular generation

After training, molecules are generated using:

```text
gschnet_generate
```

A representative Generation 1 command used in this project is:

```bash
gschnet_generate \
    modeldir=/data/horse/ws/gigi895h-QM9_gen_alpha/generative_project/models/multicond_experiment/2035167_i8035 \
    n_molecules=1000 \
    batch_size=500 \
    max_n_atoms=280 \
    ++conditions.excitation_energy=1.8 \
    ++conditions.gap=1.5 \
    ++conditions.fosc=0.5 \
    ++conditions.soc=0.00006 \
    ++conditions.relative_atomic_energy=-0.005 \
    outputfile=/data/horse/ws/gigi895h-QM9_gen_alpha/generative_project/generation_1/generated_molecules/structures_1.db
```

The main generation arguments are:

| Argument | Description |
|---|---|
| `modeldir` | Directory containing the trained cG-SchNet model |
| `n_molecules` | Number of molecular structures requested for the target combination |
| `batch_size` | Number of structures generated per batch |
| `max_n_atoms` | Maximum number of atoms allowed in a generated molecule |
| `++conditions.*` | Target values used for conditional sampling |
| `outputfile` | ASE database containing the generated 3D structures |

In this workflow:

```text
n_molecules = 1000
batch_size  = 500
max_n_atoms = 280
```

were used for each target-value combination.

---

## Target-value combinations

cG-SchNet requires a value for every conditioning variable used during training.

Instead of performing only one generation run, all desired combinations of the target values were sampled independently.

For a fully conditioned model, a generic combination has the form:

```bash
gschnet_generate \
    modeldir=<trained-model-directory> \
    n_molecules=1000 \
    batch_size=500 \
    max_n_atoms=280 \
    ++conditions.excitation_energy=<E_exc> \
    ++conditions.gap=<E_gap> \
    ++conditions.fosc=<f_osc> \
    ++conditions.soc=<SOC> \
    ++conditions.relative_atomic_energy=-0.005 \
    outputfile=<output-database>
```

Thus, each combination of:

```text
excitation energy
× HOMO-LUMO gap
× oscillator strength
× SOC
× relative atomic energy
```

corresponds to an independent cG-SchNet generation run.

For models containing fewer conditioning variables, only the conditions used during training are passed to `gschnet_generate`.

For example, a reduced model conditioned only on excitation energy and relative atomic energy follows the general form:

```bash
gschnet_generate \
    modeldir=<trained-model-directory> \
    n_molecules=1000 \
    batch_size=500 \
    max_n_atoms=280 \
    ++conditions.excitation_energy=<E_exc> \
    ++conditions.relative_atomic_energy=-0.005 \
    outputfile=<output-database>
```

Generation 4 additionally includes the PCA-derived conditioning variables:

```bash
++conditions.pc1=<PC1>
++conditions.pc2=<PC2>
```

together with the corresponding quantum-mechanical conditioning properties.

The exact condition names must match those defined in the YAML configuration used to train the model.

---

# 3. Automated generation of SLURM jobs

Because many combinations of target values had to be evaluated independently, generation was automated rather than launching each `gschnet_generate` command manually.

Two helper scripts were used:

```text
create_generation.py
run_generation.py
```

## `create_generation.py`

`create_generation.py` generates the individual SLURM generation scripts:

```text
generation.slurm
```

for the different combinations of target conditioning values.

Conceptually, the script constructs commands of the form:

```bash
gschnet_generate \
    modeldir=<model-directory> \
    n_molecules=1000 \
    batch_size=500 \
    max_n_atoms=280 \
    ++conditions.<property1>=<value1> \
    ++conditions.<property2>=<value2> \
    ... \
    outputfile=<structures_N.db>
```

for every required target combination.

It can be launched with:

```bash
python create_generation.py
```

The generated jobs produce ASE databases such as:

```text
structures_1.db
structures_2.db
structures_3.db
...
```

where each database corresponds to one conditioning-value combination.

---

## `run_generation.py`

The resulting generation jobs are submitted using:

```bash
python run_generation.py
```

`run_generation.py` automates submission of the generated:

```text
generation.slurm
```

jobs to the HPC scheduler.

The generation workflow is therefore:

```text
trained model
     │
     ▼
create_generation.py
     │
     ▼
generation.slurm jobs
     │
     ▼
run_generation.py
     │
     ▼
gschnet_generate
     │
     ▼
structures_1.db
structures_2.db
structures_3.db
...
```

---

# 4. Filtering generated molecules

The raw structures produced by cG-SchNet must subsequently be checked for chemical validity and duplicate molecular graphs.

The filtering procedure uses the standard:

```text
check_validity.py
```

script provided by `schnetpack-gschnet`.

For example, one of the filtering commands used for Generation 1 was:

```bash
python /data/horse/ws/gigi895h-QM9_gen_alpha/schnetpack-gschnet/src/scripts/check_validity.py \
    structures_1.db \
    --compute_uniqueness \
    --compare_db_path /data/horse/ws/gigi895h-QM9_gen_alpha/generative_project/dataset2.db \
    --compare_db_split_path /data/horse/ws/gigi895h-QM9_gen_alpha/generative_project/models/multicond_experiment/2035167_i8035/split.npz \
    --ignore_enantiomers \
    --timeout 2 \
    --results_db_path auto \
    --results_db_flags unique
```

The relevant options are:

| Option | Purpose |
|---|---|
| `structures_1.db` | Database containing raw cG-SchNet-generated structures |
| `--compute_uniqueness` | Identifies duplicate generated molecular graphs |
| `--compare_db_path` | Compares generated molecules with the reference dataset |
| `--compare_db_split_path` | Uses the model split to identify training/validation/test matches |
| `--ignore_enantiomers` | Treats mirror-image stereoisomers as equivalent during comparison |
| `--timeout 2` | Limits excessively long 3D-to-molecular-graph conversion attempts |
| `--results_db_path auto` | Automatically determines the output database path |
| `--results_db_flags unique` | Stores the structures satisfying the uniqueness criterion |

With:

```text
--results_db_path auto
```

the filtered database is automatically written alongside the original generated database.

---

# 5. Automated filtering of all generation databases

Since every target-value combination generates an independent:

```text
structures_N.db
```

database, the filtering procedure was also automated.

Two helper scripts were used:

```text
cp_filter.py
run_filter.py
```

## `cp_filter.py`

`cp_filter.py` prepares the filtering jobs for the generated molecular databases.

For every generation database, it creates the corresponding filtering command based on:

```bash
python <path-to-schnetpack-gschnet>/src/scripts/check_validity.py \
    <structures_N.db> \
    --compute_uniqueness \
    --compare_db_path <training-database> \
    --compare_db_split_path <model-directory>/split.npz \
    --ignore_enantiomers \
    --timeout 2 \
    --results_db_path auto \
    --results_db_flags unique
```

and writes the associated:

```text
filter.slurm
```

job files.

The script is run with:

```bash
python cp_filter.py
```

---

## `run_filter.py`

The filtering SLURM jobs are then submitted using:

```bash
python run_filter.py
```

This executes the generated:

```text
filter.slurm
```

jobs across all databases produced during conditional generation.

The complete filtering sequence is:

```text
structures_1.db
structures_2.db
structures_3.db
       ...
        │
        ▼
   cp_filter.py
        │
        ▼
   filter.slurm
        │
        ▼
   run_filter.py
        │
        ▼
 check_validity.py
        │
        ▼
valid + unique molecular structures
```

---

# 6. Complete HPC workflow

The complete sequence used to train the models, generate molecules, and filter the resulting structures is:

```text
Hydra experiment YAML
        │
        ▼
   gschnet_train
        │
        ▼
 trained cG-SchNet model
        │
        ├── checkpoints
        └── split.npz
        │
        ▼
create_generation.py
        │
        ▼
 generation.slurm
        │
        ▼
run_generation.py
        │
        ▼
 gschnet_generate
        │
        ▼
structures_1.db
structures_2.db
structures_3.db
       ...
        │
        ▼
   cp_filter.py
        │
        ▼
    filter.slurm
        │
        ▼
   run_filter.py
        │
        ▼
 check_validity.py
        │
        ▼
Valid and unique generated structures
        │
        ▼
Aggregation across target combinations
        │
        ▼
SMILES-based cross-deduplication
        │
        ▼
generation_1.csv
generation_2.csv
generation_3.csv
generation_4.csv
```

---

# Minimal command sequence

For a single experiment and a single target-value combination, the essential sequence is therefore:

### 1. Train

```bash
gschnet_train \
    --config-dir=/data/horse/ws/gigi895h-QM9_gen_alpha/my_gschnet_multimod_configs \
    experiment=multicond_experiment_gen1 \
    data.datapath=/data/horse/ws/gigi895h-QM9_gen_alpha/generative_project/dataset2.db \
    trainer.accelerator=gpu
```

### 2. Generate

```bash
gschnet_generate \
    modeldir=/data/horse/ws/gigi895h-QM9_gen_alpha/generative_project/models/multicond_experiment/2035167_i8035 \
    n_molecules=1000 \
    batch_size=500 \
    max_n_atoms=280 \
    ++conditions.excitation_energy=1.8 \
    ++conditions.gap=1.5 \
    ++conditions.fosc=0.5 \
    ++conditions.soc=0.00006 \
    ++conditions.relative_atomic_energy=-0.005 \
    outputfile=/data/horse/ws/gigi895h-QM9_gen_alpha/generative_project/generation_1/generated_molecules/structures_1.db
```

### 3. Filter

```bash
python /data/horse/ws/gigi895h-QM9_gen_alpha/schnetpack-gschnet/src/scripts/check_validity.py \
    /data/horse/ws/gigi895h-QM9_gen_alpha/generative_project/generation_1/generated_molecules/structures_1.db \
    --compute_uniqueness \
    --compare_db_path /data/horse/ws/gigi895h-QM9_gen_alpha/generative_project/dataset2.db \
    --compare_db_split_path /data/horse/ws/gigi895h-QM9_gen_alpha/generative_project/models/multicond_experiment/2035167_i8035/split.npz \
    --ignore_enantiomers \
    --timeout 2 \
    --results_db_path auto \
    --results_db_flags unique
```

For the complete production workflow, these individual commands were generated and submitted automatically using:

```bash
python create_generation.py
python run_generation.py

python cp_filter.py
python run_filter.py
```

This automation enabled all requested combinations of cG-SchNet conditioning values to be generated and filtered independently using the HPC scheduler.
