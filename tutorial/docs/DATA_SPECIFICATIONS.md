# Data Specifications for POD Tutorial

## Overview

This document specifies the exact data format and requirements for the three test cases used in the POD tutorial.

---

## General Snapshot Matrix Format

### Required Convention

All snapshot data **must** follow this matrix convention:

```python
snapshots.shape == (n_spatial_dofs, n_snapshots)
```

Where:
- **n_spatial_dofs** = Number of spatial degrees of freedom
- **n_snapshots** = Number of time instances (temporal snapshots)

### Example Calculation

For a 2D cavity flow on a 128×128 grid with velocity components u and v:

```
n_spatial = 128 × 128 × 2 = 32,768
n_snapshots = 500
snapshots shape = (32768, 500)

Memory (float64) = 32768 × 500 × 8 bytes ≈ 130 MB
```

### Transposition Note

If your data is in the format (n_snapshots, n_spatial):
```python
# WRONG shape
snapshots.shape == (500, 32768)

# FIX by transposing
snapshots = snapshots.T  # Now (32768, 500) ✓
```

---

## 1. Lid-Driven Cavity Flow

### Problem Description

**Domain:** Square cavity [0,1] × [0,1]  
**Boundary Conditions:**
- Top wall (y=1): Moving at velocity U₀ = 1.0 in x-direction
- All other walls: No-slip (u=v=0)

**Reynolds Number:** Re = U₀ × L / ν = 1000

**Characteristics:**
- Steady-state driven circulation
- Primary vortex in center
- Secondary vortices in bottom corners
- Well-suited for POD: clear modal structure

### Expected Data Files

```
data/cavity_flow/
│
├── u_snapshots.npy
│   Type: numpy array (.npy)
│   Shape: (128×128, n_snapshots) = (16384, 500)
│   Content: u-velocity component
│   Range: [-0.15, 1.0] m/s (typical)
│
├── v_snapshots.npy
│   Type: numpy array (.npy)
│   Shape: (128×128, n_snapshots) = (16384, 500)
│   Content: v-velocity component
│   Range: [-0.25, 0.25] m/s (typical)
│
├── pressure_snapshots.npy (optional)
│   Type: numpy array (.npy)
│   Shape: (16384, 500)
│   Content: Pressure field
│   Note: Optional; not required for basic POD analysis
│
├── mesh.npy (optional)
│   Type: numpy array (.npy)
│   Shape: (16384, 2) for 2D coordinates (x, y)
│   Content: Spatial grid coordinates
│
├── time_vector.npy (optional)
│   Type: numpy array (.npy)
│   Shape: (500,)
│   Content: Time instances corresponding to snapshots
│
└── parameters.json
    Type: JSON file
    Content: Case metadata (see below)
```

### Expected parameters.json Format

```json
{
  "case_name": "Lid-Driven Cavity Flow",
  "description": "2D steady-state cavity flow with moving top lid",
  "reynolds_number": 1000,
  "grid": {
    "nx": 128,
    "ny": 128,
    "type": "uniform"
  },
  "domain": {
    "length": 1.0,
    "height": 1.0,
    "units": "m"
  },
  "flow": {
    "lid_velocity": 1.0,
    "kinematic_viscosity": 0.001,
    "density": 1.0
  },
  "snapshots": {
    "total": 500,
    "time_start": 0.0,
    "time_end": 100.0,
    "dt": 0.2
  },
  "components": ["u", "v"],
  "normalization": "none",
  "reference_velocity": 1.0,
  "reference_length": 1.0
}
```

### Data Loading Example

```python
import numpy as np
import json
from data_utils import DataHandler, SnaphotProcessor

# Load velocity components
u = DataHandler.load_npy('data/cavity_flow/u_snapshots.npy')
v = DataHandler.load_npy('data/cavity_flow/v_snapshots.npy')

# Combine components
snapshots = SnaphotProcessor.combine_velocity_components(u, v)
# Result: shape (32768, 500)

# Load metadata
with open('data/cavity_flow/parameters.json', 'r') as f:
    params = json.load(f)

print(f"Cavity flow analysis")
print(f"  Re = {params['reynolds_number']}")
print(f"  Grid: {params['grid']['nx']} × {params['grid']['ny']}")
print(f"  Snapshots: {snapshots.shape}")
```

