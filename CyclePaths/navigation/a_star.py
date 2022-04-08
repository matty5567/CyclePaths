from heapq import heappop, heappush
from tracemalloc import start
import networkx as nx
from collections import defaultdict
import pandas as pd


def calc_h(graph, a, b):
    a_lat  = graph.nodes()[a]['estimateLat']
    a_long = graph.nodes()[a]['estimateLong']

    b_lat  = graph.nodes()[b]['estimateLat']
    b_long = graph.nodes()[b]['estimateLong']

    return ((a_lat - b_lat)**2 + (a_long - b_long)**2)





def astar_path(graph, startNode, endNode, weight):

    startH = calc_h(graph, startNode, endNode)
    
    open = []

    cameFrom = {}
    closeSet = set()

    gScore = defaultdict(lambda:1000000000, {startNode: 0})
    fScore = defaultdict(lambda:1000000000, {startNode: startH})

    heappush(open, (startH, startNode))

    while True:
        curF, curNode = heappop(open)
        
        if curNode == endNode:
            nodes = set()
            elevations = []
            while curNode in cameFrom:
                nodes.add(curNode)
                nextNode = cameFrom[curNode]
                elevationInDir = graph.get_edge_data(curNode, nextNode)['ElevationGainInDir']
                elevationInOppDir = graph.get_edge_data(curNode, nextNode)['ElevationGainInOppDir']
                elevations.append(elevationInDir - elevationInOppDir)
                curNode = nextNode

            cum_elevations = 0
            total_elevations = []
            for i in elevations[::-1]:
                cum_elevations += i
                total_elevations.append(cum_elevations)

            return nodes, total_elevations

        closeSet.add(curNode)
        for node in graph.neighbors(curNode):
            if node not in closeSet:
                tent_g_score = gScore[curNode] + graph.get_edge_data(curNode, node)[weight]
                if tent_g_score < gScore[node]:
                    cameFrom[node] = curNode
                    gScore[node] = tent_g_score
                    fScore[node] = tent_g_score + calc_h(graph, node, endNode)
                    heappush(open, (fScore[node], node))

    

                




