# POD Tutorial - Quick Reference Guide

## 🚀 30-Second Quick Start

```python
# 1. Import
from src.pod_solver import POD_Solver
from src.data_utils import DataHandler

# 2. Load data
u = DataHandler.load_npy('data/cavity_flow/u_snapshots.npy')  # (n, m)
v = DataHandler.load_npy('data/cavity_flow/v_snapshots.npy')  # (n, m)

# 3. Combine
snapshots = np.vstack([u, v])  # (2n, m)

# 4. Analyze
pod = POD_Solver(snapshots)
pod.compute_svd()

# 5. Visualize
pod.plot_cumulative_energy().show()
pod.plot_modes(n_modes=4, spatial_shape=(128, 128, 2)).show()
```

## 📊 POD_Solver API Summary

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `preprocess()` | None | Modifies `self` | Center snapshots |
| `compute_svd()` | method: str | Modifies `self` | Compute POD modes |
| `reconstruct(K)` | n_modes: int | Array (n, m) | ROM reconstruction |
| `project_onto_modes(K)` | n_modes: int | Array (K, m) | Temporal coefficients |
| `get_modes(K)` | n_modes: int | Array (n, K) | Extract first K modes |
| `error_l2(K)` | n_modes: int | float | L2 relative error |
| `energy_content(K)` | n_modes: int | float | Cumulative energy % |
| `plot_cumulative_energy()` | n_max: int | Figure | Energy decay plot |
| `plot_reconstruction_error()` | max_modes: int | Figure | Error evolution |
| `plot_modes()` | n_modes: int | Figure | Mode visualization |
| `summary()` | None | Dict | Analysis summary |

## 📁 Directory Structure

```
tutorial/
├── README.md ........................... Project overview
├── src/
│   ├── __init__.py ..................... Module interface
│   ├── pod_solver.py ................... Main POD class (450+ lines)
│   └── data_utils.py ................... Data I/O (350+ lines)
├── data/
│   ├── cavity_flow/ .................... [YOUR CAVITY DATA HERE]
│   ├── backward_facing_step/ ........... [YOUR STEP DATA HERE]
│   └── cylinder_flow/ .................. [YOUR CYLINDER DATA HERE]
├── notebooks/
│   ├── 01_POD_Fundamentals.ipynb ....... [PLANNED]
│   ├── 02_Cavity_Flow_Analysis.ipynb ... [PLANNED]
│   ├── 03_Backward_Facing_Step.ipynb ... [PLANNED]
│   └── 04_Cylinder_Flow_Analysis.ipynb . [PLANNED]
├── results/ ............................ Output plots & data
└── docs/
    ├── POD_MATHEMATICAL_FOUNDATION.md .. Theory (complete)
    ├── DATA_SPECIFICATIONS.md .......... Format guide (complete)
    ├── PROJECT_SUMMARY.md .............. Deliverables summary
    └── QUICK_REFERENCE.md .............. This file
```

## 🔑 Key Classes

### POD_Solver
```python
POD_Solver(snapshots, verbose=True)

Attributes:
  .snapshots ............. Original data (n_spatial, n_snapshots)
  .mean_field ............ Temporal mean
  .centered_data ......... Data after mean subtraction
  .U ..................... POD modes (n_spatial, n_modes)
  .s ..................... Singular values
  .Vt .................... Temporal coefficients
  .energy ................ Energy per mode
  .cumulative_energy ..... Cumulative energy fraction
```

### DataHandler
```python
DataHandler.load_data(filepath, **kwargs)    # Auto-detect format
DataHandler.load_npy(filepath)               # NumPy .npy
DataHandler.load_npz(filepath, key=None)     # NumPy .npz
DataHandler.load_csv(filepath, delimiter=',') # CSV
DataHandler.load_h5(filepath, key)           # HDF5
```

### SnaphotProcessor
```python
SnaphotProcessor.combine_velocity_components(u, v, w=None)
SnaphotProcessor.split_velocity_components(snapshots, n_spatial, n_comp=2)
SnaphotProcessor.normalize_snapshots(snapshots, norm_type='l2')
SnaphotProcessor.remove_outliers(snapshots, threshold=3.0)
```

## 📋 Data Format Requirements

### Snapshot Matrix Shape
```python
snapshots.shape = (n_spatial_dofs, n_snapshots)
```

**Example:** 2D Cavity Flow (128×128 grid, u+v components)
```
n_spatial = 128 × 128 × 2 = 32,768
n_snapshots = 500
shape = (32768, 500)  ✓ CORRECT
shape = (500, 32768)  ✗ WRONG (transposed)
```

### Required Files Per Case
```
data/cavity_flow/
├── u_snapshots.npy ............... (n_spatial, n_snapshots)
├── v_snapshots.npy ............... (n_spatial, n_snapshots)
└── parameters.json ............... Case metadata
```

