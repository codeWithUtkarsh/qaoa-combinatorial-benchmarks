#include "FileUtils.hpp"
#include <iostream>
#include <fstream>

GraphMatrix *FileUtils::loadGraph(std::string filePath)
{
    std::ifstream fin(filePath);

    if (!fin)
    {
        return NULL;
    }

    std::string name;
    fin >> name;

    int verticesNum;
    fin >> verticesNum;

    GraphMatrix *graph = new GraphMatrix(verticesNum);
    for (int i = 0; i < verticesNum; i++)
    {
        for (int j = 0; j < verticesNum; j++)
        {
            int weight;
            fin >> weight;
            graph->addEdge(i, j, weight);
        }
    }

    int optimum;
    fin >> optimum;
    graph->setOptimum(optimum);

    fin.close();
    return graph;
}

void FileUtils::writeInstanceTestHeader(std::string filePath)
{
    std::ofstream fout(filePath);

    if (!fout)
        return;

    fout << "Sample_Name, Sample_Execution_Time_ns, Path, Path_Weight, Is_Correct\n";
    fout.close();
}

void FileUtils::appendTestResult(std::string filePath, TestResult testResult)
{
    std::ofstream ofs;

    ofs.open(filePath, std::ios_base::app);

    if (!ofs)
        return;

    ofs << testResult.instanceName
        << ", "
        << testResult.elapsedTime
        << ", "
        << pathToStr(testResult.path.vertices)
        << ", "
        << testResult.path.weight
        << ", "
        << (testResult.isCorrect ? "true" : "false")
        << "\n";

    ofs.close();
}

void FileUtils::appendRandomInstanceTestResult(std::string filePath, std::string identifier,  int vertexCount, int iteration, unsigned long sampleExecutionTime)
{
    std::ofstream ofs;

    ofs.open(filePath, std::ios_base::app);

    if (!ofs)
        return;

    ofs << identifier
        << ", "
        << vertexCount
        << ", "
        << iteration
        << ", "
        << sampleExecutionTime
        << "\n";

    ofs.close();
}

void FileUtils::writeRandomInstanceTestHeader(std::string filePath)
{
    std::ofstream fout(filePath);

    if (!fout)
        return;

    fout << "Sample_Name, No_of_Nodes, Iteration, Sample_Execution_Time_ns\n";
    fout.close();
}

std::string FileUtils::pathToStr(std::vector<int> path)
{
    std::string res;
    for (long unsigned int i = 0; i <= path.size() - 2; i++)
    {
        res += std::to_string(path[i]) + "->";
    }
    res += std::to_string(path[path.size() - 1]);
    return res;
}
