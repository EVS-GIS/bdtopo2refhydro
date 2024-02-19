#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
"This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
-------------------------------------------------------------------------------
"""

from qgis.core import QgsVectorLayer, QgsFeatureRequest

# uncomment if not runned by workflow
# wd = 'C:/Users/lmanie01/Documents/Gitlab/bdtopo2refhydro/'
# inputs = 'inputs/'
# outputs = 'outputs/'
# corr_reseau_hydrographique_gpkg = 'corr_reseau_hydrographique.gpkg'
# troncon_hydrographique_corr_connection_and_dir_ecoulement = 'troncon_hydrographique_corr_connection_and_dir_ecoulement'
# troncon_hydrographique_cours_d_eau_corr_gpkg = 'troncon_hydrographique_cours_d_eau_corr.gpkg'
# troncon_hydrographique_cours_d_eau_corr = 'troncon_hydrographique_cours_d_eau_corr'

def fix_connection_and_direction(source_gpkg, source_layername, cible_gpkg, cible_layername):
    """
    Fix connection and direction on cible layer from source layer.
    Add the features from the source_layer to the cible_layer, then reverse the line.

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

    no_duplicate = processing.run('native:deleteduplicategeometries',
                    {
                        'INPUT' : source,
                        'OUTPUT': 'TEMPORARY_OUTPUT'
                    })['OUTPUT']

    # Get ids from source
    identifiants = []
    for feature in no_duplicate.getFeatures():
        identifiants.append("'" + feature['cleabs'] + "'")

    # check if there are already in the cible
    nomodif = []
    for feature in cible.getFeatures(QgsFeatureRequest().setFilterExpression('"cleabs" IN ({})'.format(','.join(identifiants)))):
        nomodif.append("'" + feature['cleabs'] + "'")
    nouvelle_liste = [id for id in identifiants + nomodif if id not in identifiants or id not in nomodif]
    if not nomodif:
        print('Features id to check, already in the layer to fix ' + str(nomodif))
    else :
        print('no features from the layer to fix, no check needed')

    # Add the features not present in the cible
    with edit(cible):
        # get features from the source 
        for feature in no_duplicate.getFeatures(QgsFeatureRequest().setFilterExpression('"cleabs" IN ({})'.format(','.join(nouvelle_liste)))):
            fet = QgsFeature(feature)
            fet['fid'] = None
            cible.addFeatures([fet])
            print(fet['cleabs'] + ' line added')

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
    print('features fixed : connection and direction')
    return

fix_connection_and_direction(corr_reseau_hydrographique_gpkg, troncon_hydrographique_corr_connection_and_dir_ecoulement, 
                             troncon_hydrographique_cours_d_eau_corr_gpkg, troncon_hydrographique_cours_d_eau_corr)