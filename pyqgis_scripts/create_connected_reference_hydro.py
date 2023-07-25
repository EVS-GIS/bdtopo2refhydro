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

def create_connected_reference_hydro(cours_d_eau_corr_gpkg, cours_d_eau_corr_layername, exutoire_gpkg, exutoire_buffer_layername,
                                     reference_hydrographique_gpkg, reference_hydrographique_layername):
    """
    Create a connected reference hydrographic network. The reference hydrographic network is selected by moving upstream from the outlets.

    Parameters:
        cours_d_eau_corr_gpkg (str): Path to the cours d'eau corrected GeoPackage file.
        cours_d_eau_corr_layername (str): Layer name in the cours d'eau corrected GeoPackage.
        exutoire_gpkg (str): Path to the exutoire GeoPackage file.
        exutoire_buffer_layername (str): Exutoire with buffer layer name in the exutoire GeoPackage file.
        reference_hydrographique_gpkg (str): Path to the output reference hydrographique GeoPackage file.
        reference_hydrographique_layername (str): Reference hydrographique layer name in the reference hydrographique GeoPackage.

    Returns:
        None

    Raises:
        IOError: If there is an error to load inputs layers.

    Notes:
        This function creates a connected reference hydrographique network by identifying network nodes,
        selecting connected reaches, and saving the results in a GeoPackage file.

    Example:
        create_connected_reference_hydro('input_cours_d_eau_corr.gpkg', 'cours_d_eau_corr_layer',
                                         'input_exutoire.gpkg', 'exutoire_buffer_layer',
                                         'output_reference_hydro.gpkg', 'reference_hydro_layer')
    """

    ### Paths
    cours_d_eau_corr_gpkg_path = wd + outputs + cours_d_eau_corr_gpkg
    exutoire_gpkg_path = wd + outputs + exutoire_gpkg
    reference_hydrographique_gpkg_path = wd + outputs + reference_hydrographique_gpkg
    # inputs
    cours_d_eau_corr = f"{cours_d_eau_corr_gpkg_path}|layername={cours_d_eau_corr_layername}"
    exutoire_buffer = f"{exutoire_gpkg_path}|layername={exutoire_buffer_layername}"
    # output 
    reference_hydrographique = f"{reference_hydrographique_gpkg_path}|layername={reference_hydrographique_layername}"
    # load layers
    cours_d_eau_corr = QgsVectorLayer(cours_d_eau_corr, cours_d_eau_corr_layername, 'ogr')
    exutoire_buffer_layer = QgsVectorLayer(exutoire_buffer, exutoire_buffer_layername, 'ogr')

    # check inputs layers
    for layer in cours_d_eau_corr, exutoire_buffer_layer:
        if not layer.isValid():
            raise IOError(f"{layer} n'a pas été chargée correctement")
    
    print('IdentifyNetworkNodes processing, this could take some time')
    # Identify Network Nodes
    IdentifyNetworkNodes = processing.run('fct:identifynetworknodes', 
        {
            'INPUT': cours_d_eau_corr,
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

    # select by outlets (exutoire)
    processing.run('native:selectbylocation', 
        {
            'INPUT': IdentifyNetworkNodes,
            'INTERSECT': exutoire_buffer_layer,
            'METHOD': 0,  # Créer une nouvelle sélection
            'PREDICATE': [0],  # intersecte
        })
    print('IdentifyNetworkNodes selected by exutoire')

    # Select Connected Reaches. 
    # Selection by moving upstream (and downstream for some features) to have connected reaches which flow downstream
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

    saving_gpkg(IdentifyNetworkNodes, reference_hydrographique_layername, reference_hydrographique, save_selected=True)

    print('End : hydrological reference network fixed and connected to sea or lac outlets created in ' + reference_hydrographique)
    return

create_connected_reference_hydro(cours_d_eau_corr_gpkg = 'troncon_hydrographique_cours_d_eau_corr.gpkg', 
                                 cours_d_eau_corr_layername = 'troncon_hydrographique_cours_d_eau_corr', 
                                 exutoire_gpkg = 'exutoire.gpkg', 
                                 exutoire_buffer_layername = 'exutoire_buffer50',
                                 reference_hydrographique_gpkg = 'reference_hydrographique.gpkg', 
                                 reference_hydrographique_layername = 'reference_hydrographique')

