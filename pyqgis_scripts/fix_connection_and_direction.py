# coding: utf-8

"""
Add the features from the source_layer to the cible_layer the reverse the line


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

wd = 'C:/Users/lmanie01/Documents/Gitlab/bdtopo2refhydro/'

# Paths to files
source_gpkg = wd + 'correction_files/reference_hydrographique.gpkg|layername=troncon_hydrographique_corr_connection_and_dir_ecoulement'
cible_gpkg = wd + 'reference_correction/troncon_hydrographique_cours_d_eau_corr.gpkg|layername=troncon_hydrographique_cours_d_eau_corr'

# Load layers
source_layer = QgsVectorLayer(source_gpkg, 'troncon_hydrographique_corr_connection_and_dir_ecoulement', 'ogr')
cible_layer = QgsVectorLayer(cible_gpkg, 'troncon_hydrographique_cours_d_eau_corr', 'ogr')

# Check if layers are valids
if not source_layer.isValid() or not cible_layer.isValid():
    print('Une des couches n\'a pas été chargée correctement')

# Get ids from source_layer
identifiants = []
for feature in source_layer.getFeatures():
    identifiants.append("'" + feature['cleabs'] + "'")

# check if there are already in the cible_layer
nomodif = []
for feature in cible_layer.getFeatures(QgsFeatureRequest().setFilterExpression('"cleabs" IN ({})'.format(','.join(identifiants)))):
    nomodif.append("'" + feature['cleabs'] + "'")
nouvelle_liste = [id for id in identifiants + nomodif if id not in identifiants or id not in nomodif]
if not nomodif:
    print('Features id to check, already in the layer to fix ' + str(nomodif))
else :
    print('no features from the layer to fix, no check needed')

# Add the features not present in the cible_layer
with edit(cible_layer):
    # get features from the source_layer 
    for feature in source_layer.getFeatures(QgsFeatureRequest().setFilterExpression('"cleabs" IN ({})'.format(','.join(nouvelle_liste)))):
        fet = QgsFeature(feature)
        fet['fid'] = None
        cible_layer.addFeatures([fet])
        print(fet['cleabs'] + ' line added')

# Reverse the flow direction for the features in the target layer
with edit(cible_layer):
    for feature in cible_layer.getFeatures(QgsFeatureRequest().setFilterExpression('"cleabs" IN ({})'.format(','.join(identifiants)))):
        # Get the geometry of the feature
        geom = feature.geometry()
        lines = geom.asPolyline()
        # Reverse the flow direction
        lines.reverse()
        newgeom = QgsGeometry.fromPolylineXY(lines)
        # Update the geometry of the feature
        cible_layer.changeGeometry(feature.id(), newgeom)
        print(feature['cleabs'] + ' line direction inversed')