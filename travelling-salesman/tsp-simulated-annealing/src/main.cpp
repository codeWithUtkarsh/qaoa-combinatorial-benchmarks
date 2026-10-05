#include "main.hpp"

#include <iostream>
#include "graphGenerator.hpp"
#include "FileUtils.hpp"
#include "Timer.hpp"
#include "tests.hpp"
#include "GraphMatrix.hpp"
#include "printColor.hpp"
#include "TSPAlgorithm.hpp"

int main(void)
{
    srand(1);

    ini.SetUnicode();

    SI_Error rc = ini.LoadFile("settings.ini");
    if (rc < 0)
    {
        printf("Could not load 'settings.ini' file\n");
        return 1;
    };

    const std::string mode = ini.GetValue("common", "mode", "UNKNOWN");
    const std::string inputDir = ini.GetValue("common", "input_dir", "./instances");
    const std::string outputDir = ini.GetValue("common", "output_dir", "./results");

    if (mode == "file_instance_test")
    {
        fileInstanceTest(inputDir, outputDir);
    }
    else if (mode == "random_instance_test")
    {
        randomInstanceTest(outputDir);
    }
    else
    {
        printf("Wrong mode value.\n");
        return 1;
    }

    return 0;
}

void fileInstanceTest(std::string inputDir, std::string outputDir)
{
    const int instanceCount = atoi(ini.GetValue("file_instance_test", "number_of_instances", "1"));
    const auto params = getAlorithmParams();

    for (int i = 0; i < instanceCount; i++)
    {
        std::string instanceTag = "instance_" + std::to_string(i);
        printf("\n%s:\n", instanceTag.c_str());

        const std::string instanceName = ini.GetValue(instanceTag.c_str(), "instance", "UNKNOWN");
        const std::string outputFile = ini.GetValue(instanceTag.c_str(), "output", "UNKNOWN");
        const int iterCount = atoi(ini.GetValue(instanceTag.c_str(), "iterations", "1"));

        const std::string inputFilePath = inputDir + "/" + instanceName;
        const std::string outputFilePath = outputDir + "/" + outputFile;

        printf("Input: %s\n", inputFilePath.c_str());
        printf("Output: %s\n", outputFilePath.c_str());
        printf("Iteration count: %i\n\n", iterCount);

        // Wczytanie grafu
        GraphMatrix *graph = FileUtils::loadGraph(inputFilePath);
        if (graph == NULL)
        {
            printf("File not found.\n");
            continue;
        }
        printf("Graph read from file:\n");
        graph->display();

        Tests::fileInstanceTest(graph, iterCount, instanceName, outputFilePath, params);

        printf("Finished.\n");
        printf("Results saved to file.\n");
        delete graph;
    }
}

void randomInstanceTest(std::string outputDir)
{
    printf("Random instance test\n\n");
    const char *tag = "random_instance_test";
    const auto params = getAlorithmParams();

    const int minSize = atoi(ini.GetValue(tag, "min_size", "1"));
    const int maxSize = atoi(ini.GetValue(tag, "max_size", "1"));
    const int instanceCountPerSize = atoi(ini.GetValue(tag, "instance_num_per_size", "1"));
    const int iterCountPerInstance = atoi(ini.GetValue(tag, "iter_num_per_instance", "1"));
    const std::string outputFile = ini.GetValue(tag, "output", "UNKNOWN");

    const std::string outputFilePath = outputDir + "/" + outputFile;

    Tests::randomInstanceTest(minSize, maxSize, iterCountPerInstance, instanceCountPerSize, outputFilePath, params);
}

AlgorithmParams getAlorithmParams()
{
    const char *tag = "algorithm_params";
    InitialPathMode initialPathMode;
    NeighborMode neighborMode;

    int maxExecTimeMs = atoi(ini.GetValue(tag, "max_exec_time_ms", "30000"));

    std::string initialPathModeStr = ini.GetValue(tag, "initial_path_mode", "greedy");
    std::string neighborModeStr = ini.GetValue(tag, "neighbor_mode", "swap");
    float coolingRate = std::stof(ini.GetValue(tag, "cooling_rate", "0.999"));
    float temperatureCoefficient = std::stof(ini.GetValue(tag, "temp_coeff", "100.0"));

    initialPathMode = initialPathModeStr == "greedy" ? Greedy : InOrder;
    neighborMode = neighborModeStr == "swap" ? Swap : Invert;

    auto params = AlgorithmParams(
        maxExecTimeMs,
        initialPathMode,
        neighborMode,
        coolingRate,
        temperatureCoefficient);

    params.print();
    return params;
}
