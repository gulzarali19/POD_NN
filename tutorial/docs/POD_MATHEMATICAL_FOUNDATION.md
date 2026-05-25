# Proper Orthogonal Decomposition (POD) - Mathematical Foundation

## Overview

Proper Orthogonal Decomposition (POD) is a model reduction technique that extracts coherent structures and dominant patterns from high-dimensional fluid flow data. It provides an optimal basis for projecting the Navier-Stokes equations onto a lower-dimensional subspace, enabling efficient computational modeling.

## Fundamental Concepts

### 1. Snapshot Matrix

From time-dependent CFD simulations, we collect spatial field data at discrete time instances:

$$\mathbf{X} = [\mathbf{u}_1, \mathbf{u}_2, \ldots, \mathbf{u}_M] \in \mathbb{R}^{n \times M}$$

where:
- $n$ = number of spatial degrees of freedom (grid points × number of variables)
- $M$ = number of snapshots (temporal instances)
- $\mathbf{u}_i \in \mathbb{R}^{n}$ = instantaneous field at time $t_i$

For example, in 2D cavity flow:
- If grid is $128 \times 128$ and we track $u$ and $v$ components
- Then $n = 128 \times 128 \times 2 = 32,768$

### 2. Data Centering

To remove temporal mean effects, center the snapshot matrix:

$$\mathbf{X}' = \mathbf{X} - \overline{\mathbf{u}} \mathbf{1}^T$$

where:
$$\overline{\mathbf{u}} = \frac{1}{M} \sum_{i=1}^{M} \mathbf{u}_i$$

is the temporal mean field, and $\mathbf{1} \in \mathbb{R}^{M}$ is a vector of ones.

### 3. Correlation Matrix (Ensemble Average)

The spatial correlation matrix is:

$$\mathbf{C} = \frac{1}{M} \mathbf{X}'^T \mathbf{X}'$$

This symmetric positive-definite matrix captures spatial correlations across the flow.

## Proper Orthogonal Decomposition

### POD Mode Definition

POD modes $\{\psi_i\}_{i=1}^{M}$ are the eigenvectors of the correlation matrix $\mathbf{C}$, ordered by decreasing eigenvalues:

$$\mathbf{C} \psi_i = \lambda_i \psi_i, \quad \lambda_1 \geq \lambda_2 \geq \cdots \geq \lambda_M \geq 0$$

The mode $\psi_i$ is optimal in the sense that it maximizes the variance (kinetic energy) captured:

$$\psi_1 = \arg\max_{\|\psi\|=1} \frac{1}{M} \sum_{i=1}^{M} (\psi^T \mathbf{u}_i)^2$$

### Reduced Order Model (ROM)

The original flow field is approximated as a linear combination of POD modes:

$$\Phi(x, t) \approx \overline{\mathbf{u}} + \sum_{k=1}^{K} a_k(t) \psi_k(x)$$

where:
- $K$ = number of retained modes ($K \ll M$)
- $a_k(t)$ = temporal coefficient (mode amplitude)
- $\psi_k(x)$ = spatial basis function (POD mode)

**Energy Content:**

Each mode captures a fraction of the total variance:

$$\text{Energy}_k = \frac{\lambda_k}{\sum_{j=1}^{M} \lambda_j}$$

The cumulative energy of the first $K$ modes:

$$E(K) = \frac{\sum_{k=1}^{K} \lambda_k}{\sum_{j=1}^{M} \lambda_j} \quad (0 \leq E(K) \leq 1)$$

## The Method of Snapshots

For large-scale spatial problems ($n \gg M$), direct SVD of $\mathbf{X}'$ is computationally expensive. The **Method of Snapshots** provides an elegant solution.

### Derivation

Instead of solving:
$$\mathbf{X}''^T \mathbf{X}' \psi = \lambda \psi \quad (\text{expensive: } n \times n \text{ matrix})$$

we solve the dual problem:
$$\mathbf{X}' \mathbf{X}'^T \phi = \lambda \phi \quad (\text{efficient: } M \times M \text{ matrix})$$

### Relationship Between Solutions

If $\phi_i$ is an eigenvector of $\mathbf{X}' \mathbf{X}'^T$:

$$\psi_i = \frac{1}{\sqrt{\lambda_i}} \mathbf{X}' \phi_i$$

is the corresponding eigenvector of $\mathbf{X}'^T \mathbf{X}'$.

### Computational Steps

1. **Form the reduced correlation matrix:**
   $$\mathbf{G} = \frac{1}{M} \mathbf{X}'^T \mathbf{X}' \quad \text{(size: } M \times M\text{)}$$

2. **Eigenvalue decomposition:**
   $$\mathbf{G} \boldsymbol{\Phi} = \boldsymbol{\Phi} \boldsymbol{\Lambda}$$

