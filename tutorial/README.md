# Reduced Order Modeling using POD for Fluid Flows - Tutorial

## Overview

This tutorial provides a comprehensive guide to **Proper Orthogonal Decomposition (POD)** for reduced-order modeling (ROM) of fluid flows. It combines rigorous mathematical theory with practical Python implementations, using three canonical CFD benchmark problems.

## 📁 Project Structure

```
tutorial/
├── data/                           # Input data directories
│   ├── cavity_flow/                # Lid-driven cavity flow data
│   ├── backward_facing_step/       # Backward facing step data
│   └── cylinder_flow/              # Cylinder flow (Von Kármán vortex street)
│
├── src/                            # Core Python modules
│   ├── pod_solver.py               # Main POD_Solver class
│   ├── data_utils.py               # Data preprocessing utilities
│   └── __init__.py
│
├── notebooks/                      # Jupyter notebooks
│   ├── 01_POD_Fundamentals.ipynb   # Theory and basic usage
│   ├── 02_Cavity_Flow_Analysis.ipynb
│   ├── 03_Backward_Facing_Step.ipynb
│   └── 04_Cylinder_Flow_Analysis.ipynb
│
├── results/                        # Output results
│   ├── cavity_flow/
│   ├── backward_facing_step/
│   └── cylinder_flow/
│
├── docs/                           # Documentation
│   ├── POD_MATHEMATICAL_FOUNDATION.md
│   ├── DATA_SPECIFICATIONS.md
│   └── TUTORIAL_GUIDE.md
│
└── README.md                       # This file
```

## 📚 Learning Path

### Level 1: Fundamentals
- [ ] Read `docs/POD_MATHEMATICAL_FOUNDATION.md`
- [ ] Review SVD and eigenvalue decomposition concepts
- [ ] Understand the Method of Snapshots

### Level 2: Implementation
- [ ] Explore `src/pod_solver.py` class structure
- [ ] Review `src/data_utils.py` utilities
- [ ] Run `notebooks/01_POD_Fundamentals.ipynb`

### Level 3: Applications
- [ ] Analyze Cavity Flow (`notebooks/02_Cavity_Flow_Analysis.ipynb`)
- [ ] Study Backward Facing Step (`notebooks/03_Backward_Facing_Step.ipynb`)
- [ ] Investigate Cylinder Flow (`notebooks/04_Cylinder_Flow_Analysis.ipynb`)

### Level 4: Advanced Topics
- [ ] Reconstruct ROM predictions
- [ ] Compute error metrics
- [ ] Compare modal structures across cases

## 🔧 Installation & Setup

### Requirements
```bash
pip install numpy scipy matplotlib h5py
```

### Optional (for advanced visualization)
```bash
pip install plotly seaborn pandas
```

### Verify Installation
```python
import sys
sys.path.insert(0, 'path/to/tutorial/src')
from pod_solver import POD_Solver
from data_utils import DataHandler, SnaphotProcessor

print("✓ POD tutorial packages loaded successfully!")
```

## 📊 Test Cases

### 1️⃣ Lid-Driven Cavity Flow

**Physical Setup:**
- 2D square domain (0 ≤ x, y ≤ 1)
- Top lid moving at velocity $U_0 = 1.0$, other walls at rest
- Steady-state driven circulation

**Characteristics:**
- Internal flow with smooth boundaries
- Primary circulation in the cavity
- Corner eddies at Re = 1000
- Good test for POD mode interpretation

**Expected Data Format:**
```
cavity_flow/
├── u_snapshots.npy        # u-velocity (n_spatial, n_snapshots)
├── v_snapshots.npy        # v-velocity (n_spatial, n_snapshots)
├── pressure_snapshots.npy  # pressure (optional)
├── mesh.npy               # grid coordinates (optional)
└── parameters.json        # Re, geometry info
```

### 2️⃣ Backward Facing Step

**Physical Setup:**
- Sudden expansion of channel
- Flow separates at step edge
- Reattachment zone downstream

**Characteristics:**
- Separated flow phenomena
- Recirculation bubble
- Unsteady at moderate Re
- Tests POD performance on transient flows

**Expected Data Format:**
```
backward_facing_step/
├── u_snapshots.npy
├── v_snapshots.npy
├── mesh.npy
└── parameters.json
```

### 3️⃣ Cylinder Flow (Von Kármán Vortex Street)

**Physical Setup:**
- 2D cylinder in cross-flow
- Periodic vortex shedding
- Re = 100-200 range

**Characteristics:**
- Highly transient, periodic phenomena
- Dominant Strouhal frequency
- Complex coherent structures
- Excellent for testing ROM accuracy

**Expected Data Format:**
```
cylinder_flow/
├── u_snapshots.npy
├── v_snapshots.npy
├── vorticity_snapshots.npy  # Optional
├── time_vector.npy          # Time instances
└── parameters.json
```

## 📝 Data Format Specifications

### Snapshot Matrix Format

All snapshot data should follow this convention:

```python
snapshots.shape = (n_spatial_dofs, n_snapshots)
```

