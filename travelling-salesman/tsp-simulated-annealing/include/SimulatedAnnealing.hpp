#ifndef SIMULATED_ANNEALING_HPP
#define SIMULATED_ANNEALING_HPP

#include "GraphMatrix.hpp"
#include <iostream>
#include <utility>
#include <cmath>

#include "TSPAlgorithm.hpp"
#include "Path.hpp"
#include "AlgorithmParams.hpp"

class SimulatedAnnealing : public TSPAlgorithm
{
private:
    float coolingRate;
    float temperatureCoefficient;

    // The iteration number
    int iteration;

    /**
     * @brief Calculates and returns the initial temperature
     *
     * @return The calculated initial temperature
     */
    double getInitialTemperature();

    /**
     * @brief Calculates and returns the average of the graph edge weight
     */
    double getAverageEdgeWeight();

public:
    /**
     * @brief Calculates the average absolute deviation (AAD) of the edge weights of the graph
     *
     * @return The average absolute deviation of egde weights
     */
    double getEdgeWeightAAD();

    /**
     * @brief Construct a new Simulated Annealing object
     *
     * @param graph The graph on which the algorithm is executed.
     */
    SimulatedAnnealing(GraphMatrix *graph, AlgorithmParams params);

    /**
     * @brief Solves the Traveling Salesman Problem using the Simulated Anealing algorithm.
     */
    Path solveTSP();

    /**
     * @brief Gets the new path permutation
     */
    void getNextPathPermutation();

    /**
     * @brief Returns the probability of making the transition from the currentPath to a candidate nextPath
     *
     * @paragraph
     * If the nextPath is shorter then the currentPath, then the probability is 1.0
     * If the nextPath is longer then the currentPath, then the probability is calculated based on the temperature
     *
     * @return The probability of accepting the new solution
     */
    double transitionProbability(double temperature);

    void acceptNextPath();
};

#endif
