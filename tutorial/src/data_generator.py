"""
Synthetic CFD Data Generator for POD Tutorial
==============================================
Generates realistic but synthetic CFD snapshot data for:
  1. Lid-driven cavity flow
  2. Backward-facing step flow
  3. Cylinder flow (Von Kármán vortex street)

Author: CFD/SciML Expert
Date: 2026
"""

import numpy as np
from typing import Tuple, Dict, Optional
import json
from pathlib import Path


class SyntheticCFDGenerator:
    """
    Generates synthetic but realistic CFD snapshot data for ROM testing.
    
    Characteristics:
    - Modal structure resembles real CFD (smooth, energetic modes)
    - Energy distribution follows typical POD energy decay
    - Temporal dynamics based on physical principles
    - Multiple velocity components (u, v)
    """
    
    @staticmethod
    def cavity_flow(
        grid_size: int = 128,
        n_snapshots: int = 500,
        Re: float = 1000.0,
        seed: int = 42
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict]:
        """
        Generate synthetic lid-driven cavity flow data.
        
        Physical Setup:
        - Square domain [0, 1] × [0, 1]
        - Top lid moving at U=1.0, other walls stationary
        - Reynolds number Re = 1000
        - Steady-state quasi-periodic behavior
        
        Parameters:
            grid_size (int): Grid resolution (grid_size × grid_size)
            n_snapshots (int): Number of time snapshots
            Re (float): Reynolds number
            seed (int): Random seed for reproducibility
            
        Returns:
            u_snapshots (np.ndarray): u-velocity snapshots (n_spatial, n_snapshots)
            v_snapshots (np.ndarray): v-velocity snapshots (n_spatial, n_snapshots)
            time_vector (np.ndarray): Time instances
            metadata (Dict): Problem parameters
        """
        np.random.seed(seed)
        
        n_spatial = grid_size * grid_size
        
        # Create spatial grid
        x = np.linspace(0, 1, grid_size)
        y = np.linspace(0, 1, grid_size)
        X, Y = np.meshgrid(x, y)
        
        # Initialize snapshots
        u_snapshots = np.zeros((n_spatial, n_snapshots))
        v_snapshots = np.zeros((n_spatial, n_snapshots))
        time_vector = np.linspace(0, 1, n_snapshots)
        
        # Create dominant modes (physical circulation patterns)
        modes_u = []
        modes_v = []
        energies = []
        
        # Primary circulation (strongest mode)
        circulation = np.exp(-50 * ((X - 0.5)**2 + (Y - 0.5)**2))
        circulation = circulation * (X * (1 - X) * Y * (1 - Y))  # Enforce boundary conditions
        modes_u.append(circulation)
        modes_v.append(-np.gradient(circulation, axis=0))
        energies.append(1.0)
        
        # Secondary vortex modes (corner eddies)
        vortex1 = np.exp(-100 * ((X - 0.25)**2 + (Y - 0.25)**2))
        vortex1 = vortex1 * (X * (1 - X) * Y * (1 - Y))
        modes_u.append(vortex1)
        modes_v.append(-np.gradient(vortex1, axis=0))
        energies.append(0.3)
        
        vortex2 = np.exp(-100 * ((X - 0.75)**2 + (Y - 0.25)**2))
        vortex2 = vortex2 * (X * (1 - X) * Y * (1 - Y))
        modes_u.append(vortex2)
        modes_v.append(-np.gradient(vortex2, axis=0))
        energies.append(0.2)
        
        # Fine-scale fluctuations (higher modes)
        for k in range(1, 4):
            mode_k = np.sin(k * np.pi * X) * np.cos(k * np.pi * Y)
            mode_k = mode_k * (X * (1 - X) * Y * (1 - Y))
            modes_u.append(mode_k)
            modes_v.append(np.cos(k * np.pi * X) * np.sin(k * np.pi * Y))
            energies.append(0.15 / (k + 1))
        
        # Normalize energies
        energies = np.array(energies)
        energies = energies / energies.sum()
        
        # Generate snapshots as superposition of modes with time-varying coefficients
        for t in range(n_snapshots):
            tau = time_vector[t]
            
            for mode_idx, energy in enumerate(energies):
                freq = (mode_idx + 1) * np.pi  # Different frequencies
                amplitude = np.sqrt(energy) * (1 + 0.3 * np.sin(2 * np.pi * freq * tau))
                
                u_snapshots[:, t] += amplitude * modes_u[mode_idx].flatten()
                v_snapshots[:, t] += amplitude * modes_v[mode_idx].flatten()
        
        # Add small-scale noise and enforce boundary conditions
        u_snapshots += 0.02 * np.random.randn(*u_snapshots.shape)
        v_snapshots += 0.02 * np.random.randn(*v_snapshots.shape)
        
        # Enforce no-slip boundary conditions
        u_boundary = np.zeros((grid_size, n_snapshots))
        u_snapshots[::grid_size, :] = u_boundary  # Bottom
        u_snapshots[(grid_size-1)::grid_size, :] = 1.0  # Top (lid velocity)
        
        metadata = {
            'case': 'cavity_flow',
            'description': 'Lid-driven cavity flow',
            'grid_size': grid_size,
            'n_snapshots': n_snapshots,
            'Reynolds_number': Re,
            'domain': '(0, 1) x (0, 1)',
            'boundary_conditions': 'No-slip on 3 walls, moving lid on top',
            'n_modes_dominant': len(energies),
            'characteristic_velocity': 1.0
        }
        
        return u_snapshots, v_snapshots, time_vector, metadata
    
    @staticmethod
    def backward_facing_step(
        grid_size: int = 128,
        n_snapshots: int = 500,
        Re: float = 389.0,
        seed: int = 42
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict]:
        """
        Generate synthetic backward-facing step flow data.
        
        Physical Setup:
        - Channel with step expansion
        - Inlet flow from left, outlet on right
        - Recirculation zone behind step
        - Complex separation/reattachment
        
        Parameters:
            grid_size (int): Grid resolution
            n_snapshots (int): Number of time snapshots
            Re (float): Reynolds number
            seed (int): Random seed
            
        Returns:
            u_snapshots, v_snapshots, time_vector, metadata
        """
        np.random.seed(seed)
        
        n_spatial = grid_size * grid_size
        
        x = np.linspace(0, 3, grid_size)
        y = np.linspace(-0.5, 0.5, grid_size)
        X, Y = np.meshgrid(x, y)
        
        u_snapshots = np.zeros((n_spatial, n_snapshots))
        v_snapshots = np.zeros((n_spatial, n_snapshots))
        time_vector = np.linspace(0, 2, n_snapshots)
        
        # Inlet profile (parabolic)
        y_inlet = np.linspace(-0.5, 0.5, grid_size)
        u_inlet = 4 * (y_inlet + 0.5) * (0.5 - y_inlet)  # Parabolic profile
        
        # Generate base flow (mean field + perturbations)
        modes = []
        energies_list = []
        
        # Mode 1: Recirculation zone
        recirculation = np.exp(-20 * ((X - 0.8)**2 + Y**2)) * np.sin(np.pi * (X - 0.5))
        recirculation = recirculation * (X > 0.5)  # Only downstream
        modes.append(recirculation)
        energies_list.append(0.4)
        
        # Mode 2: Shear layer oscillation
        shear_layer = np.exp(-30 * (Y - 0.1)**2) * np.sin(3 * np.pi * X)
        modes.append(shear_layer)
        energies_list.append(0.3)
        
        # Mode 3: Channel fluctuations
        channel_mode = np.sin(2 * np.pi * X) * np.cos(np.pi * Y)
        modes.append(channel_mode)
        energies_list.append(0.2)
        
        # Mode 4: Reattachment region
        reattach = np.exp(-15 * ((X - 2.0)**2 + Y**2))
        modes.append(reattach)
        energies_list.append(0.1)
        
        energies_list = np.array(energies_list)
        energies_list = energies_list / energies_list.sum()
        
        # Generate time-varying snapshots
        for t in range(n_snapshots):
            tau = time_vector[t]
            
            # Base inlet flow
            u_snapshots[:, t] = np.tile(u_inlet, grid_size)
            
            # Add modal perturbations
            for mode_idx, energy in enumerate(energies_list):
                freq = (mode_idx + 0.5) * np.pi
                amplitude = np.sqrt(energy) * (1 + 0.4 * np.sin(freq * tau))
                
                u_snapshots[:, t] += 0.15 * amplitude * modes[mode_idx].flatten()
                v_snapshots[:, t] += 0.1 * amplitude * np.gradient(modes[mode_idx], axis=0).flatten()
        
        # Add noise
        u_snapshots += 0.01 * np.random.randn(*u_snapshots.shape)
        v_snapshots += 0.01 * np.random.randn(*v_snapshots.shape)
        
        metadata = {
            'case': 'backward_facing_step',
            'description': 'Backward-facing step with recirculation',
            'grid_size': grid_size,
            'n_snapshots': n_snapshots,
            'Reynolds_number': Re,
            'domain': '(0, 3) x (-0.5, 0.5)',
            'boundary_conditions': 'Parabolic inlet, zero-gradient outlet, slip/no-slip walls',
            'characteristic_length': 1.0,
            'characteristic_velocity': 1.0
        }
        
        return u_snapshots, v_snapshots, time_vector, metadata
    
    @staticmethod
    def cylinder_flow(
        grid_size: int = 128,
        n_snapshots: int = 500,
        Re: float = 100.0,
        seed: int = 42
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict]:
        """
        Generate synthetic cylinder flow data (Von Kármán vortex street).
        
        Physical Setup:
        - Circular cylinder in cross-flow
        - Periodic vortex shedding at Strouhal frequency
        - Characteristic Strouhal number for Re=100: St ≈ 0.164
        
        Parameters:
            grid_size (int): Grid resolution
            n_snapshots (int): Number of time snapshots
            Re (float): Reynolds number
            seed (int): Random seed
            
        Returns:
            u_snapshots, v_snapshots, time_vector, metadata
        """
        np.random.seed(seed)
        
        n_spatial = grid_size * grid_size
        
        x = np.linspace(-2, 4, grid_size)
        y = np.linspace(-2, 2, grid_size)
        X, Y = np.meshgrid(x, y)
        
        # Cylinder center at (0, 0) with radius 0.5
        R = np.sqrt(X**2 + Y**2)
        cylinder_mask = (R <= 0.5).astype(float)
        
        u_snapshots = np.zeros((n_spatial, n_snapshots))
        v_snapshots = np.zeros((n_spatial, n_snapshots))
        time_vector = np.linspace(0, 10, n_snapshots)
        
        # Strouhal frequency (empirical for Re=100)
        St = 0.164
        omega = 2 * np.pi * St
        
        # Create vortex shedding modes
        modes = []
        energies_list = []
        
        # Mode 1: Lower vortex wake
        vortex_lower = np.exp(-8 * ((X - 1.5)**2 + (Y + 0.5)**2)) * np.sin(np.pi * Y)
        modes.append(vortex_lower)
        energies_list.append(0.5)
        
        # Mode 2: Upper vortex wake
        vortex_upper = np.exp(-8 * ((X - 1.5)**2 + (Y - 0.5)**2)) * np.sin(np.pi * Y)
        modes.append(vortex_upper)
        energies_list.append(0.5)
        
        # Mode 3: Near-field circulation
        circulation = np.exp(-10 * R) * np.sin(2 * np.arctan2(Y, X))
        modes.append(circulation)
        energies_list.append(0.3)
        
        # Mode 4: Far-field wake
        far_wake = np.exp(-3 * np.abs(X)) * np.sin(np.pi * Y / 2)
        modes.append(far_wake)
        energies_list.append(0.2)
        
        energies_list = np.array(energies_list)
        energies_list = energies_list / energies_list.sum()
        
        # Generate snapshots with periodic vortex shedding
        for t in range(n_snapshots):
            tau = time_vector[t]
            
            # Freestream velocity
            u_snapshots[:, t] = 1.0 * (1 - 0.3 * cylinder_mask.flatten())
            
            # Vortex shedding (alternating)
            phase_odd = np.sin(omega * tau)
            phase_even = np.cos(omega * tau)
            
            u_snapshots[:, t] += 0.3 * phase_odd * modes[0].flatten()
            u_snapshots[:, t] += 0.3 * phase_even * modes[1].flatten()
            v_snapshots[:, t] += 0.3 * phase_odd * modes[2].flatten()
            v_snapshots[:, t] += 0.2 * np.sin(omega * tau + np.pi/4) * modes[3].flatten()
            
            # Add small-scale turbulence
            u_snapshots[:, t] += 0.05 * np.sin(4 * omega * tau) * modes[0].flatten()
            v_snapshots[:, t] += 0.05 * np.cos(4 * omega * tau) * modes[2].flatten()
        
        # Add noise
        u_snapshots += 0.01 * np.random.randn(*u_snapshots.shape)
        v_snapshots += 0.01 * np.random.randn(*v_snapshots.shape)
        
        # Enforce no-slip on cylinder
        cylinder_mask_flat = cylinder_mask.flatten()[:, np.newaxis]
        u_snapshots = u_snapshots * (1 - cylinder_mask_flat)
        v_snapshots = v_snapshots * (1 - cylinder_mask_flat)
        
        metadata = {
            'case': 'cylinder_flow',
            'description': 'Circular cylinder in cross-flow (Von Kármán vortex street)',
            'grid_size': grid_size,
            'n_snapshots': n_snapshots,
            'Reynolds_number': Re,
            'cylinder_diameter': 1.0,
            'domain': '(-2, 4) x (-2, 2)',
            'boundary_conditions': 'No-slip on cylinder, slip on far-field',
            'Strouhal_number': St,
            'shedding_frequency': St
        }
        
        return u_snapshots, v_snapshots, time_vector, metadata