---

## 2. Backward Facing Step

### Problem Description

**Domain:** Step at x=0, upstream height H, downstream height 2H  
**Inflow:** Uniform velocity U₀ = 1.0 at height 2H  
**Outflow:** Pressure-outlet

**Reynolds Number:** Re = U₀ × (2H) / ν = 500-1000

**Characteristics:**
- Separated flow (eddy at step corner)
- Reattachment zone downstream
- Time-dependent at moderate Re
- Complex recirculation region

### Expected Data Files

```
data/backward_facing_step/
│
├── u_snapshots.npy
│   Shape: (nx × ny, n_snapshots)
│   Example: (10240, 600)  [128×80 grid]
│   Range: [-0.1, 1.2] m/s
│
├── v_snapshots.npy
│   Shape: (10240, 600)
│   Range: [-0.3, 0.3] m/s
│
├── mesh.npy (optional)
│   Shape: (10240, 2) or (10240, 3) for 3D
│   Content: (x, y) or (x, y, z) coordinates
│
└── parameters.json
    Content: (see format below)
```

### parameters.json Format

```json
{
  "case_name": "Backward Facing Step",
  "description": "Channel flow with sudden 2:1 expansion",
  "reynolds_number": 700,
  "grid": {
    "nx": 128,
    "ny": 80,
    "type": "non-uniform"
  },
  "domain": {
    "upstream_height": 1.0,
    "downstream_height": 2.0,
    "step_location": 0.0,
    "outlet_length": 10.0,
    "units": "m"
  },
  "flow": {
    "inlet_velocity": 1.0,
    "inlet_height": 2.0,
    "kinematic_viscosity": 0.001
  },
  "snapshots": {
    "total": 600,
    "time_start": 0.0,
    "time_end": 120.0,
    "dt": 0.2
  },
  "components": ["u", "v"],
  "unsteady": true,
  "shedding_frequency": 0.15
}
```

---

## 3. Cylinder Flow (Von Kármán Vortex Street)

### Problem Description

**Domain:** Cylinder of diameter D = 1.0 in cross-flow  
**Inflow:** Uniform velocity U∞ = 1.0  
**Reynolds Number:** Re = U∞ × D / ν ≈ 100-200

**Characteristics:**
- Periodic vortex shedding
- Dominant Strouhal frequency: St = f×D/U∞ ≈ 0.16-0.20
- Highly transient, synchronized motion
- Excellent for ROM: high regularity

### Expected Data Files

```
data/cylinder_flow/
│
├── u_snapshots.npy
│   Shape: (n_grid, n_snapshots)
│   Example: (16384, 1000)  [extended domain]
│   Range: [-0.3, 1.2] m/s
│
├── v_snapshots.npy
│   Shape: (16384, 1000)
│   Range: [-0.6, 0.6] m/s
│
├── vorticity_snapshots.npy (optional)
│   Shape: (16384, 1000)
│   Content: ω = ∂v/∂x - ∂u/∂y
│
├── time_vector.npy
│   Shape: (1000,)
│   Content: Exact time of each snapshot
│   Important for frequency analysis
│
├── mesh.npy
│   Shape: (16384, 2)
│   Content: (x, y) coordinates
│
└── parameters.json
```

### parameters.json Format

```json
{
  "case_name": "Cylinder Flow (Von Kármán Vortex Street)",
  "description": "2D flow around circular cylinder",
  "reynolds_number": 100,
  "geometry": {
    "object": "circle",
    "diameter": 1.0,
    "center": [0.0, 0.0]
  },
  "domain": {
    "x_min": -5.0,
    "x_max": 15.0,
    "y_min": -8.0,
    "y_max": 8.0,
    "units": "m"
  },
  "grid": {
    "nx": 256,
    "ny": 256,
    "type": "non-uniform",
    "refinement": "cylinder boundary"
  },
  "flow": {
    "free_stream_velocity": 1.0,
    "kinematic_viscosity": 0.01,
    "density": 1.0
  },
  "snapshots": {
    "total": 1000,
    "time_start": 0.0,
    "time_end": 200.0,
    "dt": 0.2
  },
  "vortex_shedding": {
    "frequency": 0.164,
    "strouhal_number": 0.164,
    "period": 6.097
  },
  "components": ["u", "v"],
  "transient": true,
  "periodic": true
}
```

