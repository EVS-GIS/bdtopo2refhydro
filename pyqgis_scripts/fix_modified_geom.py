# coding: utf-8

"""
 The script iterates through the features in the target layer with a filter expression to match the 
 identifiers in the source layer. For each matching feature, it extracts its unique identifier, 
 finds the corresponding feature in the source layer, and updates the geometry of the target 
 feature with the geometry of the source feature.

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

def fix_modified_geom(source_gpkg, source_layername, cible_gpkg, cible_layername):
    """
    Fix modified geometries on cible layer from source layer

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

    # Get identifiers of features in source layer
    identifiants = []
    for feature in source.getFeatures():
        identifiants.append("'" + feature['cleabs'] + "'")

    # Update geometry of target layer using source layer
    with edit(cible):
        for feature in cible.getFeatures(QgsFeatureRequest().setFilterExpression('"cleabs" IN ({})'.format(','.join(identifiants)))):
            # Get and modify identifier of the current feature in the target layer
            id = "'" + feature['cleabs'] +"'"
            # Get geometry from source layer that matches the identifier of the current feature in the target layer
            geom = next(source.getFeatures(QgsFeatureRequest().setFilterExpression('"cleabs" IN ({})'.format(id)))).geometry()
            # Update the geometry of the feature
            cible.changeGeometry(feature.id(), geom)
            print(feature['cleabs'] + ' line modified')
        
    print('features fixed : modified geom')
    return

fix_modified_geom('corr_reseau_hydrographique.gpkg', 'troncon_hydrographique_corr_geom', 
                  'troncon_hydrographique_cours_d_eau_corr.gpkg', 'troncon_hydrographique_cours_d_eau_corr')