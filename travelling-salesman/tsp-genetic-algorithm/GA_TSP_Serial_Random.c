#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>

#define MIN_NODES 5
#define MAX_NODES 30
#define BASE_WEIGHT 100.0  // Base edge weight
#define WEIGHT_VARIATION 0.005  // 0.5% variation
#define NUM_RUNS 3  // Number of runs per node count for averaging
#define MAX_FILENAME 256
#define MAX_INSTANCE_NAME 50
#define INSTANCES_DIR "instances"
#define RESULTS_DIR "results"
#define MAX_INSTANCES 100

int chromo_length; // Number of cities
int popl_size; // Number of chromosomes
int no_generation; //Number of iterations (Generations)
float **dist_matrix = NULL; //Stores distance between cities

//Structures stores genes (sequence of cities) for a chromosome, and its fitness value
typedef struct{
    int * genes;
    float fitness;
} Chromosome;
Chromosome * population = NULL;

// Structure to store results for each test
typedef struct {
    char instance_name[MAX_INSTANCE_NAME];
    int nodes;
    int run;
    double execution_time;
    float best_distance;
    float best_fitness;
    int generations_to_converge;
    float optimal_distance;  // Known optimal from file
    float gap_percentage;    // Gap from optimal
} TestResult;

// Structure to store instance data
typedef struct {
    char name[MAX_INSTANCE_NAME];
    int num_nodes;
    float **matrix;
    float optimal_value;
} InstanceData;

//Create results directory if it doesn't exist
void create_results_directory() {
    struct stat st = {0};
    if (stat(RESULTS_DIR, &st) == -1) {
        #ifdef _WIN32
            _mkdir(RESULTS_DIR);
        #else
            mkdir(RESULTS_DIR, 0700);
        #endif
#ifdef DEBUG
        printf("Created results directory: %s/\n", RESULTS_DIR);
#endif
    }
}

//Check if file has valid extension for TSP instances
int is_valid_instance_file(const char* filename) {
    int len = strlen(filename);
    if(len < 4) return 0;

    // Check for common TSP file extensions
    const char* ext = filename + len - 4;
    return (strcmp(ext, ".tsp") == 0 ||
            strcmp(ext, ".atsp") == 0 ||
            strcmp(ext, ".txt") == 0);
}

//Get list of instance files from directory
int get_instance_files(char filenames[][MAX_FILENAME], int max_files) {
    DIR *dir;
    struct dirent *entry;
    int count = 0;

    dir = opendir(INSTANCES_DIR);
    if(dir == NULL) {
        printf("Error: Cannot open instances directory '%s'\n", INSTANCES_DIR);
        printf("Please create an 'instances' directory and place your TSP files there.\n");
        return 0;
    }

#ifdef DEBUG
    printf("Scanning instances directory '%s'...\n", INSTANCES_DIR);
#endif

    while((entry = readdir(dir)) != NULL && count < max_files) {
        // Skip hidden files and directories
        if(entry->d_name[0] == '.') continue;

        // Check if it's a valid instance file
        if(is_valid_instance_file(entry->d_name)) {
            snprintf(filenames[count], MAX_FILENAME, "%s/%s", INSTANCES_DIR, entry->d_name);
#ifdef DEBUG
            printf("  Found: %s\n", entry->d_name);
#endif
            count++;
        }
    }

    closedir(dir);
#ifdef DEBUG
    printf("Found %d instance files.\n\n", count);
#endif
    return count;
}
float random_float() {
    return (float)rand() / RAND_MAX;
}

//Generate random edge weight with 0.5% variation
float generate_random_weight() {
    float variation = (random_float() - 0.5f) * 2.0f * WEIGHT_VARIATION; // -0.5% to +0.5%
    return BASE_WEIGHT * (1.0f + variation);
}

//Clean up distance matrix
void cleanup_dist_matrix() {
    if(dist_matrix) {
        for(int i = 0; i < chromo_length; i++) {
            if(dist_matrix[i]) {
                free(dist_matrix[i]);
                dist_matrix[i] = NULL;
            }
        }
        free(dist_matrix);
        dist_matrix = NULL;
    }
}

//Clean up instance data
void cleanup_instance_data(InstanceData *instance) {
    if(instance && instance->matrix) {
        for(int i = 0; i < instance->num_nodes; i++) {
            if(instance->matrix[i]) {
                free(instance->matrix[i]);
            }
        }
        free(instance->matrix);
        instance->matrix = NULL;
    }
}

//Read instance from file
int read_instance_file(const char* filename, InstanceData* instance) {
    FILE *fp = fopen(filename, "r");
    if(!fp) {
        printf("Error: Cannot open file %s\n", filename);
        return 0;
    }

    // Read instance name
    if(fscanf(fp, "%49s", instance->name) != 1) {
        printf("Error: Cannot read instance name\n");
        fclose(fp);
        return 0;
    }

    // Read number of nodes
    if(fscanf(fp, "%d", &instance->num_nodes) != 1) {
        printf("Error: Cannot read number of nodes\n");
        fclose(fp);
        return 0;
    }

    if(instance->num_nodes <= 0 || instance->num_nodes > 1000) {
        printf("Error: Invalid number of nodes: %d\n", instance->num_nodes);
        fclose(fp);
        return 0;
    }

    // Allocate matrix
    instance->matrix = malloc(sizeof(float*) * instance->num_nodes);
    for(int i = 0; i < instance->num_nodes; i++) {
        instance->matrix[i] = malloc(sizeof(float) * instance->num_nodes);
    }

    // Read distance matrix
    for(int i = 0; i < instance->num_nodes; i++) {
        for(int j = 0; j < instance->num_nodes; j++) {
            if(fscanf(fp, "%f", &instance->matrix[i][j]) != 1) {
#ifdef DEBUG
                printf("Error: Cannot read matrix element [%d][%d]\n", i, j);
#endif
                cleanup_instance_data(instance);
                fclose(fp);
                return 0;
            }
        }
    }

    // Read optimal value
    if(fscanf(fp, "%f", &instance->optimal_value) != 1) {
        printf("Error: Cannot read optimal value\n");
        cleanup_instance_data(instance);
        fclose(fp);
        return 0;
    }

    fclose(fp);
#ifdef DEBUG
    printf("Successfully loaded instance: %s (%d nodes, optimal: %.0f)\n",
           instance->name, instance->num_nodes, instance->optimal_value);
#endif
    return 1;
}

