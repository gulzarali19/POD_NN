"""
Data Preprocessing and I/O Utilities for POD
=============================================
Handles loading, preprocessing, and saving snapshot data.

Author: CFD/SciML Expert
"""

import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Optional, List
import json


class DataHandler:
    """
    Utility class for loading and preprocessing CFD snapshot data.
    
    Supports multiple formats:
        - .npy (NumPy binary)
        - .npz (NumPy compressed)
        - .csv (Comma-separated values)
        - .h5 (HDF5, if h5py available)
    """
    
    @staticmethod
    def load_npy(filepath: str) -> np.ndarray:
        """Load data from NumPy .npy file."""
        data = np.load(filepath)
        print(f"✓ Loaded .npy file: {filepath}")
        print(f"  Shape: {data.shape}, Dtype: {data.dtype}")
        return data
    
    @staticmethod
    def load_npz(filepath: str, key: str = None) -> np.ndarray:
        """
        Load data from NumPy .npz file.
        
        Parameters:
            filepath (str): Path to .npz file
            key (str): Key to extract (if None, uses first key)
            
        Returns:
            np.ndarray: Loaded data
        """
        data_dict = np.load(filepath)
        
        if key is None:
            key = list(data_dict.keys())[0]
            print(f"✓ Available keys: {list(data_dict.keys())}")
            print(f"  Using key: {key}")
        
        data = data_dict[key]
        print(f"✓ Loaded .npz file: {filepath} (key='{key}')")
        print(f"  Shape: {data.shape}, Dtype: {data.dtype}")
        return data
    
    @staticmethod
    def load_csv(filepath: str, delimiter: str = ',',
                 skip_header: int = 0) -> np.ndarray:
        """
        Load data from CSV file.
        
        Parameters:
            filepath (str): Path to CSV file
            delimiter (str): Delimiter character
            skip_header (int): Number of header lines to skip
            
        Returns:
            np.ndarray: Loaded data
        """
        data = np.loadtxt(filepath, delimiter=delimiter, skiprows=skip_header)
        print(f"✓ Loaded CSV file: {filepath}")
        print(f"  Shape: {data.shape}, Dtype: {data.dtype}")
        return data
    
    @staticmethod
    def load_h5(filepath: str, key: str) -> np.ndarray:
        """
        Load data from HDF5 file.
        
        Parameters:
            filepath (str): Path to .h5 file
            key (str): Dataset key in HDF5 file
            
        Returns:
            np.ndarray: Loaded data
        """
        try:
            import h5py
        except ImportError:
            raise ImportError("h5py is required for HDF5 support. "
                            "Install with: pip install h5py")
        
        with h5py.File(filepath, 'r') as f:
            print(f"✓ Available keys in HDF5: {list(f.keys())}")
            data = f[key][:]
        
        print(f"✓ Loaded HDF5 file: {filepath} (key='{key}')")
        print(f"  Shape: {data.shape}, Dtype: {data.dtype}")
        return data
    
    @staticmethod
    def load_data(filepath: str, **kwargs) -> np.ndarray:
        """
        Automatically detect and load data file.
        
        Parameters:
            filepath (str): Path to data file
            **kwargs: Additional arguments for specific loaders
            
        Returns:
            np.ndarray: Loaded data
        """
        filepath = Path(filepath)
        suffix = filepath.suffix.lower()
        
        if suffix == '.npy':
            return DataHandler.load_npy(str(filepath))
        elif suffix == '.npz':
            return DataHandler.load_npz(str(filepath), **kwargs)
        elif suffix == '.csv':
            return DataHandler.load_csv(str(filepath), **kwargs)
        elif suffix == '.h5' or suffix == '.hdf5':
            return DataHandler.load_h5(str(filepath), **kwargs)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    
    @staticmethod
    def save_npy(data: np.ndarray, filepath: str) -> None:
        """Save data to NumPy .npy file."""
        np.save(filepath, data)
        print(f"✓ Saved to {filepath}")
    
    @staticmethod
    def save_npz(data_dict: Dict[str, np.ndarray], filepath: str) -> None:
        """
        Save multiple arrays to .npz file.
        
        Parameters:
            data_dict (Dict[str, np.ndarray]): Dictionary of name: array pairs
            filepath (str): Output path
        """
        np.savez(filepath, **data_dict)
        print(f"✓ Saved to {filepath}")
        print(f"  Keys: {list(data_dict.keys())}")
    
    @staticmethod
    def save_csv(data: np.ndarray, filepath: str, delimiter: str = ',') -> None:
        """Save data to CSV file."""
        np.savetxt(filepath, data, delimiter=delimiter)
        print(f"✓ Saved to {filepath}")


