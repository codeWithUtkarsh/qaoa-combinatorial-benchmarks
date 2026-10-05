# Prerequisites

Use **Python 3.11**.

You will need:

- Python 3.11
- `venv`
- `pip`
- Jupyter Notebook

The current QAOA workflow uses the **local Qiskit Aer CPU simulator**, so an IBM Quantum account is not required.

---

# QAOA Graph Colouring Benchmark

This directory contains an experimental implementation of the **Graph Colouring Problem** using the **Quantum Approximate Optimization Algorithm (QAOA)**.

The current notebook runs QAOA locally using **Qiskit Aer on CPU**, decodes the most probable measured state into a graph colouring, validates the result, retries when necessary, and records end-to-end execution behaviour.

The main implementation is:

```text
QAOA_Analysis.ipynb
```

---

## Problem

Given a graph

```text
G = (V, E)
```

assign a colour to each vertex such that no two adjacent vertices have the same colour.

For every edge

```text
(u, v) ∈ E
```

a valid colouring must satisfy

```text
colour(u) != colour(v)
```

The notebook investigates this problem using a QUBO / Hamiltonian formulation solved with QAOA.

---

## Directory Contents

```text
graph-colouring/
├── QAOA_Analysis.ipynb
├── accuracy_analysis.ipynb
├── plot_GC.py
├── Plot_tsp.py
├── GC_Data.zip
├── tsp_data.zip
├── requirements.txt
└── README.md
```

| File | Purpose |
|---|---|
| `QAOA_Analysis.ipynb` | Main graph-colouring QAOA experiment |
| `accuracy_analysis.ipynb` | Post-processing and accuracy analysis |
| `plot_GC.py` | Graph-colouring benchmark parsing and plotting |
| `Plot_tsp.py` | Additional benchmark parsing / comparison utilities |
| `GC_Data.zip` | Stored graph-colouring experiment data |
| `tsp_data.zip` | Additional experimental data |
| `requirements.txt` | Python dependencies |

---

# Current QAOA Pipeline

The final notebook follows this execution flow:

```text
Generate random graph
        ↓
Build graph-colouring QUBO
        ↓
Convert QUBO to Pauli Hamiltonian
        ↓
Construct QAOA ansatz
        ↓
Optimise parameters with COBYLA
        ↓
Execute using Qiskit Aer on CPU
        ↓
Extract most probable state
        ↓
Decode state into colours
        ↓
Validate graph colouring
        ↓
Retry if invalid
        ↓
Remap / plot valid colouring
        ↓
Record runtime and result
```

The current active experiment uses a fixed:

```text
QAOA depth p = 3
```

---

# Graph Generation

Random graphs are generated using NetworkX:

```python
def generate_graph(num_nodes, edge_prob=0.5):
    return nx.erdos_renyi_graph(num_nodes, edge_prob)
```

The default edge probability is:

```text
0.5
```

Because no graph-generation seed is currently specified, repeated notebook runs may generate different graphs and therefore different optimisation behaviour.

---

# QUBO Formulation

The function:

```python
create_qubo_hamiltonian(graph, num_colors)
```

constructs a QUBO matrix with one binary variable for each vertex-colour pair.

For:

```text
N = number of vertices
K = number of allowed colours
```

the formulation creates:

```text
N × K
```

binary variables.

The QUBO includes terms for:

- assigning colours to vertices,
- penalising multiple colours assigned to the same vertex,
- penalising adjacent vertices assigned the same colour.

The symmetric QUBO matrix is then converted into a Hamiltonian using Pauli-Z operators and represented with Qiskit's:

```python
SparsePauliOp
```

---

# QAOA Execution

QAOA is executed by:

```python
run_qaoa(...)
```

The current implementation uses:

```python
optimizer = COBYLA(
    maxiter=max_iter,
    tol=1e-6,
    disp=True
)
```

and an Aer sampler:

```python
base_sampler = Sampler(
    backend_options={
        "method": "automatic",
        "device": "CPU"
    },
    run_options={
        "shots": shots,
        "seed": 42
    }
)
```

QAOA is then created with:

```python
qaoa = QAOA(
    optimizer=optimizer,
    reps=p,
    sampler=base_sampler,
    callback=optimizer_callback
)
```

The active notebook therefore runs entirely on the **local Aer simulator** and does not require IBM Quantum credentials.

