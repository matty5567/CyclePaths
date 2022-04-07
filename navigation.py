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


def loadData(loc='data.pq'):
    gdf = gpd.read_parquet(loc)

    def cyclingWeight(row):

        weight = 0
        weight += roadWeight[row['RouteHierarchy']]
        weight += row['Length'] / 1000
        weight += row['ElevationGainInDir'] / 10
        weight += row['ElevationGainInOppDir'] / 100

        return weight

    gdf['weight'] = gdf.apply(cyclingWeight, axis=1)

    return gdf




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
        

    gdf = loadData()

    startNode = gdf[gdf['RoadName1'] == startRoad][['StartNodeGraded']].values[0].item()
    endNode   = gdf[gdf['RoadName1'] == endRoad][['EndNodeGraded']].values[0].item()

    if not startNode:
        raise Exception('start not found')

    elif not startNode:
        raise Exception('end not found')

    else:
        print('endpoints found, calculating route ....')


    graph = nx.from_pandas_edgelist(gdf, 'StartNodeGraded', 'EndNodeGraded', ['weight', 'Length'])

        
    dijkstraLengthNodes = nx.dijkstra_path(graph, startNode, endNode, 'Length')
    dijkstraWeightNodes = nx.dijkstra_path(graph, startNode, endNode, 'weight')

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

    
    gdf['dijkstraLengthMask'] = gdf['StartNodeGraded'].isin(dijkstraLengthNodes) & gdf['EndNodeGraded'].isin(dijkstraLengthNodes)
    gdf['dijkstraWeightMask'] = gdf['StartNodeGraded'].isin(dijkstraWeightNodes) & gdf['EndNodeGraded'].isin(dijkstraWeightNodes)

    
    logo_url = 'https://labs.os.uk/public/os-api-branding/v0.1.0/img/os-logo-maps.svg'
    
    m = folium.Map(location=[50.916438, -1.397284],
               min_zoom=7,
               max_zoom=16)

    
    dijkstraLengthOverlay.add_to(m)
    dijkstraWeightOverlay.add_to(m)

    total_bbox = [[gdf.total_bounds[1], gdf.total_bounds[0]], [gdf.total_bounds[3], gdf.total_bounds[2]]]

    m.fit_bounds(total_bbox)

    
    print(f'saving route from {startRoad} to {endRoad} to {OUTPUT_FILE}')
    m.save(OUTPUT_FILE)
    webbrowser.open('file://' + os.path.join(os.getcwd(), OUTPUT_FILE))



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('start', type=str)

    parser.add_argument('end', type=str)

    args = parser.parse_args()

    googleMapsSucks(args.start, args.end)


if __name__ == '__main__':

    SystemExit(main())




    