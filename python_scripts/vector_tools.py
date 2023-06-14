# coding: utf-8

"""
DOCME

***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import fiona
import fiona.crs
from shapely.geometry import shape
from rtree import index
from shapely.geometry import LineString, MultiLineString, mapping
import numpy as np

def FeatureInPolygonWithDistance(linestring_path, polygon_path, output_path, distance_threshold):

    selected_features = []

    # Create spatial index for polygon layer
    polygon_index = index.Index()
    with fiona.open(polygon_path, 'r') as polygon_layer:
        for idx, polygon_feature in polygon_layer.items():
            polygon = shape(polygon_feature['geometry'])
            polygon_index.insert(idx, polygon.bounds)

    # Create spatial index for linestring layer
    linestring_index = index.Index()
    with fiona.open(linestring_path, 'r') as linestring_layer:
        for idx, linestring_feature in linestring_layer.items():
            linestring = shape(linestring_feature['geometry'])
            linestring_index.insert(idx, linestring.bounds)

    with fiona.open(polygon_path, 'r') as polygon_layer, fiona.open(linestring_path, 'r') as linestring_layer:
        options = dict(
                driver=linestring_layer.driver,
                schema=linestring_layer.schema.copy(),
                crs=linestring_layer.crs)

        for polygon_feature in polygon_layer:
            # print(polygon_feature)
            polygon = shape(polygon_feature['geometry'])

            # Get potential linestrings within the bounding box of the polygon
            potential_linestrings = list(linestring_index.intersection(polygon.bounds))

            for linestring_id  in potential_linestrings:
                linestring_feature = linestring_layer[linestring_id]
                # print(linestring_feature)
                linestring = shape(linestring_feature['geometry'])

                if linestring.intersects(polygon):
                    clipped_linestring = linestring.intersection(polygon)
                    linestring_length = clipped_linestring.length
                    if linestring_length > distance_threshold:
                        selected_features.append(linestring_feature)
    
    # Create a new GeoPackage file and write the selected features to it
    with fiona.open(output_path, 'w', **options) as output_layer:
        for feature in selected_features:
            output_layer.write(feature)