---

# Runtime Metrics

The notebook tracks two different timing concepts.

## 1. Aer sampling / measurement time

The QAOA callback reads:

```python
metadata["simulator_metadata"]["sample_measure_time"]
```

for every objective-function evaluation.

These values are accumulated into:

```text
qaoa_exec_time
```

This represents the simulator-reported sampling / measurement component and should **not** be interpreted as the complete QAOA runtime.

## 2. QAOA wall-clock time

The full call to:

```python
qaoa.compute_minimum_eigenvalue(...)
```

is measured using:

```python
time.perf_counter()
```

This produces:

```text
total_wall_time
```

which represents the complete wall-clock duration of the QAOA optimisation call.

The higher-level experiment also measures the complete retry workflow.

This distinction is important when comparing quantum-simulation cost with classical optimisation overhead.

---

# Optimisation Callback

The current callback records:

```text
objective evaluation count
callback / optimisation iteration count
Aer sample_measure_time per evaluation
sum of Aer sampling / measurement time
```

The callback intentionally uses:

```python
metadata.get(...)
```

rather than assuming that every Aer version exposes the same simulator metadata fields.

---

# Solution Extraction

After optimisation, the notebook selects the most probable state from:

```python
result.eigenstate
```

The state is converted into a bitstring and decoded into colour assignments.

The helper:

```python
decode_binary_coloring(...)
```

maps the binary representation to one colour index per vertex.

Invalid encodings are represented using:

```text
-1
```

---

# Validity Check

The function:

```python
is_valid_coloring(graph, coloring)
```

checks every graph edge.

A result is accepted only if:

1. every node has a valid colour assignment, and
2. no adjacent vertices share the same colour.

---

# Retry Strategy

The notebook does not assume that one QAOA run will immediately produce a valid colouring.

The function:

```python
run_qaoa_with_retry(...)
```

starts with:

```text
2 colours
```

and increases the allowed colour count up to:

```text
max_colors
```

For each colour count it performs up to:

```text
5 QAOA attempts
```

The process is approximately:

```text
Try 2 colours
    ↓
Run QAOA
    ↓
Valid colouring?
  ├── yes → return solution
  └── no  → retry, up to 5 times
                 ↓
             try 3 colours
                 ↓
                ...
```

If no valid colouring is found before reaching `max_colors`, the function raises:

```python
ValueError
```

---

# Colour Remapping

Valid QAOA colour assignments are normalised using:

```python
remap_colors(...)
```

For example, a solution using colour labels:

```text
[1, 3, 1, 2]
```

can be remapped to contiguous labels:

```text
[0, 2, 0, 1]
```

This makes result interpretation and plotting easier.

---

# Visualisation

The function:

```python
plot_coloring(...)
```

uses NetworkX and Matplotlib to display the graph with nodes coloured according to the QAOA solution.

A spring layout is used for graph positioning.

---

# Current Experiment Configuration

The final execution cell currently runs:

```python
for num_nodes in range(3, 5):
    G = generate_graph(num_nodes=num_nodes)
    results = sweep_qaoa_p_levels(
        G,
        max_colors=3,
        max_iter=500,
        shots=1024
    )
```

This corresponds to:

| Parameter | Current value |
|---|---:|
| Graph sizes | 3 and 4 nodes |
| Edge probability | 0.5 |
| QAOA depth `p` | 3 |
| Maximum colours | 3 |
| COBYLA maximum iterations | 500 |
| Shots | 1024 |
| Aer device | CPU |
| Aer method | Automatic |
| Sampler seed | 42 |
| QAOA attempts per colour count | 5 |

---

# Example Output from the Final Notebook

The saved notebook contains a successful example run for both graph sizes.

For the captured 3-node graph, QAOA found a valid two-colour solution:

```text
Number of colors allowed: 2
Number of colors actually used: 2
Coloring: [0, 1, 0]
```

The recorded retry-workflow wall time was approximately:

```text
0.83 s
```

For the captured 4-node graph, several two-colour attempts failed before the algorithm moved to three colours. A valid three-colour result was eventually found:

```text
Number of colors allowed: 3
Number of colors actually used: 3
Coloring: [0, 2, 2, 1]
```

The saved run recorded approximately:

```text
16.02 s
```

for the complete retry workflow.

