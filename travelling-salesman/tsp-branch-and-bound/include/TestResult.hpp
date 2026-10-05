#ifndef TEST_RES_H
#define TEST_RES_H

#include <string>
#include "Path.hpp"

struct TestResult
{
    std::string instanceName;
    unsigned long elapsedTime;
    Path path;
    bool isCorrect;

    TestResult(std::string instanceName, unsigned long elapsedTime, Path path, bool isCorrect)
    {
        this->instanceName = instanceName;
        this->elapsedTime = elapsedTime;
        this->path = path;
        this->isCorrect = isCorrect;
    }
};

#endif