//Initialize distance matrix with random weights
void init_random_dist_matrix(int num_nodes){
    // Clean up previous matrix
    cleanup_dist_matrix();

    chromo_length = num_nodes;
    dist_matrix = malloc(sizeof(float *) * chromo_length);

    // Allocate memory for each row
    for (int i = 0; i < chromo_length; i++) {
        dist_matrix[i] = calloc(chromo_length, sizeof(float));
    }

    // Generate random distances
    for (int i = 0; i < chromo_length; i++){
        for (int j = i + 1; j < chromo_length; j++){
            float weight = generate_random_weight();
            dist_matrix[i][j] = dist_matrix[j][i] = weight;
        }
        dist_matrix[i][i] = 0.0f; // Distance from node to itself is 0
    }
}

//Initialize distance matrix from instance data
void init_dist_matrix_from_instance(InstanceData* instance) {
    cleanup_dist_matrix();

    chromo_length = instance->num_nodes;
    dist_matrix = malloc(sizeof(float *) * chromo_length);

    // Allocate memory for each row
    for (int i = 0; i < chromo_length; i++) {
        dist_matrix[i] = malloc(sizeof(float) * chromo_length);
    }

    // Copy matrix from instance
    for (int i = 0; i < chromo_length; i++) {
        for (int j = 0; j < chromo_length; j++) {
            dist_matrix[i][j] = instance->matrix[i][j];
        }
    }
}

//Print distance matrix (for debugging small instances)
void print_dist_matrix() {
#ifdef DEBUG
    printf("\nDistance Matrix:\n");
    printf("     ");
    for (int j = 0; j < chromo_length; j++)
        printf("%8d ", j + 1);
    printf("\n");

    for (int i = 0; i < chromo_length; i++){
        printf("%2d | ", i + 1);
        for (int j = 0; j < chromo_length; j++)
            printf("%8.0f ", dist_matrix[i][j]);
        printf("\n");
    }
    printf("\n");
#endif
}

//Calculates fitness value for each chromosome
void calculate_fitness(Chromosome *ptr_chromosome){
    float fitness = 0;
    int i = 0;

    for (i = 0; i < chromo_length-1; i++)
        fitness += dist_matrix[ptr_chromosome->genes[i] - 1][ptr_chromosome->genes[i+1] - 1];

    fitness += dist_matrix[ptr_chromosome->genes[i] - 1][0]; // Return to start
    fitness = 10000.0f / fitness; // Higher fitness for shorter paths
    ptr_chromosome->fitness = fitness;
}

//Send each chromosome to the above function
void calculate_population_fitness(Chromosome *population){
    for(int i = 0; i < popl_size; i++)
        calculate_fitness(&population[i]);
}

//Generating a random number
int getRandomNumber(){
    return rand() % chromo_length;
}

//Clean up a single chromosome
void cleanup_chromosome(Chromosome *chrom) {
    if(chrom && chrom->genes) {
        free(chrom->genes);
        chrom->genes = NULL;
    }
}

//Initialising the chromosome path or solution as random
void fill_randomly_the_chromosome(Chromosome *chrom){
    int *array = malloc(chromo_length * sizeof(int));

    // Clean up existing genes
    cleanup_chromosome(chrom);

    chrom->genes = malloc(chromo_length * sizeof(int));

    //Initialize array with node numbers (1-based)
    for(int i = 0; i < chromo_length; i++)
        array[i] = i + 1;

    //Fisher-Yates shuffle
    for(int i = chromo_length - 1; i > 0; i--){
        int j = rand() % (i + 1);
        int tmp = array[i];
        array[i] = array[j];
        array[j] = tmp;
    }

    // Copy shuffled array to genes
    for(int i = 0; i < chromo_length; i++) {
        chrom->genes[i] = array[i];
    }

    free(array);
    calculate_fitness(chrom);
}

//Swapping two chromosomes
void swap_chromosomes(Chromosome *pop, int src, int dest){
    Chromosome chrom = pop[src];
    pop[src] = pop[dest];
    pop[dest] = chrom;
}

//Sorting population on the basis of fitness value (descending order)
void sort_population(Chromosome *population){
    for(int i = 0; i < popl_size; i++)
        for(int j = i+1; j < popl_size; j++)
            if(population[i].fitness < population[j].fitness)
                swap_chromosomes(population, i, j);
}

//Generate a random chromosome index to be used during crossover
int get_random_index_of_chrom(){
    return rand() % popl_size;
}

//Selecting some chromosomes for crossover
void selection(Chromosome *pop){
    int n = (40 * popl_size) / 100;
    for(int i = 0; i < (10 * popl_size) / 100; i++){
        int randNb = (popl_size / 2) + get_random_index_of_chrom() % (popl_size / 2);
        swap_chromosomes(population, n + i, randNb);
    }
}