These values are **example outputs from the saved notebook**, not general benchmark results. Since graph generation is currently unseeded, future runs may use different graph instances.

---

# Result Structure

`sweep_qaoa_p_levels(...)` returns a list containing a result dictionary with fields including:

```python
{
    "p": ...,
    "num_colors_allowed": ...,
    "num_colors_used": ...,
    "coloring": ...,
    "runtime": ...,
    "result": ...,
    "iterations": ...
}
```

Results are also written to:

```text
qaoa_results.log
```

using JSON-compatible logging with:

```python
json.dumps(..., default=str)
```

---

# DSATUR Classical Baseline

The notebook contains a classical DSATUR implementation:

```python
dsatur_coloring(...)
run_dsatur(...)
```

The implementation records:

```text
classical execution time
classical iteration count
```

These functions are available for classical comparison, but the current final experiment loop does **not yet invoke DSATUR alongside each QAOA run**.

They can be integrated into a later benchmark pass for direct QAOA-vs-classical comparisons.

---

# Graph c-depth Utilities

The notebook also contains:

```python
edge_bfs_depth(...)
compute_c_depth(...)
```

These functions estimate a covering-style graph depth using BFS over adjacent edges.

The notebook contains commented experimental code intended to use this value when selecting or sweeping QAOA `p` levels.

At present, however, the active experiment uses:

```python
p = 3
```

rather than dynamically selecting `p` from graph c-depth.

---

# Installation

## Python Version

Use **Python 3.11**.

The dependency set used by this repository is not compatible with Python 3.14.

Create the environment:

```bash
cd graph-colouring

python3.11 -m venv .venv
source .venv/bin/activate
```

Upgrade the packaging tools:

```bash
python -m pip install --upgrade pip setuptools wheel
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

---

## Dependency Notes

The supplied `requirements.txt` already includes the tested Qiskit/Aer versions, scientific packages, PySAT, Plotly, notebook dependencies, and the Windows-only `pywin32` platform guard.

A fresh environment should therefore require only:

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

No manual dependency edits should be needed.

---

# Jupyter Setup

Install Jupyter Notebook and the kernel package if required:

```bash
pip install notebook ipykernel
```

Register the virtual environment as a Jupyter kernel:

```bash
python -m ipykernel install \
    --user \
    --name qaoa-graph \
    --display-name "Python (qaoa-graph)"
```

Start Jupyter:

```bash
jupyter notebook
```

Open:

```text
QAOA_Analysis.ipynb
```

and select:

```text
Python (qaoa-graph)
```

To verify that the notebook is using the virtual environment:

```python
import sys
print(sys.executable)
```

The path should point to:

```text
graph-colouring/.venv/bin/python
```

---

# Running the Notebook

Run the cells from top to bottom.

The active experiment eventually executes:

```python
for num_nodes in range(3, 5):
    G = generate_graph(num_nodes=num_nodes)
    results = sweep_qaoa_p_levels(
        G,
        max_colors=3,
        max_iter=500,
        shots=1024
    )
```

To test the environment before running the full notebook, start with a single small graph:

```python
G = generate_graph(3)

results = sweep_qaoa_p_levels(
    G,
    max_colors=3,
    max_iter=50,
    shots=1024
)
```

---

# Recommended Next Benchmark Step

The current notebook demonstrates the complete graph-colouring QAOA pipeline successfully.

For a more rigorous benchmark, the next step would be to:

```text
fix / record random graph seeds
        ↓
generate multiple graphs per node count
        ↓
run multiple QAOA trials per graph
        ↓
run DSATUR on the same graph
        ↓
record:
    QAOA wall time
    Aer sample time
    objective evaluations
    retries
    colours used
    validity / success rate
    DSATUR time
        ↓
aggregate statistics
        ↓
plot scaling behaviour
```

Useful aggregate statistics include:

```text
mean
median
standard deviation
success rate
minimum / maximum runtime
```

This is important because both the random graph instance and the QAOA optimisation process affect individual-run results.

---

# Notes

This project is a **research / benchmarking implementation**, not a production graph-colouring library.

The current notebook is designed to study:

- graph-colouring QUBO construction,
- QAOA optimisation,
- local quantum simulation,
- solution validity,
- retry behaviour,
- runtime decomposition,
- classical comparison opportunities,
- and scaling as graph size increases.

---

# License

The repository-level licence is located at:

```text
../LICENSE
```