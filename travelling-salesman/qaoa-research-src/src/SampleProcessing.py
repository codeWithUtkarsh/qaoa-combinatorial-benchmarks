from typing import Union, OrderedDict, Dict, List

import numpy as np
import logging

logger = logging.getLogger(__name__)

def sample_most_likely(
        state_vector: Union[dict, np.ndarray]) -> np.ndarray:

    """Compute the most likely binary string from state vector."""
    if isinstance(state_vector, (OrderedDict, dict)):
        binary_string = max(state_vector.items(), key=lambda kv: kv[1])[0]
        x = np.asarray([int(y) for y in reversed(list(binary_string))])
        return x
    elif isinstance(state_vector, np.ndarray):
        n = int(np.log2(state_vector.shape[0]))
        k = np.argmax(np.abs(state_vector))
        x = np.zeros(n)
        for i in range(n):
            x[i] = k % 2
            k >>= 1
        return x
    else:
        raise ValueError(f"Unsupported type: {type(state_vector)}")

def decode_tsp_result(bitstring_array, num_vertices):
    """Decode TSP result from bitstring array"""
    bitstring = ''.join(['1' if bit > 0.5 else '0' for bit in bitstring_array])

    logger.debug(f"Bitstring: {bitstring}")
    logger.debug(f"Length: {len(bitstring)} (expected: {num_vertices * num_vertices})")

    tour = [-1] * num_vertices
    assignments = {}

    for i in range(num_vertices):
        for k in range(num_vertices):
            idx = i * num_vertices + k
            if idx < len(bitstring) and bitstring[idx] == '1':
                if k in assignments:
                    logger.debug(f"Conflict: Position {k} already has city {assignments[k]}, trying to add city {i}")
                else:
                    assignments[k] = i
                    tour[k] = i

    logger.debug(f"Initial tour: {tour}")
    logger.debug(f"Assignments: {assignments}")

    used_cities = set(city for city in tour if city != -1)
    missing_cities = [i for i in range(num_vertices) if i not in used_cities]
    empty_positions = [k for k in range(num_vertices) if tour[k] == -1]

    logger.debug(f"Used cities: {used_cities}")
    logger.debug(f"Missing cities: {missing_cities}")
    logger.debug(f"Empty positions: {empty_positions}")

    if missing_cities or empty_positions:
        logger.debug("Fixing constraint violations...")

        for pos, city in zip(empty_positions, missing_cities):
            tour[pos] = city

        if len(set(tour)) != num_vertices or -1 in tour:
            logger.debug("Creating fallback tour...")
            tour = list(range(num_vertices))

    return tour


def validate_tsp_tour(tour, num_vertices):
    """Validate if tour is a valid TSP solution"""
    if len(tour) != num_vertices:
        return False, f"Tour length {len(tour)} != {num_vertices}"

    if len(set(tour)) != num_vertices:
        return False, f"Tour has duplicate cities: {tour}"

    if any(city < 0 or city >= num_vertices for city in tour):
        return False, f"Tour has invalid city indices: {tour}"

    return True, "Valid tour"

def _result_to_x(result: Union[Dict, np.ndarray]) -> np.ndarray:
    # Return result.x for OptimizationResult and return result itself for np.ndarray
    if isinstance(result, Dict):
        x = result.x
    elif isinstance(result, np.ndarray):
        x = result
    else:
        raise TypeError(
            "Unsupported format of result. Provide an　OptimizationResult or a",
            f" binary array using np.ndarray instead of {type(result)}",
        )
    return x

def interpret(result: Union[Dict, np.ndarray], n
    ) -> List[Union[int, List[int]]]:
        """Interpret a result as a list of node indices

        Args:
            result : The calculated result of the problem

        Returns:
            A list of nodes whose indices correspond to its order in a prospective cycle.
        """
        x = _result_to_x(result)
        route = []  # type: List[Union[int, List[int]]]
        for p__ in range(n):
            p_step = []
            for i in range(n):
                if x[i * n + p__]:
                    p_step.append(i)
            if len(p_step) == 1:
                route.extend(p_step)
            else:
                route.append(p_step)
        return route