#include "GraphMatrix.hpp"
#include <string>

#ifndef TESTS_H
#define TESTS_H

namespace Tests
{
    /**
     * @brief Measures algorithm execution time on randomly generated instances
     *
     * @param minVerticesNum Minimum number of vertices (inclusive)
     * @param maxVerticesNum Maximum number of vertices (inclusive)
     * @param iterCount Number of algorithm iterations for each instance size
     */
    void randomInstanceTest(int minVerticesNum, int maxVerticesNum, int iterCount, std::string outputPath);

    // Checks if results are correct for all of the provided instances
    void testAlgorithm(std::vector<std::string> instances);

    /**
     * @brief Tests algorithm, saves results to file
     *
     * @param graph Graph for which to test the algorithm
     * @param iterCount Number of test repetitions
     * @param instanceName Name of the tested instance
     * @param outputPath Path of the results file for single instance test
     **/
    void fileInstanceTest(GraphMatrix *graph, int iterCount, std::string instanceName, std::string outputPath);
};

#endif