def generate_all_test_data(
    output_dir: str = 'd:\\Github\\POD_NN\\tutorial\\data',
    grid_size: int = 128,
    n_snapshots: int = 500
) -> None:
    """
    Generate and save all synthetic CFD test data.
    
    Parameters:
        output_dir (str): Directory to save data
        grid_size (int): Grid resolution
        n_snapshots (int): Number of snapshots
    """
    
    output_path = Path(output_dir)
    
    print("=" * 70)
    print("SYNTHETIC CFD DATA GENERATION")
    print("=" * 70)
    
    # Case 1: Cavity Flow
    print("\n[1/3] Generating Cavity Flow...")
    u_cav, v_cav, t_cav, meta_cav = SyntheticCFDGenerator.cavity_flow(
        grid_size=grid_size, n_snapshots=n_snapshots, seed=42
    )
    cavity_dir = output_path / 'cavity_flow'
    cavity_dir.mkdir(parents=True, exist_ok=True)
    np.save(str(cavity_dir / 'u_snapshots.npy'), u_cav)
    np.save(str(cavity_dir / 'v_snapshots.npy'), v_cav)
    np.save(str(cavity_dir / 'time_vector.npy'), t_cav)
    with open(cavity_dir / 'parameters.json', 'w') as f:
        json.dump(meta_cav, f, indent=2)
    print(f"[OK] Saved to {cavity_dir}")
    print(f"  u shape: {u_cav.shape}, v shape: {v_cav.shape}")
    
    # Case 2: Backward Facing Step
    print("\n[2/3] Generating Backward-Facing Step...")
    u_step, v_step, t_step, meta_step = SyntheticCFDGenerator.backward_facing_step(
        grid_size=grid_size, n_snapshots=n_snapshots, seed=42
    )
    step_dir = output_path / 'backward_facing_step'
    step_dir.mkdir(parents=True, exist_ok=True)
    np.save(str(step_dir / 'u_snapshots.npy'), u_step)
    np.save(str(step_dir / 'v_snapshots.npy'), v_step)
    np.save(str(step_dir / 'time_vector.npy'), t_step)
    with open(step_dir / 'parameters.json', 'w') as f:
        json.dump(meta_step, f, indent=2)
    print(f"[OK] Saved to {step_dir}")
    print(f"  u shape: {u_step.shape}, v shape: {v_step.shape}")
    
    # Case 3: Cylinder Flow
    print("\n[3/3] Generating Cylinder Flow...")
    u_cyl, v_cyl, t_cyl, meta_cyl = SyntheticCFDGenerator.cylinder_flow(
        grid_size=grid_size, n_snapshots=n_snapshots, seed=42
    )
    cyl_dir = output_path / 'cylinder_flow'
    cyl_dir.mkdir(parents=True, exist_ok=True)
    np.save(str(cyl_dir / 'u_snapshots.npy'), u_cyl)
    np.save(str(cyl_dir / 'v_snapshots.npy'), v_cyl)
    np.save(str(cyl_dir / 'time_vector.npy'), t_cyl)
    with open(cyl_dir / 'parameters.json', 'w') as f:
        json.dump(meta_cyl, f, indent=2)
    print(f"[OK] Saved to {cyl_dir}")
    print(f"  u shape: {u_cyl.shape}, v shape: {v_cyl.shape}")
    
    print("\n" + "=" * 70)
    print("[SUCCESS] ALL TEST DATA GENERATED")
    print("=" * 70)


if __name__ == '__main__':
    generate_all_test_data()
