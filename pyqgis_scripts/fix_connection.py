# coding: utf-8

"""
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
corr_reseau_hydrographique_gpkg = 'corr_reseau_hydrographique.gpkg'
troncon_hydrographique_corr_connection = 'troncon_hydrographique_corr_connection'
troncon_hydrographique_cours_d_eau_corr_gpkg = 'troncon_hydrographique_cours_d_eau_corr.gpkg'
troncon_hydrographique_cours_d_eau_corr = 'troncon_hydrographique_cours_d_eau_corr'



def fix_connection(source_gpkg, source_layername, cible_gpkg, cible_layername):
    """
    Fix connection on cible layer from source layer.
    Add the features from the source_layer to the cible_layer.

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

    # get Ids from source
    identifiants = []
    for feature in source.getFeatures():
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
        for feature in source.getFeatures(QgsFeatureRequest().setFilterExpression('"cleabs" IN ({})'.format(','.join(nouvelle_liste)))):
            fet = QgsFeature(feature)
            fet['fid'] = None
            cible.addFeatures([fet])
            print(fet['cleabs'] + ' line added')
    
    print('features fixed : connection')
    return

fix_connection(corr_reseau_hydrographique_gpkg, troncon_hydrographique_corr_connection, 
               troncon_hydrographique_cours_d_eau_corr_gpkg, troncon_hydrographique_cours_d_eau_corr)
