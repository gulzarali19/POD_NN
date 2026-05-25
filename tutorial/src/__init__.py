"""
POD Tutorial - Core Modules
===========================

Proper Orthogonal Decomposition (POD) for Reduced Order Modeling of Fluid Flows

Modules:
    - pod_solver: Main POD_Solver class for ROM analysis
    - data_utils: Data preprocessing and I/O utilities

Example:
    >>> from pod_solver import POD_Solver
    >>> from data_utils import DataHandler
    >>> 
    >>> snapshots = DataHandler.load_npy('data/cavity_flow/u_snapshots.npy')
    >>> pod = POD_Solver(snapshots)
    >>> pod.compute_svd()
    >>> pod.plot_cumulative_energy()

Author: CFD/SciML Expert
Date: 2026
"""

__version__ = "1.0.0"
__all__ = ['POD_Solver', 'DataHandler', 'SnaphotProcessor']

from .pod_solver import POD_Solver
from .data_utils import DataHandler, SnaphotProcessor, create_sample_snapshot_data
