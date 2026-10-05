import numpy as np
from qiskit.quantum_info import SparsePauliOp, Pauli
import logging

logger = logging.getLogger(__name__)

class ImprovedTSPHamiltonian:

    def __init__(self, num_cities, seed=None):
        self.num_cities = num_cities
        self.num_qubits = num_cities * num_cities
        if seed:
            np.random.seed(seed)
        self.distances = self._generate_distance_matrix()
        self.connections = np.ones((num_cities, num_cities)) - np.eye(num_cities)

    def _generate_distance_matrix(self):
        """Generate random symmetric distance matrix"""
        distances = np.random.rand(self.num_cities, self.num_cities) * 10
        distances = (distances + distances.T) / 2  # Make symmetric
        np.fill_diagonal(distances, 0)  # Zero diagonal
        return distances

    def bit_index(self, city, position):
        """Returns the qubit index for city at position"""
        return position * self.num_cities + city

    def create_d_operator(self, city, position):
        """Create D operator: D(city, position) = 0.5 * (I - Z)"""
        qubit_idx = self.bit_index(city, position)

        # Create I operator (identity)
        i_paulis = ['I'] * self.num_qubits
        i_coeffs = [0.5]

        # Create Z operator
        z_paulis = ['I'] * self.num_qubits
        z_paulis[qubit_idx] = 'Z'
        z_coeffs = [-0.5]

        # Combine into SparsePauliOp
        pauli_strings = [''.join(i_paulis), ''.join(z_paulis)]
        coeffs = i_coeffs + z_coeffs

        return SparsePauliOp(pauli_strings, coeffs)

    def create_hamiltonian(self, penalty_weight=1.0):
        """Build the complete TSP Hamiltonian with constraints"""

        # Initialize empty Hamiltonian
        hamiltonian = SparsePauliOp(['I' * self.num_qubits], [0.0])

        # Constraint (a): Each city visited exactly once (sum over positions = 1)
        logger.debug("Adding constraint (a): Each city visited exactly once")
        for city in range(self.num_cities):
            constraint_term = SparsePauliOp(['I' * self.num_qubits], [1.0])  # Start with I

            for position in range(self.num_cities):
                d_op = self.create_d_operator(city, position)
                constraint_term = constraint_term - d_op

            # Square the constraint: (1 - sum_j D(city, j))^2
            hamiltonian = hamiltonian + constraint_term @ constraint_term

        # Constraint (b): Each position has exactly one city (sum over cities = 1)
        logger.debug("Adding constraint (b): Each position has exactly one city")
        for position in range(self.num_cities):
            constraint_term = SparsePauliOp(['I' * self.num_qubits], [1.0])  # Start with I

            for city in range(self.num_cities):
                d_op = self.create_d_operator(city, position)
                constraint_term = constraint_term - d_op

            # Square the constraint: (1 - sum_i D(i, position))^2
            hamiltonian = hamiltonian + constraint_term @ constraint_term

        # Constraint (c): Connectivity constraint (adjacent positions must be connected cities)
        logger.debug("Adding constraint (c): Connectivity constraint")
        for position in range(self.num_cities - 1):
            connectivity_term = SparsePauliOp(['I' * self.num_qubits], [1.0])  # Start with I

            for city1 in range(self.num_cities):
                for city2 in range(self.num_cities):
                    if self.connections[city1, city2] > 0:  # If cities are connected
                        d1_op = self.create_d_operator(city1, position)
                        d2_op = self.create_d_operator(city2, position + 1)
                        connectivity_term = connectivity_term - (d1_op @ d2_op)

            hamiltonian = hamiltonian + connectivity_term

        # Constraint (d): Distance weighting
        logger.debug("Adding constraint (d): Distance weighting")
        for position in range(self.num_cities - 1):
            distance_term = SparsePauliOp(['I' * self.num_qubits], [1.0])  # Start with I

            for city1 in range(self.num_cities):
                for city2 in range(self.num_cities):
                    if self.connections[city1, city2] > 0:  # If cities are connected
                        distance = self.distances[city1, city2]
                        d1_op = self.create_d_operator(city1, position)
                        d2_op = self.create_d_operator(city2, position + 1)
                        distance_term = distance_term - (d1_op @ d2_op) * distance

            hamiltonian = hamiltonian + distance_term * penalty_weight

        # Add return to start constraint
        return_term = SparsePauliOp(['I' * self.num_qubits], [1.0])
        for city1 in range(self.num_cities):
            for city2 in range(self.num_cities):
                if self.connections[city1, city2] > 0:
                    distance = self.distances[city1, city2]
                    d1_op = self.create_d_operator(city1, self.num_cities - 1)  # Last position
                    d2_op = self.create_d_operator(city2, 0)  # First position
                    return_term = return_term - (d1_op @ d2_op) * distance

        hamiltonian = hamiltonian + return_term * penalty_weight

        return hamiltonian

    def calculate_tour_distance(self, tour):
        """Calculate total distance for a given tour"""
        total_distance = 0
        for i in range(len(tour)):
            current_city = tour[i]
            next_city = tour[(i + 1) % len(tour)]
            total_distance += self.distances[current_city, next_city]
        return total_distance

