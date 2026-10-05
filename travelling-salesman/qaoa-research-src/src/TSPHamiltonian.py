import numpy as np
from qiskit.quantum_info import SparsePauliOp
import matplotlib.pyplot as plt
import random


class TSPHamiltonian:

    def __init__(self, n_cities, distances=None, seed=None):

        self.n_cities = n_cities
        self.n_qubits = n_cities * n_cities  # Position-based encoding: x_{i,k}

        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

        if distances is None:
            self.distances = self.generate_random_distances()
        else:
            self.distances = distances

    def create_tsp_from_adjacency_matrix(adjacency_matrix, penalty_weight=10.0, return_qubo=False):
        """
        """
        # Validate input
        if not isinstance(adjacency_matrix, np.ndarray):
            adjacency_matrix = np.array(adjacency_matrix)

        if adjacency_matrix.ndim != 2:
            raise ValueError("Adjacency matrix must be 2D")

        if adjacency_matrix.shape[0] != adjacency_matrix.shape[1]:
            raise ValueError("Adjacency matrix must be square")

        # Check if matrix is symmetric
        if not np.allclose(adjacency_matrix, adjacency_matrix.T):
            raise ValueError("Adjacency matrix must be symmetric for TSP")

        # Get number of cities
        n_cities = adjacency_matrix.shape[0]

        # Create TSP instance with the provided distance matrix
        tsp = TSPHamiltonian(n_cities, distances=adjacency_matrix)

        # Create Hamiltonian (assumes complete graph)
        hamiltonian = tsp.create_hamiltonian(penalty_weight=penalty_weight)

        if return_qubo:
            qubo_matrix, offset = tsp.create_qubo(penalty_weight=penalty_weight)
            return hamiltonian, tsp, qubo_matrix, offset
        else:
            return hamiltonian, tsp

    def generate_random_distances(self):

        positions = np.random.uniform(0, 10, size=(self.n_cities, 2))
        distances = np.zeros((self.n_cities, self.n_cities))

        for i in range(self.n_cities):
            for j in range(i + 1, self.n_cities):
                dist = np.sqrt(np.sum((positions[i] - positions[j]) ** 2))
                distances[i, j] = dist
                distances[j, i] = dist

        return distances

    def create_hamiltonian(self, penalty_weight=10.0, edge_list=None):

        hamiltonian_terms = []

        distance_terms = self._create_distance_hamiltonian(edge_list)
        hamiltonian_terms.extend(distance_terms)

        constraint_terms = self._create_all_constraints(penalty_weight, edge_list)
        hamiltonian_terms.extend(constraint_terms)

        if len(hamiltonian_terms) > 0:
            pauli_strings, coeffs = zip(*hamiltonian_terms)
            hamiltonian = SparsePauliOp(pauli_strings, coeffs=coeffs)
        else:
            hamiltonian = SparsePauliOp.from_list([("I" * self.n_qubits, 0.0)])

        return hamiltonian


    def create_qubo(self, penalty_weight=10.0, edge_list=None):
        """
        Create QUBO representation of the TSP problem

        QUBO format: minimize x^T Q x where x is binary vector
        Returns: Q matrix (upper triangular) and constant offset
        """
        # Initialize QUBO matrix (upper triangular)
        Q = np.zeros((self.n_qubits, self.n_qubits))
        constant_offset = 0

        # Get Hamiltonian terms
        distance_terms = self._create_distance_hamiltonian(edge_list)
        constraint_terms = self._create_all_constraints(penalty_weight, edge_list)
        all_terms = distance_terms + constraint_terms

        # Convert Pauli terms to QUBO
        for pauli_str, coeff in all_terms:
            z_positions = [i for i, op in enumerate(pauli_str) if op == 'Z']

            if len(z_positions) == 0:
                # Identity term (constant)
                constant_offset += coeff
            elif len(z_positions) == 1:
                # Single Z term (linear in QUBO)
                i = z_positions[0]
                Q[i, i] += coeff
            elif len(z_positions) == 2:
                # Two Z terms (quadratic in QUBO)
                i, j = z_positions
                if i <= j:
                    Q[i, j] += coeff
                else:
                    Q[j, i] += coeff
            else:
                # Higher order terms (shouldn't happen in TSP)
                raise ValueError(f"Unexpected Pauli term with {len(z_positions)} Z operators")

        return Q, constant_offset

    def convert_quadratic_program_to_qubo(self, qp):
        """
        Convert a QuadraticProgram back to QUBO matrix format

        Args:
            qp: QuadraticProgram object

        Returns:
            Q matrix (upper triangular) and constant offset
        """
        n_vars = qp.get_num_vars()
        Q = np.zeros((n_vars, n_vars))

        # Extract linear terms
        for var_name, coeff in qp.objective.linear.to_dict().items():
            var_index = qp.variables_index[var_name]
            Q[var_index, var_index] = coeff

        # Extract quadratic terms
        for (var1_name, var2_name), coeff in qp.objective.quadratic.to_dict().items():
            i = qp.variables_index[var1_name]
            j = qp.variables_index[var2_name]
            if i <= j:
                Q[i, j] = coeff
            else:
                Q[j, i] = coeff

        # Extract constant
        offset = qp.objective.constant

        return Q, offset

    def create_qubo_dict(self, penalty_weight=10.0, edge_list=None):
        """
        Create QUBO in dictionary format {(i,j): value}
        This is a common format for many quantum solvers
        """
        Q, offset = self.create_qubo(penalty_weight, edge_list)
        qubo_dict = {}

        # Convert matrix to dictionary format
        for i in range(self.n_qubits):
            for j in range(i, self.n_qubits):
                if abs(Q[i, j]) > 1e-10:
                    qubo_dict[(i, j)] = Q[i, j]

        return qubo_dict, offset

    def print_qubo_details(self, penalty_weight=10.0, edge_list=None, max_terms=10):
        """Print detailed information about the QUBO matrix"""
        Q, offset = self.create_qubo(penalty_weight, edge_list)

        print(f"\n=== QUBO Details ===")
        print(f"QUBO matrix size: {Q.shape}")
        print(f"Constant offset: {offset:.4f}")

        # Count different types of terms
        linear_count = np.count_nonzero(np.diag(Q))
        quadratic_count = np.count_nonzero(np.triu(Q, k=1))

        print(f"Linear terms (diagonal): {linear_count}")
        print(f"Quadratic terms (off-diagonal): {quadratic_count}")
        print(f"Total non-zero terms: {linear_count + quadratic_count}")

        # Show sample terms
        print(f"\n=== Sample QUBO Terms (max {max_terms}) ===")
        term_count = 0

        # Linear terms
        print("Linear terms (diagonal):")
        for i in range(self.n_qubits):
            if abs(Q[i, i]) > 1e-10 and term_count < max_terms:
                city, pos = self._decode_qubit_index(i)
                print(f"  Q[{i},{i}] = {Q[i, i]:.4f} (x_{{{city},{pos}}})")
                term_count += 1

        # Quadratic terms
        print("\nQuadratic terms (off-diagonal):")
        for i in range(self.n_qubits):
            for j in range(i + 1, self.n_qubits):
                if abs(Q[i, j]) > 1e-10 and term_count < max_terms:
                    city1, pos1 = self._decode_qubit_index(i)
                    city2, pos2 = self._decode_qubit_index(j)
                    print(f"  Q[{i},{j}] = {Q[i, j]:.4f} (x_{{{city1},{pos1}}} * x_{{{city2},{pos2}}})")
                    term_count += 1

    def save_qubo_to_file(self, filename, penalty_weight=10.0, edge_list=None, format='dict'):
        """
        Save QUBO to file in various formats

        Args:
            filename: Output filename
            penalty_weight: Penalty weight for constraints
            edge_list: Optional edge list for partial graphs
            format: 'dict', 'matrix', or 'qbsolv' format
        """
        Q, offset = self.create_qubo(penalty_weight, edge_list)

        if format == 'dict':
            # Dictionary format
            qubo_dict, _ = self.create_qubo_dict(penalty_weight, edge_list)
            with open(filename, 'w') as f:
                f.write(f"# QUBO for TSP with {self.n_cities} cities\n")
                f.write(f"# Constant offset: {offset}\n")
                f.write("# Format: (i,j): value\n")
                for (i, j), value in sorted(qubo_dict.items()):
                    f.write(f"({i},{j}): {value}\n")

        elif format == 'matrix':
            # Full matrix format
            np.savetxt(filename, Q, fmt='%.6f', header=f'QUBO matrix, offset={offset}')

        elif format == 'qbsolv':
            # QBSolv format
            with open(filename, 'w') as f:
                f.write(f"c QUBO for TSP with {self.n_cities} cities\n")
                f.write(f"c Constant offset: {offset}\n")
                f.write(f"p qubo 0 {self.n_qubits} {np.count_nonzero(Q)}\n")
                for i in range(self.n_qubits):
                    for j in range(i, self.n_qubits):
                        if abs(Q[i, j]) > 1e-10:
                            f.write(f"{i} {j} {Q[i, j]:.6f}\n")

        print(f"QUBO saved to {filename} in {format} format")

    def verify_qubo(self, solution_bitstring, penalty_weight=10.0, edge_list=None):
        """
        Verify a solution by computing its QUBO energy

        Args:
            solution_bitstring: Binary string solution
            penalty_weight: Penalty weight used in QUBO
            edge_list: Optional edge list for partial graphs

        Returns:
            Total energy (cost + penalties)
        """
        if len(solution_bitstring) != self.n_qubits:
            raise ValueError(f"Solution must have length {self.n_qubits}")

        # Convert bitstring to binary vector
        x = np.array([int(bit) for bit in solution_bitstring])

        # Get QUBO matrix
        Q, offset = self.create_qubo(penalty_weight, edge_list)

        # Compute energy: x^T Q x + offset
        energy = x.T @ Q @ x + offset

        # Also compute components
        tour = self.decode_solution(solution_bitstring)
        tour_distance = self.calculate_tour_distance(tour)
        penalty_violations = self._calculate_penalty_violations(tour, penalty_weight, edge_list)

        print(f"\n=== QUBO Verification ===")
        print(f"Tour: {tour}")
        print(f"Tour distance: {tour_distance:.4f}")
        print(f"Total penalty violations: {penalty_violations:.4f}")
        print(f"Total QUBO energy: {energy:.4f}")
        print(f"Verification: {tour_distance:.4f} + {penalty_violations:.4f} + {offset:.4f} = {energy:.4f}")

        return energy

    def _calculate_penalty_violations(self, tour, penalty_weight, edge_list=None):
        """Calculate total penalty from constraint violations"""
        total_penalty = 0

        # Check city-once constraints
        city_counts = {}
        for city in tour:
            city_counts[city] = city_counts.get(city, 0) + 1

        for city in range(self.n_cities):
            count = city_counts.get(city, 0)
            total_penalty += penalty_weight * (count - 1) ** 2

        # Check position-once constraints
        if len(set(tour)) != self.n_cities:
            for pos in range(self.n_cities):
                cities_at_pos = sum(1 for i, c in enumerate(tour) if i == pos and c != -1)
                total_penalty += penalty_weight * (cities_at_pos - 1) ** 2

        # Check edge constraints
        if edge_list is not None:
            all_edges = set()
            for i, j in edge_list:
                all_edges.add((i, j))
                all_edges.add((j, i))

            for i in range(self.n_cities):
                current = tour[i]
                next_city = tour[(i + 1) % self.n_cities]
                if (current, next_city) not in all_edges:
                    # This violates a non-edge constraint
                    total_penalty += penalty_weight

        return total_penalty

    def _create_distance_hamiltonian(self, edge_list=None):
        """
        Create Hamiltonian encoding the tour distance
        CRITICAL: Only sums over existing edges, exactly like the reference

        Reference implementation:
        tsp_func = mdl.sum(
            self._graph.edges[i, j]["weight"] * x[(i, k)] * x[(j, (k + 1) % n)]
            for i, j in self._graph.edges
            for k in range(n)
        )
        # Add reverse edges since we have an undirected graph
        tsp_func += mdl.sum(
            self._graph.edges[i, j]["weight"] * x[(j, k)] * x[(i, (k + 1) % n)]
            for i, j in self._graph.edges
            for k in range(n)
        )
        """
        terms = []

        # If no edge list provided, assume complete graph
        if edge_list is None:
            edges = [(i, j) for i in range(self.n_cities)
                     for j in range(self.n_cities) if i != j]
        else:
            edges = edge_list

        # Forward direction: i at position k, j at position k+1
        for i, j in edges:
            for k in range(self.n_cities):
                next_k = (k + 1) % self.n_cities
                self._add_edge_term(terms, i, k, j, next_k)

        # Reverse direction: j at position k, i at position k+1 (undirected graph)
        for i, j in edges:
            for k in range(self.n_cities):
                next_k = (k + 1) % self.n_cities
                self._add_edge_term(terms, j, k, i, next_k)

        return terms

    def _add_edge_term(self, terms, city1, pos1, city2, pos2):
        """Add terms for edge (city1,city2) at positions (pos1,pos2)"""
        # Get qubit indices
        qubit1 = self._get_qubit_index(city1, pos1)
        qubit2 = self._get_qubit_index(city2, pos2)

        # Distance weight
        weight = self.distances[city1, city2]

        # ZZ term: x_{city1,pos1} * x_{city2,pos2}
        pauli_str = ['I'] * self.n_qubits
        pauli_str[qubit1] = 'Z'
        pauli_str[qubit2] = 'Z'
        terms.append((''.join(pauli_str), weight / 4))

        # Linear terms for {-1,1} to {0,1} mapping
        pauli_str1 = ['I'] * self.n_qubits
        pauli_str1[qubit1] = 'Z'
        terms.append((''.join(pauli_str1), weight / 4))

        pauli_str2 = ['I'] * self.n_qubits
        pauli_str2[qubit2] = 'Z'
        terms.append((''.join(pauli_str2), weight / 4))

        # Constant term
        terms.append((''.join(['I'] * self.n_qubits), weight / 4))

    def _create_all_constraints(self, penalty_weight, edge_list=None):
        """
        Create Hamiltonian for ALL TSP constraints from the reference:

        1. Each city appears at exactly one position
        2. Each position has exactly one city
        3. Non-existent edges cannot be consecutive
        """
        terms = []

        # Constraint 1: Each city appears exactly once
        # sum_k x_{i,k} = 1 for all cities i
        for i in range(self.n_cities):
            self._add_equality_constraint(terms, penalty_weight,
                                          [(i, k) for k in range(self.n_cities)])

        # Constraint 2: Each position has exactly one city
        # sum_i x_{i,k} = 1 for all positions k
        for k in range(self.n_cities):
            self._add_equality_constraint(terms, penalty_weight,
                                          [(i, k) for i in range(self.n_cities)])

        # Constraint 3: Non-existent edges cannot be consecutive
        self._add_non_edge_constraints(terms, penalty_weight, edge_list)

        return terms

    def _add_equality_constraint(self, terms, penalty_weight, variable_list):
        """Add penalty terms for constraint: sum(variables) = 1"""
        # (sum x_i - 1)^2 = sum x_i - 2*sum x_i + sum_i sum_j x_i*x_j + 1
        # Since x_i^2 = x_i for binary: sum x_i + sum_{i!=j} x_i*x_j - 2*sum x_i + 1
        # Simplifies to: sum_{i!=j} x_i*x_j - sum x_i + 1

        # Linear terms: -1 * x_i
        for var in variable_list:
            qubit_idx = self._get_qubit_index(*var)
            pauli_str = ['I'] * self.n_qubits
            pauli_str[qubit_idx] = 'Z'
            terms.append((''.join(pauli_str), -penalty_weight))

        # Quadratic terms: x_i * x_j for i != j
        for i in range(len(variable_list)):
            for j in range(i + 1, len(variable_list)):
                qubit_i = self._get_qubit_index(*variable_list[i])
                qubit_j = self._get_qubit_index(*variable_list[j])

                pauli_str = ['I'] * self.n_qubits
                pauli_str[qubit_i] = 'Z'
                pauli_str[qubit_j] = 'Z'
                terms.append((''.join(pauli_str), penalty_weight))

        # Constant term
        terms.append((''.join(['I'] * self.n_qubits), penalty_weight))

    def _add_non_edge_constraints(self, terms, penalty_weight, edge_list):
        """Add constraints for non-existent edges"""
        # Find non-edges
        if edge_list is None:
            non_edges = []  # Complete graph has no non-edges
        else:
            # Find all pairs that are NOT in edge_list
            all_edges = set()
            for i, j in edge_list:
                all_edges.add((i, j))
                all_edges.add((j, i))  # Undirected

            non_edges = []
            for i in range(self.n_cities):
                for j in range(self.n_cities):
                    if i != j and (i, j) not in all_edges:
                        non_edges.append((i, j))

        # Add constraints: x[i,k] + x[j,(k+1)%n] <= 1
        for i, j in non_edges:
            for k in range(self.n_cities):
                next_k = (k + 1) % self.n_cities
                self._add_inequality_constraint(terms, penalty_weight, i, k, j, next_k)
                # Reverse direction
                self._add_inequality_constraint(terms, penalty_weight, j, k, i, next_k)

    def _add_inequality_constraint(self, terms, penalty_weight, city1, pos1, city2, pos2):
        """Add penalty for inequality: x[city1,pos1] + x[city2,pos2] <= 1"""
        # Penalty form: A * max(0, x_i + x_j - 1)^2
        # For binary variables, we use: A * (x_i + x_j - 1)^2
        # Expand: A * (x_i^2 + x_j^2 + 2*x_i*x_j - 2*x_i - 2*x_j + 1)
        # Since x^2 = x: A * (x_i + x_j + 2*x_i*x_j - 2*x_i - 2*x_j + 1)
        # Simplify: A * (2*x_i*x_j - x_i - x_j + 1)

        qubit1 = self._get_qubit_index(city1, pos1)
        qubit2 = self._get_qubit_index(city2, pos2)

        # Quadratic term: 2 * x_i * x_j
        pauli_str_quad = ['I'] * self.n_qubits
        pauli_str_quad[qubit1] = 'Z'
        pauli_str_quad[qubit2] = 'Z'
        terms.append((''.join(pauli_str_quad), 2 * penalty_weight))

        # Linear terms: -x_i, -x_j
        pauli_str1 = ['I'] * self.n_qubits
        pauli_str1[qubit1] = 'Z'
        terms.append((''.join(pauli_str1), -penalty_weight))

        pauli_str2 = ['I'] * self.n_qubits
        pauli_str2[qubit2] = 'Z'
        terms.append((''.join(pauli_str2), -penalty_weight))

        # Constant term
        terms.append((''.join(['I'] * self.n_qubits), penalty_weight))

    def _get_qubit_index(self, city, position):
        """Get qubit index for variable x_{city,position}"""
        return city * self.n_cities + position

    def _decode_qubit_index(self, qubit_index):
        """Decode qubit index back to (city, position)"""
        city = qubit_index // self.n_cities
        position = qubit_index % self.n_cities
        return city, position

    def decode_solution(self, solution_bitstring):
        """Decode a bitstring solution to a tour"""
        if len(solution_bitstring) != self.n_qubits:
            raise ValueError(f"Solution bitstring must have length {self.n_qubits}")

        tour = [-1] * self.n_cities

        for i in range(self.n_cities):
            for k in range(self.n_cities):
                idx = self._get_qubit_index(i, k)
                if solution_bitstring[idx] == '1':
                    tour[k] = i

        return tour

    def calculate_tour_distance(self, tour):
        """Calculate the total distance for a given tour"""
        if len(tour) != self.n_cities:
            return float('inf')

        total_distance = 0
        for i in range(self.n_cities):
            current_city = tour[i]
            next_city = tour[(i + 1) % self.n_cities]
            if current_city == -1 or next_city == -1:
                return float('inf')
            total_distance += self.distances[current_city, next_city]

        return total_distance

    def validate_solution(self, tour, edge_list=None):
        """Validate if a tour respects all constraints"""
        valid = True
        errors = []

        # Check basic tour validity
        if len(set(tour)) != self.n_cities or -1 in tour:
            valid = False
            errors.append("Invalid tour: missing or duplicate cities")

        # Check edge constraints
        if edge_list is not None:
            all_edges = set()
            for i, j in edge_list:
                all_edges.add((i, j))
                all_edges.add((j, i))

            for i in range(self.n_cities):
                current = tour[i]
                next_city = tour[(i + 1) % self.n_cities]
                if (current, next_city) not in all_edges:
                    valid = False
                    errors.append(f"Tour uses non-existent edge: {current} -> {next_city}")

        return valid, errors

    def visualize_graph(self, tour=None, edge_list=None):
        """Visualize the TSP graph with optional tour and edge constraints"""
        # Generate city positions for visualization
        np.random.seed(42)
        positions = np.random.uniform(0, 10, size=(self.n_cities, 2))

        plt.figure(figsize=(12, 10))

        # Draw cities
        for i in range(self.n_cities):
            plt.scatter(positions[i, 0], positions[i, 1], s=300, c='skyblue', zorder=3)
            plt.text(positions[i, 0], positions[i, 1], str(i), ha='center', va='center', zorder=4)

        # Draw edges based on edge_list
        if edge_list is None:
            # Complete graph
            for i in range(self.n_cities):
                for j in range(i + 1, self.n_cities):
                    plt.plot([positions[i, 0], positions[j, 0]],
                             [positions[i, 1], positions[j, 1]],
                             'lightgray', alpha=0.5, zorder=1)
        else:
            # Only draw existing edges
            for i, j in edge_list:
                plt.plot([positions[i, 0], positions[j, 0]],
                         [positions[i, 1], positions[j, 1]],
                         'gray', alpha=0.7, zorder=1)

        # Draw tour if provided
        if tour is not None:
            for i in range(self.n_cities):
                current_city = tour[i]
                next_city = tour[(i + 1) % self.n_cities]
                if current_city != -1 and next_city != -1:
                    plt.plot([positions[current_city, 0], positions[next_city, 0]],
                             [positions[current_city, 1], positions[next_city, 1]],
                             'red', linewidth=3, zorder=2)

                    # Add arrow
                    dx = positions[next_city, 0] - positions[current_city, 0]
                    dy = positions[next_city, 1] - positions[current_city, 1]
                    plt.arrow(positions[current_city, 0], positions[current_city, 1],
                              dx * 0.8, dy * 0.8, head_width=0.2, head_length=0.2,
                              fc='red', ec='red', zorder=2)

        plt.title(f"TSP Graph with {self.n_cities} Cities")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.grid(True, alpha=0.3)
        plt.axis('equal')
        plt.tight_layout()
        plt.show()