class SnaphotProcessor:
    """
    Processes raw CFD field data into snapshot matrices.
    
    Converts field data (e.g., velocity components on a grid) into
    snapshot format: (n_spatial_dofs, n_snapshots)
    """
    
    @staticmethod
    def flatten_field(field_data: np.ndarray) -> np.ndarray:
        """
        Flatten multi-dimensional field data to 1D spatial representation.
        
        Parameters:
            field_data (np.ndarray): Shape (...spatial_dims, n_snapshots) or similar
            
        Returns:
            np.ndarray: Flattened snapshots of shape (n_spatial_dofs, n_snapshots)
        """
        raise NotImplementedError("Override for specific field structure")
    
    @staticmethod
    def reshape_field(snapshot: np.ndarray, spatial_shape: Tuple[int, ...]) -> np.ndarray:
        """
        Reshape a single snapshot back to spatial grid.
        
        Parameters:
            snapshot (np.ndarray): 1D spatial vector
            spatial_shape (Tuple[int, ...]): Target grid shape
            
        Returns:
            np.ndarray: Reshaped field
        """
        return snapshot.reshape(spatial_shape)
    
    @staticmethod
    def combine_velocity_components(u: np.ndarray, v: np.ndarray,
                                    w: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Combine velocity components into a single snapshot matrix.
        
        For 2D flows (u, v):
            snapshot = [u_1, u_2, ..., v_1, v_2, ...]
        
        Parameters:
            u (np.ndarray): u-component snapshots, shape (n_spatial, n_snapshots)
            v (np.ndarray): v-component snapshots, shape (n_spatial, n_snapshots)
            w (np.ndarray): Optional w-component for 3D flows
            
        Returns:
            np.ndarray: Combined snapshots
        """
        if w is None:
            # 2D case
            combined = np.vstack([u, v])
        else:
            # 3D case
            combined = np.vstack([u, v, w])
        
        print(f"✓ Combined velocity components")
        print(f"  Combined shape: {combined.shape}")
        return combined
    
    @staticmethod
    def split_velocity_components(snapshots: np.ndarray, n_spatial: int,
                                 n_components: int = 2) -> List[np.ndarray]:
        """
        Split combined snapshots back into individual components.
        
        Parameters:
            snapshots (np.ndarray): Combined snapshots of shape (n_spatial*n_comp, n_snap)
            n_spatial (int): Number of spatial DOFs per component
            n_components (int): Number of velocity components (2 or 3)
            
        Returns:
            List[np.ndarray]: List of component arrays
        """
        components = []
        for i in range(n_components):
            start_idx = i * n_spatial
            end_idx = (i + 1) * n_spatial
            components.append(snapshots[start_idx:end_idx, :])
        
        return components
    
    @staticmethod
    def normalize_snapshots(snapshots: np.ndarray,
                           norm_type: str = 'l2') -> Tuple[np.ndarray, Dict]:
        """
        Normalize snapshot data.
        
        Parameters:
            snapshots (np.ndarray): Snapshot matrix
            norm_type (str): 'l2' (Frobenius norm) or 'minmax'
            
        Returns:
            Tuple[np.ndarray, Dict]: Normalized snapshots and scaling info
        """
        if norm_type == 'l2':
            norm_factor = np.linalg.norm(snapshots, 'fro')
            normalized = snapshots / norm_factor
            scaling_info = {'method': 'l2', 'factor': norm_factor}
        
        elif norm_type == 'minmax':
            data_min = np.min(snapshots)
            data_max = np.max(snapshots)
            normalized = (snapshots - data_min) / (data_max - data_min)
            scaling_info = {'method': 'minmax', 'min': data_min, 'max': data_max}
        
        else:
            raise ValueError(f"Unknown normalization: {norm_type}")
        
        print(f"✓ Normalized snapshots ({norm_type})")
        return normalized, scaling_info
    
    @staticmethod
    def denormalize_snapshots(normalized: np.ndarray,
                             scaling_info: Dict) -> np.ndarray:
        """
        Denormalize snapshot data to original scale.
        
        Parameters:
            normalized (np.ndarray): Normalized snapshots
            scaling_info (Dict): Scaling information from normalize_snapshots
            
        Returns:
            np.ndarray: Denormalized snapshots
        """
        method = scaling_info.get('method')
        
        if method == 'l2':
            denormalized = normalized * scaling_info['factor']
        
        elif method == 'minmax':
            denormalized = (normalized * (scaling_info['max'] - scaling_info['min']) +
                           scaling_info['min'])
        
        else:
            raise ValueError(f"Unknown normalization method: {method}")
        
        return denormalized
    
    @staticmethod
    def remove_outliers(snapshots: np.ndarray,
                       threshold: float = 3.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Remove outlier snapshots using z-score.
        
        Parameters:
            snapshots (np.ndarray): Snapshot matrix
            threshold (float): Z-score threshold (default: 3.0)
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Filtered snapshots and outlier indices
        """
        # Compute L2 norm of each snapshot
        norms = np.linalg.norm(snapshots, axis=0)
        
        # Compute z-scores
        mean_norm = np.mean(norms)
        std_norm = np.std(norms)
        z_scores = np.abs((norms - mean_norm) / std_norm)
        
        # Identify outliers
        outlier_indices = np.where(z_scores > threshold)[0]
        inlier_indices = np.where(z_scores <= threshold)[0]
        
        filtered = snapshots[:, inlier_indices]
        
        print(f"✓ Removed {len(outlier_indices)} outlier snapshots (threshold={threshold})")
        return filtered, outlier_indices


def create_sample_snapshot_data(n_spatial: int = 128, n_snapshots: int = 100,
                               n_components: int = 2, seed: int = 42) -> np.ndarray:
    """
    Create synthetic snapshot data for testing.
    
    Parameters:
        n_spatial (int): Number of spatial DOFs per component
        n_snapshots (int): Number of snapshots
        n_components (int): Number of velocity components
        seed (int): Random seed for reproducibility
        
    Returns:
        np.ndarray: Synthetic snapshots of shape (n_spatial*n_comp, n_snapshots)
    """
    np.random.seed(seed)
    
    # Create realistic snapshot data with multiple dominant modes
    snapshots = np.zeros((n_spatial * n_components, n_snapshots))
    
    # Mode 1: Large amplitude, slow decay
    mode1 = np.random.randn(n_spatial * n_components)
    amplitude1 = np.exp(-np.arange(n_snapshots) / 30) * np.cos(2 * np.pi * np.arange(n_snapshots) / 50)
    
    # Mode 2: Medium amplitude
    mode2 = np.random.randn(n_spatial * n_components)
    amplitude2 = np.sin(2 * np.pi * np.arange(n_snapshots) / 25) * 0.5
    
    # Mode 3: Low amplitude
    mode3 = np.random.randn(n_spatial * n_components) * 0.3
    amplitude3 = np.random.randn(n_snapshots) * 0.2
    
    # Combine modes
    for i in range(n_snapshots):
        snapshots[:, i] = (amplitude1[i] * mode1 +
                          amplitude2[i] * mode2 +
                          amplitude3[i] * mode3)
    
    return snapshots
