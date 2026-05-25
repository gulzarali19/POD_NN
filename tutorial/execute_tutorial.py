#!/usr/bin/env python3
"""
Comprehensive ROM-POD Tutorial Execution Script
Runs all components step-by-step and stores results
"""

import sys
import os
import json
import time
import traceback
from datetime import datetime
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Ensure results directory exists
results_dir = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(results_dir, exist_ok=True)

def log(msg, step="", level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = f"[{timestamp}] {level}"
    if step:
        prefix += f" [{step}]"
    print(f"{prefix}: {msg}")

def save_results(name, data):
    """Save results to JSON file"""
    filepath = os.path.join(results_dir, f"{name}.json")
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    log(f"Results saved to {filepath}", level="SAVE")
    return filepath

def save_arrays(name, arrays_dict):
    """Save numpy arrays to results directory"""
    filepaths = {}
    for key, array in arrays_dict.items():
        filepath = os.path.join(results_dir, f"{name}_{key}.npy")
        np.save(filepath, array)
        filepaths[key] = filepath
    log(f"Arrays saved for {name}", level="SAVE")
    return filepaths

# ============================================================================
# STEP 1: DATA GENERATION
# ============================================================================
def step1_generate_data():
    """Step 1: Generate synthetic CFD test data"""
    log("STARTING DATA GENERATION", "STEP 1")
    
    try:
        from src.data_generator import generate_all_test_data
        
        start_time = time.time()
        result = generate_all_test_data()
        elapsed = time.time() - start_time
        
        results = {
            "status": "SUCCESS",
            "elapsed_time_seconds": elapsed,
            "timestamp": datetime.now().isoformat(),
            "message": "All synthetic test data generated successfully",
            "cases_generated": ["cavity_flow", "backward_facing_step", "cylinder_flow"]
        }
        
        log(f"Data generation completed in {elapsed:.2f}s", "STEP 1")
        save_results("step1_data_generation", results)
        return True, results
        
    except Exception as e:
        log(f"ERROR: {str(e)}", "STEP 1", "ERROR")
        traceback.print_exc()
        return False, {"status": "FAILED", "error": str(e)}

# ============================================================================
# STEP 2: POD ANALYSIS ON CAVITY FLOW
# ============================================================================
def step2_pod_cavity():
    """Step 2: POD analysis on cavity flow"""
    log("STARTING POD ANALYSIS (CAVITY FLOW)", "STEP 2")
    
    try:
        from src.pod_solver import POD_Solver
        from src.data_utils import DataHandler
        
        start_time = time.time()
        
        # Load cavity flow data
        log("Loading cavity flow data...", "STEP 2")
        u_snapshots = DataHandler.load_npy('data/cavity_flow/u_snapshots.npy')
        v_snapshots = DataHandler.load_npy('data/cavity_flow/v_snapshots.npy')
        
        # Stack into single snapshot matrix
        snapshots = np.vstack([u_snapshots, v_snapshots])
        log(f"Loaded snapshots shape: {snapshots.shape}", "STEP 2")
        
        # Initialize POD Solver
        pod = POD_Solver(snapshots)
        pod.preprocess()
        log("Data preprocessed", "STEP 2")
        
        # Compute SVD
        pod.compute_svd()
        log("SVD computed", "STEP 2")
        
        elapsed = time.time() - start_time
        
        # Extract results
        results = {
            "case": "cavity_flow",
            "status": "SUCCESS",
            "elapsed_time_seconds": elapsed,
            "timestamp": datetime.now().isoformat(),
            "data_shape": snapshots.shape,
            "modes_count": len(pod.s),
            "energy_values": pod.s[:20].tolist() if len(pod.s) >= 20 else pod.s.tolist(),
            "cumulative_energy_90": float(np.where(pod.cumulative_energy >= 0.90)[0][0] + 1),
            "cumulative_energy_95": float(np.where(pod.cumulative_energy >= 0.95)[0][0] + 1),
            "cumulative_energy_99": float(np.where(pod.cumulative_energy >= 0.99)[0][0] + 1),
        }
        
        # Save arrays
        arrays = {
            "singular_values": pod.s,
            "modes": pod.U,
            "temporal_coefficients": pod.Vt
        }
        save_arrays("step2_pod_cavity", arrays)
        
        log(f"POD analysis completed in {elapsed:.2f}s", "STEP 2")
        log(f"Modes for 90% energy: {results['cumulative_energy_90']}", "STEP 2")
        log(f"Modes for 95% energy: {results['cumulative_energy_95']}", "STEP 2")
        
        save_results("step2_pod_cavity", results)
        return True, results, pod
        
    except Exception as e:
        log(f"ERROR: {str(e)}", "STEP 2", "ERROR")
        traceback.print_exc()
        return False, {"status": "FAILED", "error": str(e)}, None

# ============================================================================
# STEP 3: POD-GALERKIN ROM
# ============================================================================
def step3_galerkin_rom(pod):
    """Step 3: POD-Galerkin ROM construction and prediction"""
    log("STARTING POD-GALERKIN ROM", "STEP 3")
    
    try:
        from src.pod_galerkin_rom import PODGalerkinROM
        
        start_time = time.time()
        
        # Create ROM from POD
        rom = PODGalerkinROM.from_pod_solver(pod)
        log("POD-Galerkin ROM initialized", "STEP 3")
        
        # Initial condition: first mode coefficient
        a_init = pod.Vt[:, 0]
        
        # Time integration
        log("Running time integration (RK45)...", "STEP 3")
        t_pred, a_pred, u_pred = rom.predict(a_init, t_final=1.0, n_steps=100, method='RK45')
        
        elapsed = time.time() - start_time
        
        results = {
            "status": "SUCCESS",
            "elapsed_time_seconds": elapsed,
            "timestamp": datetime.now().isoformat(),
            "prediction_shape": u_pred.shape,
            "time_steps": len(t_pred),
            "method": "RK45",
            "time_span": [float(t_pred[0]), float(t_pred[-1])]
        }
        
        # Save prediction data
        arrays = {
            "time_vector": t_pred,
            "modal_coefficients": a_pred,
            "reconstructed_field": u_pred
        }
        save_arrays("step3_galerkin_rom", arrays)
        
        log(f"POD-Galerkin ROM completed in {elapsed:.2f}s", "STEP 3")
        log(f"Predicted {len(t_pred)} time steps", "STEP 3")
        
        save_results("step3_galerkin_rom", results)
        return True, results
        
    except Exception as e:
        log(f"ERROR: {str(e)}", "STEP 3", "ERROR")
        traceback.print_exc()
        return False, {"status": "FAILED", "error": str(e)}

# ============================================================================
# STEP 4: POD-NN SURROGATE
# ============================================================================
def step4_nn_surrogate(pod):
    """Step 4: POD neural network surrogate training"""
    log("STARTING POD-NN SURROGATE", "STEP 4")
    
    try:
        from src.pod_nn_surrogate import PODNNSurrogate
        
        start_time = time.time()
        
        # Create POD-NN surrogate
        log("Initializing POD-NN surrogate...", "STEP 4")
        surrogate = PODNNSurrogate(
            pod_modes=pod.U,
            pod_energy=pod.s**2,
            mean_field=pod.mean_field,
            nn_hidden_dims=(64, 64)
        )
        
        # Train on POD coefficients
        log("Training neural network...", "STEP 4")
        history = surrogate.train_from_snapshots(
            pod_coeffs=pod.Vt,
            epochs=100,
            learning_rate=0.01
        )
        
        # Forecast
        log("Running forecast...", "STEP 4")
        a_init = pod.Vt[:, 0]
        a_forecast, u_forecast = surrogate.forecast_dynamics(a_init, n_steps=50)
        
        elapsed = time.time() - start_time
        
        results = {
            "status": "SUCCESS",
            "elapsed_time_seconds": elapsed,
            "timestamp": datetime.now().isoformat(),
            "training_epochs": 100,
            "final_train_loss": float(history['train_loss'][-1]) if history else 0,
            "final_val_loss": float(history['val_loss'][-1]) if history else 0,
            "forecast_steps": 50,
            "forecast_shape": u_forecast.shape,
            "model_layers": 2,
            "layer_size": 64
        }
        
        # Save arrays
        arrays = {
            "train_loss": np.array(history['train_loss']) if history else np.array([]),
            "val_loss": np.array(history['val_loss']) if history else np.array([]),
            "forecast_coefficients": a_forecast,
            "forecast_field": u_forecast
        }
        save_arrays("step4_nn_surrogate", arrays)
        
        log(f"POD-NN Surrogate completed in {elapsed:.2f}s", "STEP 4")
        log(f"Final training loss: {results['final_train_loss']:.6f}", "STEP 4")
        log(f"Final validation loss: {results['final_val_loss']:.6f}", "STEP 4")
        
        save_results("step4_nn_surrogate", results)
        return True, results
        
    except Exception as e:
        log(f"ERROR: {str(e)}", "STEP 4", "ERROR")
        traceback.print_exc()
        return False, {"status": "FAILED", "error": str(e)}

# ============================================================================
# STEP 5: ROM VALIDATION
# ============================================================================
def step5_validation(pod):
    """Step 5: ROM validation with multiple error metrics"""
    log("STARTING ROM VALIDATION", "STEP 5")
    
    try:
        from src.data_utils import DataHandler
        
        start_time = time.time()
        
        # Load test data
        u_snapshots = DataHandler.load_npy('data/cavity_flow/u_snapshots.npy')
        v_snapshots = DataHandler.load_npy('data/cavity_flow/v_snapshots.npy')
        snapshots = np.vstack([u_snapshots, v_snapshots])
        
        # Test different mode counts
        log("Testing different mode counts...", "STEP 5")
        mode_counts = [5, 10, 15, 20, 30]
        convergence_results = {}
        
        for n_modes in mode_counts:
            # Reconstruct with n_modes (only first 100 snapshots to save memory)
            u_modes = pod.U[:, :n_modes]
            a_coeffs = pod.Vt[:n_modes, :100]  # Use only first 100 snapshots
            reconstructed = pod.mean_field + u_modes @ a_coeffs
            reference = snapshots[:, :100]
            
            # Compute L2 error
            error_field = reconstructed - reference
            l2_error = np.linalg.norm(error_field) / np.linalg.norm(reference)
            
            # Compute energy error
            energy_rom = np.sum(reconstructed**2)
            energy_ref = np.sum(reference**2)
            energy_error = np.abs(energy_rom - energy_ref) / energy_ref
            
            convergence_results[str(n_modes)] = {
                "modes": n_modes,
                "l2_error": float(l2_error),
                "energy_error": float(energy_error),
                "snapshot_range": "100 snapshots"
            }
            
            log(f"  {n_modes} modes: L2={convergence_results[str(n_modes)]['l2_error']:.6f}", "STEP 5")
        
        elapsed = time.time() - start_time
        
        results = {
            "status": "SUCCESS",
            "elapsed_time_seconds": elapsed,
            "timestamp": datetime.now().isoformat(),
            "validation_metrics": {
                "l2_error": "Relative L2 norm of reconstruction error",
                "energy_error": "Relative kinetic energy difference"
            },
            "convergence_analysis": convergence_results,
            "best_mode_count": min(convergence_results.items(), key=lambda x: x[1]['l2_error'])[0]
        }
        
        log(f"ROM Validation completed in {elapsed:.2f}s", "STEP 5")
        
        save_results("step5_validation", results)
        return True, results
        
    except Exception as e:
        log(f"ERROR: {str(e)}", "STEP 5", "ERROR")
        traceback.print_exc()
        return False, {"status": "FAILED", "error": str(e)}

# ============================================================================
# STEP 6: CROSS-CASE ANALYSIS
# ============================================================================
def step6_cross_case_analysis():
    """Step 6: Compare all three test cases"""
    log("STARTING CROSS-CASE ANALYSIS", "STEP 6")
    
    try:
        from src.pod_solver import POD_Solver
        from src.data_utils import DataHandler
        
        start_time = time.time()
        
        cases = ["cavity_flow", "backward_facing_step", "cylinder_flow"]
        case_results = {}
        
        for case in cases:
            log(f"Analyzing {case}...", "STEP 6")
            
            # Load data
            u = DataHandler.load_npy(f'data/{case}/u_snapshots.npy')
            v = DataHandler.load_npy(f'data/{case}/v_snapshots.npy')
            snapshots = np.vstack([u, v])
            
            # POD analysis
            pod = POD_Solver(snapshots)
            pod.preprocess()
            pod.compute_svd()
            
            # Calculate energy thresholds
            cum_energy = pod.cumulative_energy
            
            case_results[case] = {
                "snapshot_shape": snapshots.shape,
                "total_modes": len(pod.s),
                "modes_90_energy": int(np.where(cum_energy >= 0.90)[0][0] + 1),
                "modes_95_energy": int(np.where(cum_energy >= 0.95)[0][0] + 1),
                "modes_99_energy": int(np.where(cum_energy >= 0.99)[0][0] + 1),
                "dominant_mode_energy_percent": float(pod.s[0]**2 / np.sum(pod.s**2) * 100),
                "top_5_energies": pod.s[:5].tolist()
            }
        
        elapsed = time.time() - start_time
        
        results = {
            "status": "SUCCESS",
            "elapsed_time_seconds": elapsed,
            "timestamp": datetime.now().isoformat(),
            "case_analysis": case_results,
            "summary": "Comparative analysis of three CFD test cases"
        }
        
        log(f"Cross-case analysis completed in {elapsed:.2f}s", "STEP 6")
        
        save_results("step6_cross_case_analysis", results)
        return True, results
        
    except Exception as e:
        log(f"ERROR: {str(e)}", "STEP 6", "ERROR")
        traceback.print_exc()
        return False, {"status": "FAILED", "error": str(e)}

# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    """Execute all steps"""
    
    print("\n" + "="*70)
    print("  ROM-POD TUTORIAL - COMPREHENSIVE EXECUTION")
    print("="*70 + "\n")
    
    log("Starting comprehensive ROM-POD tutorial execution", level="INIT")
    
    all_results = {}
    step_status = {}
    
    # Step 1: Data Generation
    success, result = step1_generate_data()
    all_results['step1'] = result
    step_status['Step 1: Data Generation'] = "[OK]" if success else "[FAIL]"
    
    if not success:
        log("Data generation failed, cannot proceed", level="CRITICAL")
        print_summary(step_status, all_results)
        return 1
    
    # Step 2: POD Analysis
    success, result, pod = step2_pod_cavity()
    all_results['step2'] = result
    step_status['Step 2: POD Analysis'] = "[OK]" if success else "[FAIL]"
    
    if not success or pod is None:
        log("POD analysis failed, cannot proceed", level="CRITICAL")
        print_summary(step_status, all_results)
        return 1
    
    # Step 3: Galerkin ROM
    success, result = step3_galerkin_rom(pod)
    all_results['step3'] = result
    step_status['Step 3: POD-Galerkin ROM'] = "[OK]" if success else "[FAIL]"
    
    # Step 4: NN Surrogate
    success, result = step4_nn_surrogate(pod)
    all_results['step4'] = result
    step_status['Step 4: POD-NN Surrogate'] = "[OK]" if success else "[FAIL]"
    
    # Step 5: Validation
    success, result = step5_validation(pod)
    all_results['step5'] = result
    step_status['Step 5: ROM Validation'] = "[OK]" if success else "[FAIL]"
    
    # Step 6: Cross-case Analysis
    success, result = step6_cross_case_analysis()
    all_results['step6'] = result
    step_status['Step 6: Cross-Case Analysis'] = "[OK]" if success else "[FAIL]"
    
    print_summary(step_status, all_results)
    
    # Save master results file
    master_results = {
        "execution_date": datetime.now().isoformat(),
        "status": "COMPLETE",
        "step_status": step_status,
        "all_results": all_results,
        "results_directory": os.path.abspath(results_dir)
    }
    
    with open(os.path.join(results_dir, 'EXECUTION_SUMMARY.json'), 'w') as f:
        json.dump(master_results, f, indent=2, default=str)
    
    log(f"Master results saved to {os.path.join(results_dir, 'EXECUTION_SUMMARY.json')}", level="COMPLETE")
    
    return 0

def print_summary(step_status, all_results):
    """Print execution summary"""
    print("\n" + "="*70)
    print("  EXECUTION SUMMARY")
    print("="*70)
    
    for step, status in step_status.items():
        # Replace fancy characters with ASCII
        status_ascii = status.replace("✓", "[OK]").replace("✗", "[FAIL]")
        print(f"  {step:<35} {status_ascii}")
    
    print("\n" + "="*70)
    print(f"  Results saved to: {os.path.abspath(results_dir)}")
    print("="*70 + "\n")

if __name__ == "__main__":
    sys.exit(main())