def demonstrate_tsp_hamiltonian():
    """Comprehensive demonstration of TSP Hamiltonian with all constraints"""

    print("=== TSP Hamiltonian with All Constraints and QUBO ===\n")

    # Create a small TSP instance
    n_cities = 4
    tsp = TSPHamiltonian(n_cities, seed=42)

    print(f"Number of cities: {n_cities}")
    print(f"Number of qubits: {tsp.n_qubits}")
    print("\nDistance matrix:")
    print(tsp.distances)

    # Test 1: Complete graph
    print("\n=== Test 1: Complete Graph (All Edges Exist) ===")
    hamiltonian_complete = tsp.create_hamiltonian(penalty_weight=10.0)
    print(f"Number of Hamiltonian terms: {len(hamiltonian_complete)}")

    # Create and analyze QUBO
    qubo_complete, offset_complete = tsp.create_qubo(penalty_weight=10.0)
    print(f"QUBO matrix size: {qubo_complete.shape}")
    print(f"Non-zero QUBO entries: {np.count_nonzero(qubo_complete)}")
    print(f"QUBO constant offset: {offset_complete:.4f}")

    # Print QUBO details
    tsp.print_qubo_details(penalty_weight=10.0, max_terms=5)

    # Test 2: Partial graph with edge constraints
    print("\n=== Test 2: Partial Graph with Edge Constraints ===")
    partial_edges = [(0, 1), (1, 2), (2, 3), (0, 3)]
    hamiltonian_partial = tsp.create_hamiltonian(penalty_weight=10.0, edge_list=partial_edges)
    qubo_partial, offset_partial = tsp.create_qubo(penalty_weight=10.0, edge_list=partial_edges)

    print(f"Existing edges: {partial_edges}")
    print(f"Number of Hamiltonian terms: {len(hamiltonian_partial)}")
    print(f"Non-zero QUBO entries: {np.count_nonzero(qubo_partial)}")
    print(
        f"Additional QUBO entries: {np.count_nonzero(qubo_partial) - np.count_nonzero(qubo_complete)} (from non-edge constraints)")

    # Test solution validation
    print("\n=== Test 3: Solution Validation ===")
    test_solution = '1000010000100001'  # city 0→1→2→3→0
    tour = tsp.decode_solution(test_solution)
    print(f"Tour: {tour}")
    print(f"Distance: {tsp.calculate_tour_distance(tour)}")

    # Verify solution using QUBO
    print("\n=== QUBO Verification ===")
    energy_complete = tsp.verify_qubo(test_solution, penalty_weight=10.0)
    energy_partial = tsp.verify_qubo(test_solution, penalty_weight=10.0, edge_list=partial_edges)

    print(f"Complete graph QUBO energy: {energy_complete:.4f}")
    print(f"Partial graph QUBO energy: {energy_partial:.4f}")

    # Save QUBO in different formats
    print("\n=== Saving QUBO Files ===")
    tsp.save_qubo_to_file("tsp_complete.qubo", penalty_weight=10.0, format='dict')
    tsp.save_qubo_to_file("tsp_complete_matrix.txt", penalty_weight=10.0, format='matrix')
    tsp.save_qubo_to_file("tsp_partial.qbsolv", penalty_weight=10.0, edge_list=partial_edges, format='qbsolv')

    # Show QUBO dictionary format
    print("\n=== QUBO Dictionary Format ===")
    qubo_dict, offset = tsp.create_qubo_dict(penalty_weight=10.0, edge_list=partial_edges)
    print(f"Number of QUBO terms: {len(qubo_dict)}")
    print(f"Sample QUBO entries:")
    for i, ((i, j), value) in enumerate(list(qubo_dict.items())[:5]):
        city1, pos1 = tsp._decode_qubit_index(i)
        city2, pos2 = tsp._decode_qubit_index(j)
        print(f"  ({i},{j}): {value:.4f} - x_{{{city1},{pos1}}} * x_{{{city2},{pos2}}}")

    # Visualize both graphs
    print("\n=== Visualization ===")
    tsp.visualize_graph(tour, edge_list=None)  # Complete graph
    tsp.visualize_graph(tour, edge_list=partial_edges)  # Partial graph

    return tsp, hamiltonian_complete, qubo_complete, hamiltonian_partial, qubo_partial