//Checking the percentage difference in two chromosomes
float percentage_of_difference(Chromosome chro1, Chromosome chro2){
    float sum = 0;
    for(int i = 0; i < chromo_length; i++)
        if(chro1.genes[i] != chro2.genes[i])
            sum++;
    return (sum * 100) / chromo_length;
}

//If a vertex exists in the chromosome
int if_exist(Chromosome *chrom, int x){
    for(int i = 0; i < chromo_length; i++)
        if(x == chrom->genes[i])
            return 1;
    return 0;
}

//Create children from crossover
void create_ChildV2(Chromosome p, Chromosome m, Chromosome *Chro){
    // Clean up existing genes
    cleanup_chromosome(Chro);

    Chro->genes = malloc(chromo_length * sizeof(int));
    int z = 1;
    int n = getRandomNumber() % chromo_length;

    for(int i = 0; i < chromo_length; i++)
        Chro->genes[i] = 0;

    for(int i = n; i < n + ((chromo_length * 30) / 100); i++){
        z = i % chromo_length;
        Chro->genes[z] = p.genes[z];
    }

    int c = 0;
    int i = (z + 1) % chromo_length;
    while(i != z){
        c = c % chromo_length;
        if(if_exist(Chro, m.genes[c]) != 1)
            Chro->genes[i] = m.genes[c];
        else{
            if(Chro->genes[i] == 0){
                while(if_exist(Chro, m.genes[c]) == 1)
                    c++;
                Chro->genes[i] = m.genes[c];
            }
        }
        c++;
        i++;
        i = i % chromo_length;
    }
}

//used to perform crossover of two chromosomes
void crossoverV2(Chromosome *pop){
    int nb = 0;
    for(int i = 0; i < (popl_size / 2); i++){
        do{
            nb = getRandomNumber() % (popl_size / 2);
        }while(nb == i && percentage_of_difference(pop[i], pop[nb]) < 70);
        create_ChildV2(pop[i], pop[nb], &pop[(popl_size / 2) + i]);
    }
}

//Used to perform mutation in a chromosome
void mutation(Chromosome *pop){
    for(int z = 0; z < 5; z++){
        int i = getRandomNumber() % chromo_length;
        int j = getRandomNumber() % chromo_length;
        int k = getRandomNumber() % (popl_size - (20 * popl_size / 100));
        int temp = pop[(20 * popl_size / 100) + k].genes[j];
        pop[(20 * popl_size / 100) + k].genes[j] = pop[(20 * popl_size / 100) + k].genes[i];
        pop[(20 * popl_size / 100) + k].genes[i] = temp;
    }
}

//Calculate actual distance for a chromosome
float calculate_actual_distance(Chromosome *chrom) {
    float total_distance = 0;
    for(int i = 0; i < chromo_length - 1; i++) {
        total_distance += dist_matrix[chrom->genes[i] - 1][chrom->genes[i + 1] - 1];
    }
    total_distance += dist_matrix[chrom->genes[chromo_length - 1] - 1][chrom->genes[0] - 1];
    return total_distance;
}

//Find generation where algorithm converged (no improvement for 50 generations)
int find_convergence_generation(float *fitness_history, int total_generations) {
    if(total_generations < 50) return total_generations;

    for(int i = 50; i < total_generations; i++) {
        int converged = 1;
        for(int j = i - 50; j < i; j++) {
            if(fabs(fitness_history[j] - fitness_history[i]) > 0.000001) {
                converged = 0;
                break;
            }
        }
        if(converged) return i - 50;
    }
    return total_generations;
}

//Clean up population
void cleanup_population() {
    if(population) {
        for(int i = 0; i < popl_size; i++) {
            cleanup_chromosome(&population[i]);
        }
        free(population);
        population = NULL;
    }
}

//Initialize population
void init_population(int size) {
    cleanup_population();
    popl_size = size;
    population = (Chromosome *)malloc(popl_size * sizeof(Chromosome));

    // Initialize all chromosome pointers to NULL
    for(int i = 0; i < popl_size; i++) {
        population[i].genes = NULL;
        population[i].fitness = 0.0f;
    }
}

//Print best solution with path
void print_best_solution(Chromosome *population, const char* instance_name, float optimal) {
#ifdef DEBUG
    printf("\n=== BEST SOLUTION FOR %s ===\n", instance_name);
    printf("Best Path: ");
    for(int i = 0; i < chromo_length; i++) {
        printf("%d", population[0].genes[i]);
        if(i < chromo_length - 1) printf(" -> ");
    }
    printf(" -> %d (return to start)\n", population[0].genes[0]);

    float total_distance = calculate_actual_distance(&population[0]);
    float gap = ((total_distance - optimal) / optimal) * 100.0f;

    printf("Found Distance: %.2f\n", total_distance);
    printf("Optimal Distance: %.2f\n", optimal);
    printf("Gap from Optimal: %.2f%%\n", gap);
    printf("Fitness Value: %.6f\n", population[0].fitness);
    printf("===============================\n");
#endif
}

