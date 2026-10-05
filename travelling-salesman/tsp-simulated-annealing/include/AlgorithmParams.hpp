#ifndef GEN_ALG_PARAMS
#define GEN_ALG_PARAMS

#include <iostream>
#include "TSPAlgorithm.hpp"

struct AlgorithmParams
{
    int maxExecutionTimeMs;
    InitialPathMode initialPathMode;
    NeighborMode neighborMode;
    float coolingRate;
    float temperatureCoefficient;

    AlgorithmParams(){};

    AlgorithmParams(
        int maxExecutionTimeMs,
        InitialPathMode initialPathMode,
        NeighborMode neighborMode,
        float coolingRate,
        float temperatureCoefficient)
    {

        this->maxExecutionTimeMs = maxExecutionTimeMs;
        this->initialPathMode = initialPathMode;
        this->neighborMode = neighborMode;
        this->coolingRate = coolingRate;
        this->temperatureCoefficient = temperatureCoefficient;
    }

    void print()
    {
        std::string initialPathModeStr = initialPathMode == Greedy ? "greedy" : "in order";
        std::string neighborModeStr = neighborMode == Swap ? "swap" : "invert";

        printf("Max execution time: %i\n", maxExecutionTimeMs);
        printf("Initial path mode: %s\n", initialPathModeStr.c_str());
        printf("neighbor mode: %s\n", neighborModeStr.c_str());
        printf("Cooling rate: %.4f\n", coolingRate);
        printf("Temperature coefficient: %.4f\n", temperatureCoefficient);
    }
};

#endif
