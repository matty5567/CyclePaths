import geopandas as gpd
import networkx as nx
import folium
from flask import redirect
import argparse
import os
import sys
from functools import cache
from CyclePaths.navigation.a_star import astar_path
import pandas as pd
import altair as alt

os.system('gsutil cp gs://os-road-data-hackathon/data_with_estimate.pq .')
gdf = gpd.read_parquet('data_with_estimate.pq')


@cache
def googleMapsSucks(startRoad, endRoad, dangerLevel):

    def cyclingWeight(row):

        roadWeight = {
            'Restricted Local Access Road': 0,
            'Minor Road': 1,
            'Local Road': 2,
            'A Road': 100,
            'A Road Primary': 150,
            'B Road': 100,
            'B Road Primary': 150,
            'Restricted Secondary Access Road': 0,
            'Local Access Road': 0,
            'Secondary Access Road': 0,
            'Motorway': 1000
        }

        weight = 0
        weight += roadWeight[row['RouteHierarchy']] * (10/dangerLevel)
        weight += row['Length'] * (1/(10-dangerLevel))
        return weight


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

    if not startNode or not endNode:
        return redirect("/", code=302)


    gdf['weight'] = gdf.apply(cyclingWeight, axis=1)

    graph = nx.from_pandas_edgelist(gdf, 'StartNodeGraded', 'EndNodeGraded', ['weight', 'Length', 'ElevationGainInDir', 'ElevationGainInOppDir'])

    series1 = gdf[['estimateLat', 'estimateLong', 'StartNodeGraded']].rename(columns={'StartNodeGraded': 'node'})
    series2 = gdf[['estimateLat', 'estimateLong', 'EndNodeGraded']].rename(columns={'EndNodeGraded': 'node'})

    series = pd.concat((series1, series2), axis=0)

    series = series.drop_duplicates('node')
    series = series.set_index('node')

    series = series.to_dict(orient='index')

    nx.set_node_attributes(graph, series)


    m = folium.Map(location=[51.508273,-0.121259],
               min_zoom=12, max_zoom=16)

    if dangerLevel > 6:
        
        dijkstraLengthNodes, elevations = astar_path(graph, startNode, endNode, weight='Length')
        gdf['dijkstraLengthMask'] = gdf['StartNodeGraded'].isin(dijkstraLengthNodes) & gdf['EndNodeGraded'].isin(dijkstraLengthNodes)

        dijkstraLengthOverlay = folium.GeoJson(gdf[gdf['dijkstraLengthMask']==True],
                         name='dijkstraLength',
                         style_function=dijkstraLowestLength,
                         highlight_function=highlight)

        dijkstraLengthOverlay.add_to(m)

        total_journey_length = gdf[gdf['dijkstraLengthMask']==True]['Length'].sum() / 1000

    else:

        dijkstraWeightNodes, elevations = astar_path(graph, startNode, endNode, weight='weight')

        gdf['dijkstraWeightMask'] = gdf['StartNodeGraded'].isin(dijkstraWeightNodes) & gdf['EndNodeGraded'].isin(dijkstraWeightNodes)

        journeyNodes = gdf[gdf['dijkstraWeightMask']==True]

        dijkstraWeightOverlay = folium.GeoJson(journeyNodes,
                            name='dijkstraWeight',
                            style_function=dijkstraLowestWeight,
                            highlight_function=highlight)

    
        dijkstraWeightOverlay.add_to(m)

        total_journey_length = gdf[gdf['dijkstraWeightMask']==True]['Length'].sum() / 1000


    x_label = f'distance: {round(total_journey_length, 2)}km'

    elevations_df = pd.DataFrame(elevations, columns=['Elavation'])
    elevations_df['x'] = elevations_df.index

    print(elevations_df)


    chart = alt.Chart(elevations_df).mark_line().encode(x=alt.X('x', axis=alt.Axis(title=x_label)),y='Elavation')

    chart.save('chart.html')
    chart = chart.to_json()

    end_loc = [graph.nodes()[endNode]['estimateLong'], graph.nodes()[endNode]['estimateLat']]


    folium.Marker(location=end_loc, popup=folium.Popup(max_width=450).add_child(folium.VegaLite(chart, width=450, height=250))).add_to(m)


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




    