//Run genetic algorithm for given instance
TestResult run_genetic_algorithm_instance(InstanceData* instance, int run_number) {
    TestResult result;
    strcpy(result.instance_name, instance->name);
    result.nodes = instance->num_nodes;
    result.run = run_number;
    result.optimal_distance = instance->optimal_value;

    // Adjust parameters based on problem size
    int target_popl_size, target_generations;
    if(instance->num_nodes <= 8) {
        target_popl_size = 50;
        target_generations = 300;
    } else if(instance->num_nodes <= 12) {
        target_popl_size = 75;
        target_generations = 400;
    } else if(instance->num_nodes <= 16) {
        target_popl_size = 100;
        target_generations = 500;
    } else if(instance->num_nodes <= 25) {
        target_popl_size = 150;
        target_generations = 600;
    } else {
        target_popl_size = 200;
        target_generations = 800;
    }

    no_generation = target_generations;

    init_dist_matrix_from_instance(instance);
    init_population(target_popl_size);

    // Track fitness history for convergence analysis
    float *fitness_history = malloc(no_generation * sizeof(float));

    //Start clock
    clock_t start = clock();

    //Initialise chromosomes
    for(int i = 0; i < popl_size; i++)
        fill_randomly_the_chromosome(&population[i]);

    sort_population(population);
    fitness_history[0] = population[0].fitness;

    int i = 0;
    while(i < no_generation){
        selection(population);
        crossoverV2(population);
        mutation(population);
        calculate_population_fitness(population);
        sort_population(population);

        fitness_history[i] = population[0].fitness;
        i++;
    }

    clock_t end = clock();
    result.execution_time = ((double)(end - start)) / CLOCKS_PER_SEC;
    result.best_fitness = population[0].fitness;
    result.best_distance = calculate_actual_distance(&population[0]);
    result.generations_to_converge = find_convergence_generation(fitness_history, no_generation);
    result.gap_percentage = ((result.best_distance - result.optimal_distance) / result.optimal_distance) * 100.0f;

    free(fitness_history);
    return result;
}

//Run genetic algorithm for random graphs
TestResult run_genetic_algorithm_random(int num_nodes, int run_number) {
    TestResult result;
    strcpy(result.instance_name, "Random");
    result.nodes = num_nodes;
    result.run = run_number;
    result.optimal_distance = -1; // Unknown for random graphs

    // Adjust parameters based on problem size
    int target_popl_size, target_generations;
    if(num_nodes <= 8) {
        target_popl_size = 50;
        target_generations = 300;
    } else if(num_nodes <= 12) {
        target_popl_size = 75;
        target_generations = 400;
    } else if(num_nodes <= 16) {
        target_popl_size = 100;
        target_generations = 500;
    } else {
        target_popl_size = 150;
        target_generations = 600;
    }

    no_generation = target_generations;

    init_random_dist_matrix(num_nodes);
    init_population(target_popl_size);

    // Track fitness history for convergence analysis
    float *fitness_history = malloc(no_generation * sizeof(float));

    //Start clock
    clock_t start = clock();

    //Initialise chromosomes
    for(int i = 0; i < popl_size; i++)
        fill_randomly_the_chromosome(&population[i]);

    sort_population(population);
    fitness_history[0] = population[0].fitness;

    int i = 0;
    while(i < no_generation){
        selection(population);
        crossoverV2(population);
        mutation(population);
        calculate_population_fitness(population);
        sort_population(population);

        fitness_history[i] = population[0].fitness;
        i++;
    }

    clock_t end = clock();
    result.execution_time = ((double)(end - start)) / CLOCKS_PER_SEC;
    result.best_fitness = population[0].fitness;
    result.best_distance = calculate_actual_distance(&population[0]);
    result.generations_to_converge = find_convergence_generation(fitness_history, no_generation);
    result.gap_percentage = 0.0f; // Not applicable for random graphs

    free(fitness_history);
    return result;
}

//Print usage information
void print_usage(const char* program_name) {
    printf("Usage:\n");
    printf("  %s                              - Run batch testing (random graphs 5-20 nodes)\n", program_name);
    printf("  %s instance_mode                - Run all instances from 'instances' directory\n", program_name);
    printf("  %s instance_mode -r <runs>      - Run all instances with specified number of runs\n", program_name);
    printf("  %s -f <filename>                - Run single instance from file\n", program_name);
    printf("  %s -f <filename> -r <runs>      - Run single instance multiple times\n", program_name);
    printf("  %s -h                           - Show this help\n", program_name);
    printf("\nDirectory structure:\n");
    printf("  ./instances/          - Input TSP instance files\n");
    printf("    ├── instance1.tsp\n");
    printf("    ├── instance2.atsp\n");
    printf("    └── instance3.txt\n");
    printf("  ./results/           - Output directory (created automatically)\n");
    printf("    ├── *.csv           - Detailed results data\n");
    printf("    ├── *_summary.txt   - Human-readable reports\n");
    printf("    └── best_solution_*.txt - Best solution paths\n");
    printf("\nFile format:\n");
    printf("  Line 1: Instance name\n");
    printf("  Line 2: Number of nodes\n");
    printf("  Lines 3+: Distance matrix (space-separated)\n");
    printf("  Last line: Optimal value\n");
}

