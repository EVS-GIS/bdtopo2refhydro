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

from qgis.core import *
from qgis.core import QgsVectorLayer, QgsVectorFileWriter
import processing

# uncomment if not runned by workflow
# wd = 'C:/Users/lmanie01/Documents/Gitlab/bdtopo2refhydro/'
# inputs = 'inputs/'
# outputs = 'outputs/'

# Paths to files
hydro_corr = wd + outputs + 'troncon_hydrographique_cours_d_eau_corr.gpkg|layername=troncon_hydrographique_cours_d_eau_corr'
exutoire_buffer = wd + outputs + 'exutoire.gpkg|layername=exutoire_buffer50'

# output 
ref_hydro_gpkg = wd + outputs + 'reference_hydrographique.gpkg'
ref_hydro_name = 'reference_hydrographique'
ref_hydro = f"{ref_hydro_gpkg}|layername={ref_hydro_name}"

# load layers
hydro_corr_layer = QgsVectorLayer(hydro_corr, 'troncon_hydrographique_cours_d_eau_corr', 'ogr')
exutoire_buffer_layer = QgsVectorLayer(exutoire_buffer, 'exutoire_buffer50', 'ogr')

# Check if layers are valid
if not hydro_corr_layer.isValid() or not exutoire_buffer_layer.isValid():
    print('Une des couches n\'a pas été chargée correctement')

print('IdentifyNetworkNodes processing, this could take some time')
# Identify Network Nodes
IdentifyNetworkNodes = processing.run('fct:identifynetworknodes', 
    {
        'INPUT': hydro_corr_layer,
        'QUANTIZATION': 100000000,
        'NODES': 'TEMPORARY_OUTPUT',
        'OUTPUT': 'TEMPORARY_OUTPUT'
    })['OUTPUT']
print('IdentifyNetworkNodes created')

# add indexes
IdentifyNetworkNodes.dataProvider().createSpatialIndex()
print('IdentifyNetworkNodes index created')
exutoire_buffer_layer.dataProvider().createSpatialIndex()
print('exutoire_buffer_layer index created')

# uncomment below to see output IdentifyNetworkNodes
# Add the processed layer to the map canvas
# QgsProject.instance().addMapLayer(IdentifyNetworkNodes)
# Refresh the map canvas
# iface.mapCanvas().refresh()

# select by location
processing.run('native:selectbylocation', 
    {
        'INPUT': IdentifyNetworkNodes,
        'INTERSECT': exutoire_buffer_layer,
        'METHOD': 0,  # Créer une nouvelle sélection
        'PREDICATE': [0],  # intersecte
    })
print('IdentifyNetworkNodes selected by exutoire')

# Select Connected Reaches
processing.run('fct:selectconnectedcomponents',  
    {
        'DIRECTION': 2,  # Up/Downstream
        'FROM_NODE_FIELD': 'NODEA',
        'INPUT': IdentifyNetworkNodes,
        'TO_NODE_FIELD': 'NODEB'
    })
print('IdentifyNetworkNodes selected by connected Up/Downstream')

# remove NODEA and NODEB fields
with edit(IdentifyNetworkNodes):
    # Find the field indexes of the fields you want to remove
    node_a_index = IdentifyNetworkNodes.fields().indexFromName("NODEA")
    node_b_index = IdentifyNetworkNodes.fields().indexFromName("NODEB")
    # Delete the attributes (fields) using the field indexes
    IdentifyNetworkNodes.dataProvider().deleteAttributes([node_a_index, node_b_index])
    # Update the fields to apply the changes
    IdentifyNetworkNodes.updateFields()

def saving_gpkg(layer: QgsVectorLayer, name: str, out_path: str, save_selected: bool = False) -> None:
    """
    Save a QGIS vector layer to a GeoPackage (GPKG) file.

    Parameters:
        layer (QgsVectorLayer): The QGIS vector layer to be saved.
        name (str): The name of the layer to be saved within the GeoPackage.
        out_path (str): The output path where the GeoPackage file will be saved.
        save_selected (bool, optional): If True, only the selected features will be saved to the GeoPackage.
            Default is False.

    Raises:
        IOError: If there is an error during the save process.

    Notes:
        - The function saves the provided vector layer to a GeoPackage file at the specified output path.
        - If the GeoPackage file already exists, the function will update the layer with the new data.
        - If the GeoPackage file does not exist, it will be created, and the layer will be saved in it.
        - The 'save_selected' option is useful when you want to save only a subset of the features from the layer.

    Example:
        # Save the 'my_layer' vector layer to 'output.gpkg' with layer name 'my_saved_layer'
        saving_gpkg(my_layer, 'my_saved_layer', 'output.gpkg')

        # Save only the selected features of 'my_layer' to 'output.gpkg' with layer name 'my_saved_layer'
        saving_gpkg(my_layer, 'my_saved_layer', 'output.gpkg', save_selected=True)
    """

    # options.onlySelected = True not working with gpkg
    if save_selected:
        saved_layer = processing.run("native:saveselectedfeatures", {'INPUT': layer, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']
    else:
        saved_layer = layer

    options = QgsVectorFileWriter.SaveVectorOptions()
    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer  # update mode
    options.EditionCapability = QgsVectorFileWriter.CanAddNewLayer
    options.layerName = name
    options.fileEncoding = saved_layer.dataProvider().encoding()
    options.driverName = "GPKG"

    _writer = QgsVectorFileWriter.writeAsVectorFormat(saved_layer, out_path, options)

    # if file and layer exist, overwrite the layer
    if _writer[0] == QgsVectorFileWriter.NoError:
        print("Layer updated successfully.")
    # if file does not exist, switch to create mode
    elif _writer[0] == QgsVectorFileWriter.ErrCreateDataSource:
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile  # create mode
        _writer = QgsVectorFileWriter.writeAsVectorFormat(saved_layer, out_path, options)
        if _writer[0] == QgsVectorFileWriter.NoError:
            print("GeoPackage created successfully.")
        else:
            raise IOError(f"Failed to create GeoPackage: {_writer[1]}")
    else:
        raise IOError(f"Error: {_writer[1]}")

saving_gpkg(IdentifyNetworkNodes, ref_hydro_name, ref_hydro_gpkg, save_selected=True)

print('end : hydrological reference network fixed and connected to sea or lac outlets created in ' + ref_hydro)

