import numpy as np
from matplotlib import pyplot as plt
import logging

logger = logging.getLogger(__name__)

def visualize_tsp_graph(tsp_instance, tour=None, title="TSP Graph"):

    np.random.seed(123)
    positions = np.random.uniform(0, 10, size=(tsp_instance.n_cities, 2))

    plt.figure(figsize=(10, 8))

    # Draw all possible edges (light gray)
    for i in range(tsp_instance.n_cities):
        for j in range(i + 1, tsp_instance.n_cities):
            plt.plot([positions[i, 0], positions[j, 0]],
                     [positions[i, 1], positions[j, 1]],
                     'lightgray', alpha=0.3, linewidth=1, zorder=1)

            mid_x = (positions[i, 0] + positions[j, 0]) / 2
            mid_y = (positions[i, 1] + positions[j, 1]) / 2
            distance = tsp_instance.distances[i, j]
            plt.text(mid_x, mid_y, f'{distance:.1f}',
                     fontsize=8, ha='center', va='center',
                     bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))

    # Draw cities
    for i in range(tsp_instance.n_cities):
        plt.scatter(positions[i, 0], positions[i, 1], s=500, c='lightblue',
                    edgecolors='black', linewidth=2, zorder=3)
        plt.text(positions[i, 0], positions[i, 1], str(i), ha='center', va='center',
                 fontsize=14, fontweight='bold', zorder=4)

    # Draw tour if provided
    if tour is not None:
        total_distance = 0

        for i in range(len(tour)):
            current_city = tour[i]
            next_city = tour[(i + 1) % len(tour)]

            plt.plot([positions[current_city, 0], positions[next_city, 0]],
                     [positions[current_city, 1], positions[next_city, 1]],
                     'red', linewidth=4, zorder=2, alpha=0.8)

            dx = positions[next_city, 0] - positions[current_city, 0]
            dy = positions[next_city, 1] - positions[current_city, 1]
            plt.arrow(positions[current_city, 0], positions[current_city, 1],
                      dx * 0.7, dy * 0.7, head_width=0.3, head_length=0.3,
                      fc='red', ec='red', zorder=2, alpha=0.8)

            total_distance += tsp_instance.distances[current_city, next_city]

        tour_str = " → ".join([str(city) for city in tour] + [str(tour[0])])
        title += f"\nTour: {tour_str}\nTotal Distance: {total_distance:.2f}"

    plt.title(title, fontsize=14, fontweight='bold', pad=20)
    plt.xlabel("X Coordinate", fontsize=12)
    plt.ylabel("Y Coordinate", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.axis('equal')

    if tour is not None:
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color='lightgray', alpha=0.5, label='All possible edges'),
            Line2D([0], [0], color='red', linewidth=3, label='Optimal tour'),
            plt.scatter([], [], s=500, c='lightblue', edgecolors='black', label='Cities')
        ]
        plt.legend(handles=legend_elements, loc='upper right')

    plt.tight_layout()
    plt.show()


def compare_tours(tsp_instance, tours_dict, title_prefix="TSP Comparison"):
    """Compare multiple tours side by side"""

    n_tours = len(tours_dict)
    fig, axes = plt.subplots(1, n_tours, figsize=(6 * n_tours, 5))

    if n_tours == 1:
        axes = [axes]

    np.random.seed(123)
    positions = np.random.uniform(0, 10, size=(tsp_instance.n_cities, 2))

    for idx, (tour_name, tour) in enumerate(tours_dict.items()):
        ax = axes[idx]

        # Draw all edges (light)
        for i in range(tsp_instance.n_cities):
            for j in range(i + 1, tsp_instance.n_cities):
                ax.plot([positions[i, 0], positions[j, 0]],
                        [positions[i, 1], positions[j, 1]],
                        'lightgray', alpha=0.3, linewidth=1)

        # Draw cities
        for i in range(tsp_instance.n_cities):
            ax.scatter(positions[i, 0], positions[i, 1], s=400, c='lightblue',
                       edgecolors='black', linewidth=2, zorder=3)
            ax.text(positions[i, 0], positions[i, 1], str(i), ha='center', va='center',
                    fontsize=12, fontweight='bold', zorder=4)

        # Draw tour
        if tour is not None:
            total_distance = 0
            for i in range(len(tour)):
                current_city = tour[i]
                next_city = tour[(i + 1) % len(tour)]

                ax.plot([positions[current_city, 0], positions[next_city, 0]],
                        [positions[current_city, 1], positions[next_city, 1]],
                        'red', linewidth=3, zorder=2)

                total_distance += tsp_instance.distances[current_city, next_city]

            tour_str = " → ".join([str(city) for city in tour] + [str(tour[0])])
            ax.set_title(f"{tour_name}\n{tour_str}\nDistance: {total_distance:.2f}",
                         fontsize=10, fontweight='bold')
        else:
            ax.set_title(f"{tour_name}\nNo valid tour", fontsize=10, fontweight='bold')

        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.grid(True, alpha=0.3)
        ax.axis('equal')

    plt.suptitle(f"{title_prefix} - {tsp_instance.n_cities} Cities", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()

def visualize_tsp_matrix_view(x, num_cities):
    logger.debug(f"Position in x: {list(range(len(x)))}")
    logger.debug("Matrix format:")

    header = "                 " + "".join(f"Position {j:>11}" for j in range(num_cities))
    logger.debug(header)

    logger.debug("            ┌" + "─" * (12 * num_cities - 1) + "┐")
    for i in range(num_cities):
        row = f"    City {i}   │"
        for j in range(num_cities):
            idx = j * num_cities + i  # position * num_cities + city
            cell = f"    x[{idx}]={x[idx]}"
            row += f"{cell:>12}"
        row += "   │"
        logger.debug(row)
    logger.debug("            └" + "─" * (12 * num_cities - 1) + "┘")