//Print comprehensive summary for all instances
void print_all_instances_summary(TestResult *results, int total_results) {
#ifdef DEBUG
    printf("\n=== ALL INSTANCES COMPREHENSIVE SUMMARY ===\n");
    printf("%-15s %-6s %-4s %-10s %-10s %-10s %-8s %-8s\n",
           "Instance", "Number of vertices", "Run", "Time(s)", "Found", "Optimal", "Gap%", "Conv");
    printf("---------------------------------------------------------------------------------\n");

    for(int i = 0; i < total_results; i++) {
        printf("%-15s %-6d %-4d %-10.4f %-10.1f %-10.1f %-8.2f %-8d\n",
               results[i].instance_name, results[i].nodes, results[i].run,
               results[i].execution_time, results[i].best_distance,
               results[i].optimal_distance, results[i].gap_percentage,
               results[i].generations_to_converge);
    }

    // Calculate overall statistics
    printf("\n=== OVERALL STATISTICS ===\n");

    // Group by instance name for averages
    char unique_instances[MAX_INSTANCES][MAX_INSTANCE_NAME];
    int unique_count = 0;

    // Find unique instance names
    for(int i = 0; i < total_results; i++) {
        int found = 0;
        for(int j = 0; j < unique_count; j++) {
            if(strcmp(results[i].instance_name, unique_instances[j]) == 0) {
                found = 1;
                break;
            }
        }
        if(!found && unique_count < MAX_INSTANCES) {
            strcpy(unique_instances[unique_count], results[i].instance_name);
            unique_count++;
        }
    }

    printf("%-15s %-6s %-10s %-10s %-8s %-8s %-8s\n",
           "Instance", "Number of vertices", "Avg.Time", "Avg.Found", "Optimal", "Avg.Gap%", "Success");
    printf("------------------------------------------------------------------------\n");

    for(int inst = 0; inst < unique_count; inst++) {
        double avg_time = 0;
        float avg_distance = 0;
        float avg_gap = 0;
        int total_runs = 0;
        int success_runs = 0; // Runs within 5% of optimal
        int nodes = 0;
        float optimal = 0;

        for(int i = 0; i < total_results; i++) {
            if(strcmp(results[i].instance_name, unique_instances[inst]) == 0) {
                avg_time += results[i].execution_time;
                avg_distance += results[i].best_distance;
                avg_gap += results[i].gap_percentage;
                if(results[i].gap_percentage <= 5.0) success_runs++;
                total_runs++;
                nodes = results[i].nodes;
                optimal = results[i].optimal_distance;
            }
        }

        if(total_runs > 0) {
            printf("%-15s %-6d %-10.4f %-10.1f %-8.1f %-8.2f %d/%d\n",
                   unique_instances[inst], nodes,
                   avg_time/total_runs, avg_distance/total_runs, optimal,
                   avg_gap/total_runs, success_runs, total_runs);
        }
    }
#endif
}
void print_instance_summary_table(TestResult *results, int total_results) {
#ifdef DEBUG
    printf("\n=== INSTANCE RESULTS SUMMARY ===\n");
    printf("%-12s %-6s %-4s %-12s %-12s %-12s %-12s %-10s\n",
           "Instance", "Number of vertices", "Run", "Time(s)", "Distance", "Optimal", "Gap%", "Conv.Gen");
    printf("--------------------------------------------------------------------------------------\n");

    for(int i = 0; i < total_results; i++) {
        printf("%-12s %-6d %-4d %-12.4f %-12.2f %-12.2f %-12.2f %-10d\n",
               results[i].instance_name, results[i].nodes, results[i].run,
               results[i].execution_time, results[i].best_distance,
               results[i].optimal_distance, results[i].gap_percentage,
               results[i].generations_to_converge);
    }

    // Calculate averages if multiple runs
    if(total_results > 1) {
        double avg_time = 0;
        float avg_distance = 0;
        float avg_gap = 0;
        int avg_conv = 0;

        for(int i = 0; i < total_results; i++) {
            avg_time += results[i].execution_time;
            avg_distance += results[i].best_distance;
            avg_gap += results[i].gap_percentage;
            avg_conv += results[i].generations_to_converge;
        }

        printf("--------------------------------------------------------------------------------------\n");
        printf("%-12s %-6s %-4s %-12.4f %-12.2f %-12s %-12.2f %-10d\n",
               "AVERAGE", "", "", avg_time/total_results, avg_distance/total_results,
               "", avg_gap/total_results, avg_conv/total_results);
    }
#endif
}

//Print summary table for random graphs
void print_summary_table(TestResult *results, int total_results) {
#ifdef DEBUG
    printf("\n=== COMPREHENSIVE RESULTS SUMMARY ===\n");
    printf("%-6s %-4s %-12s %-12s %-12s %-12s\n",
           "Number of vertices", "Run", "Time(s)", "Distance", "Fitness", "Conv.Gen");
    printf("--------------------------------------------------------------\n");

    for(int i = 0; i < total_results; i++) {
        printf("%-6d %-4d %-12.4f %-12.2f %-12.6f %-12d\n",
               results[i].nodes, results[i].run, results[i].execution_time,
               results[i].best_distance, results[i].best_fitness,
               results[i].generations_to_converge);
    }

    // Calculate and print averages for each node count
    printf("\n=== AVERAGE RESULTS BY NODE COUNT ===\n");
    printf("%-6s %-12s %-12s %-12s %-12s\n",
           "Number of vertices", "Avg.Time(s)", "Avg.Distance", "Avg.Fitness", "Avg.Conv");
    printf("------------------------------------------------------\n");

    for(int nodes = MIN_NODES; nodes <= MAX_NODES; nodes++) {
        double avg_time = 0;
        float avg_distance = 0;
        float avg_fitness = 0;
        int avg_conv = 0;
        int count = 0;

        for(int i = 0; i < total_results; i++) {
            if(results[i].nodes == nodes) {
                avg_time += results[i].execution_time;
                avg_distance += results[i].best_distance;
                avg_fitness += results[i].best_fitness;
                avg_conv += results[i].generations_to_converge;
                count++;
            }
        }

        if(count > 0) {
            printf("%-6d %-12.4f %-12.2f %-12.6f %-12d\n",
                   nodes, avg_time/count, avg_distance/count,
                   avg_fitness/count, avg_conv/count);
        }
    }
#endif
}

