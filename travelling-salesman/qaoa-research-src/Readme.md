# Quantum TSP Solver with QAOA

## Overview

This project solves small Traveling Salesman Problem (TSP) instances with the Quantum Approximate Optimization Algorithm (QAOA) using Qiskit, and benchmarks the result against the exact classical (brute-force) optimum. It runs on a local simulator out of the box; an IBM Quantum account is only needed for noisy simulation or real hardware.

## Quick Start

```bash
# 1. Clone and enter this directory
git clone https://github.com/codeWithUtkarsh/qaoa-combinatorial-benchmarks.git
cd qaoa-combinatorial-benchmarks/travelling-salesman/qaoa-research-src

# 2. Create a virtual environment (Python 3.11+)
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Run (default config: 3 cities on the ideal local simulator, no account needed)
python main.py
```

Alternatively, `./startup.sh` does steps 2–4 in one go (macOS/Linux).

> Always run from this directory: `config.yaml` and `saved_result/` are resolved relative to the working directory.

## Configuration

All settings live in `config.yaml`:

```yaml
output_dir: './saved_result'

# Problem
num_cities_list: [3]     # one run per entry; n cities -> n^2 qubits
penalty_weight: 0.01     # weight of the distance terms in the Hamiltonian

# QAOA
p_level: 1               # QAOA repetitions (reps)
optimizer: 'COBYLA'      # any gradient-free scipy.optimize.minimize method
max_iter: 100
shots: 2000
seed: null               # integer for reproducible runs, null for random

# Backend
use_simulator: true      # false -> run on real IBM Quantum hardware
noisy_simulator: false   # simulator only: true -> copy the noise model of `backend_name` (needs IBM account)
backend_name: 'ibm_brisbane'
```

### Backend modes

| `use_simulator` | `noisy_simulator` | Backend | IBM account needed |
|---|---|---|---|
| `true` | `false` | Ideal `AerSimulator` | No |
| `true` | `true` | `AerSimulator` with the noise model of `backend_name` | Yes |
| `false` | — | Real device `backend_name` | Yes (consumes your quantum time) |

### IBM Quantum credentials

Credentials are **never** stored in `config.yaml`. Provide them through environment variables:

```bash
export QISKIT_IBM_TOKEN='<your API key>'
export QISKIT_IBM_INSTANCE='<your instance CRN>'
```

If these are not set, the account previously saved with `QiskitRuntimeService.save_account(...)` is used. Make sure `backend_name` is a device your instance has access to.

### Problem size

Each city count `n` needs `n²` qubits, so simulation cost grows quickly: 3 cities (9 qubits) runs in seconds, 5 cities (25 qubits) can take a long time on a laptop. The classical brute-force comparison runs for `n < 6`.

## Output

Results go to `output_dir` (default `./saved_result/`):

- `experiment_data.json` — metrics per city count. New runs are **merged** into the existing file and overwrite entries for the same city count.
- `app_<cities>_<timestamp>.log` — full run log.

Recorded metrics:

| Key | Description |
|---|---|
| `classical_optimal_tour`, `classical_optimal_distance` | Exact optimum (brute force, `n < 6`) |
| `quantum_best_tour_found`, `quantum_best_tour_distance` | Best tour decoded from the most likely bitstring. If that bitstring violates the constraints, the decoder repairs it (fills empty positions with unused cities), so the tour may not have been measured directly |
| `quantum_possible_best_tours` | All tours decoded from that bitstring |
| `gap` | % gap between quantum and classical tour distance (`n < 6`) |
| `transpiled_circuit_depth`, `transpiled_gate_count` | Size of the transpiled circuit |
| `circuit_execution_estimated_time(ns)` | Sum of calibrated gate durations (0 on the ideal simulator, which has no calibration data) |
| `iterations`, `optimization_time(sec)` | Cost-function evaluations and wall time of the classical optimizer |
| `p_level`, `optimizer`, `optimization_level`, `backend_in_use` | Settings actually used for the run |
| `real_execution_time` | Hardware execution time of the final sampling job (real hardware only) |

## Algorithm Description

### 1. Problem formulation (`src/ImprovedTSPHamiltonian.py`)
- **Distance matrix:** random symmetric matrix, values in [0, 10), generated with fixed seed `123` so the instance for a given `n` is always the same.
- **Encoding:** `n²` qubits, one per (city, position) pair; qubit index = `position * n + city` (Qiskit little-endian, so qubit 0 is the rightmost bit of a measured bitstring).
- **D operator:** `D(city, position) = 0.5 * (I - Z)`, the projector onto "city is at position".

### 2. Hamiltonian

Standard TSP QUBO (Lucas, *Ising formulations of many NP problems*, 2014), with positions taken cyclically so the tour returns to its start:

```
H = H_a + H_b + H_c + penalty_weight * H_d

H_a : each city appears in exactly one position     Σ_city (1 - Σ_pos D(city, pos))²
H_b : each position holds exactly one city          Σ_pos  (1 - Σ_city D(city, pos))²
H_c : penalty for unconnected cities in adjacent    Σ_pos Σ_(u,v) not connected  D(u, pos) D(v, pos+1)
      positions (zero for the complete graphs used here)
H_d : tour length                                   Σ_pos Σ_(u,v) d(u,v) D(u, pos) D(v, pos+1)
```

The ground state of `H` is the optimal tour as long as `penalty_weight * max(d)` is below 1 (the constraint weight). With distances in [0, 10) the default `penalty_weight: 0.01` satisfies this.

### 3. QAOA pipeline (`src/ProcessQaoa.py`)

```
1. ImprovedTSPHamiltonian(num_cities, seed=123)
2. tsp.create_hamiltonian(penalty_weight)
3. QAOAAnsatz(cost_operator=H, reps=p_level)
4. generate_preset_pass_manager(backend, optimization_level=3, seed_transpiler=42)
5. scipy.optimize.minimize(<EstimatorV2 expectation value>, method=optimizer, maxiter=max_iter)
     initial parameters ~ Uniform[-π/8, π/8]
6. SamplerV2 on the optimised circuit -> bitstring distribution
7. Most likely bitstring -> city/position matrix -> valid tours -> shortest tour
```

## Project Structure

```
qaoa-research-src/
├── main.py                       # entry point: reads config, loops over num_cities_list
├── config.yaml                   # run settings (no secrets)
├── startup.sh                    # venv + install + run helper
├── requirements.txt              # pinned dependencies
├── src/
│   ├── ProcessQaoa.py            # backend selection, QAOA loop, classical comparison
│   ├── ImprovedTSPHamiltonian.py # Hamiltonian used by the pipeline
│   ├── TSPHamiltonian.py         # earlier Hamiltonian formulation (not used by main.py)
│   ├── SampleProcessing.py       # most-likely bitstring, bitstring -> matrix
│   ├── DecodeBitstringTSP.py     # matrix -> tour sequences
│   ├── Utility.py                # circuit metrics, experiment_data.json I/O
│   └── Visualization.py          # plotting helpers
├── documents/                    # algorithm write-ups
└── saved_result/                 # results and logs from previous runs
```

## Verify Installation

```bash
python --version   # 3.11 or newer
python -c "import qiskit, qiskit_aer; print('Qiskit', qiskit.__version__, '| Aer', qiskit_aer.__version__)"
```
