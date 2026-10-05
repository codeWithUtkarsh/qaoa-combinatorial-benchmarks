#include "tests.hpp"

#include <iostream>
#include "Timer.hpp"
#include "graphGenerator.hpp"
#include "FileUtils.hpp"
#include "printColor.hpp"
#include "TestResult.hpp"
#include "Path.hpp"
#include "branchAndBound.hpp"

void Tests::fileInstanceTest(GraphMatrix *graph, int iterCount, std::string instanceName, std::string outputPath)
{
    FileUtils::writeInstanceTestHeader(outputPath);
    Timer timer;
    const int startingVertex = 0;

    for (int i = 0; i < iterCount; ++i)
    {
        timer.start();
        Path path = BranchAndBound::execute(graph, startingVertex);
        const unsigned long elapsedTime = timer.getElapsedNs();

        bool isCorrect = path.weight == graph->optimum;

        TestResult testResult(instanceName, elapsedTime, path, isCorrect);

        FileUtils::appendTestResult(outputPath, testResult);
    }
}

void Tests::randomInstanceTest(int minSize, int maxSize, int iterCountPerInstance, int instanceCountPerSize, std::string outputPath)
{
    const int startingVertex = 0;
    FileUtils::writeRandomInstanceTestHeader(outputPath);
    Timer timer;
    GraphMatrix *graph;
    printf("Iteration Per Instance %i, No of Instance %i\n", iterCountPerInstance, instanceCountPerSize);

    for (int vertexCount = minSize; vertexCount <= maxSize; vertexCount++)
    {
        srand(1);
        for (int i = 1; i <= instanceCountPerSize; ++i)
        {
            graph = graphGenerator::getRandom(vertexCount, 10);

            long unsigned totalTime = 0;
            for (int j = 1; j <= iterCountPerInstance; ++j)
            {
                std::string identifier = "sample_" + std::to_string(vertexCount) + "_" + std::to_string(i) + "_" + std::to_string(j);
                timer.start();
                BranchAndBound::execute(graph, startingVertex);

                long unsigned execution_time_for_sample = timer.getElapsedNs();
                FileUtils::appendRandomInstanceTestResult(outputPath, identifier, vertexCount, j, execution_time_for_sample);
            }
            delete graph;
            graph = NULL;
        }
    }
    printf("Done. Saved to file.\n");
}

void Tests::testAlgorithm(std::vector<std::string> instances)
{
    const int startingVertex = 0;

    for (std::string instanceName : instances)
    {
        GraphMatrix *graph;
        graph = FileUtils::loadGraph(instanceName);

        Path path = BranchAndBound::execute(graph, startingVertex);
        const bool correctRes = path.weight == graph->optimum;

        printf("%14s", instanceName.c_str());

        if (correctRes)
        {
            printColor(" PASS\n", GREEN, BOLD, BOLD);
        }
        else
        {
            printColor(" FAIL\n", RED, BOLD, BOLD);
        }

        delete graph;
        graph = NULL;
    }
}