//Save results to CSV file in results directory
void save_results_to_csv(TestResult *results, int total_results, const char* filename) {
    create_results_directory();

    char full_path[MAX_FILENAME];
    snprintf(full_path, sizeof(full_path), "%s/%s", RESULTS_DIR, filename);

    FILE *fp = fopen(full_path, "w");
    if(fp == NULL) {
#ifdef DEBUG
        printf("Could not create CSV file %s\n", full_path);
#endif
        return;
    }

    fprintf(fp, "Instance,Number of vertices,Run,ExecutionTime,BestDistance,OptimalDistance,GapPercentage,BestFitness,ConvergenceGeneration\n");
    for(int i = 0; i < total_results; i++) {
        fprintf(fp, "%s,%d,%d,%.6f,%.2f,%.2f,%.2f,%.6f,%d\n",
                results[i].instance_name, results[i].nodes, results[i].run,
                results[i].execution_time, results[i].best_distance,
                results[i].optimal_distance, results[i].gap_percentage,
                results[i].best_fitness, results[i].generations_to_converge);
    }

    fclose(fp);
#ifdef DEBUG
    printf("\nResults saved to '%s'\n", full_path);
#endif
}

//Save detailed summary report to text file
void save_summary_report(TestResult *results, int total_results, const char* filename, const char* mode_description) {
    create_results_directory();

    char full_path[MAX_FILENAME];
    snprintf(full_path, sizeof(full_path), "%s/%s", RESULTS_DIR, filename);

    FILE *fp = fopen(full_path, "w");
    if(fp == NULL) {
#ifdef DEBUG
        printf("Could not create summary report %s\n", full_path);
#endif
        return;
    }

    time_t rawtime;
    struct tm * timeinfo;
    char timestamp[80];

    time(&rawtime);
    timeinfo = localtime(&rawtime);
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", timeinfo);

    fprintf(fp, "=== GA TSP RESULTS SUMMARY REPORT ===\n");
    fprintf(fp, "Generated: %s\n", timestamp);
    fprintf(fp, "Mode: %s\n", mode_description);
    fprintf(fp, "Total Results: %d\n", total_results);
    fprintf(fp, "========================================\n\n");

    // Individual results
    fprintf(fp, "DETAILED RESULTS:\n");
    fprintf(fp, "%-15s %-6s %-4s %-10s %-10s %-10s %-8s %-8s\n",
           "Instance", "Number of vertices", "Run", "Time(s)", "Found", "Optimal", "Gap%%", "Conv");
    fprintf(fp, "---------------------------------------------------------------------------------\n");

    for(int i = 0; i < total_results; i++) {
        fprintf(fp, "%-15s %-6d %-4d %-10.4f %-10.1f %-10.1f %-8.2f %-8d\n",
               results[i].instance_name, results[i].nodes, results[i].run,
               results[i].execution_time, results[i].best_distance,
               results[i].optimal_distance, results[i].gap_percentage,
               results[i].generations_to_converge);
    }

    // Calculate statistics for instances (if applicable)
    if(results[0].optimal_distance > 0) { // Instance mode
        fprintf(fp, "\nSTATISTICAL SUMMARY:\n");

        // Find unique instances
        char unique_instances[MAX_INSTANCES][MAX_INSTANCE_NAME];
        int unique_count = 0;

        for(int i = 0; i < total_results; i++) {
            int found = 0;
            for(int j = 0; j < unique_count; j++) {
                if(strcmp(results[i].instance_name, unique_instances[j]) == 0) {
                    found = 1;
                    break;
                }
            }
            if(!found && unique_count < MAX_INSTANCES) {
                strcpy(unique_instances[unique_count], results[i].instance_name);
                unique_count++;
            }
        }

        fprintf(fp, "%-15s %-6s %-10s %-10s %-8s %-8s %-8s\n",
               "Instance", "Number of vertices", "Avg.Time", "Avg.Found", "Optimal", "Avg.Gap%%", "Success");
        fprintf(fp, "------------------------------------------------------------------------\n");

        for(int inst = 0; inst < unique_count; inst++) {
            double avg_time = 0;
            float avg_distance = 0;
            float avg_gap = 0;
            int total_runs = 0;
            int success_runs = 0;
            int nodes = 0;
            float optimal = 0;

            for(int i = 0; i < total_results; i++) {
                if(strcmp(results[i].instance_name, unique_instances[inst]) == 0) {
                    avg_time += results[i].execution_time;
                    avg_distance += results[i].best_distance;
                    avg_gap += results[i].gap_percentage;
                    if(results[i].gap_percentage <= 5.0) success_runs++;
                    total_runs++;
                    nodes = results[i].nodes;
                    optimal = results[i].optimal_distance;
                }
            }

            if(total_runs > 0) {
                fprintf(fp, "%-15s %-6d %-10.4f %-10.1f %-8.1f %-8.2f %d/%d\n",
                       unique_instances[inst], nodes,
                       avg_time/total_runs, avg_distance/total_runs, optimal,
                       avg_gap/total_runs, success_runs, total_runs);
            }
        }
    } else { // Random graph mode
        fprintf(fp, "\nAVERAGE RESULTS BY NODE COUNT:\n");
        fprintf(fp, "%-6s %-12s %-12s %-12s %-12s\n",
               "Number of vertices", "Avg.Time(s)", "Avg.Distance", "Avg.Fitness", "Avg.Conv");
        fprintf(fp, "------------------------------------------------------\n");

        for(int nodes = MIN_NODES; nodes <= MAX_NODES; nodes++) {
            double avg_time = 0;
            float avg_distance = 0;
            float avg_fitness = 0;
            int avg_conv = 0;
            int count = 0;

            for(int i = 0; i < total_results; i++) {
                if(results[i].nodes == nodes) {
                    avg_time += results[i].execution_time;
                    avg_distance += results[i].best_distance;
                    avg_fitness += results[i].best_fitness;
                    avg_conv += results[i].generations_to_converge;
                    count++;
                }
            }

            if(count > 0) {
                fprintf(fp, "%-6d %-12.4f %-12.2f %-12.6f %-12d\n",
                       nodes, avg_time/count, avg_distance/count,
                       avg_fitness/count, avg_conv/count);
            }
        }
    }

    fclose(fp);
#ifdef DEBUG
    printf("\nSummary report saved to '%s'\n", full_path);
#endif
}