### Sample parameters.json
```json
{
  "case_name": "Lid-Driven Cavity Flow",
  "reynolds_number": 1000,
  "grid": {"nx": 128, "ny": 128},
  "snapshots": {
    "total": 500,
    "time_start": 0.0,
    "time_end": 100.0,
    "dt": 0.2
  },
  "components": ["u", "v"]
}
```

## ✅ Data Validation Script

```python
import numpy as np

def validate_snapshots(snapshots):
    """Check snapshot data quality"""
    assert snapshots.ndim == 2, "Data must be 2D"
    assert snapshots.shape[0] > snapshots.shape[1], "Shape must be (n_spatial, n_snap)"
    assert np.isfinite(snapshots).all(), "Contains NaN or Inf"
    assert np.linalg.norm(snapshots, 'fro') > 0, "All-zero data"
    return True

# Load and validate
u = np.load('data/cavity_flow/u_snapshots.npy')
v = np.load('data/cavity_flow/v_snapshots.npy')
snapshots = np.vstack([u, v])

assert validate_snapshots(snapshots)
print("✓ Data validated!")
```

## 📈 Typical Workflow

```
1. Load Data
   ↓
2. Preprocess (center, normalize)
   ↓
3. Compute SVD
   ↓
4. Analyze Energy Content
   ↓
5. Choose K (number of modes)
   ↓
6. Reconstruct ROM
   ↓
7. Evaluate Error
   ↓
8. Visualize & Interpret
```

## 🎯 Common Analysis Goals

### Goal: "How many modes do I need?"
```python
pod = POD_Solver(snapshots)
pod.compute_svd()

# Find modes for 95% energy
for k in range(1, 21):
    energy = pod.energy_content(k) * 100
    if energy >= 95:
        print(f"Need {k} modes for 95% energy")
        break
```

### Goal: "Reconstruct with K modes"
```python
K = 5
rom_snapshots = pod.reconstruct(n_modes=K)
error = pod.error_l2(n_modes=K)
print(f"L2 Error ({K} modes): {error:.4e}")
```

### Goal: "Extract temporal evolution of mode k"
```python
k = 1  # First mode
temporal_coeff = pod.project_onto_modes(n_modes=1)
plt.plot(temporal_coeff[0, :])
plt.xlabel('Time')
plt.ylabel(f'Mode {k} Amplitude')
```

## 🔍 Key Equations

### POD Approximation
$$\Phi(x, t) \approx \overline{\mathbf{u}} + \sum_{k=1}^{K} a_k(t) \psi_k(x)$$

### Cumulative Energy
$$E(K) = \frac{\sum_{k=1}^{K} \lambda_k}{\sum_{j=1}^{M} \lambda_j}$$

### L2 Relative Error
$$\epsilon = \frac{\|\mathbf{X} - \tilde{\mathbf{X}}_K\|_F}{\|\mathbf{X}\|_F}$$

## ⚠️ Common Mistakes

| Mistake | Issue | Fix |
|---------|-------|-----|
| Transposed snapshots | Wrong POD modes | Transpose: `snapshots = snapshots.T` |
| Not centering data | Mode 1 ≈ mean field | Use `pod.preprocess()` |
| Too few snapshots | Noise dominates | Collect more snapshots (n_snap > 100) |
| Including outliers | Spurious modes | Use `SnaphotProcessor.remove_outliers()` |
| Not normalizing | Scale-dependent results | Normalize before comparison |

## 📞 Troubleshooting

**Q: "POD_Solver gives all-zero modes"**  
A: Data is probably all-zero. Check: `print(snapshots.max())`

**Q: "Singular values don't decay"**  
A: Data lacks coherent structures. Verify it's not random noise.

**Q: "First mode seems trivial"**  
A: Likely the mean field. Try `snapshots -= snapshots.mean(axis=1, keepdims=True)`

**Q: "Can't load data with DataHandler"**  
A: Check file extension. Supported: .npy, .npz, .csv, .h5

## 📚 Documentation Map

```
For Theory ...................... POD_MATHEMATICAL_FOUNDATION.md
For Data Formats ................ DATA_SPECIFICATIONS.md
For Project Overview ............ README.md
For Implementation Details ...... Source code docstrings
For Quick Help .................. QUICK_REFERENCE.md (this file)
For Deliverables Summary ........ PROJECT_SUMMARY.md
```

## 🎓 Learning Resources

**Mathematical Foundations:**
- Sirovich (1987) - POD definition
- Holmes et al. (2012) - Coherent structures
- Volkwein (2013) - SVD and POD

**Computational Methods:**
- See `POD_MATHEMATICAL_FOUNDATION.md` (Sections 4-5)

**Applications:**
- See notebooks when available (Phase 2)

---

**Version:** 1.0.0  
**Last Updated:** May 2026  
**Status:** Production Ready
