#include "branchAndBound.hpp"
#include <climits>

Node::Node(int vertex, int lowerBound, Node *parent)
{
    this->vertex = vertex;
    // this->path = path;
    // this->availableVertices = availableVertices;
    this->lowerBound = lowerBound;
    this->parent = parent;
}

#define VERBOSE false

int *BranchAndBound::minWeights;

GraphMatrix *BranchAndBound::graph;
int BranchAndBound::graphSize;
int BranchAndBound::startingVertex;

int BranchAndBound::upperBound;

int BranchAndBound::firstImprovement;

// Comparison object to order the heap
struct comp
{
    bool operator()(const Node *lhs, const Node *rhs) const
    {
        return lhs->lowerBound > rhs->lowerBound;
    }
};

Path BranchAndBound::execute(GraphMatrix *graph, int startingVertex)
{
    std::priority_queue<Node *, std::vector<Node *>, comp> pq;
    std::vector<Node *> allNodes;
    std::vector<int> bestPath;

    graphSize = graph->getVertexCount();
    minWeights = new int[graphSize];

    // The lower bound of the starting vertex
    int lowerBound = 0;
    for (int i = 0; i < graphSize; ++i)
    {
        int minWeight = INT_MAX;
        for (int j = 0; j < graphSize; ++j)
        {
            if (i != j)
            {
                int weight = graph->getWeight(i, j);
                if (weight < minWeight)
                {
                    minWeight = weight;
                }
            }
        }
        minWeights[i] = minWeight;
        lowerBound += minWeight;
    }

    Node *root = new Node(startingVertex, lowerBound, NULL);
    allNodes.push_back(root);

    int upperBound = INT_MAX;

    // get the lower bound of the path starting at node 0

    // Add root to the list of live nodes
    pq.push(root);

    // Finds a live node with the least cost, adds its children to the list of
    // live nodes, and finally deletes it from the list
    while (!pq.empty())
    {
        Node *node = pq.top();
        pq.pop();

        // Reached the leaf node (last vertex of the path)
        std::unordered_set<int> availableVertices = getAvailableVertices(node);

        if (availableVertices.size() == 0)
        {
            // return to starting city
            // node->path.push_back(0);

            // Lower bound from the last vertex back to the startingVertex
            node->lowerBound = node->lowerBound - minWeights[node->vertex] + graph->getWeight(node->vertex, startingVertex);
            if (node->lowerBound < upperBound)
            {
                // update the upper bound
                upperBound = node->lowerBound;
                bestPath = getPath(node);
            }
        }

        for (int childVertex : availableVertices)
        {
            lowerBound = node->lowerBound - minWeights[node->vertex] + graph->getWeight(node->vertex, childVertex);

            if (lowerBound < upperBound)
            {
                Node *child = new Node(childVertex, lowerBound, node);
                allNodes.push_back(child);
                pq.push(child);
            }
        }
    }
    if (VERBOSE)
    {

        printPath(bestPath);
        printf("weight: %i\n", upperBound);
    }

    delete[] minWeights;
    for (Node *node : allNodes)
    {
        delete node;
    }
    return Path(bestPath, upperBound);
}

void BranchAndBound::printMinWeights()
{
    printf("Min weights: ");
    for (int i = 0; i < graph->getVertexCount(); ++i)
    {
        printf("%i, ", minWeights[i]);
    }
    printf("\n");
}

void BranchAndBound::printPath(std::vector<int> path)
{
    for (int vertex : path)
    {
        printf("%i -> ", vertex);
    }
    printf("\n");
    // printf("%i\n", startingVertex);
}

void BranchAndBound::printImprovement(int weight)
{
    const int optimum = graph->getOptimum();
    const float prd = (100.0 * (weight - optimum)) / optimum;
    printf("%4i %.2f%%\n", weight, prd);
}

std::unordered_set<int> BranchAndBound::getAvailableVertices(Node *node)
{
    std::unordered_set<int> availableVertices;
    // const int graphSize = graph->getVertexCount();
    for (int i = 0; i < graphSize; ++i)
    {
        availableVertices.insert(i);
    }

    while (node != NULL)
    {
        availableVertices.erase(node->vertex);
        node = node->parent;
    }

    return availableVertices;
}

std::vector<int> BranchAndBound::getPath(Node *node)
{
    std::vector<int> path;
    while (node != NULL)
    {
        path.push_back(node->vertex);
        node = node->parent;
    }

    return path;
}