### Key Differences from Other Cases

1. **Much longer time integration** (1000 snapshots vs. 500)
   - Captures multiple shedding cycles
   - Better statistics for POD modes

2. **Extended domain** 
   - Far-field effects included
   - More spatial DOFs

3. **Time vector critical**
   - Frequency analysis requires exact times
   - Default assumption: uniform dt = 0.2 s

### Data Loading Example (Cylinder)

```python
import numpy as np
import json
from data_utils import DataHandler, SnaphotProcessor

# Load data
u = DataHandler.load_npy('data/cylinder_flow/u_snapshots.npy')
v = DataHandler.load_npy('data/cylinder_flow/v_snapshots.npy')
time = DataHandler.load_npy('data/cylinder_flow/time_vector.npy')

# Combine velocity components
snapshots = SnaphotProcessor.combine_velocity_components(u, v)

# Load metadata
with open('data/cylinder_flow/parameters.json', 'r') as f:
    params = json.load(f)

# Frequency analysis
dt = time[1] - time[0]
shedding_freq = params['vortex_shedding']['frequency']
print(f"Shedding period: {1/shedding_freq:.3f} time units")
print(f"Snapshots per period: {int(1/(shedding_freq*dt))}")
```

---

## Data Validation Checklist

Before running POD analysis, verify:

### ✓ File Structure
- [ ] All required .npy files present
- [ ] parameters.json exists and is valid JSON
- [ ] No spaces in filenames (use underscores)

### ✓ Array Properties
```python
import numpy as np

u = np.load('u_snapshots.npy')
v = np.load('v_snapshots.npy')

# Shape check
assert u.shape[0] > u.shape[1], "Data in wrong orientation!"
assert u.shape == v.shape, "Components have different shapes"

# Data integrity
assert np.isfinite(u).all(), "NaN or Inf detected in u!"
assert np.isfinite(v).all(), "NaN or Inf detected in v!"

# Normality check
assert np.linalg.norm(u, 'fro') > 0, "All-zero data!"
assert np.linalg.norm(v, 'fro') > 0, "All-zero data!"

# Value ranges (typical for normalized data)
assert np.abs(u).max() < 10, "Data might not be normalized"
assert np.abs(v).max() < 10, "Data might not be normalized"

print("✓ All validation checks passed!")
```

### ✓ Metadata
- [ ] All required JSON keys present
- [ ] Reynolds number reasonable (100-10000)
- [ ] n_snapshots in JSON matches actual array dimensions
- [ ] Time values increase monotonically

---

## Creating Sample Data

If you need to generate synthetic data for testing:

```python
from data_utils import create_sample_snapshot_data

# Create synthetic data
snapshots = create_sample_snapshot_data(
    n_spatial=1024,    # Number of spatial DOFs
    n_snapshots=100,   # Number of time instances
    n_components=2,    # u and v
    seed=42
)

# Save
np.save('data/test/synthetic_snapshots.npy', snapshots)
```

---

## Common Issues & Solutions

### Issue: "AttributeError: shape has more than 2 dimensions"
**Cause:** 3D data when 2D expected  
**Solution:** Check grid dimensions; flatten extra dimensions if needed

### Issue: "All singular values are equal"
**Cause:** Randomized/very noisy data without correlation structure  
**Solution:** Verify data comes from actual CFD simulation, not random noise

### Issue: "First POD mode is trivial (all same value)"
**Cause:** Data not centered before POD  
**Solution:** POD_Solver auto-centers, but verify with:
```python
pod = POD_Solver(snapshots)
pod.preprocess()
assert np.allclose(pod.centered_data.mean(axis=1), 0)
```

---

## Summary Table

| Case | Grid | n_spatial | n_snapshots | Steady? | Comments |
|------|------|-----------|-------------|---------|----------|
| Cavity | 128×128 | 32,768 | 500 | Yes | Best for learning |
| Step | 128×80 | 10,240 | 600 | No | Moderate complexity |
| Cylinder | 256×256 | 65,536 | 1000 | No | Periodic dynamics |

---

**Last Updated:** May 2026  
**Questions?** Refer to README.md or POD_MATHEMATICAL_FOUNDATION.md
