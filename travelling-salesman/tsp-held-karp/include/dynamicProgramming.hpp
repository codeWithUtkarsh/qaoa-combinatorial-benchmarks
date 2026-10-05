#ifndef DYNAMIC_PROGRAMMING_H
#define DYNAMIC_PROGRAMMING_H

#include "GraphMatrix.hpp"
#include <iostream>
#include "Path.hpp"

class DynamicProgramming
{
private:
    /**
     * A 2d array containing the computed results of previous function calls
     * notation: previousResults[setMask][endingVertex]
     * // debug in gdb: e.g. **previousResults@1023@10
     * setMask bit-mask representing a set of vertices
     * endingVertex The ending vertex
     */
    static int **previousResults;
    // The second-to-last vertex to x from set S. Used for constructing the TSP path back at the end
    // predecessor[S][x]
    static int **predecessors;
    static int startingVertex;
    static GraphMatrix *graph;
    static int graphSize;
    static int initialMask;

public:
    /**
     * @brief Finds the shortest Hamiltonian path in the graph using the Branch and Bound algorithm
     * @param graph the graph on which the algorithm will be executed
     * @param startingVertex Index of the starting vertex
     */
    static Path execute(GraphMatrix *graph);

    /**
     * @brief Returns the shortest path from starting vertex, passing through every vertex in the set (setMask) and ending at the endVertex
     * @param setMask bit-mask representing a set of intermediate vertices
     * @param endVertex The ending vertex
     */
    static int heldKarpAlgorithm(int setMask, int endVertex);

    static void initializeValues();

    /**
     * @brief Prints the mask in binary form and as a set of vertices
     * @param mask the mask to print
     */
    static void printMask(int mask);

    static void printPath(int **predecessors, int initialMask, int startingVertex, int graphSize);

    static void printResult(int weight);

    static std::vector<int> getPathVector(int **predecessors, int initialMask, int startingVertex, int graphSize);
};

#endif
