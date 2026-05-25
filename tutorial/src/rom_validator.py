"""
ROM Validation & Comparison Framework
=====================================
Tools for validating and comparing different ROM methods.

Features:
  - Error metrics (L2, H1, pointwise)
  - Convergence analysis
  - Stability assessment
  - Cross-validation
  - ROM vs Full simulation comparison

Author: CFD/SciML Expert
Date: 2026
"""

import numpy as np
from typing import Tuple, Dict, List, Optional
import warnings


class ROMValidator:
    """
    Validates ROM performance against ground truth data.
    """
    
    def __init__(self, verbose: bool = False):
        """Initialize validator."""
        self.verbose = verbose
        self.metrics = {}
    
    def compute_l2_error(self, u_pred: np.ndarray, u_true: np.ndarray) -> np.ndarray:
        """
        Compute L2 relative error.
        
        error_L2 = ||u_true - u_pred|| / ||u_true||
        """
        norm_true = np.linalg.norm(u_true, axis=0)
        norm_diff = np.linalg.norm(u_true - u_pred, axis=0)
        return norm_diff / (norm_true + 1e-10)
    
    def compute_h1_error(self, u_pred: np.ndarray, u_true: np.ndarray, 
                        grid_size: int = 128) -> np.ndarray:
        """
        Compute H1 seminorm error (includes gradient).
        """
        l2_error = self.compute_l2_error(u_pred, u_true)
        
        # Approximate gradient using finite differences
        grad_true = np.gradient(u_true, axis=0)
        grad_pred = np.gradient(u_pred, axis=0)
        
        grad_error = np.linalg.norm(grad_true - grad_pred, axis=0) / \
                    (np.linalg.norm(grad_true, axis=0) + 1e-10)
        
        h1_error = np.sqrt(l2_error**2 + grad_error**2)
        return h1_error
    
    def compute_pointwise_error(self, u_pred: np.ndarray, u_true: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Compute pointwise (spatial) error."""
        abs_error = np.abs(u_true - u_pred)
        rel_error = abs_error / (np.abs(u_true) + 1e-10)
        return abs_error, rel_error
    
    def compute_energy_error(self, u_pred: np.ndarray, u_true: np.ndarray) -> float:
        """Compute energy error (kinetic energy difference)."""
        E_true = 0.5 * np.mean(np.sum(u_true**2, axis=0))
        E_pred = 0.5 * np.mean(np.sum(u_pred**2, axis=0))
        return np.abs(E_true - E_pred) / (E_true + 1e-10)
    
    def compute_spectral_error(self, u_pred: np.ndarray, u_true: np.ndarray) -> float:
        """Compute spectral content error using FFT."""
        fft_true = np.fft.fft(u_true, axis=1)
        fft_pred = np.fft.fft(u_pred, axis=1)
        
        power_true = np.mean(np.abs(fft_true)**2, axis=0)
        power_pred = np.mean(np.abs(fft_pred)**2, axis=0)
        
        error = np.linalg.norm(power_true - power_pred) / (np.linalg.norm(power_true) + 1e-10)
        return error
    
    def validate_rom(self, u_pred: np.ndarray, u_true: np.ndarray, 
                    grid_size: int = 128, name: str = 'ROM') -> Dict:
        """
        Comprehensive ROM validation.
        
        Parameters:
            u_pred (np.ndarray): Predicted field (n_spatial, n_time)
            u_true (np.ndarray): Ground truth field (n_spatial, n_time)
            grid_size (int): Grid resolution
            name (str): ROM name for labeling
            
        Returns:
            Dict: Validation metrics
        """
        results = {
            'name': name,
            'l2_error_mean': np.mean(self.compute_l2_error(u_pred, u_true)),
            'l2_error_max': np.max(self.compute_l2_error(u_pred, u_true)),
            'l2_error_std': np.std(self.compute_l2_error(u_pred, u_true)),
        }
        
        try:
            results['h1_error_mean'] = np.mean(self.compute_h1_error(u_pred, u_true, grid_size))
        except:
            results['h1_error_mean'] = None
        
        results['energy_error'] = self.compute_energy_error(u_pred, u_true)
        
        try:
            results['spectral_error'] = self.compute_spectral_error(u_pred, u_true)
        except:
            results['spectral_error'] = None
        
        # Spatial error statistics
        abs_err, rel_err = self.compute_pointwise_error(u_pred, u_true)
        results['spatial_error_mean'] = np.mean(abs_err)
        results['spatial_error_max'] = np.max(abs_err)
        
        if self.verbose:
            self._print_validation_results(results)
        
        self.metrics[name] = results
        return results
    
    def _print_validation_results(self, results: Dict) -> None:
        """Print validation results."""
        print(f"\n{'='*60}")
        print(f"ROM VALIDATION: {results['name']}")
        print(f"{'='*60}")
        print(f"L2 Error:        mean={results['l2_error_mean']*100:.4f}% "
              f"max={results['l2_error_max']*100:.4f}% "
              f"std={results['l2_error_std']*100:.4f}%")
        
        if results['h1_error_mean'] is not None:
            print(f"H1 Error:        {results['h1_error_mean']*100:.4f}%")
        
        print(f"Energy Error:    {results['energy_error']*100:.4f}%")
        
        if results['spectral_error'] is not None:
            print(f"Spectral Error:  {results['spectral_error']*100:.4f}%")
        
        print(f"Spatial Error:   mean={results['spatial_error_mean']:.2e} "
              f"max={results['spatial_error_max']:.2e}")
        print("="*60 + "\n")
    
    def compare_methods(self, methods_dict: Dict[str, Tuple[np.ndarray, np.ndarray]], 
                       u_true: np.ndarray, grid_size: int = 128) -> Dict:
        """
        Compare multiple ROM methods.
        
        Parameters:
            methods_dict: Dict mapping method names to (u_pred, info) tuples
            u_true: Ground truth field
            grid_size: Grid resolution
            
        Returns:
            Dict: Comparison results
        """
        comparison = {}
        
        for name, (u_pred, info) in methods_dict.items():
            results = self.validate_rom(u_pred, u_true, grid_size, name)
            comparison[name] = results
        
        # Compute rankings
        print("\n" + "="*70)
        print("CROSS-METHOD COMPARISON")
        print("="*70)
        
        metrics_to_compare = ['l2_error_mean', 'energy_error']
        
        for metric in metrics_to_compare:
            print(f"\n{metric}:")
            sorted_methods = sorted(comparison.items(), 
                                   key=lambda x: x[1][metric])
            
            for rank, (method, results) in enumerate(sorted_methods, 1):
                print(f"  {rank}. {method:20s}: {results[metric]*100:8.4f}%")
        
        print("="*70 + "\n")
        
        return comparison
    
    def plot_error_distribution(self, u_pred: np.ndarray, u_true: np.ndarray, 
                               grid_size: int = 128) -> Dict:
        """Compute error statistics for plotting."""
        l2_errors = self.compute_l2_error(u_pred, u_true)
        abs_err, rel_err = self.compute_pointwise_error(u_pred, u_true)
        
        return {
            'l2_errors': l2_errors,
            'absolute_errors': abs_err,
            'relative_errors': rel_err,
            'stats': {
                'mean_l2': np.mean(l2_errors),
                'max_l2': np.max(l2_errors),
                'median_l2': np.median(l2_errors),
                'mean_abs': np.mean(abs_err),
                'max_abs': np.max(abs_err),
            }
        }


class ConvergenceAnalyzer:
    """
    Analyze ROM convergence properties.
    """
    
    @staticmethod
    def mode_convergence(errors: np.ndarray, n_modes_range: np.ndarray) -> Dict:
        """
        Analyze how error decreases with number of modes.
        
        Returns:
            Dict: Convergence metrics
        """
        # Exponential fit
        log_error = np.log(errors + 1e-10)
        coeffs = np.polyfit(n_modes_range, log_error, 1)
        decay_rate = coeffs[0]
        
        return {
            'decay_rate': decay_rate,
            'error_reduction_per_mode': 100 * (1 - np.exp(decay_rate)),
            'modes_for_1pct_error': n_modes_range[np.argmax(errors < 0.01)],
            'modes_for_01pct_error': n_modes_range[np.argmax(errors < 0.001)],
        }
    
    @staticmethod
    def temporal_convergence(errors_over_time: np.ndarray, time_vector: np.ndarray) -> Dict:
        """
        Analyze how error evolves over time.
        """
        return {
            'initial_error': errors_over_time[0],
            'final_error': errors_over_time[-1],
            'max_error': np.max(errors_over_time),
            'mean_error': np.mean(errors_over_time),
            'error_growth_rate': (errors_over_time[-1] - errors_over_time[0]) / time_vector[-1],
            'is_stable': np.mean(np.diff(errors_over_time)) < 0  # Error decreasing
        }
    
    @staticmethod
    def print_convergence_report(n_modes_range: np.ndarray, errors: np.ndarray) -> None:
        """Print convergence analysis report."""
        analysis = ConvergenceAnalyzer.mode_convergence(errors, n_modes_range)
        
        print("\nCONVERGENCE ANALYSIS")
        print("="*50)
        print(f"Decay rate: {analysis['decay_rate']:.4f}")
        print(f"Error reduction per mode: {analysis['error_reduction_per_mode']:.2f}%")
        
        if analysis['modes_for_1pct_error'] > 0:
            print(f"Modes for 1% error: {analysis['modes_for_1pct_error']}")
        
        if analysis['modes_for_01pct_error'] > 0:
            print(f"Modes for 0.1% error: {analysis['modes_for_01pct_error']}")
        
        print("="*50 + "\n")


class StabilityAssessment:
    """
    Assess long-term ROM stability.
    """
    
    @staticmethod
    def growth_rate_analysis(errors_over_time: np.ndarray, 
                            time_vector: np.ndarray) -> Dict:
        """Analyze error growth rate."""
        dt = np.mean(np.diff(time_vector))
        
        # Estimate exponential growth
        mask = errors_over_time > 1e-6
        if np.sum(mask) > 2:
            fit = np.polyfit(time_vector[mask], np.log(errors_over_time[mask]), 1)
            growth_rate = fit[0]
            doubling_time = np.log(2) / (growth_rate + 1e-10)
        else:
            growth_rate = 0
            doubling_time = np.inf
        
        return {
            'exponential_growth_rate': growth_rate,
            'error_doubling_time': doubling_time,
            'is_stable': growth_rate < 0.01,
            'max_integration_time': -np.log(100) / (growth_rate + 1e-10) * time_vector[-1]
        }
    
    @staticmethod
    def print_stability_report(errors_over_time: np.ndarray, 
                              time_vector: np.ndarray) -> None:
        """Print stability analysis report."""
        analysis = StabilityAssessment.growth_rate_analysis(errors_over_time, time_vector)
        
        print("\nSTABILITY ASSESSMENT")
        print("="*50)
        print(f"Growth rate: {analysis['exponential_growth_rate']:.6f}")
        print(f"Error doubling time: {analysis['error_doubling_time']:.2f}")
        print(f"Status: {'STABLE' if analysis['is_stable'] else 'UNSTABLE'}")
        print("="*50 + "\n")