**Example for 2D cavity (128×128 grid):**
- n_spatial = 128 × 128 × 2 (u and v components) = 32,768
- n_snapshots = 500 (time instances)
- Shape: (32768, 500)

### Metadata (parameters.json)

Required JSON file with flow parameters:

```json
{
  "case_name": "Lid-Driven Cavity Flow",
  "reynolds_number": 1000,
  "nx": 128,
  "ny": 128,
  "geometry": {
    "domain": "square",
    "length": 1.0,
    "height": 1.0
  },
  "time": {
    "n_snapshots": 500,
    "t_start": 0.0,
    "t_end": 100.0,
    "dt": 0.2
  },
  "solver": {
    "method": "Finite Difference / FEM / CFD tool",
    "scheme": "2nd order implicit",
    "convergence": "steady-state"
  },
  "components": ["u", "v"],
  "normalization": "none"
}
```

### Loading Your Data

```python
from data_utils import DataHandler, SnaphotProcessor

# Load snapshots
u_snapshots = DataHandler.load_npy('data/cavity_flow/u_snapshots.npy')
v_snapshots = DataHandler.load_npy('data/cavity_flow/v_snapshots.npy')

# Combine components
snapshots = SnaphotProcessor.combine_velocity_components(u_snapshots, v_snapshots)

print(f"Loaded snapshots shape: {snapshots.shape}")
```

## 🚀 Quick Start Example

```python
import numpy as np
from src.pod_solver import POD_Solver
from src.data_utils import create_sample_snapshot_data

# Create sample data (or load your own)
snapshots = create_sample_snapshot_data(n_spatial=1024, n_snapshots=100)

# Initialize POD solver
pod = POD_Solver(snapshots, verbose=True)

# Compute POD
pod.preprocess()
pod.compute_svd()

# Analyze modes
print(f"Energy of first 5 modes: {pod.cumulative_energy[:5]}")

# Reconstruct with 5 modes
reconstructed = pod.reconstruct(n_modes=5)
error = pod.error_l2(n_modes=5)
print(f"L2 reconstruction error (5 modes): {error:.4e}")

# Visualize
fig1 = pod.plot_cumulative_energy()
fig2 = pod.plot_reconstruction_error(max_modes=20)
```

## 📈 Key Outputs

### Per-Case Analysis

1. **Cumulative Energy Plot**
   - Shows minimum modes needed for 95%, 99% energy
   - Diagnostic for ROM complexity

2. **POD Mode Visualizations**
   - First 4 modes (highest energy)
   - Reveals coherent structures
   - Validates physical interpretation

3. **Reconstruction Error Analysis**
   - L2 error vs. number of modes
   - Trade-off: accuracy vs. model size
   - Quantifies ROM performance

4. **Comparative Metrics**
   - Original vs. Reconstructed fields
   - Error distribution
   - Mode orthogonality verification

## 📋 Checklist for Data Preparation

Before analyzing your data:

- [ ] Snapshots saved in (n_spatial, n_snapshots) format
- [ ] Data is centered (optional; code handles it)
- [ ] No NaN or Inf values present
  ```python
  assert np.isfinite(snapshots).all()
  ```
- [ ] Time dimension is last dimension
  ```python
  assert snapshots.shape[1] > snapshots.shape[0]  # More snapshots than DOFs
  ```
- [ ] Metadata saved in JSON format
- [ ] Velocity components properly combined or documented

## 🔍 Troubleshooting

### Issue: "Method of Snapshots not working well"
- **Cause:** More DOFs than snapshots (n > M)
- **Solution:** Always ensure n_spatial > n_snapshots for efficiency, or use direct SVD

### Issue: "POD modes don't look physical"
- **Check:** Data properly centered? Outliers removed?
- **Solution:** Use `SnaphotProcessor.remove_outliers()` and verify centering

### Issue: "High reconstruction error despite many modes"
- **Cause:** Data normalization issues or numerical precision
- **Solution:** Normalize data, check singular value decay rate

## 📚 References & Further Reading

1. **Sirovich, L. (1987).** Turbulence and the dynamics of coherent structures.
2. **Holmes, P., Lumley, J. L., & Berkooz, G. (2012).** Turbulence, Coherent Structures, Dynamical Systems and Symmetry.
3. **Volkwein, S. (2013).** Proper orthogonal decomposition and singular value decomposition.
4. **Brunton, S. L., & Kutz, J. N. (2019).** Data-driven science and engineering.

## 🎯 Next Steps

1. **Prepare your data** according to specifications
2. **Place data files** in appropriate `data/*/` directories
3. **Update parameters.json** with flow information
4. **Run preprocessing script** to validate data
5. **Execute POD analysis** using provided notebooks
6. **Interpret results** and extract insights

---

## 📧 Questions & Contributions

For questions about implementation or data formats, refer to:
- `docs/POD_MATHEMATICAL_FOUNDATION.md` for theory
- `src/pod_solver.py` docstrings for API
- `src/data_utils.py` for data handling examples

## License

This tutorial is provided for educational purposes.

---

**Last Updated:** May 2026  
**Status:** Ready for Data Input