//Save best solution details to file
void save_best_solution(Chromosome *chromosome, const char* instance_name, float optimal, int nodes) {
    create_results_directory();

    char filename[MAX_FILENAME];
    snprintf(filename, sizeof(filename), "%s/best_solution_%s.txt", RESULTS_DIR, instance_name);

    FILE *fp = fopen(filename, "w");
    if(fp == NULL) {
        printf("Error: Could not create best solution file %s\n", filename);
        return;
    }

    time_t rawtime;
    struct tm * timeinfo;
    char timestamp[80];

    time(&rawtime);
    timeinfo = localtime(&rawtime);
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", timeinfo);

    fprintf(fp, "=== BEST SOLUTION FOR %s ===\n", instance_name);
    fprintf(fp, "Generated: %s\n", timestamp);
    fprintf(fp, "Number of vertices: %d\n", nodes);
    fprintf(fp, "===============================\n\n");

    fprintf(fp, "SOLUTION PATH:\n");
    for(int i = 0; i < nodes; i++) {
        fprintf(fp, "%d", chromosome->genes[i]);
        if(i < nodes - 1) fprintf(fp, " -> ");
    }
    fprintf(fp, " -> %d (return to start)\n\n", chromosome->genes[0]);

    float total_distance = calculate_actual_distance(chromosome);
    float gap = optimal > 0 ? ((total_distance - optimal) / optimal) * 100.0f : 0.0f;

    fprintf(fp, "SOLUTION QUALITY:\n");
    fprintf(fp, "Found Distance: %.2f\n", total_distance);
    if(optimal > 0) {
        fprintf(fp, "Optimal Distance: %.2f\n", optimal);
        fprintf(fp, "Gap from Optimal: %.2f%%\n", gap);
    }
    fprintf(fp, "Fitness Value: %.6f\n", chromosome->fitness);

    fclose(fp);
#ifdef DEBUG
    printf("Best solution saved to '%s'\n", filename);
#endif
}

