"""
POD Tutorial - Complete ROM Framework
=====================================

Proper Orthogonal Decomposition (POD) + Neural Networks for Reduced Order Modeling

Modules:
    - pod_solver: Core POD_Solver for ROM basis extraction
    - data_utils: Data preprocessing and I/O
    - data_generator: Synthetic CFD data generation
    - pod_galerkin_rom: Intrusive ROM time-stepping
    - pod_nn_surrogate: Neural network ROM surrogates
    - rom_validator: Validation and comparison tools

Quick Start:
    >>> from pod_solver import POD_Solver
    >>> from data_utils import DataHandler
    >>> 
    >>> snapshots = DataHandler.load_npy('data/cavity_flow/u_snapshots.npy')
    >>> pod = POD_Solver(snapshots)
    >>> pod.compute_svd()
    >>> rom = PODGalerkinROM.from_pod_solver(pod)
    >>> t, a, u = rom.predict(init_coeffs, t_final=1.0)

Author: CFD/SciML Expert
Date: 2026
Version: 2.0.0
"""

__version__ = "2.0.0"

# Core POD implementation
from .pod_solver import POD_Solver
from .data_utils import DataHandler, SnaphotProcessor, create_sample_snapshot_data
from .data_generator import SyntheticCFDGenerator, generate_all_test_data

# ROM implementations
from .pod_galerkin_rom import PODGalerkinROM
from .pod_nn_surrogate import PODNeuralNetwork, PODNNSurrogate, compare_rom_methods

# Validation tools
from .rom_validator import ROMValidator, ConvergenceAnalyzer, StabilityAssessment

__all__ = [
    # Core
    'POD_Solver',
    'DataHandler',
    'SnaphotProcessor',
    'create_sample_snapshot_data',
    
    # Data generation
    'SyntheticCFDGenerator',
    'generate_all_test_data',
    
    # ROM methods
    'PODGalerkinROM',
    'PODNeuralNetwork',
    'PODNNSurrogate',
    'compare_rom_methods',
    
    # Validation
    'ROMValidator',
    'ConvergenceAnalyzer',
    'StabilityAssessment'
]
