#!/usr/bin/env python3
import math
import time
import yaml
import logging
import numpy as np
from scipy.optimize import minimize
from itertools import permutations

from qiskit.circuit.library import QAOAAnsatz
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler, EstimatorV2 as Estimator
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator

from src.ImprovedTSPHamiltonian import ImprovedTSPHamiltonian
from src.SampleProcessing import interpret, sample_most_likely
from src.Utility import estimate_quantum_circuit, update_experiment_data
from src.Visualization import visualize_tsp_matrix_view
from src.DecodeBitstringTSP import generate_city_sequences

logger = logging.getLogger(__name__)

config_file = "./config.yaml"
with open(config_file, "r") as file:
    config = yaml.safe_load(file)

token = config['token']
instance = config['instance']

def get_backend(num_qubits, use_simulator):
    QiskitRuntimeService.delete_account()
    QiskitRuntimeService.save_account(token=token,instance=instance,overwrite=True)
    service = QiskitRuntimeService()
    if use_simulator:
        logger.info("Using Simulator")
        real_backend = service.backend('ibm_brisbane')
        # real_backend = service.least_busy(
        #     operational=True, simulator=False, min_num_qubits=num_qubits * num_qubits
        # )
        simulator = AerSimulator.from_backend(real_backend)
        # simulator = AerSimulator()
        return simulator
    else:
        logger.info("Using Real Hardware")
        return service.backend('ibm_brisbane')
        # return service.least_busy(
        #     operational=True, simulator=False, min_num_qubits=num_qubits * num_qubits,
        # )

def run_qaoa(
        num_cities,
        tsp,
        penalty_weight=0.01,
        p_level=2,
        max_iter=100,
        shots=1000,
        use_simulator=True):
    """Run QAOA with improved TSP Hamiltonian"""

    logger.debug("Distance matrix:")
    logger.debug(tsp.distances)

    # Create Hamiltonian
    cost_hamiltonian = tsp.create_hamiltonian(penalty_weight=penalty_weight)
    logger.debug(f"Hamiltonian created with {len(cost_hamiltonian)} terms")

    # Create QAOA circuit
    _quantum_circuit = QAOAAnsatz(cost_operator=cost_hamiltonian, reps=1)
    _backend = get_backend(num_cities, use_simulator)

    preset_manager = generate_preset_pass_manager(
        backend=_backend, optimization_level=3, seed_transpiler=42
    )
    isa_circuit = preset_manager.run(_quantum_circuit)
    isa_circuit.global_phase = 0.0
    quantum_result_attributes = estimate_quantum_circuit(_backend, isa_circuit, num_cities)

    # Setup estimator
    estimator = Estimator(_backend)
    estimator.options.default_shots = shots

    objective_func_vals = []

    def cost_func_estimator(params, ansatz, hamiltonian, _estimator):
        isa_hamiltonian = hamiltonian.apply_layout(ansatz.layout)
        pub = (ansatz, isa_hamiltonian, params)
        job = _estimator.run([pub])
        results = job.result()[0]
        cost = results.data.evs
        objective_func_vals.append(cost)
        logger.debug(f"Cost: {cost:.6f}")
        return cost

    # Initialize parameters
    num_params = _quantum_circuit.num_parameters
    initial_params = np.random.uniform(-np.pi / 8, np.pi / 8, num_params)

    # Optimize
    logger.debug("Starting optimization...")
    start_time = time.time()

    result = minimize(
        cost_func_estimator,
        initial_params,
        args=(isa_circuit, cost_hamiltonian, estimator),
        method='COBYLA',
        options={'maxiter': max_iter, 'disp': True}
    )
    quantum_result_attributes['iterations'] = result['nfev']
    quantum_result_attributes['optimization_time(sec)'] = time.time() - start_time
    quantum_result_attributes['p_level'] = 1
    quantum_result_attributes['optimization_level'] = 3

    # Sample final circuit
    sampler = Sampler(_backend)
    optimal_circuit = isa_circuit.assign_parameters(result.x)
    optimal_circuit.measure_active()

    final_job = sampler.run([(optimal_circuit, None)], shots=shots)
    final_result = final_job.result()
    distribution = final_result[0].data.meas.get_counts()
    if not use_simulator:
        real_execution_time = final_result.metadata['execution']['execution_spans'].duration
        quantum_result_attributes['real_execution_time'] = real_execution_time

    return distribution, quantum_result_attributes


def analyse_result_distribution(distribution, num_cities, tsp):
    max_prob_bitstring = sample_most_likely(distribution)
    logger.debug("\nQuantum result:")
    visualize_tsp_matrix_view(max_prob_bitstring, num_cities)
    possible_tours_qaoa = interpret(max_prob_bitstring, num_cities)
    optimal_tours_qaoa = generate_city_sequences(possible_tours_qaoa, num_cities)

    optimal_tour_qaoa = None
    optimal_tour_distance_qaoa = float('inf')
    for q_tour in optimal_tours_qaoa:
        current_distance = tsp.calculate_tour_distance(q_tour)
        if current_distance < optimal_tour_distance_qaoa:
            optimal_tour_distance_qaoa = current_distance
            optimal_tour_qaoa = q_tour

    return {
        "quantum_possible_best_tours": optimal_tours_qaoa,
        "quantum_best_tour_found": optimal_tour_qaoa,
        "quantum_best_tour_distance": optimal_tour_distance_qaoa,
    }


def save_attributes(quantum_result_attributes, num_vertices):
    for key, value in quantum_result_attributes.items():
        update_experiment_data(num_vertices, key, str(value))


def process(
        num_cities,
        p_level,
        penalty_weight=0.01,
        max_iter = 100,
        shots = 1000,
        use_simulator = True):

    # num_cities = 4
    # penalty_weight = 0.01
    # p_level = 5
    # max_iter = 100
    # shots = 2000
    # use_simulator = True

    # p_level = int(math.ceil(math.log2(num_cities*num_cities)))
    logger.info(f"Using p_level:: {p_level}")

    do_classical = True if num_cities < 6 else False
    tsp = ImprovedTSPHamiltonian(num_cities, seed=123)

    optimal_tour_classical = None
    optimal_distance_classical = float('inf')
    if do_classical:
        for perm in permutations(range(num_cities)):
            tour = list(perm)
            distance = tsp.calculate_tour_distance(tour)
            if distance < optimal_distance_classical:
                optimal_distance_classical = distance
                optimal_tour_classical = tour
        update_experiment_data(num_cities, "classical_optimal_tour", str(optimal_tour_classical))
        update_experiment_data(num_cities, "classical_optimal_distance", str(optimal_distance_classical))

    logger.debug(f"Running improved TSP QAOA with {num_cities} cities")
    logger.debug("=" * 50)

    distribution, quantum_result_attributes = run_qaoa(
        num_cities=num_cities,
        tsp=tsp,
        penalty_weight=penalty_weight,
        p_level=p_level,
        max_iter=max_iter,
        shots=shots,
        use_simulator=use_simulator
    )

    distribution_attributes = analyse_result_distribution(distribution, num_cities, tsp)
    if do_classical:
        gap = abs(
            optimal_distance_classical - distribution_attributes['quantum_best_tour_distance']
        ) / optimal_distance_classical * 100
        update_experiment_data(num_cities, "gap", str(gap))
        logger.debug(f"Gap from optimal: {gap:.2f}%")

    save_attributes(quantum_result_attributes, num_cities)
    save_attributes(distribution_attributes, num_cities)