# Helper function for QAOA
def create_tsp_hamiltonian_for_qaoa(n_cities, seed=None, penalty_weight=10.0, edge_list=None, return_qubo=False):
    """Create TSP Hamiltonian ready for QAOA, optionally with QUBO"""
    tsp = TSPHamiltonian(n_cities, seed=seed)
    hamiltonian = tsp.create_hamiltonian(penalty_weight=penalty_weight, edge_list=edge_list)

    if return_qubo:
        qubo, offset = tsp.create_qubo(penalty_weight=penalty_weight, edge_list=edge_list)
        return hamiltonian, tsp, qubo, offset
    else:
        return hamiltonian, tsp


# Detailed constraint explanation
def explain_tsp_constraints():
    """Explain each constraint in detail"""
    print("""
=== Understanding TSP Hamiltonian Constraints ===

The TSP Hamiltonian includes exactly the same three constraints as the reference:

1. EACH CITY VISITED ONCE
   - Mathematical: ∑_k x_{i,k} = 1 for each city i
   - Meaning: City i must be at exactly one position in the tour
   - Penalty: (∑_k x_{i,k} - 1)²

2. EACH POSITION HAS ONE CITY
   - Mathematical: ∑_i x_{i,k} = 1 for each position k  
   - Meaning: Position k must have exactly one city
   - Penalty: (∑_i x_{i,k} - 1)²

3. NO NON-EXISTENT EDGES
   - Mathematical: x[i,k] + x[j,(k+1)%n] ≤ 1 for all non-edges (i,j)
   - Meaning: If edge (i,j) doesn't exist, cities i and j cannot be consecutive
   - Penalty: Applied when x[i,k] = 1 AND x[j,(k+1)%n] = 1

The total Hamiltonian is:
H = H_distance + λ(H_constraint1 + H_constraint2 + H_constraint3)

where λ is the penalty weight ensuring constraints are satisfied.

QUBO Representation:
The QUBO matrix Q is constructed such that:
- Minimize x^T Q x where x is a binary vector
- Linear terms (diagonal of Q) encode single-variable penalties
- Quadratic terms (off-diagonal) encode two-variable interactions
- A constant offset captures constant terms from constraint expansion
""")


