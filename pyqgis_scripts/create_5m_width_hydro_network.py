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

from qgis.core import *
from qgis.core import QgsVectorLayer, QgsVectorFileWriter
import processing

# uncomment if not runned by workflow
wd = 'C:/Users/lmanie01/Documents/Gitlab/bdtopo2refhydro/'
outputs = 'outputs/'

def create_5m_width_hydro_network(hydrographie_cours_d_eau_5m_gpkg, surface_hydrographique_layername, reference_hydrographique_layername,
                                  reference_hydrographique_gpkg, reference_hydrographique_5m_layername):
    """
    Create a hydrological reference network with a 5-meter width based on input hydrographical data.

    Parameters:
        hydrographie_cours_d_eau_5m_gpkg (str): The name of the GeoPackage file for hydrographical data with a 5-meter width processing.
        surface_hydrographique_layername (str): The name of the surface layer.
        reference_hydrographique_layername (str): The name of the reference hydrographical network layer.
        reference_hydrographique_gpkg (str): The name of the reference hydrographical network GeoPackage.
        reference_hydrographique_5m_layername (str): The name of the layer for the 5-meter width hydrological reference network.

    Raises:
        IOError: Raised if there is an error during the save process.

    Notes:
        - This function processes hydrographical data to create a hydrological reference network with a 5-meter width.
        - It uses various QGIS processing algorithms to perform geospatial operations.
        - The 'saving_gpkg' function is used to save QGIS vector layers to a GeoPackage file.
          It can save the entire layer or only the selected features.
        - The GeoPackage file will be created if it does not exist, and it will be updated if it already exists.
        - The 'save_selected' parameter in 'saving_gpkg' allows you to save only selected features if set to True.

    Example:
        # Calling the create_5m_width_hydro_network function
        create_5m_width_hydro_network(
            "hydrographie.gpkg",
            "surface_hydro_layer",
            "reference_hydro_layer",
            "reference_hydro.gpkg",
            "hydro_reference_5m"
        )
    """

    ### Paths
    surface_hydrographique_gpkg_path = wd + outputs + hydrographie_cours_d_eau_5m_gpkg
    reference_hydrographique_gpkg_path = wd + outputs + reference_hydrographique_gpkg
    # inputs
    surface_hydro = f"{surface_hydrographique_gpkg_path}|layername={surface_hydrographique_layername}"
    ref_hydro = f"{surface_hydrographique_gpkg_path}|layername={reference_hydrographique_layername}"
    # load layers
    surface_hydro_layer = QgsVectorLayer(surface_hydro, surface_hydrographique_layername, 'ogr')
    ref_hydro_layer = QgsVectorLayer(ref_hydro, surface_hydrographique_layername, 'ogr')

    # check inputs layers
    for layer in surface_hydro_layer, ref_hydro_layer:
        if not layer.isValid():
            raise IOError(f"{layer} n'a pas été chargée correctement")
    
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
    
    ### Processing

    # merge all surface features
    surface_hydro_merge = processing.run('native:dissolve', 
        {
            'FIELD' : [], 
            'INPUT' : surface_hydro_layer, 
            'OUTPUT' : 'TEMPORARY_OUTPUT'
        })['OUTPUT']
    
    # buffer surface by 10m
    surface_hydro_buffer = processing.run('native:buffer', 
        {
            'DISSOLVE' : False, 
            'DISTANCE' : 10, 
            'END_CAP_STYLE' : 0, 
            'INPUT' : surface_hydro_merge, 
            'JOIN_STYLE' : 0, 
            'MITER_LIMIT' : 2, 
            'SEGMENTS' : 5,
            'OUTPUT' : 'TEMPORARY_OUTPUT' 
        })['OUTPUT']

    # Identified network nodes on reference hydro segment
    print('IdentifyNetworkNodes processing, this could take some time')
    IdentifyNetworkNodes = processing.run('fct:identifynetworknodes', 
        {
            'INPUT': ref_hydro_layer,
            'QUANTIZATION': 100000000,
            'NODES': 'TEMPORARY_OUTPUT',
            'OUTPUT': 'TEMPORARY_OUTPUT'
        })['OUTPUT']

    # extract network by location
    hydro_in_surface = processing.run('qgis:extractbylocation', 
        {
            'INPUT' : IdentifyNetworkNodes, 
            'INTERSECT' : surface_hydro_buffer, 
            'PREDICATE' : [6], # "est à l'intérieur de" (are within)
            'OUTPUT' : 'TEMPORARY_OUTPUT' 
        })['OUTPUT']
    
    # fix network connectivity
    fixed_network = processing.run('fct:fixnetworkconnectivity', 
        {
            'INPUT' : IdentifyNetworkNodes, 
            'SUBSET' : hydro_in_surface, 
            'FROM_NODE_FIELD' : 'NODEA', 
            'TO_NODE_FIELD' : 'NODEB',
            'OUTPUT' : 'TEMPORARY_OUTPUT', 
        })['OUTPUT']
    
    # remove working fields
    with edit(fixed_network):
        # Find the field indexes of the fields you want to remove
        gid_index = fixed_network.fields().indexFromName("GID")
        length_index = fixed_network.fields().indexFromName("LENGTH")
        category_index = fixed_network.fields().indexFromName("CATEGORY")
        node_a_index = fixed_network.fields().indexFromName("NODEA")
        node_b_index = fixed_network.fields().indexFromName("NODEB")
        # Delete the attributes (fields) using the field indexes
        fixed_network.dataProvider().deleteAttributes([gid_index, length_index, category_index, node_a_index, node_b_index])
        # Update the fields to apply the changes
        fixed_network.updateFields()
    
    # Identify Network Nodes
    print('New IdentifyNetworkNodes processing, this could take some time')
    NewIdentifyNetworkNodes = processing.run('fct:identifynetworknodes', 
    {
        'INPUT': fixed_network,
        'QUANTIZATION': 100000000,
        'NODES': 'TEMPORARY_OUTPUT',
        'OUTPUT': 'TEMPORARY_OUTPUT'
    })['OUTPUT']
    
    
    # Aggregate reaches to intersection
    fields = NewIdentifyNetworkNodes.fields()
    field_names = [field.name() for field in fields if field.name() not in ['NODEA', 'NODEB']] # get all fields but NODEA and NODEB in a list to copy it
    print('Aggregate reaches to intersection')
    # need this trick with QgsProcessingFeatureSourceDefinition(NewIdentifyNetworkNodes.source()) 
    # to avoid unsolved error AttributeError: 'NoneType' object has no attribute 'getFeature' with AggregateSegment
    QgsProject.instance().addMapLayer(NewIdentifyNetworkNodes)

    AggregateSegment = processing.run('fct:aggregatestreamsegments',
                                     {
                                        'INPUT': QgsProcessingFeatureSourceDefinition(NewIdentifyNetworkNodes.source()),
                                        'CATEGORY_FIELD' : '',
                                        'COPY_FIELDS' : field_names,
                                        'FROM_NODE_FIELD' : 'NODEA',
                                        'TO_NODE_FIELD' : 'NODEB',
                                        'OUTPUT' : 'TEMPORARY_OUTPUT'
                                     })['OUTPUT']

    QgsProject.instance().removeMapLayer(NewIdentifyNetworkNodes)

     # remove working fields
    with edit(AggregateSegment):
        # Find the field indexes of the fields you want to remove
        gid_index = AggregateSegment.fields().indexFromName("GID")
        length_index = AggregateSegment.fields().indexFromName("LENGTH")
        category_index = AggregateSegment.fields().indexFromName("CATEGORY")
        node_a_index = AggregateSegment.fields().indexFromName("NODEA")
        node_b_index = AggregateSegment.fields().indexFromName("NODEB")
        # Delete the attributes (fields) using the field indexes
        AggregateSegment.dataProvider().deleteAttributes([gid_index, length_index, category_index, node_a_index, node_b_index])
        # Update the fields to apply the changes
        AggregateSegment.updateFields()

    # save output
    saving_gpkg(AggregateSegment, reference_hydrographique_5m_layername, reference_hydrographique_gpkg_path, save_selected=False)

    print('End : hydrological reference network 5m from hydrographic surface created')

    return

create_5m_width_hydro_network(hydrographie_cours_d_eau_5m_gpkg = 'hydrographie_cours_d_eau_5m.gpkg', 
                              surface_hydrographique_layername = 'surface_hydrographique_naturel_retenue', 
                              reference_hydrographique_layername = 'reference_hydrographique_segment_zone',
                              reference_hydrographique_gpkg = 'reference_hydrographique.gpkg', 
                              reference_hydrographique_5m_layername = 'reference_hydrographique_5m_isere')


