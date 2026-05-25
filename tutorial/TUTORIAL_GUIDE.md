# Comprehensive ROM-POD Tutorial Guide

## Welcome to the POD + Neural Network Tutorial!

This tutorial provides a complete introduction to **Proper Orthogonal Decomposition (POD)** combined with **Neural Networks (NN)** for **Reduced Order Modeling (ROM)** of fluid flows.

---

## 📚 Learning Path

### **Level 1: Fundamentals (Notebooks 01)**
**Time**: ~1-2 hours

Start with **01_POD_Fundamentals.ipynb** to learn:
- ✓ SVD and POD theory
- ✓ Mode extraction and energy analysis
- ✓ Reconstruction from reduced basis
- ✓ Error metrics and convergence

**Key Results**: 
- Understand why first few modes capture most energy
- See how POD achieves 1000x dimensionality reduction
- Learn to interpret modal structures

---

### **Level 2: Applications (Notebooks 02-04)**
**Time**: ~2-3 hours

Analyze three canonical CFD benchmark problems:

#### **Notebook 02: Cavity Flow Analysis**
- Internal recirculating flow
- Well-suited for POD (high modal concentration)
- Training vs testing data splits
- Mode contribution analysis

#### **Notebook 03: Backward-Facing Step**
- Complex separation/reattachment
- Requires more modes than cavity
- Spatial error distribution
- Comparison with simpler cases

#### **Notebook 04: Cylinder Flow & Vortex Shedding**
- Periodic dynamics (Von Kármán street)
- Frequency analysis and Strouhal number
- Paired mode structures
- Comparative benchmark

---

### **Level 3: Advanced ROM Methods**
**Time**: ~3-4 hours

#### **POD-Galerkin ROM** (`src/pod_galerkin_rom.py`)
Intrusive ROM that projects Navier-Stokes onto POD basis:
```python
from pod_galerkin_rom import PODGalerkinROM
rom = PODGalerkinROM.from_pod_solver(pod_solver)
t, a, u = rom.predict(a_init, t_final=1.0, n_steps=100)
```

**Capabilities:**
- Time-stepping predictions
- Multiple integration schemes (RK4, implicit Euler)
- Stability analysis
- ROM parameter tuning

#### **POD-NN Surrogate** (`src/pod_nn_surrogate.py`)
Neural network learns latent space dynamics:
```python
from pod_nn_surrogate import PODNNSurrogate
surrogate = PODNNSurrogate(pod_modes, pod_energy, mean_field)
surrogate.train_from_snapshots(pod_coeffs, epochs=100)
a_forecast, u_forecast = surrogate.forecast_dynamics(a_init, n_steps=50)
```

**Advantages:**
- Non-intrusive (no Navier-Stokes discretization needed)
- Fast training and prediction
- Flexible architecture
- Transfer learning possibilities

---

### **Level 4: Validation & Comparison**
**Time**: ~1-2 hours

Comprehensive ROM validation tools:

```python
from rom_validator import ROMValidator, ConvergenceAnalyzer

validator = ROMValidator(verbose=True)
results = validator.validate_rom(u_pred, u_true, grid_size=128)
comparison = validator.compare_methods(methods_dict, u_true)
```

**Metrics Computed:**
- L2 error (global)
- H1 seminorm error (includes gradients)
- Pointwise spatial error
- Energy error
- Spectral error (frequency content)
- Convergence rates
- Stability assessment

---

## 🚀 Quick Start (5 minutes)

### Step 1: Generate Test Data
```python
from src.data_generator import generate_all_test_data
generate_all_test_data()  # Creates synthetic CFD data
```

### Step 2: Run First Notebook
```bash
jupyter notebook notebooks/01_POD_Fundamentals.ipynb
```

### Step 3: Extract POD Basis
```python
import sys
sys.path.insert(0, 'src')
from pod_solver import POD_Solver
from data_utils import DataHandler
import numpy as np

# Load data
u = DataHandler.load_npy('data/cavity_flow/u_snapshots.npy')
v = DataHandler.load_npy('data/cavity_flow/v_snapshots.npy')
snapshots = np.vstack([u, v])

# Compute POD
pod = POD_Solver(snapshots)
pod.preprocess()
pod.compute_svd()

# Analyze results
pod.plot_cumulative_energy()
pod.plot_modes(n_modes=4, spatial_shape=(128, 128, 2))
```

