# coding: utf-8

"""
Remove the feature in the cible layer from the source layer.

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

# Paths to the GPKG files
source_gpkg = wd + 'correction_files/reference_hydrographique.gpkg|layername=troncon_hydrographique_corr_suppr_canal'
cible_gpkg = wd + 'reference_correction/troncon_hydrographique_cours_d_eau_corr.gpkg|layername=troncon_hydrographique_cours_d_eau_corr'

# Load the source and target layers
source_layer = QgsVectorLayer(source_gpkg, 'troncon_hydrographique_corr_suppr_canal', 'ogr')
cible_layer = QgsVectorLayer(cible_gpkg, 'troncon_hydrographique_cours_d_eau_corr', 'ogr')

# Check that the layers were loaded correctly
if not source_layer.isValid() or not cible_layer.isValid():
    print('Une des couches n\'a pas été chargée correctement')

# Get the IDs of the features in the source layer
identifiants = []
for feature in source_layer.getFeatures():
    identifiants.append("'" + feature['cleabs'] + "'")

cible_layer.startEditing()

# filter by cleabs in source
request = QgsFeatureRequest().setFilterExpression('"cleabs" IN ({})'.format(','.join(identifiants)))

# get feature with request
selected_features = [f.id() for f in cible_layer.getFeatures(request)]

# Delete the selected features one by one
if selected_features:
    for feature_id in selected_features:
        cible_layer.deleteFeatures([feature_id])

# Commit the changes
cible_layer.commitChanges()

print('features canal removed')