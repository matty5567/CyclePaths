import pandas as pd
import geopandas as gpd
import networkx as nx
from datetime import datetime
import matplotlib.pyplot as plt
from os_paw.wfs_api import WFS_API
import folium
from folium.plugins import FloatImage
import argparse
import webbrowser
import os
import sys
from functools import cache


OUTPUT_FILE = 'output_map.html'



roadWeight = {
    'Restricted Local Access Road': 0,
    'Minor Road': 10,
    'Local Road': 20,
    'A Road': 100,
    'A Road Primary': 150,
    'B Road': 100,
    'B Road Primary': 150,
    'Restricted Secondary Access Road': 0,
    'Local Access Road': 0,
    'Secondary Access Road': 0,
    'Motorway': 1000
}


gdf = gpd.read_parquet('data_with_estimate.pq')

def cyclingWeight(row):

    weight = 0
    weight += roadWeight[row['RouteHierarchy']]
    weight += row['Length'] / 1000
    weight += row['ElevationGainInDir'] / 10
    weight += row['ElevationGainInOppDir'] / 100

    return weight

gdf['weight'] = gdf.apply(cyclingWeight, axis=1)




@cache
def googleMapsSucks(startRoad, endRoad):

    def roadlink(feature):

        return {'fillColor': '#009ADE',
                'color': '#009ADE',
                'weight': 2,
                'fillOpacity':.3}

    def highlight(feature):

        return {'weight':9,
                'color':'#AF58BA'}

    def dijkstraLowestWeight(feature):

        return {'fillColor': '#00CD6C',
                'color': '#00CD6C',
                'weight': 5,
                'fillOpacity':.3}

    def dijkstraLowestLength(feature):

        return {'fillColor': '#FF1F5B',
                'color': '#FF1F5B',
                'weight': 9,
                'fillOpacity':.3}

    def a_star_heuristic(a, b):
        a_lat  = graph.nodes()[a]['estimateLat']
        a_long = graph.nodes()[a]['estimateLong']

        b_lat  = graph.nodes()[b]['estimateLat']
        b_long = graph.nodes()[b]['estimateLong']

        return ((a_lat - b_lat)**2 + (a_long - b_long)**2)
        

    print("called with: ", startRoad, endRoad, file=sys.stderr)

    startNode = gdf[gdf['RoadName1'] == startRoad][['StartNodeGraded']].values[0].item()
    endNode   = gdf[gdf['RoadName1'] == endRoad][['EndNodeGraded']].values[0].item()

    if not startNode:
        raise Exception('start not found')

    elif not startNode:
        raise Exception('end not found')

    else:
        print('endpoints found, calculating route ....')



    graph = nx.from_pandas_edgelist(gdf, 'StartNodeGraded', 'EndNodeGraded', ['weight', 'Length'])


    series1 = gdf[['estimateLat', 'estimateLong', 'StartNodeGraded']].rename(columns={'StartNodeGraded': 'node'})
    series2 = gdf[['estimateLat', 'estimateLong', 'EndNodeGraded']].rename(columns={'EndNodeGraded': 'node'})

    series = pd.concat((series1, series2), axis=0)

    series = series.drop_duplicates('node')
    series = series.set_index('node')

    series = series.to_dict(orient='index')

    nx.set_node_attributes(graph, series)


        
    dijkstraLengthNodes = nx.astar_path(graph, startNode, endNode, heuristic=a_star_heuristic, weight='Length')
    dijkstraWeightNodes = nx.astar_path(graph, startNode, endNode, heuristic=a_star_heuristic, weight='weight')

    gdf['dijkstraLengthMask'] = gdf['StartNodeGraded'].isin(dijkstraLengthNodes) & gdf['EndNodeGraded'].isin(dijkstraLengthNodes)
    gdf['dijkstraWeightMask'] = gdf['StartNodeGraded'].isin(dijkstraWeightNodes) & gdf['EndNodeGraded'].isin(dijkstraWeightNodes)


    
    dijkstraWeightOverlay = folium.GeoJson(gdf[gdf['dijkstraWeightMask']==True],
                         name='dijkstraWeight',
                         style_function=dijkstraLowestWeight,
                         highlight_function=highlight)

    dijkstraLengthOverlay = folium.GeoJson(gdf[gdf['dijkstraLengthMask']==True],
                         name='dijkstraLength',
                         style_function=dijkstraLowestLength,
                         highlight_function=highlight)


    
    
    m = folium.Map(location=[51.508273,-0.121259],
               min_zoom=12, max_zoom=16)


    end_loc = [graph.nodes()[endNode]['estimateLong'], graph.nodes()[endNode]['estimateLat']]

    folium.Marker(location=end_loc, popup="Waypoint").add_to(m)


    
    dijkstraLengthOverlay.add_to(m)
    dijkstraWeightOverlay.add_to(m)


    m.fit_bounds(graph.nodes()[startNode]['estimateLat'], graph.nodes()[startNode]['estimateLong'], graph.nodes()[endNode]['estimateLat'], graph.nodes()[endNode]['estimateLong'])

    return m
    


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('start', type=str)

    parser.add_argument('end', type=str)

    args = parser.parse_args()

    googleMapsSucks(args.start, args.end)


if __name__ == '__main__':

    SystemExit(main())




    