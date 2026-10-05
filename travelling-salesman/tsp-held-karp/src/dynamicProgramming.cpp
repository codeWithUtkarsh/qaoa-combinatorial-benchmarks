#include "dynamicProgramming.hpp"
#include <climits>
#include <iostream>

#define VERBOSE false

int **DynamicProgramming::previousResults;
int **DynamicProgramming::predecessors;
int DynamicProgramming::startingVertex;
GraphMatrix *DynamicProgramming::graph;
int DynamicProgramming::graphSize;
int DynamicProgramming::initialMask;

void DynamicProgramming::printMask(int mask)
{
    for (int j = 0; j < graphSize - 1; j++)
    {
        const int bit = (mask >> j) & 1;
        printf("%i", bit);
    }

    printf(" = { ");
    for (int j = 0; j < graphSize - 1; j++)
    {
        if ((mask >> j) & 1)
        {
            printf("%i, ", j);
        }
    }
    printf("}\n");
}

void DynamicProgramming::printResult(int weight)
{
    const int optimum = graph->getOptimum();
    const float prd = (100.0 * (weight - optimum)) / optimum;
    printf("%4i %.2f%%\n", weight, prd);
}

void DynamicProgramming::printPath(int **predecessors, int initialMask, int startingVertex, int graphSize)
{
    int *path = new int[graphSize];
    int mask = initialMask;
    int vertex = startingVertex;
    for (int i = graphSize - 1; i >= 0; --i)
    {
        path[i] = vertex;
        vertex = predecessors[mask][vertex];

        const int vertexMask = 1 << vertex;
        mask = mask ^ vertexMask;
    }

    printf("%i", startingVertex);
    for (int i = 0; i < graphSize; ++i)
    {
        printf(" -> %i", path[i]);
    }
    printf("\n");
    delete[] path;
}

std::vector<int> DynamicProgramming::getPathVector(int **predecessors, int initialMask, int startingVertex, int graphSize)
{
    std::vector<int> path(graphSize);
    int mask = initialMask;
    int vertex = startingVertex;
    for (int i = graphSize - 1; i >= 0; --i)
    {
        path[i] = vertex;
        vertex = predecessors[mask][vertex];

        const int vertexMask = 1 << vertex;
        mask = mask ^ vertexMask;
    }

    return path;
}

Path DynamicProgramming::execute(GraphMatrix *_graph)
{
    graph = _graph;
    graphSize = _graph->getVertexCount();
    startingVertex = graphSize - 1;

    // bitmask representing a set of every vertex except of the last one
    // the last vertex is both the staring and the ending vertex
    initialMask = (1 << (graphSize - 1)) - 1;
    previousResults = new int *[initialMask + 1];
    predecessors = new int *[initialMask + 1];

    for (int i = 0; i <= initialMask; ++i)
    {
        previousResults[i] = new int[graphSize];
        predecessors[i] = new int[graphSize];

        for (int j = 0; j < graphSize; ++j)
        {
            previousResults[i][j] = -1;
        }
    }

    initializeValues();

    const int res = heldKarpAlgorithm(initialMask, startingVertex);
    if (VERBOSE)
    {
        printResult(res);
        printPath(predecessors, initialMask, startingVertex, graphSize);
    }

    std::vector<int> resPath = getPathVector(predecessors, initialMask, startingVertex, graphSize);

    // free memory
    for (int i = 0; i <= initialMask; ++i)
    {
        delete[] previousResults[i];
        delete[] predecessors[i];
    }
    delete[] previousResults;
    delete[] predecessors;

    return Path(resPath, res);
}

void DynamicProgramming::initializeValues()
{
    for (int i = 0; i < graphSize; ++i)
    {
        previousResults[0][i] = graph->getWeight(startingVertex, i);
    }
}

int DynamicProgramming::heldKarpAlgorithm(int setMask, int endVertex)
{
    const int previousResult = previousResults[setMask][endVertex];

    if (previousResult != -1)
    {
        return previousResult;
    }

    // D(S, p) = min_{x in (S-{p})}(D(S-{p}, x) + d(x, p))

    int predecessor;
    int minPathWeight = INT_MAX;
    for (int vertex = 0; vertex < graphSize - 1; ++vertex)
    {
        const int mask = 1 << vertex;
        // If both setMask and mask have '1' on the same spot, this will return true
        // which means that vertex represented by "mask" is present in set represented in "setMask"
        if ((setMask & mask) == mask)
        {
            const int newSetMask = (setMask ^ mask);
            const int pathWeight = heldKarpAlgorithm(newSetMask, vertex) + graph->getWeight(vertex, endVertex);
            if (pathWeight < minPathWeight)
            {
                minPathWeight = pathWeight;
                predecessor = vertex;
            }
        }
    }

    predecessors[setMask][endVertex] = predecessor;
    previousResults[setMask][endVertex] = minPathWeight;
    return minPathWeight;
}
