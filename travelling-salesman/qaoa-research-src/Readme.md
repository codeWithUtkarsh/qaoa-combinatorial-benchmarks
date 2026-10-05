# Quantum TSP Solver with QAOA

## Overview

This project implements a quantum-enhanced Traveling Salesman Problem (TSP) solver using the Quantum Approximate Optimization Algorithm (QAOA). The implementation leverages Qiskit's quantum computing framework to solve TSP instances and compare quantum vs classical optimization approaches.

## Quick Start

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/codeWithUtkarsh/tsp-quantum-algorithm.git
cd tsp-quantum-algorithm/CPU

# Create and activate virtual environment (using Python 3.11.9)
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure (Optional)
Edit `config.yaml` to customize your run:
```yaml
num_cities_list: [3, 4, 5]  # Adjust problem sizes
optimizers: ['COBYLA']
penalty_weight: 0.01
use_simulator: true # Update to False to use the real quantum device
shots: 1024
max_iter: 100

```

### 3. Run
```bash
python main.py
```

## Algorithm Description

### QAOA-based TSP Algorithm

The core algorithm implements a quantum approach to solving the TSP using an improved Hamiltonian formulation:

#### 1. TSP Problem Formulation
- **Distance Matrix Generation**: Creates random symmetric distance matrices with seeded random generation
- **Qubit Encoding**: Uses n² qubits for n cities (one qubit per city-position pair)
- **Hamiltonian Construction**: Builds TSP Hamiltonian with multiple constraint terms

#### 2. Improved TSP Hamiltonian Components

The algorithm uses four main constraint terms:

```python
# Hamiltonian Structure:
H = H_a + H_b + H_c + penalty_weight * H_d

Where:
- H_a: Each city visited exactly once
- H_b: Each position has exactly one city  
- H_c: Connectivity constraint (adjacent positions must be connected)
- H_d: Distance weighting (minimize total tour distance)
```

**D Operator Definition:**
- D(city, position) = 0.5 * (I - Z)
- Maps qubit states to city assignments

#### 3. Quantum Optimization Pipeline

```python
# Algorithm Flow:
1. TSP Instance Creation
   └── ImprovedTSPHamiltonian(num_cities, seed=123)

2. Hamiltonian Construction
   └── tsp.create_hamiltonian(penalty_weight=0.01)

3. QAOA Circuit Creation
   └── QAOAAnsatz(cost_operator=hamiltonian, reps=p_level)
   └── p_level = ceil(log2(num_cities²))

4. Circuit Transpilation
   └── generate_preset_pass_manager(backend, optimization_level=2)

5. Quantum Optimization
   └── EstimatorV2 with COBYLA optimizer

6. Result Sampling
   └── SamplerV2 to get final bitstring distribution
```

#### 4. QAOA Configuration

**Quantum Components:**
- **Backend**: IBM Quantum Runtime or Aer Simulator
- **Shots**: 1000 (default, configurable)
- **Transpiler**: Optimization level 2 with seed 42

**Classical Optimizer:**
- **Algorithm**: COBYLA (Constrained Optimization BY Linear Approximation)
- **Max Iterations**: 100 (default, configurable)
- **Initial Parameters**: Random uniform in [-π/8, π/8]

**QAOA Parameters:**
- **Repetitions (p)**: Dynamically calculated as ceil(log2(n²))
- **Ansatz**: QAOAAnsatz with problem-specific cost Hamiltonian

#### 4. Performance Metrics Tracking

The algorithm tracks comprehensive performance metrics:

```python
Metrics Collected:
├── optimization_time        # Total optimization time
├── iterations              # Number of function evaluations
├── quantum_width           # Circuit width
├── quantum_depth           # Circuit depth  
├── quantum_size            # Total gate count
└── gap                     # Percentage gap from classical optimal (if computed)
```

#### 5. Solution Processing

**Result Analysis:**
- Extracts most probable bitstring from measurement distribution
- Interprets bitstring as city-position matrix
- Generates valid tour sequences from matrix
- Calculates tour distances and selects optimal

**Classical Comparison:**
- For small instances (n < 6), computes exact solution via brute force
- Calculates optimality gap for benchmarking

## Installation and Setup

### Prerequisites

- Python 3.11.9 (required)
- pip package manager

### Detailed Installation Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/codeWithUtkarsh/tsp-quantum-algorithm.git
cd tsp-quantum-algorithm
```

#### 2. Navigate to CPU Directory

```bash
cd CPU
```

#### 3. Create Virtual Environment (Highly Recommended)

```bash
# Create virtual environment (ensure Python 3.11.9 is installed)
python3.11 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# On Windows PowerShell:
venv\Scripts\Activate.ps1
```

#### 4. Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install required packages
pip install -r requirements.txt
```

**Key Dependencies:**
- `PyYAML` - YAML file parsing and configuration management
- `numpy` - Numerical computations and array operations
- `qiskit-optimization` - Quantum optimization algorithms (QAOA, VQE)
- `psutil` - System monitoring and process utilities
- `matplotlib` - Data visualization and plotting
- `qiskit==2.0.3` - Core quantum computing framework
- `py-cpuinfo` - CPU information and hardware profiling
- `pandas` - Data manipulation and analysis
- `qiskit-aer` - High-performance quantum circuit simulator
- `qiskit-algorithms` - Quantum algorithms library
- `qiskit-ibm-runtime` - IBM Quantum cloud services integration

#### 5. Verify Installation

```bash
# Test if installation is successful
python3 --version  # Should show Python 3.11.9
python3 -c "import qiskit; print(f'Qiskit version: {qiskit.__version__}')"
```
