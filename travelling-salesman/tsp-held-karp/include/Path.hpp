#ifndef PATH_H
#define PATH_H

#include <vector>

struct Path
{
    std::vector<int> vertices;
    int weight;

    Path() {}

    Path(std::vector<int> vertices, int weight)
    {
        this->vertices = vertices;
        this->weight = weight;
    }
};

#endif
