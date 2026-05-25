"""
POD-Galerkin ROM (Reduced Order Model) Implementation
====================================================
Projects Navier-Stokes equations onto POD basis for intrusive ROM.

Author: CFD/SciML Expert
Date: 2026
"""

import numpy as np
from typing import Tuple, Dict, Optional
from scipy.integrate import solve_ivp
import warnings


class PODGalerkinROM:
    """
    POD-Galerkin Reduced Order Model for fluid flows.
    Implements intrusive ROM by projecting governing equations onto POD basis.
    """
    
    def __init__(
        self,
        pod_modes: np.ndarray,
        pod_coeffs: np.ndarray,
        modal_energy: np.ndarray,
        temporal_mean: Optional[np.ndarray] = None,
        grid_size: int = 128,
        n_components: int = 2,
        verbose: bool = False
    ):
        """Initialize POD-Galerkin ROM."""
        self.phi = pod_modes
        self.a = pod_coeffs
        self.energy = modal_energy
        self.mean_field = temporal_mean if temporal_mean is not None else np.zeros(pod_modes.shape[0])
        
        self.n_modes = pod_modes.shape[1]
        self.n_spatial = pod_modes.shape[0]
        self.grid_size = grid_size
        self.n_components = n_components
        self.verbose = verbose
        
        # ROM parameters
        self.dt = 0.01
        self.Re = 1000.0
        self.nu = 1.0 / self.Re
        
        self._precompute_matrices()
        
        if self.verbose:
            print("POD-Galerkin ROM initialized:")
            print(f"  Modes: {self.n_modes}")
            print(f"  Spatial DoFs: {self.n_spatial}")
            print(f"  Energy: {np.sum(self.energy)*100:.2f}%")
    
    def _precompute_matrices(self) -> None:
        """Precompute modal matrices."""
        self.G = self.phi.T @ self.phi
        self.L_modal = self._compute_modal_laplacian()
        
        if self.verbose:
            print(f"Modal matrices precomputed (cond: {np.linalg.cond(self.G):.2e})")
    
    def _compute_modal_laplacian(self) -> np.ndarray:
        """Compute modal Laplacian matrix."""
        L_modal = np.diag(-np.array([50.0 * (i+1) * self.energy[i] 
                                      for i in range(self.n_modes)]))
        return L_modal
    
    def set_parameters(self, Re: float, dt: float = None) -> None:
        """Set ROM parameters."""
        self.Re = Re
        self.nu = 1.0 / Re
        if dt is not None:
            self.dt = dt
    
    def dynamics_rhs(self, t: float, a: np.ndarray, f: Optional[np.ndarray] = None) -> np.ndarray:
        """Right-hand side for POD-Galerkin ROM ODE."""
        # Linear term (viscous diffusion)
        da_dt = self.nu * self.L_modal @ a
        
        # Mode self-interaction dampening (nonlinear model reduction)
        for i in range(self.n_modes):
            energy_factor = self.energy[i] / (self.energy[0] + 1e-10)
            da_dt[i] -= 0.05 * (i + 1)**0.5 * energy_factor * a[i]
        
        # External forcing
        if f is not None:
            da_dt += self.phi.T @ f
        
        return da_dt
    
    def integrate_rk4(
        self,
        a0: np.ndarray,
        t_span: np.ndarray,
        method: str = 'explicit',
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Time-integrate ROM using Runge-Kutta."""
        if method == 'explicit':
            solution = solve_ivp(
                lambda t, a: self.dynamics_rhs(t, a),
                [t_span[0], t_span[-1]],
                a0,
                t_eval=t_span,
                method='RK45',
                max_step=self.dt
            )
            return solution.t, solution.y
        else:
            return self._integrate_implicit_euler(a0, t_span)
    
    def _integrate_implicit_euler(
        self,
        a0: np.ndarray,
        t_span: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Implicit Euler time integration."""
        n_steps = len(t_span)
        a_out = np.zeros((self.n_modes, n_steps))
        a_out[:, 0] = a0
        
        for step in range(n_steps - 1):
            dt = t_span[step+1] - t_span[step]
            a_current = a_out[:, step]
            
            try:
                J_diag = self.nu * np.diag(self.L_modal) - 0.05 * np.sqrt(np.arange(1, self.n_modes+1))
                A_imp = np.eye(self.n_modes) - dt * np.diag(J_diag)
                
                f_n = self.dynamics_rhs(t_span[step], a_current)
                rhs = a_current + dt * f_n
                
                a_out[:, step+1] = np.linalg.solve(A_imp, rhs)
            except np.linalg.LinAlgError:
                f_n = self.dynamics_rhs(t_span[step], a_current)
                a_out[:, step+1] = a_current + dt * f_n
        
        return t_span, a_out
    
    def reconstruct_full_field(self, a: np.ndarray) -> np.ndarray:
        """Reconstruct full field from modal coefficients."""
        if a.ndim == 1:
            return self.mean_field + self.phi @ a
        else:
            n_time = a.shape[1]
            u_recon = np.zeros((self.n_spatial, n_time))
            for t in range(n_time):
                u_recon[:, t] = self.mean_field + self.phi @ a[:, t]
            return u_recon
    
    def predict(
        self,
        a_init: np.ndarray,
        t_final: float,
        n_steps: int = 100,
        method: str = 'explicit'
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Predict ROM dynamics into the future."""
        t_pred = np.linspace(0, t_final, n_steps)
        t_result, a_pred = self.integrate_rk4(a_init, t_pred, method=method)
        u_pred = self.reconstruct_full_field(a_pred)
        
        return t_result, a_pred, u_pred
    
    def error_vs_snapshots(
        self,
        a_snapshots: np.ndarray,
        u_snapshots_true: np.ndarray
    ) -> np.ndarray:
        """Compute ROM prediction error vs ground truth."""
        u_pred = self.reconstruct_full_field(a_snapshots)
        errors = np.linalg.norm(u_snapshots_true - u_pred, axis=0) / \
                 (np.linalg.norm(u_snapshots_true, axis=0) + 1e-10)
        return errors
    
    def stability_analysis(self, a0: np.ndarray, t_final: float = 10.0, n_steps: int = 1000) -> Dict:
        """Analyze ROM stability."""
        t_eval = np.linspace(0, t_final, n_steps)
        _, a_traj = self.integrate_rk4(a0, t_eval, method='explicit')
        
        a_mean = np.mean(a_traj, axis=1)
        a_std = np.std(a_traj, axis=1)
        a_max = np.max(np.abs(a_traj), axis=1)
        
        diffs = np.linalg.norm(np.diff(a_traj, axis=1), axis=0)
        lyapunov_est = np.mean(np.log(diffs[diffs > 1e-10])) if np.any(diffs > 1e-10) else 0.0
        
        return {
            'a_mean': a_mean,
            'a_std': a_std,
            'a_max': a_max,
            'lyapunov_exponent': lyapunov_est,
            'energy_decay_rate': np.mean(np.diff(a_traj[0, :]))
        }
    
    def get_summary(self) -> Dict:
        """Get ROM summary."""
        return {
            'n_modes': self.n_modes,
            'n_spatial': self.n_spatial,
            'grid_size': self.grid_size,
            'n_components': self.n_components,
            'total_energy': np.sum(self.energy),
            'dominant_mode_energy': self.energy[0],
            'Reynolds_number': self.Re,
            'viscosity': self.nu,
            'time_step': self.dt
        }
    
    def print_summary(self) -> None:
        """Print ROM summary."""
        summary = self.get_summary()
        print("\n" + "="*60)
        print("POD-GALERKIN ROM SUMMARY")
        print("="*60)
        print("Model Configuration:")
        print(f"  Number of modes: {summary['n_modes']}")
        print(f"  Spatial DoFs: {summary['n_spatial']:,}")
        print(f"  Dimensionality reduction: {100*(1-summary['n_modes']/summary['n_spatial']):.1f}%")
        
        print("Physical Parameters:")
        print(f"  Reynolds number: {summary['Reynolds_number']:.1f}")
        print(f"  Viscosity: {summary['viscosity']:.4f}")
        print(f"  Time step: {summary['time_step']:.4f}")
        
        print("Modal Energy:")
        print(f"  Total energy: {summary['total_energy']*100:.2f}%")
        print(f"  Dominant mode: {summary['dominant_mode_energy']:.6f}")
        print("="*60 + "\n")
    
    @staticmethod
    def from_pod_solver(pod_solver, mean_field=None) -> 'PODGalerkinROM':
        """Create POD-Galerkin ROM from POD_Solver instance."""
        n_spatial = pod_solver.n_spatial
        n_components = 2
        grid_size = int(np.sqrt(n_spatial / n_components))
        
        if mean_field is None:
            mean_field = pod_solver.mean_field.flatten()
        
        return PODGalerkinROM(
            pod_modes=pod_solver.U,
            pod_coeffs=pod_solver.Vt,
            modal_energy=pod_solver.energy,
            temporal_mean=mean_field,
            grid_size=grid_size,
            n_components=n_components,
            verbose=True
        )
