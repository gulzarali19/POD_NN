"""
POD + Neural Network Integration (POD_NN)
=========================================
Combines POD basis with neural networks for surrogate modeling.

Methods:
  - POD-NN for dynamics prediction
  - Latent space neural network training
  - Multi-fidelity ROM
  - Transfer learning

Author: CFD/SciML Expert
Date: 2026
"""

import numpy as np
from typing import Tuple, Dict, Optional, Callable
import warnings


class PODNeuralNetwork:
    """
    Neural Network for latent space dynamics in POD basis.
    Predicts POD temporal coefficients using neural network.
    """
    
    def __init__(self, n_modes: int, hidden_dims: Tuple[int] = (64, 64), 
                 activation: str = 'tanh', verbose: bool = False):
        """
        Initialize POD-NN surrogate.
        
        Parameters:
            n_modes (int): Number of POD modes
            hidden_dims (Tuple): Hidden layer dimensions
            activation (str): Activation function ('tanh', 'relu')
            verbose (bool): Print information
        """
        self.n_modes = n_modes
        self.hidden_dims = hidden_dims
        self.activation = activation
        self.verbose = verbose
        
        # Network weights
        self.weights = []
        self.biases = []
        self._initialize_weights()
        
        # Training history
        self.loss_history = []
        self.validation_loss_history = []
        
        if verbose:
            print(f"POD-NN initialized: {n_modes} -> {hidden_dims} -> {n_modes}")
    
    def _initialize_weights(self):
        """Initialize network weights (He initialization)."""
        dims = [self.n_modes] + list(self.hidden_dims) + [self.n_modes]
        
        for i in range(len(dims) - 1):
            std = np.sqrt(2.0 / dims[i])  # He initialization
            W = np.random.randn(dims[i], dims[i+1]) * std
            b = np.zeros((1, dims[i+1]))
            
            self.weights.append(W)
            self.biases.append(b)
    
    def _activation_fn(self, x: np.ndarray) -> np.ndarray:
        """Apply activation function."""
        if self.activation == 'tanh':
            return np.tanh(x)
        elif self.activation == 'relu':
            return np.maximum(0, x)
        else:
            return x
    
    def _activation_deriv(self, x: np.ndarray) -> np.ndarray:
        """Derivative of activation function."""
        if self.activation == 'tanh':
            return 1 - np.tanh(x)**2
        elif self.activation == 'relu':
            return (x > 0).astype(float)
        else:
            return np.ones_like(x)
    
    def forward(self, a: np.ndarray) -> np.ndarray:
        """Forward pass through network."""
        activations = [a]
        z_values = []
        
        x = a
        for i in range(len(self.weights) - 1):
            z = x @ self.weights[i] + self.biases[i]
            z_values.append(z)
            x = self._activation_fn(z)
            activations.append(x)
        
        # Output layer (linear)
        z_out = x @ self.weights[-1] + self.biases[-1]
        z_values.append(z_out)
        activations.append(z_out)
        
        return activations, z_values
    
    def backward(self, a: np.ndarray, target: np.ndarray, learning_rate: float = 0.001):
        """Backpropagation."""
        activations, z_values = self.forward(a)
        
        # Output layer error
        delta = (activations[-1] - target)
        
        # Backpropagate errors
        deltas = [delta]
        for i in range(len(self.weights) - 2, -1, -1):
            delta = (delta @ self.weights[i+1].T) * self._activation_deriv(z_values[i])
            deltas.insert(0, delta)
        
        # Update weights and biases
        batch_size = a.shape[0]
        for i in range(len(self.weights)):
            dW = (activations[i].T @ deltas[i]) / batch_size
            db = np.sum(deltas[i], axis=0, keepdims=True) / batch_size
            
            self.weights[i] -= learning_rate * dW
            self.biases[i] -= learning_rate * db
    
    def predict_dynamics(self, a_current: np.ndarray) -> np.ndarray:
        """Predict next POD coefficients given current."""
        activations, _ = self.forward(a_current)
        return activations[-1]  # Output layer
    
    def train(self, a_history: np.ndarray, epochs: int = 100, 
              learning_rate: float = 0.001, batch_size: int = 32,
              validation_split: float = 0.2) -> Dict:
        """
        Train neural network to predict POD dynamics.
        
        Parameters:
            a_history (np.ndarray): POD coefficient history (n_snapshots, n_modes)
            epochs (int): Number of training epochs
            learning_rate (float): Learning rate
            batch_size (int): Batch size
            validation_split (float): Fraction for validation
            
        Returns:
            Dict: Training history
        """
        n_snapshots = a_history.shape[0]
        n_train = int(n_snapshots * (1 - validation_split))
        
        train_data = a_history[:n_train]
        val_data = a_history[n_train:]
        
        # Create input-target pairs (predict next step)
        X_train = train_data[:-1]
        Y_train = train_data[1:]
        X_val = val_data[:-1]
        Y_val = val_data[1:]
        
        n_batches = max(1, len(X_train) // batch_size)
        
        for epoch in range(epochs):
            # Shuffle training data
            indices = np.random.permutation(len(X_train))
            X_train_shuffled = X_train[indices]
            Y_train_shuffled = Y_train[indices]
            
            # Train on batches
            epoch_loss = 0
            for batch in range(n_batches):
                start_idx = batch * batch_size
                end_idx = min(start_idx + batch_size, len(X_train))
                
                X_batch = X_train_shuffled[start_idx:end_idx]
                Y_batch = Y_train_shuffled[start_idx:end_idx]
                
                self.backward(X_batch, Y_batch, learning_rate)
                
                # Compute loss
                pred, _ = self.forward(X_batch)
                loss = np.mean((pred[-1] - Y_batch)**2)
                epoch_loss += loss
            
            epoch_loss /= n_batches
            self.loss_history.append(epoch_loss)
            
            # Validation
            if len(X_val) > 0:
                val_pred, _ = self.forward(X_val)
                val_loss = np.mean((val_pred[-1] - Y_val)**2)
                self.validation_loss_history.append(val_loss)
            
            if (epoch + 1) % max(1, epochs // 10) == 0:
                if self.verbose:
                    val_str = f", Val: {val_loss:.4e}" if len(X_val) > 0 else ""
                    print(f"Epoch {epoch+1:3d}/{epochs}: Loss={epoch_loss:.4e}{val_str}")
        
        return {
            'loss_history': self.loss_history,
            'validation_loss_history': self.validation_loss_history,
            'final_loss': epoch_loss,
            'final_val_loss': self.validation_loss_history[-1] if len(self.validation_loss_history) > 0 else None
        }
    
    def forecast(self, a_init: np.ndarray, n_steps: int) -> np.ndarray:
        """
        Forecast POD coefficients forward in time.
        
        Parameters:
            a_init (np.ndarray): Initial POD coefficients (n_modes,)
            n_steps (int): Number of steps to forecast
            
        Returns:
            np.ndarray: Forecasted coefficients (n_steps, n_modes)
        """
        a_forecast = np.zeros((n_steps, self.n_modes))
        a_current = a_init.reshape(1, -1)
        
        for t in range(n_steps):
            a_next = self.predict_dynamics(a_current)
            a_forecast[t] = a_next[0]
            a_current = a_next
        
        return a_forecast
    
    def get_summary(self) -> Dict:
        """Get network summary."""
        total_params = sum(w.size + b.size for w, b in zip(self.weights, self.biases))
        
        return {
            'n_modes': self.n_modes,
            'architecture': [self.n_modes] + list(self.hidden_dims) + [self.n_modes],
            'total_parameters': total_params,
            'activation': self.activation,
            'training_loss': self.loss_history[-1] if len(self.loss_history) > 0 else None
        }


class PODNNSurrogate:
    """
    Complete POD-NN surrogate model combining POD basis with neural network.
    """
    
    def __init__(self, pod_modes: np.ndarray, pod_energy: np.ndarray, 
                 mean_field: np.ndarray, nn_hidden_dims: Tuple[int] = (64, 64)):
        """Initialize POD-NN surrogate."""
        self.pod_modes = pod_modes
        self.pod_energy = pod_energy
        self.mean_field = mean_field
        
        n_modes = pod_modes.shape[1]
        self.nn = PODNeuralNetwork(n_modes, hidden_dims=nn_hidden_dims)
        
        self.is_trained = False
    
    def train_from_snapshots(self, pod_coeffs: np.ndarray, epochs: int = 100, 
                            learning_rate: float = 0.001) -> Dict:
        """Train NN from POD coefficient time history."""
        history = self.nn.train(
            pod_coeffs.T,
            epochs=epochs,
            learning_rate=learning_rate
        )
        self.is_trained = True
        return history
    
    def predict_full_field(self, a: np.ndarray) -> np.ndarray:
        """Predict full field from POD coefficients."""
        if a.ndim == 1:
            return self.mean_field + self.pod_modes @ a
        else:
            n_time = a.shape[1]
            u = np.zeros((self.mean_field.shape[0], n_time))
            for t in range(n_time):
                u[:, t] = self.mean_field + self.pod_modes @ a[:, t]
            return u
    
    def forecast_dynamics(self, a_init: np.ndarray, n_steps: int) -> Tuple[np.ndarray, np.ndarray]:
        """Forecast dynamics using trained NN."""
        if not self.is_trained:
            raise RuntimeError("Neural network not trained yet. Call train_from_snapshots() first.")
        
        a_forecast = self.nn.forecast(a_init, n_steps)
        u_forecast = self.predict_full_field(a_forecast.T)
        
        return a_forecast, u_forecast


def compare_rom_methods(pod_solver, snapshots_true: np.ndarray, 
                       time_vector: np.ndarray, n_modes: int = 15) -> Dict:
    """
    Compare POD-Galerkin ROM vs POD-NN surrogate.
    
    Returns:
        Dict: Comparison metrics
    """
    from pod_galerkin_rom import PODGalerkinROM
    
    # Extract initial conditions
    a_init = pod_solver.Vt[:, 0]
    
    # POD-Galerkin
    rom_galerkin = PODGalerkinROM.from_pod_solver(pod_solver)
    t_g, a_g, u_g = rom_galerkin.predict(a_init[:n_modes], t_final=time_vector[-1], 
                                          n_steps=len(time_vector))
    error_g = np.mean(np.linalg.norm(snapshots_true - u_g[:, :snapshots_true.shape[1]], 
                                     axis=0) / np.linalg.norm(snapshots_true, axis=0))
    
    # POD-NN
    surrogate = PODNNSurrogate(pod_solver.U[:, :n_modes], 
                               pod_solver.energy[:n_modes],
                               pod_solver.mean_field.flatten())
    surrogate.train_from_snapshots(pod_solver.Vt[:n_modes, :], epochs=50, 
                                   learning_rate=0.01)
    a_nn, u_nn = surrogate.forecast_dynamics(a_init[:n_modes], len(time_vector)-1)
    error_nn = np.mean(np.linalg.norm(snapshots_true[:, 1:] - u_nn[:, :snapshots_true.shape[1]-1], 
                                      axis=0) / np.linalg.norm(snapshots_true[:, 1:], axis=0))
    
    return {
        'method_galerkin': {
            'prediction_error': error_g,
            'type': 'Intrusive ROM'
        },
        'method_nn': {
            'prediction_error': error_nn,
            'type': 'Non-intrusive surrogate'
        },
        'nn_parameters': surrogate.nn.get_summary()
    }
