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
# troncon_hydrographique_corr_suppr_canal_multichenal = 'troncon_hydrographique_corr_suppr_canal_multichenal'
# troncon_hydrographique_cours_d_eau_corr_gpkg = 'troncon_hydrographique_cours_d_eau_corr.gpkg'
# troncon_hydrographique_cours_d_eau_corr = 'troncon_hydrographique_cours_d_eau_corr'


def fix_suppr_canal_multichenal(source_gpkg, source_layername, cible_gpkg, cible_layername):
    """
    Fix modified geometries on cible layer from source layer.
    Remove the feature in the cible layer from the source layer.

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

    # Get the IDs of the features in the source layer
    identifiants = []
    for feature in no_duplicate.getFeatures():
        identifiants.append("'" + feature['cleabs'] + "'")

    cible.startEditing()

    # filter by cleabs in source
    request = QgsFeatureRequest().setFilterExpression('"cleabs" IN ({})'.format(','.join(identifiants)))

    # get feature with request
    selected_features = [f.id() for f in cible.getFeatures(request)]

    # Delete the selected features one by one
    if selected_features:
        for feature_id in selected_features:
            cible.deleteFeatures([feature_id])

    # Commit the changes
    cible.commitChanges()

    print('features fixed : suppr canal and multichenal features')
    return

fix_suppr_canal_multichenal(corr_reseau_hydrographique_gpkg, troncon_hydrographique_corr_suppr_canal_multichenal, 
                            troncon_hydrographique_cours_d_eau_corr_gpkg, troncon_hydrographique_cours_d_eau_corr)