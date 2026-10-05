# TSP Playground

A collection of Traveling Salesman Problem (TSP) algorithm implementations for performance comparison and analysis.

## Overview

This repository contains implementations of four different TSP algorithms:
- **Branch and Bound** - Exact algorithm using branch and bound technique
- **Genetic Algorithm** - Evolutionary algorithm approach
- **Held-Karp** - Dynamic programming exact algorithm
- **Simulated Annealing** - Metaheuristic optimization algorithm

## Project Structure

```
tsp-playground/
├── tsp-branch-and-bound/
├── tsp-genetic-algorithm/
├── tsp-held-karp/
├── tsp-simulated-annealing/
└── README.md
```

## Getting Started

### Prerequisites

- C/C++ compiler (gcc/g++)
- Make utility
- Standard C/C++ libraries

### Running the Algorithms

Each algorithm is contained in its own directory and can be run independently. Follow these steps for any algorithm:

#### 1. Navigate to the Algorithm Directory

```bash
cd tsp-branch-and-bound    # For Branch and Bound
# OR
cd tsp-genetic-algorithm   # For Genetic Algorithm
# OR
cd tsp-held-karp          # For Held-Karp
# OR
cd tsp-simulated-annealing # For Simulated Annealing
```

### Compile and Run for branch-and-bound, held-karp, simulated-annealing Code
#### 1. Compile the Code

```bash
make
```

This will create an executable in the `bin/` directory.

#### 2. Run the Algorithm

```bash
./bin/main
```

### Configuration

Each algorithm can be configured using the `settings.ini` file located in the respective algorithm directory.

#### Configuration Options

You can tweak the following settings in `settings.ini`:

- **random_instance_test**: Generate random TSP instances
- **File Instance Mode**: Use predefined TSP instance files

Example `settings.ini`:
```ini
;mode = file_instance_test
mode = random_instance_test

;Configure minimum node and max node
[random_instance_test]
min_size = 3
max_size = 23
```
### Compile and Run for Genetic Algorithm Code
#### 1. Compile the Code

```bash
gcc GA_TSP_Serial_Random.c -o gatsp -lm
```

This will create an executable `gatsp` in root directory.

#### 2. Run the Algorithm

##### File Instance Mode
```bash
./gatsp instance_mode
```
##### Random Instance Mode
```bash
./gatsp
```

### Configuration
Update this file for min and max nodes for which you want to run random instance test

./tsp-playground/tsp-genetic-algorithm/GA_TSP_Serial_Random.c
Example `GA_TSP_Serial_Random.c`:
```c++
#define MIN_NODES 5
#define MAX_NODES 30
```


## Algorithm Descriptions

### Branch and Bound
- **Type**: Exact algorithm
- **Best for**: Small to medium instances (< 20 vertices)
- **Time Complexity**: Exponential (worst case)

### Genetic Algorithm
- **Type**: Evolutionary metaheuristic
- **Best for**: Large instances where approximate solutions are acceptable
- **Customizable**: Population size, mutation rate, crossover rate

### Held-Karp
- **Type**: Dynamic programming exact algorithm
- **Best for**: Small instances (< 15 vertices due to memory constraints)
- **Time Complexity**: O(n²2ⁿ)

### Simulated Annealing
- **Type**: Metaheuristic optimization
- **Best for**: Large instances with good quality approximate solutions
- **Customizable**: Temperature schedule, cooling rate

## Performance Analysis

Each algorithm outputs:
- Execution time
- Best distance found
- Gap percentage (if optimal is known)
- Convergence information

## Cleaning Up

To clean compiled files in any algorithm directory:

```bash
make clean
```

## License

This project is for educational and research purposes.