int main(int argc, char **argv){
    // Seed random number generator
    srand(time(NULL));

    // Parse command line arguments
    if(argc == 1) {
        // Default batch mode - random graphs
        printf("=== GA TSP COMPREHENSIVE TESTING (RANDOM GRAPHS) ===\n");
        printf("Testing node counts from %d to %d\n", MIN_NODES, MAX_NODES);
        printf("Number of runs per node count: %d\n", NUM_RUNS);
        printf("Base edge weight: %.1f ± %.1f%%\n", BASE_WEIGHT, WEIGHT_VARIATION * 100);
        printf("====================================================\n\n");

        int total_tests = (MAX_NODES - MIN_NODES + 1) * NUM_RUNS;
        TestResult *results = malloc(total_tests * sizeof(TestResult));
        int result_index = 0;

        // Run tests for each node count
        for(int nodes = MIN_NODES; nodes <= MAX_NODES; nodes++) {
            printf("Testing with %d nodes:\n", nodes);

            for(int run = 1; run <= NUM_RUNS; run++) {
#ifdef DEBUG
                printf("  Run %d/%d...", run, NUM_RUNS);
                fflush(stdout);
#endif

                TestResult result = run_genetic_algorithm_random(nodes, run);
                results[result_index++] = result;

                printf("Time: %.4fs, Distance: %.2f, Fitness: %.6f\n",
                       result.execution_time, result.best_distance, result.best_fitness);
            }
            printf("\n");
        }

        // Print comprehensive results
        print_summary_table(results, total_tests);

        // Save to CSV and summary report
        save_results_to_csv(results, total_tests, "ga_tsp_random_results.csv");
        save_summary_report(results, total_tests, "ga_tsp_random_summary.txt", "Random Graph Testing (5-20 nodes)");

        free(results);
    }
    else if(argc >= 2 && strcmp(argv[1], "instance_mode") == 0) {
        // Instance directory mode
        int num_runs = NUM_RUNS; // Default number of runs

        // Check for number of runs argument
        if(argc >= 4 && strcmp(argv[2], "-r") == 0) {
            num_runs = atoi(argv[3]);
            if(num_runs <= 0 || num_runs > 50) {
                printf("Invalid number of runs: %d (must be 1-50)\n", num_runs);
                return 1;
            }
        }

        // Get list of instance files
        char filenames[MAX_INSTANCES][MAX_FILENAME];
        int num_files = get_instance_files(filenames, MAX_INSTANCES);

        if(num_files == 0) {
            printf("No instance files found. Please check the 'instances' directory.\n");
            return 1;
        }

        printf("=== GA TSP INSTANCE MODE ===\n");
        printf("Number of instances: %d\n", num_files);
        printf("Runs per instance: %d\n", num_runs);
        printf("============================\n\n");

        // Allocate results array
        int total_results = num_files * num_runs;
        TestResult *all_results = malloc(total_results * sizeof(TestResult));
        int result_index = 0;

        // Process each instance file
        for(int file_idx = 0; file_idx < num_files; file_idx++) {
            printf("=== Processing Instance %d/%d: %s ===\n",
                   file_idx + 1, num_files, filenames[file_idx]);

            // Read instance
            InstanceData instance = {0};
            if(!read_instance_file(filenames[file_idx], &instance)) {
                printf("Skipping invalid instance file: %s\n\n", filenames[file_idx]);
                continue;
            }

            // Show instance matrix for small problems
            if(instance.num_nodes <= 12) {
                init_dist_matrix_from_instance(&instance);
                print_dist_matrix();
                cleanup_dist_matrix();
            }

            // Run algorithm multiple times for this instance
            printf("Running %d iterations:\n", num_runs);
            for(int run = 1; run <= num_runs; run++) {
#ifdef DEBUG
                printf("  Run %d/%d...", run, num_runs);
                fflush(stdout);
#endif

                TestResult result = run_genetic_algorithm_instance(&instance, run);
                all_results[result_index++] = result;

                printf("Time: %.4fs, Distance: %.1f, Gap: %.2f%%\n",
                       result.execution_time, result.best_distance, result.gap_percentage);
            }

            // Print summary for this instance
            printf("\nSummary for %s:\n", instance.name);
            print_instance_summary_table(&all_results[result_index - num_runs], num_runs);

            // Show best solution for this instance
            if(num_runs > 0) {
                // Find best result for this instance
                int best_idx = result_index - num_runs;
                for(int i = result_index - num_runs + 1; i < result_index; i++) {
                    if(all_results[i].best_distance < all_results[best_idx].best_distance) {
                        best_idx = i;
                    }
                }

                // Re-run to get solution path (quick run for display)
                init_dist_matrix_from_instance(&instance);
                init_population(100);

                for(int i = 0; i < popl_size; i++)
                    fill_randomly_the_chromosome(&population[i]);
                sort_population(population);

                // Quick optimization
                for(int gen = 0; gen < 50; gen++) {
                    selection(population);
                    crossoverV2(population);
                    mutation(population);
                    calculate_population_fitness(population);
                    sort_population(population);
                }

                print_best_solution(population, instance.name, instance.optimal_value);
                save_best_solution(&population[0], instance.name, instance.optimal_value, instance.num_nodes);
            }

            cleanup_instance_data(&instance);
            if(file_idx < num_files - 1) {
                printf("\n");
            } else {
                printf("\n\n");
            }
        }

        // Print comprehensive summary for all instances
        if(result_index > 0) {
            print_all_instances_summary(all_results, result_index);

            // Save comprehensive results
            save_results_to_csv(all_results, result_index, "ga_tsp_all_instances_results.csv");
            save_summary_report(all_results, result_index, "ga_tsp_all_instances_summary.txt", "All Instances Processing");
        }

        free(all_results);
    }
    else if(argc >= 3 && strcmp(argv[1], "-f") == 0) {
        // Single file mode (original functionality)
        const char* filename = argv[2];
        int num_runs = 1;

        // Check for number of runs argument
        if(argc >= 5 && strcmp(argv[3], "-r") == 0) {
            num_runs = atoi(argv[4]);
            if(num_runs <= 0 || num_runs > 100) {
                printf("Invalid number of runs: %d (must be 1-100)\n", num_runs);
                return 1;
            }
        }

        // Read instance
        InstanceData instance = {0};
        if(!read_instance_file(filename, &instance)) {
            return 1;
        }

        // Show instance matrix for small problems
        if(instance.num_nodes <= 12) {
            init_dist_matrix_from_instance(&instance);
            print_dist_matrix();
            cleanup_dist_matrix();
        }

        printf("\n=== RUNNING GA ON INSTANCE %s ===\n", instance.name);
        printf("Number of runs: %d\n", num_runs);
        printf("=====================================\n\n");

        TestResult *results = malloc(num_runs * sizeof(TestResult));

        // Run algorithm multiple times
        for(int run = 1; run <= num_runs; run++) {
            printf("Run %d/%d... ", run, num_runs);
            fflush(stdout);

            TestResult result = run_genetic_algorithm_instance(&instance, run);
            results[run-1] = result;

            printf("Time: %.4fs, Distance: %.2f, Gap: %.2f%%\n",
                   result.execution_time, result.best_distance, result.gap_percentage);
        }

        // Print detailed results
        print_instance_summary_table(results, num_runs);

        // Print best solution details
        if(num_runs > 0) {
            // Find best result
            int best_idx = 0;
            for(int i = 1; i < num_runs; i++) {
                if(results[i].best_distance < results[best_idx].best_distance) {
                    best_idx = i;
                }
            }

            // Re-run the best case to get the solution path
            init_dist_matrix_from_instance(&instance);
            init_population(100);

            for(int i = 0; i < popl_size; i++)
                fill_randomly_the_chromosome(&population[i]);
            sort_population(population);

            // Run a quick optimization to get a good solution for display
            for(int gen = 0; gen < 100; gen++) {
                selection(population);
                crossoverV2(population);
                mutation(population);
                calculate_population_fitness(population);
                sort_population(population);
            }

            print_best_solution(population, instance.name, instance.optimal_value);
            save_best_solution(&population[0], instance.name, instance.optimal_value, instance.num_nodes);
        }

        // Save to CSV and summary report
        char csv_filename[MAX_FILENAME];
        char summary_filename[MAX_FILENAME];
        snprintf(csv_filename, sizeof(csv_filename), "ga_tsp_%s_results.csv", instance.name);
        snprintf(summary_filename, sizeof(summary_filename), "ga_tsp_%s_summary.txt", instance.name);

        save_results_to_csv(results, num_runs, csv_filename);
        save_summary_report(results, num_runs, summary_filename, instance.name);

        cleanup_instance_data(&instance);
        free(results);
    }
    else if(argc == 2 && strcmp(argv[1], "-h") == 0) {
        // Help mode
        print_usage(argv[0]);
        return 0;
    }
    else {
        // Invalid arguments
        printf("Error: Invalid arguments\n");
        print_usage(argv[0]);
        return 1;
    }

    // Final cleanup
    cleanup_population();
    cleanup_dist_matrix();

    printf("\nTesting completed successfully!\n");
    return 0;
}