---

## 📊 Project Structure

```
tutorial/
├── README.md .......................... Project overview
├── 
├── src/
│   ├── __init__.py .................... Module interface
│   ├── pod_solver.py .................. Core POD implementation
│   ├── data_utils.py .................. Data I/O & preprocessing
│   ├── data_generator.py .............. Synthetic data generation
│   ├── pod_galerkin_rom.py ............ Intrusive ROM
│   ├── pod_nn_surrogate.py ............ Neural network ROM
│   └── rom_validator.py ............... Validation framework
│
├── notebooks/
│   ├── 01_POD_Fundamentals.ipynb ...... Theory + basics
│   ├── 02_Cavity_Flow_Analysis.ipynb . Application study 1
│   ├── 03_Backward_Facing_Step.ipynb . Application study 2
│   └── 04_Cylinder_Flow_Analysis.ipynb Application study 3
│
├── data/
│   ├── cavity_flow/
│   │   ├── u_snapshots.npy
│   │   ├── v_snapshots.npy
│   │   ├── time_vector.npy
│   │   └── parameters.json
│   ├── backward_facing_step/
│   │   ├── u_snapshots.npy
│   │   ├── v_snapshots.npy
│   │   ├── time_vector.npy
│   │   └── parameters.json
│   └── cylinder_flow/
│       ├── u_snapshots.npy
│       ├── v_snapshots.npy
│       ├── time_vector.npy
│       └── parameters.json
│
├── results/ ........................... Output plots & data
│
└── docs/
    ├── POD_MATHEMATICAL_FOUNDATION.md . Full theory
    ├── DATA_SPECIFICATIONS.md ........ Data formats
    └── QUICK_REFERENCE.md ........... Quick API reference
```

---

## 🔧 API Quick Reference

### POD_Solver (Core class)
```python
pod = POD_Solver(snapshots, verbose=True)

# Workflow
pod.preprocess()                      # Mean subtraction
pod.compute_svd()                     # SVD computation
modes = pod.get_modes(n_modes=15)    # Extract basis
recon = pod.reconstruct(n_modes, snapshots)
error = pod.error_l2(n_modes, snapshots)
energy = pod.energy_content(n_modes)

# Visualization
pod.plot_modes(n_modes=4, spatial_shape=(128, 128, 2))
pod.plot_cumulative_energy(n_max=50)
pod.plot_reconstruction_error(max_modes=40)
```

### PODGalerkinROM (Intrusive ROM)
```python
rom = PODGalerkinROM.from_pod_solver(pod, verbose=True)
rom.set_parameters(Re=1000, dt=0.01)

# Prediction
t_pred, a_pred, u_pred = rom.predict(
    a_init, t_final=1.0, n_steps=100, method='explicit'
)

# Stability analysis
stability = rom.stability_analysis(a0, t_final=10.0)
```

### PODNNSurrogate (Neural Network ROM)
```python
surrogate = PODNNSurrogate(pod_modes, pod_energy, mean_field)

# Training
history = surrogate.train_from_snapshots(
    pod_coeffs, epochs=100, learning_rate=0.001
)

# Forecasting
a_forecast, u_forecast = surrogate.forecast_dynamics(a_init, n_steps=50)
```

### ROMValidator (Validation)
```python
validator = ROMValidator(verbose=True)

# Single ROM
results = validator.validate_rom(u_pred, u_true, grid_size=128, name='ROM1')

# Compare methods
comparison = validator.compare_methods(
    {'Method1': (u_pred1, info1), 'Method2': (u_pred2, info2)},
    u_true
)
```

---

## 📈 Typical Results

### Cavity Flow (Re=1000)
- **Dominant mode energy**: ~0.35
- **Modes for 95% energy**: 8
- **Modes for 99% energy**: 12
- **Dimensionality reduction**: 16384 → 12 (1365x)
- **ROM error (<1%)**: Achievable with 15-20 modes
- **Speedup**: ~100-1000x

### Backward-Facing Step (Re=389)
- **Modes for 95% energy**: 12
- **Complexity**: Intermediate
- **Reason**: Separation/reattachment zones
- **Best ROM**: 20-30 modes

