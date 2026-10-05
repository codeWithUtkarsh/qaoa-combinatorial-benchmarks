#ifndef PATH_H
#define PATH_H

#include <vector>

struct Path
{
    std::vector<int> vertices;
    int weight;
    float prd;

    Path() {}

    Path(std::vector<int> vertices, int weight, float prd)
    {
        this->vertices = vertices;
        this->weight = weight;
        this->prd = prd;
    }
};

#endif