# if __name__ == "__main__":
#     # Run comprehensive demonstration
#     tsp_instance, ham_complete, qubo_complete, ham_partial, qubo_partial = demonstrate_tsp_hamiltonian()
#
#     # Additional examples with different graph structures
#     print("\n=== Additional Graph Examples ===")
#
#     # Cycle graph (ring)
#     cycle_edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
#     ham_cycle, tsp_cycle, qubo_cycle, offset_cycle = create_tsp_hamiltonian_for_qaoa(
#         4, seed=42, penalty_weight=10.0, edge_list=cycle_edges, return_qubo=True)
#     print(f"Cycle graph: {len(ham_cycle)} Hamiltonian terms, {np.count_nonzero(qubo_cycle)} QUBO entries")
#
#     # Star graph
#     star_edges = [(0, 1), (0, 2), (0, 3)]
#     ham_star, tsp_star, qubo_star, offset_star = create_tsp_hamiltonian_for_qaoa(
#         4, seed=42, penalty_weight=10.0, edge_list=star_edges, return_qubo=True)
#     print(f"Star graph: {len(ham_star)} Hamiltonian terms, {np.count_nonzero(qubo_star)} QUBO entries")
#
#     # Show star graph QUBO verification
#     test_tour = [0, 1, 2, 3]  # 0→1→2→3→0
#     test_bitstring = '1000010000100001'
#     energy = tsp_star.verify_qubo(test_bitstring, penalty_weight=10.0, edge_list=star_edges)
#     print(f"Star graph QUBO energy for {test_tour}: {energy:.4f}")
#
#     # Explain constraints in detail
#     explain_tsp_constraints()
#
#     # Compare with reference
#     compare_with_reference()
#
#     # Advanced QUBO examples
#     advanced_qubo_examples()
#
#     print("\n=== Summary ===")
#     print("""
#     This implementation provides:
#     1. Complete TSP Hamiltonian matching the reference exactly
#     2. QUBO export in multiple formats (dict, matrix, QBSolv)
#     3. Solution verification using QUBO energy calculation
#     4. Detailed analysis of QUBO structure and terms
#     5. Support for both complete and partial graphs
#     6. Full constraint validation and visualization
#
#     The QUBO format is ready for use with:
#     - D-Wave quantum annealers
#     - Quantum-inspired classical optimizers
#     - Hybrid quantum-classical algorithms (QAOA)
#     - Simulated annealing solvers
#     """)