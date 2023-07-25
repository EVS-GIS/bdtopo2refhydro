# coding: utf-8

"""
From the ids of a gpkg layer (source_layer), select the features in the cible_layer and reverse the line direction.

***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from qgis.core import QgsVectorLayer, QgsFeatureRequest

# uncomment if not runned by workflow
# wd = 'C:/Users/lmanie01/Documents/Gitlab/bdtopo2refhydro/'
# inputs = 'inputs/'
# outputs = 'outputs/'

def fix_direction(source_gpkg, source_layername, cible_gpkg, cible_layername):
    """
    Fix direction on cible layer from source layer

    :param source_gpkg: The path of the GeoPackage containing the source layer.
    :type source_gpkg: str

    :param source_layername: The name of the source layer.
    :type source_layername: str

    :param cible_gpkg: The path of the GeoPackage containing the target layer.
    :type cible_gpkg: str

    :param cible_layername: The name of the target layer.
    :type cible_layername: str

    :raises IOError: If the source or target layer fails to load correctly.

    :return: None
    """

    # Paths to files
    source_path = wd + inputs + f"{source_gpkg}|layername={source_layername}"
    cible_path = wd + outputs + f"{cible_gpkg}|layername={cible_layername}"

    source = QgsVectorLayer(source_path, source_layername, 'ogr')
    cible = QgsVectorLayer(cible_path, cible_layername, 'ogr')

    # check 
    for layer in source, cible:
        if not layer.isValid():
            raise IOError(f"{layer} n'a pas été chargée correctement")

    # Get the IDs of the features in the source layer
    identifiants = []
    for feature in source.getFeatures():
        identifiants.append("'" + feature['cleabs'] + "'")

    # Reverse the flow direction for the features in the target layer
    with edit(cible):
        for feature in cible.getFeatures(QgsFeatureRequest().setFilterExpression('"cleabs" IN ({})'.format(','.join(identifiants)))):
            # Get the geometry of the feature
            geom = feature.geometry()
            lines = geom.asPolyline()
            # Reverse the flow direction
            lines.reverse()
            newgeom = QgsGeometry.fromPolylineXY(lines)
            # Update the geometry of the feature
            cible.changeGeometry(feature.id(), newgeom)
            print(feature['cleabs'] + ' line direction inversed')
    
    print('features fixed : direction')
    return

fix_direction('corr_reseau_hydrographique.gpkg', 'troncon_hydrographique_corr_dir_ecoulement', 
              'troncon_hydrographique_cours_d_eau_corr.gpkg', 'troncon_hydrographique_cours_d_eau_corr')