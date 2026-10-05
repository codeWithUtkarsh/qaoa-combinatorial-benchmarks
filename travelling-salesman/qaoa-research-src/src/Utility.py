import json
import os
from os import mkdir
from os.path import exists

import yaml
from typing import Dict, Any

import logging

logger = logging.getLogger(__name__)

config_file = "./config.yaml"
with open(config_file, "r") as file:
    config = yaml.safe_load(file)
output_dir = config.get('output_dir', '.saved_result')


def estimate_quantum_circuit(backend, qc, num_vertices):

    # backend = service.backend("ibm_brisbane")
    backend_properties = backend.properties()
    gate_durations = {}
    for gate in backend_properties.gates:
        name = gate.name
        name = ''.join(c for c in name if c.isalpha())
        qubits = tuple(gate.qubits)
        duration = next((param.value for param in gate.parameters if param.name == "gate_length"), None)
        if duration:
            gate_durations[(name, qubits)] = duration
    estimated_time = 0
    for instruction, qargs, _ in qc.data:
        gate_name = instruction.name
        qubit_indices = tuple(qc.qubits.index(q) for q in qargs)
        # Try to match the exact gate-qubit pair
        key = (gate_name, qubit_indices)
        if key in gate_durations:
            estimated_time += gate_durations[key]

    return {
        "circuit_execution_estimated_time(ns)": estimated_time,
        "transpiled_circuit_depth": qc.depth(),
        "transpiled_gate_count": qc.size(),
        "backend_in_use": backend,
    }

def update_experiment_data(
        num_node: int,
        data_key: str,
        data_value: str,
        filename: str = 'experiment_data.json',) -> Dict[str, Any]:

    experiment_data = _load_experiment_data(filename, output_dir)
    num_nodes_str = str(num_node)

    if num_nodes_str not in experiment_data["experiment_data"]:
        experiment_data["experiment_data"][num_nodes_str] = {}

    experiment_data["experiment_data"][num_nodes_str][data_key] = data_value
    _save_experiment_data(experiment_data, filename, output_dir)
    return experiment_data


def _load_experiment_data(
        filename: str,
        directory: str = ".") -> Dict[str, Any]:
    filepath = os.path.join(directory, filename)

    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                experiment_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            experiment_data = {"experiment_data": {}}
    else:
        experiment_data = {"experiment_data": {}}

    if "experiment_data" not in experiment_data:
        experiment_data["experiment_data"] = {}
    return experiment_data


def _save_experiment_data(
        experiment_data: Dict[str, Any],
        filename: str,
        directory: str = ".") -> None:
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # Join directory and filename
    filepath = os.path.join(directory, filename)

    try:
        with open(filepath, 'w') as f:
            json.dump(experiment_data, f, indent=2)
    except IOError as e:
        error_msg = f"Error saving to {filepath}: {e}"
        raise IOError(error_msg)
