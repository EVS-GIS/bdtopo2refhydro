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

from qgis.core import QgsVectorLayer

# uncomment if not runned by workflow
# wd = 'C:/Users/lmanie01/Documents/Gitlab/bdtopo2refhydro/'
# outputs = 'outputs/'

# troncon_hydrographique_cours_d_eau_corr_gpkg = 'troncon_hydrographique_cours_d_eau_corr.gpkg'
# troncon_hydrographique_cours_d_eau_corr = 'troncon_hydrographique_cours_d_eau_corr'

# exutoire_gpkg = 'exutoire.gpkg'
# exutoire_buffer_layername = 'exutoire_buffer50'

# troncon_hydrographique_cours_d_eau_corr_suppr_canal = 'troncon_hydrographique_cours_d_eau_corr_suppr_canal'

def fix_suppr_canal_auto(troncon_corr_gpkg, troncon_corr_layername, 
                         exutoire_gpkg, exutoire_buffer_layername, 
                         troncon_corr_suppr_canal_layername):
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
    troncon_corr_gpkg_path = wd + outputs + f"{troncon_corr_gpkg}"
    exutoire_gpkg_path = wd + outputs + f"{exutoire_gpkg}"

    # inputs
    troncon_corr = f"{troncon_corr_gpkg_path}|layername={troncon_corr_layername}"
    exutoire_buffer = f"{exutoire_gpkg_path}|layername={exutoire_buffer_layername}"

    # load layer
    troncon_corr_layer = QgsVectorLayer(troncon_corr, troncon_corr_layername, 'ogr')
    exutoire_buffer_layer = QgsVectorLayer(exutoire_buffer, exutoire_buffer_layername, 'ogr')

    # check 
    for layer in troncon_corr_layer, exutoire_buffer_layer:
        if not layer.isValid():
            raise IOError(f"{layer} n'a pas été chargée correctement")

    # Identify Network Nodes
    print('IdentifyNetworkNodes processing, this could take some time')
    IdentifyNetworkNodes = processing.run('fct:identifynetworknodes', 
        {
            'INPUT': troncon_corr_layer,
            'QUANTIZATION': 100000000,
            'NODES': 'TEMPORARY_OUTPUT',
            'OUTPUT': 'TEMPORARY_OUTPUT'
        })['OUTPUT']
    
    # add indexes
    IdentifyNetworkNodes.dataProvider().createSpatialIndex()
    print('IdentifyNetworkNodes index created')
    exutoire_buffer_layer.dataProvider().createSpatialIndex()
    print('exutoire_buffer_layer index created')

    # extract outlet
    print('extract outlet')
    outlet = processing.run('native:extractbylocation',
        {
            'INPUT' : IdentifyNetworkNodes, 
            'INTERSECT' : exutoire_buffer_layer,
            'PREDICATE' : [0],
            'OUTPUT' : 'TEMPORARY_OUTPUT'
        })['OUTPUT']
    
    # extract y attribut to get a network without canals or ilike
    print('extract network without canals')
    networkNocanal = processing.run('qgis:extractbyexpression',
        {
            'EXPRESSION' : '"nature" NOT LIKE \'Canal\'\nAND "nature" NOT LIKE \'Conduit forcé\'\nAND "nature" NOT LIKE \'Conduit buse\'\nAND "nature" NOT LIKE \'Ecoulement canalisé\'', 
            'INPUT' : IdentifyNetworkNodes, 
            'OUTPUT' : 'TEMPORARY_OUTPUT'
        })['OUTPUT']
    
    # merge outlet and network without canals
    print('merge outlet and network without canals')
    merge_outlet_nocanal = processing.run('native:mergevectorlayers',
        {
            'LAYERS' : [outlet, networkNocanal],
            'CRS' : None,
            'OUTPUT' : 'TEMPORARY_OUTPUT'
        })['OUTPUT']
    
    # remove working fields
    with edit(merge_outlet_nocanal):
        # Find the field indexes of the fields you want to remove
        layer_index = merge_outlet_nocanal.fields().indexFromName("layer")
        path_index = merge_outlet_nocanal.fields().indexFromName("path")
        # Delete the attributes (fields) using the field indexes
        merge_outlet_nocanal.dataProvider().deleteAttributes([layer_index, path_index])
        # Update the fields to apply the changes
        merge_outlet_nocanal.updateFields()

    print('Fix network connection')
    networkConnectFixed = processing.run('fct:fixnetworkconnectivity',
        {
             'FROM_NODE_FIELD' : 'NODEA',
             'TO_NODE_FIELD' : 'NODEB' ,
             'INPUT' : IdentifyNetworkNodes,
             'SUBSET' : merge_outlet_nocanal, 
             'OUTPUT' : 'TEMPORARY_OUTPUT'
        })['OUTPUT']
    
    # remove working fields
    with edit(networkConnectFixed):
        # Find the field indexes of the fields you want to remove
        node_a_index = networkConnectFixed.fields().indexFromName("NODEA")
        node_b_index = networkConnectFixed.fields().indexFromName("NODEB")
        fid_index = networkConnectFixed.fields().indexFromName("fid")
        # Delete the attributes (fields) using the field indexes
        networkConnectFixed.dataProvider().deleteAttributes([fid_index, node_a_index, node_b_index])
        # Update the fields to apply the changes
        networkConnectFixed.updateFields()

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
    
    saving_gpkg(networkConnectFixed, troncon_corr_suppr_canal_layername, troncon_corr_gpkg_path, save_selected=False)

    print('features fixed : suppr canal features')
    return

fix_suppr_canal_auto(troncon_hydrographique_cours_d_eau_corr_gpkg, 
                     troncon_hydrographique_cours_d_eau_corr, 
                     exutoire_gpkg, 
                     exutoire_buffer_layername,
                     troncon_hydrographique_cours_d_eau_corr_suppr_canal)