### Cylinder Flow (Re=100, Von Kármán)
- **Shedding frequency**: St ≈ 0.164
- **Periodic modes**: Paired (shedding frequency)
- **Modes for 95% energy**: 14
- **Challenges**: Captures only mean motion

---

## 💡 Key Insights

### Why POD Works
1. **Optimality**: POD basis minimizes reconstruction error (Karhunen-Loève theorem)
2. **Data-driven**: Automatically discovers dominant structures
3. **Exponential decay**: First few modes contain most energy
4. **Compression**: 10-100 modes capture complex dynamics

### When POD Fails
1. **Multiple timescales**: Needs many modes for fast + slow
2. **Chaotic systems**: Energy spreads over many modes
3. **Discontinuities**: Gibbs phenomenon at shocks
4. **Parameters vary**: Different Re needs different basis

### POD vs NN Surrogates
| Aspect | POD-Galerkin | POD-NN |
|--------|--------------|--------|
| Intrusive | Yes | No |
| Training | Fast SVD | NN training |
| Interpretability | High | Low |
| Generalization | Limited | Better |
| Speed | Very fast | Fast |
| Stability | Guaranteed (physics) | Empirical |

---

## 🎯 Recommended Exercises

### Exercise 1: Energy Analysis
- Change grid resolution, observe modal concentration
- Compare energy decay across test cases
- Interpret physical meaning of dominant modes

### Exercise 2: ROM Accuracy
- Vary number of modes, plot convergence
- Compare training vs test error
- Identify optimal mode count for 1% accuracy

### Exercise 3: Time Integration
- Switch between RK4 and implicit Euler
- Vary time step, observe stability
- Compare ROM predictions vs truth

### Exercise 4: Neural Network Training
- Vary hidden layer sizes
- Change activation functions
- Observe effect on forecast accuracy

### Exercise 5: Cross-Validation
- Train ROM on first 80% of snapshots
- Test on held-out 20%
- Assess generalization ability

---

## 📚 Further Reading

### Theory
- Holmes, Lumley, & Berkooz (1996) - "Turbulence, Coherent Structures, Dynamical Systems and Symmetry"
- Volkwein (2011) - "Model Reduction using Proper Orthogonal Decomposition"
- Quarteroni et al. (2015) - "Reduced Order Methods for Modeling and Computational Reduction"

### Applications
- Astrid et al. (2008) - "Missing Point Estimation in Models Described by Proper Orthogonal Decomposition"
- Carlberg et al. (2011) - "Efficient Structure-Preserving Model Reduction for Nonlinear Dynamical Systems"

### Neural Networks for ROMs
- Raissi et al. (2019) - "Physics-informed Neural Networks"
- Lee & You (2019) - "Data-driven prediction of unsteady flows over a cylinder"

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pod_solver'"
**Solution**: Ensure `sys.path.insert(0, 'src')` before imports

### Issue: Out of memory when loading data
**Solution**: Use `grid_size=64` instead of `128` in data generator

### Issue: Neural network training diverges
**Solution**: Reduce learning rate (try 0.0001) or add regularization

### Issue: ROM predictions blow up over time
**Solution**: Increase time step (`dt`) or switch to implicit Euler

---

## ✅ Completion Checklist

- [ ] Install dependencies (`numpy`, `scipy`, `matplotlib`)
- [ ] Run `generate_all_test_data()` to create synthetic CFD data
- [ ] Complete Notebook 01 (POD Fundamentals)
- [ ] Complete Notebook 02 (Cavity Flow)
- [ ] Complete Notebook 03 (Step Flow)
- [ ] Complete Notebook 04 (Cylinder Flow)
- [ ] Build POD-Galerkin ROM and test prediction
- [ ] Train POD-NN surrogate and compare with Galerkin
- [ ] Run ROM validation on all test cases
- [ ] Summarize findings and insights

---

## 📞 Questions & Support

For issues or questions:
1. Check the QUICK_REFERENCE.md file
2. Review error messages carefully
3. Examine notebook outputs for clues
4. Verify data file existence and format

---

## License

This tutorial is provided as-is for educational and research purposes.

**Version**: 2.0.0  
**Last Updated**: May 2026  
**Author**: CFD/SciML Expert