3. **Recover spatial modes:**
   $$\boldsymbol{\Psi} = \mathbf{X}' \boldsymbol{\Phi} \boldsymbol{\Lambda}^{-1/2}$$

### Computational Complexity

| Approach | SVD Complexity | Memory |
|----------|---|---|
| Direct SVD | $O(n^2 M)$ | $O(nM)$ |
| Method of Snapshots | $O(M^3)$ | $O(M^2)$ |

**When to use Method of Snapshots:** $n > 10^4$ and $M < n$

## Connection to Singular Value Decomposition (SVD)

The POD can be directly computed via SVD:

$$\mathbf{X}' = \mathbf{U} \boldsymbol{\Sigma} \mathbf{V}^T$$

where:
- $\mathbf{U} \in \mathbb{R}^{n \times M}$ contains POD modes as columns
- $\boldsymbol{\Sigma} = \text{diag}(\sigma_1, \ldots, \sigma_M)$ with $\sigma_k = \sqrt{M \lambda_k}$
- $\mathbf{V} \in \mathbb{R}^{M \times M}$ contains normalized temporal coefficients

**Temporal Coefficients:**
$$a_k(t) = \sigma_k V_{k,:}$$

## Reconstruction and Error Analysis

### ROM Reconstruction

The reconstructed field at time $t_j$:

$$\tilde{\Phi}_j(x) = \overline{\mathbf{u}} + \sum_{k=1}^{K} a_k(t_j) \psi_k(x) = \overline{\mathbf{u}} + \mathbf{U}_K a(t_j)$$

where $\mathbf{U}_K$ contains the first $K$ POD modes.

### L2 Norm Error

Relative reconstruction error:

$$\epsilon_K = \frac{\|\mathbf{X} - \tilde{\mathbf{X}}_K\|_F}{\|\mathbf{X}\|_F}$$

where:
$$\|\mathbf{A}\|_F = \sqrt{\sum_{i,j} A_{ij}^2} \quad \text{(Frobenius norm)}$$

This error decreases as $K$ increases and approaches zero when $K = M$.

### Optimal Number of Modes

Choose $K$ such that the cumulative energy satisfies:

$$E(K) = \frac{\sum_{k=1}^{K} \lambda_k}{\sum_{j=1}^{M} \lambda_j} \geq \text{target (e.g., 0.95 or 0.99)}$$

Typical choice: $E(K) \geq 0.95$ (95% energy retention)

## Physical Interpretation

### Karhunen-Loève Expansion

POD is equivalent to the Karhunen-Loève (KL) expansion in probability theory:

$$u(x, t) = \sum_{k=1}^{\infty} \sqrt{\lambda_k} f_k(t) \psi_k(x)$$

where $f_k(t)$ are uncorrelated random processes with unit variance.

### Coherent Structures

POD modes identify **coherent structures** in the flow:
- **Mode 1:** Dominant global circulation/large-scale patterns
- **Mode 2-5:** Secondary structures, vortex interactions
- **Higher modes:** Small-scale, high-frequency content

For example, in cavity flow:
- Mode 1 captures the primary circulation
- Mode 2-3 capture corner vortex dynamics
- Higher modes capture viscous dissipation effects

## Summary Table

| Concept | Definition | Interpretation |
|---|---|---|
| Snapshot | Field at time instance | CFD solution vector |
| POD Mode | Eigenvector of correlation matrix | Spatial basis function |
| Singular Value | $\sigma_k = \sqrt{M \lambda_k}$ | Energy amplitude of mode |
| Temporal Coeff. | $a_k(t)$ | Mode amplitude time evolution |
| Energy $E(K)$ | Cumulative variance fraction | Information capture percentage |
| ROM | Linear combination of K modes | Reduced model |

## References

1. **Lumley, J. L. (1967).** "The structure of inhomogeneous turbulent flows." *Atmospheric Turbulence and Wave Propagation.*

2. **Sirovich, L. (1987).** "Turbulence and the dynamics of coherent structures." *Quarterly of Applied Mathematics*, 45(3), 561-590.

3. **Berkooz, G., Holmes, P., & Lumley, J. L. (1993).** "The proper orthogonal decomposition in the analysis of turbulent flows." *Annual Review of Fluid Mechanics*, 25, 539-575.

4. **Volkwein, S. (2013).** "Proper orthogonal decomposition and singular value decomposition." Technical Report, University of Konstanz.

5. **Holmes, P., Lumley, J. L., & Berkooz, G. (2012).** *Turbulence, Coherent Structures, Dynamical Systems and Symmetry.* Cambridge University Press.

---

**Author:** CFD/SciML Expert  
**Last Updated:** 2026
