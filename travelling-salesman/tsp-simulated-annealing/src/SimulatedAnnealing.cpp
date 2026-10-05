#include "SimulatedAnnealing.hpp"
#include <chrono>
#include <cmath>

SimulatedAnnealing::SimulatedAnnealing(GraphMatrix *graph, AlgorithmParams params) : TSPAlgorithm(graph)
{
    this->maxNoImprovementIters = 20000 * graph->getVertexCount();
    this->maxExecutionTime = params.maxExecutionTimeMs;
    this->initialPathMode = params.initialPathMode;
    this->neighborMode = params.neighborMode;
    this->temperatureCoefficient = params.temperatureCoefficient;
    this->coolingRate = params.coolingRate;
}

double SimulatedAnnealing::getAverageEdgeWeight()
{
    double numberOfEdges = graphSize * (graphSize - 1);
    int edgeSum = 0;
    for (int i = 0; i < graphSize; ++i)
    {
        for (int j = 0; j < graphSize; ++j)
        {
            if (i != j)
            {
                edgeSum += graph->getWeight(i, j);
            }
        }
    }
    return edgeSum / numberOfEdges;
}

double SimulatedAnnealing::getEdgeWeightAAD()
{
    const int numberOfEdges = graphSize * (graphSize - 1);
    const double average = getAverageEdgeWeight();

    double deviationSum = 0.0;
    for (int i = 0; i < graphSize; ++i)
    {
        for (int j = 0; j < graphSize; ++j)
        {
            if (i != j)
            {
                deviationSum += abs(average - graph->getWeight(i, j));
            }
        }
    }

    return deviationSum / numberOfEdges;
}

double SimulatedAnnealing::getInitialTemperature()
{
    double averageDeviation = getEdgeWeightAAD();
    return temperatureCoefficient * averageDeviation;
}

Path SimulatedAnnealing::solveTSP()
{

    setInitialPath();

    this->currentPathWeight = getCurrentPathWeight();
    this->initialPathWeight = currentPathWeight;
    this->bestFoundPathWeight = currentPathWeight;
    printImprovement(0, currentPathWeight);

    // printPath(currentPath);
    // printf("Initial path weight: %i\n", currentPathWeight);

    double temperature = getInitialTemperature();

    iteration = 0;
    timer.start();
    do
    {
        temperature = temperature * coolingRate;
        printf("temp: %f\n", temperature);

        getNextPathPermutation();

        if (transitionProbability(temperature) > randomDouble())
        {
            acceptNextPath();
        }
        ++iteration;
        ++noImprovementIters;
    } while (!endCriterionIsMet());
    // printImprovement(0, initialPathWeight);
    printPath(bestFoundPath);

    float prd = getPrd(bestFoundPathWeight);
    std::vector<int> resPath(graphSize);
    for (int i = 0; i < graphSize; ++i)
    {
        resPath[i] = bestFoundPath[i];
    }
    return Path(resPath, bestFoundPathWeight, prd);
}

void SimulatedAnnealing::getNextPathPermutation()
{
    int index1 = 1 + random() % (graphSize - 2);
    int index2 = index1 + 1 + random() % (graphSize - index1 - 1);

    switch (neighborMode)
    {
    case Swap:
        swap(index1, index2);
        break;
    case Invert:
        invert(index1, index2);
        break;
    }
}

double SimulatedAnnealing::transitionProbability(double temperature)
{
    if (nextPathWeight < currentPathWeight)
    {
        return 1.0;
    }
    else
    {
        double p = exp(((double)(currentPathWeight - nextPathWeight)) / temperature);
        return p;
    }
}

void SimulatedAnnealing::acceptNextPath()
{
    copyPath(nextPath, currentPath);
    currentPathWeight = nextPathWeight;

    if (currentPathWeight < bestFoundPathWeight)
    {
        copyPath(currentPath, bestFoundPath);
        bestFoundPathWeight = currentPathWeight;

        // printf("ItersWithoutImprovement: %i\n", itersWithoutImprovement);

        printImprovement(iteration, bestFoundPathWeight);
        noImprovementIters = 0;
    }
}
