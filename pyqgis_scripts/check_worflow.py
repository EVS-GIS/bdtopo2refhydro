# coding: utf-8

"""
From plan_d_eau, frontiere and limite_terre_mer prepared layers, create the plan_d_eau_line, the exutoire reference 
layer and the exutoire reference with buffer.

This workflow select the network from the exutoire reference to check if the network is well fixed. 

***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import os
from qgis.core import *
from qgis.core import QgsVectorLayer, QgsVectorFileWriter
import processing

wd = 'C:/Users/lmanie01/Documents/Gitlab/bdtopo2refhydro/'

# Paths to files
hydro_corr = wd + 'reference_correction/reference_hydrographique.gpkg|layername=troncon_hydrographique_cours_d_eau_corr'
exutoire_buffer = wd + 'correction_files/reference_exutoire.gpkg|layername=exutoire_buffer50'

# output 
output = wd + '/outputs/reference_hydrographique.gpkg|layername=IdentifyNetworkNodes_connected'

# load layers
hydro_corr_layer = QgsVectorLayer(hydro_corr, 'troncon_hydrographique_cours_d_eau_corr', 'ogr')
exutoire_buffer_layer = QgsVectorLayer(exutoire_buffer, 'exutoire_buffer50', 'ogr')

# Identify Network Nodes
IdentifyNetworkNodes = processing.run('fct:identifynetworknodes', 
    {
        'INPUT': hydro_corr_layer,
        'QUANTIZATION': 100000000,
        'NODES': 'TEMPORARY_OUTPUT',
        'OUTPUT': 'TEMPORARY_OUTPUT'
    })

# add index

# Add the processed layer to the map canvas
QgsProject.instance().addMapLayer(IdentifyNetworkNodes['OUTPUT'])
# Refresh the map canvas
iface.mapCanvas().refresh()

# select by location
processing.run('native:selectbylocation', 
    {
        'INPUT': IdentifyNetworkNodes['OUTPUT'],
        'INTERSECT': exutoire_buffer_layer,
        'METHOD': 0,  # Créer une nouvelle sélection
        'PREDICATE': [0],  # intersecte
    })

# Select Connected Reaches
processing.run('fct:selectconnectedcomponents',  
    {
        'DIRECTION': 2,  # Up/Downstream
        'FROM_NODE_FIELD': 'NODEA',
        'INPUT': IdentifyNetworkNodes['OUTPUT'],
        'TO_NODE_FIELD': 'NODEB'
    })

layer = IdentifyNetworkNodes['OUTPUT']
# Create the new layer in the GeoPackage
context = QgsProject.instance().transformContext()
options = QgsVectorFileWriter.SaveVectorOptions()
options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
options.layerName = layer.name()
options.fileEncoding = "UTF-8"
options.driverName = "GPKG"

QgsVectorFileWriter.writeAsVectorFormatV2(layer, output, context, options)
