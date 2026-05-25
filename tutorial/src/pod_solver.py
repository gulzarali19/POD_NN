"""
Proper Orthogonal Decomposition (POD) Solver
=============================================
A modular implementation for Reduced Order Modeling (ROM) of fluid flows.

Author: CFD/SciML Expert
Date: 2026
"""

import numpy as np
from typing import Tuple, Dict, List, Optional
from scipy.linalg import svd
from scipy.spatial.distance import euclidean
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


class POD_Solver:
    """
    A comprehensive POD solver for reduced order modeling of fluid flows.
    
    Attributes:
        snapshots (np.ndarray): Snapshot matrix of shape (n_spatial, n_snapshots)
        mean_field (np.ndarray): Mean field (temporal average)
        centered_data (np.ndarray): Data after mean subtraction
        U (np.ndarray): Left singular vectors (POD modes)
        s (np.ndarray): Singular values
        Vt (np.ndarray): Right singular vectors (temporal coefficients)
        energy (np.ndarray): Cumulative energy content
        n_modes_computed (int): Number of modes computed
    """
    
    def __init__(self, snapshots: np.ndarray, verbose: bool = True):
        """
        Initialize the POD solver with snapshot data.
        
        Parameters:
            snapshots (np.ndarray): Snapshot matrix of shape (n_spatial, n_snapshots)
            verbose (bool): Print computation details
        """
        self.snapshots = snapshots
        self.n_spatial, self.n_snapshots = snapshots.shape
        self.verbose = verbose
        
        # Initialize storage
        self.mean_field = None
        self.centered_data = None
        self.U = None  # POD modes
        self.s = None  # Singular values
        self.Vt = None  # Temporal coefficients
        self.energy = None
        self.cumulative_energy = None
        self.n_modes_computed = 0
        
        if self.verbose:
            print(f"POD Solver initialized with {self.n_spatial} spatial DoFs "
                  f"and {self.n_snapshots} snapshots.")
    
    def preprocess(self) -> None:
        """
        Preprocess snapshots: compute mean field and center data.
        
        The centered data X' = X - mean(X) where X is the snapshot matrix.
        """
        self.mean_field = np.mean(self.snapshots, axis=1, keepdims=True)
        self.centered_data = self.snapshots - self.mean_field
        
        if self.verbose:
            print("✓ Data preprocessing complete (mean subtraction)")
            print(f"  Mean field shape: {self.mean_field.shape}")
            print(f"  Centered data shape: {self.centered_data.shape}")
    
    def compute_svd(self, method: str = 'numpy') -> None:
        """
        Compute Singular Value Decomposition (SVD) of centered snapshots.
        
        For tall-thin matrices (n_spatial > n_snapshots), uses Method of Snapshots:
            X'X'^T = UΣ²U^T
        
        Parameters:
            method (str): 'numpy' (default) or 'scipy'
        """
        if self.centered_data is None:
            self.preprocess()
        
        if method == 'numpy':
            self.U, self.s, self.Vt = np.linalg.svd(
                self.centered_data, full_matrices=False
            )
        elif method == 'scipy':
            self.U, self.s, self.Vt = svd(
                self.centered_data, full_matrices=False
            )
        else:
            raise ValueError(f"Unknown method: {method}")
        
        self.n_modes_computed = len(self.s)
        self._compute_energy()
        
        if self.verbose:
            print("✓ SVD computation complete")
            print(f"  Number of modes: {self.n_modes_computed}")
            print(f"  Singular value range: [{self.s[-1]:.4e}, {self.s[0]:.4e}]")
    
    def _compute_energy(self) -> None:
        """Compute cumulative energy (variance) captured by POD modes."""
        total_energy = np.sum(self.s**2)
        energy_per_mode = (self.s**2) / total_energy
        self.cumulative_energy = np.cumsum(energy_per_mode)
        self.energy = energy_per_mode
    
    def project_onto_modes(self, snapshots: Optional[np.ndarray] = None,
                          n_modes: int = 5) -> np.ndarray:
        """
        Project snapshots onto the first n_modes POD modes.
        
        Returns temporal coefficients a_i(t) such that:
            Φ(x,t) ≈ Σ a_i(t) * ψ_i(x)
        
        Parameters:
            snapshots (np.ndarray): Snapshot matrix (default: self.snapshots)
            n_modes (int): Number of modes to use
            
        Returns:
            np.ndarray: Temporal coefficients of shape (n_modes, n_snapshots)
        """
        if snapshots is None:
            snapshots = self.snapshots
        
        if self.U is None:
            self.compute_svd()
        
        if n_modes > self.n_modes_computed:
            raise ValueError(f"n_modes ({n_modes}) exceeds computed modes "
                           f"({self.n_modes_computed})")
        
        # Center the snapshots with respect to stored mean
        centered_snaps = snapshots - self.mean_field
        
        # Project onto first n_modes
        modes = self.U[:, :n_modes]
        temporal_coeff = modes.T @ centered_snaps
        
        return temporal_coeff
    
    def reconstruct(self, n_modes: int = 5,
                   snapshots: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Reconstruct snapshots from POD modes.
        
        Φ_reconstructed = mean + Σ a_i(t) * ψ_i(x)
        
        Parameters:
            n_modes (int): Number of modes to use
            snapshots (np.ndarray): Optional snapshots to project (default: self.snapshots)
            
        Returns:
            np.ndarray: Reconstructed snapshot matrix
        """
        if snapshots is None:
            snapshots = self.snapshots
        
        temporal_coeff = self.project_onto_modes(snapshots, n_modes)
        modes = self.U[:, :n_modes]
        
        # Reconstruct: mean + modes @ temporal coefficients
        reconstructed = self.mean_field + modes @ temporal_coeff
        
        return reconstructed
    
    def get_modes(self, n_modes: int = 4) -> np.ndarray:
        """
        Retrieve the first n_modes POD basis functions.
        
        Parameters:
            n_modes (int): Number of modes to retrieve
            
        Returns:
            np.ndarray: POD modes of shape (n_spatial, n_modes)
        """
        if self.U is None:
            self.compute_svd()
        
        if n_modes > self.n_modes_computed:
            raise ValueError(f"n_modes ({n_modes}) exceeds computed modes")
        
        return self.U[:, :n_modes]
    
    def energy_content(self, n_modes: int) -> float:
        """
        Get cumulative energy captured by first n_modes.
        
        Parameters:
            n_modes (int): Number of modes
            
        Returns:
            float: Cumulative energy (percentage if multiplied by 100)
        """
        if self.cumulative_energy is None:
            self.compute_svd()
        
        return self.cumulative_energy[n_modes - 1]
    
    def error_l2(self, n_modes: int,
                snapshots: Optional[np.ndarray] = None) -> float:
        """
        Compute L2 relative error: ||X - X_reconstructed||_F / ||X||_F
        
        Parameters:
            n_modes (int): Number of modes for reconstruction
            snapshots (np.ndarray): Optional snapshots (default: self.snapshots)
            
        Returns:
            float: Relative L2 error
        """
        if snapshots is None:
            snapshots = self.snapshots
        
        reconstructed = self.reconstruct(n_modes, snapshots)
        error = np.linalg.norm(snapshots - reconstructed, 'fro')
        norm_orig = np.linalg.norm(snapshots, 'fro')
        
        return error / norm_orig
    
    def summary(self) -> Dict[str, any]:
        """Return a summary of the POD analysis."""
        if self.U is None:
            self.compute_svd()
        
        summary_dict = {
            'n_spatial_dofs': self.n_spatial,
            'n_snapshots': self.n_snapshots,
            'n_modes': self.n_modes_computed,
            'singular_values': self.s.copy(),
            'cumulative_energy': self.cumulative_energy.copy(),
        }
        
        return summary_dict
    
    def plot_modes(self, n_modes: int = 4, spatial_shape: Tuple[int, int] = None,
                  cmap: str = 'RdBu_r', figsize: Tuple[int, int] = (12, 10)) -> plt.Figure:
        """
        Visualize the first n_modes POD basis functions.
        
        Parameters:
            n_modes (int): Number of modes to plot
            spatial_shape (Tuple[int, int]): 2D shape for spatial grid (e.g., (128, 128))
            cmap (str): Colormap for visualization
            figsize (Tuple[int, int]): Figure size
            
        Returns:
            plt.Figure: Matplotlib figure object
        """
        modes = self.get_modes(n_modes)
        
        fig = plt.figure(figsize=figsize)
        gs = GridSpec(2, (n_modes + 1) // 2, figure=fig)
        
        for i in range(n_modes):
            ax = fig.add_subplot(gs[i // ((n_modes + 1) // 2), i % ((n_modes + 1) // 2)])
            
            mode_data = modes[:, i]
            
            if spatial_shape is not None:
                mode_data = mode_data.reshape(spatial_shape)
                im = ax.contourf(mode_data, levels=20, cmap=cmap)
                ax.set_title(f'Mode {i+1} (Energy: {self.energy[i]*100:.2f}%)')
                plt.colorbar(im, ax=ax)
            else:
                ax.plot(mode_data, 'o-', linewidth=1.5)
                ax.set_title(f'Mode {i+1} (Energy: {self.energy[i]*100:.2f}%)')
                ax.set_xlabel('Spatial DOF')
                ax.set_ylabel('Amplitude')
            
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_cumulative_energy(self, n_max: int = None,
                               figsize: Tuple[int, int] = (10, 6)) -> plt.Figure:
        """
        Plot cumulative energy content vs. number of modes.
        
        Parameters:
            n_max (int): Maximum number of modes to display
            figsize (Tuple[int, int]): Figure size
            
        Returns:
            plt.Figure: Matplotlib figure object
        """
        if self.cumulative_energy is None:
            self.compute_svd()
        
        n_max = n_max or self.n_modes_computed
        n_modes_range = np.arange(1, n_max + 1)
        
        fig, ax = plt.subplots(figsize=figsize)
        ax.semilogy(n_modes_range, 1 - self.cumulative_energy[:n_max], 'o-', 
                   linewidth=2.5, markersize=6, label='Relative error')
        ax.axhline(y=0.01, color='r', linestyle='--', alpha=0.7, label='1% error')
        ax.axhline(y=0.001, color='g', linestyle='--', alpha=0.7, label='0.1% error')
        
        ax.set_xlabel('Number of POD Modes', fontsize=12)
        ax.set_ylabel('Relative Error (1 - Energy %)', fontsize=12)
        ax.set_title('POD: Cumulative Energy Content', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, which='both')
        ax.legend()
        
        return fig
    
    def plot_reconstruction_error(self, max_modes: int = None,
                                 figsize: Tuple[int, int] = (10, 6)) -> plt.Figure:
        """
        Plot L2 reconstruction error vs. number of modes.
        
        Parameters:
            max_modes (int): Maximum number of modes to test
            figsize (Tuple[int, int]): Figure size
            
        Returns:
            plt.Figure: Matplotlib figure object
        """
        max_modes = max_modes or min(20, self.n_modes_computed)
        
        errors = []
        for n in range(1, max_modes + 1):
            err = self.error_l2(n)
            errors.append(err)
        
        fig, ax = plt.subplots(figsize=figsize)
        ax.semilogy(range(1, max_modes + 1), errors, 'o-', linewidth=2.5, markersize=6)
        
        ax.set_xlabel('Number of POD Modes', fontsize=12)
        ax.set_ylabel('L2 Relative Error', fontsize=12)
        ax.set_title('POD: Reconstruction Error', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, which='both')
        
        return fig
