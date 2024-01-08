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

def create_5m_width_hydro_network(surface_hydrographique_gpkg,
                                surface_hydrographique_layername,
                                reference_hydrographique_gpkg,
                                reference_hydrographique_layername,
                                reference_hydrographique_5m_gpkg,
                                reference_hydrographique_5m_layername,
                                exutoire_gpkg, 
                                exutoire_buffer_layername,
                                zone_gpkg,
                                zone_layername,
                                small_segment_filter,
                                percent_stream_in_surface):
    """
    Create a hydrological reference network with a 5-meter width based on input hydrographical data.

    Parameters:
        reference_hydrographique_5m_gpkg (str): The name of the GeoPackage file for hydrographical data with a 5-meter width processing.
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
    surface_hydrographique_gpkg_path = wd + outputs + surface_hydrographique_gpkg
    reference_hydrographique_gpkg_path = wd + outputs + reference_hydrographique_gpkg
    reference_hydrographique_5m_gpkg_path = wd + outputs + reference_hydrographique_5m_gpkg
    exutoire_gpkg_path = wd + outputs + exutoire_gpkg

    if zone_gpkg and zone_layername : 
        zone_gpkg_path = wd + outputs + zone_gpkg
        reference_hydrographique_5m_layername = reference_hydrographique_5m_layername + '_' + zone_layername

    # inputs
    surface_hydro = f"{surface_hydrographique_gpkg_path}|layername={surface_hydrographique_layername}"
    ref_hydro = f"{reference_hydrographique_gpkg_path}|layername={reference_hydrographique_layername}"
    exutoire = f"{exutoire_gpkg_path}|layername={exutoire_buffer_layername}"
    if zone_gpkg and zone_layername : 
        zone = f"{zone_gpkg_path}|layername={zone_layername}"

    # load layers
    surface_hydro_layer = QgsVectorLayer(surface_hydro, surface_hydrographique_layername, 'ogr')
    ref_hydro_layer = QgsVectorLayer(ref_hydro, surface_hydrographique_layername, 'ogr')
    exutoire_layer = QgsVectorLayer(exutoire, exutoire_buffer_layername, 'ogr')
    if zone_gpkg and zone_layername : 
        zone_layer = QgsVectorLayer(zone, zone_layername, 'ogr')

    # check inputs layers
    for layer in surface_hydro_layer, ref_hydro_layer, exutoire_layer:
        if not layer.isValid():
            raise IOError(f"{layer} n'a pas été chargée correctement")
    if zone_gpkg and zone_layername : 
        if not zone_layer.isValid():
            raise IOError(f"{zone_layer} n'a pas été chargée correctement")
            
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

    if zone_layer : 

        surface_hydro_layer = processing.run('qgis:extractbylocation', 
        {
            'INPUT' : surface_hydro_layer, 
            'INTERSECT' : zone_layer, 
            'PREDICATE' : [0], # intersect
            'OUTPUT' : 'TEMPORARY_OUTPUT' 
        })['OUTPUT']

        ref_hydro_layer = processing.run('qgis:extractbylocation', 
        {
            'INPUT' : ref_hydro_layer, 
            'INTERSECT' : zone_layer, 
            'PREDICATE' : [0], # intersect
            'OUTPUT' : 'TEMPORARY_OUTPUT' 
        })['OUTPUT']

    # merge all surface features
    surface_hydro_merge = processing.run('native:dissolve', 
        {
            'FIELD' : [], 
            'INPUT' : surface_hydro_layer, 
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
    
    # add indexes
    IdentifyNetworkNodes.dataProvider().createSpatialIndex()
    print('IdentifyNetworkNodes index created')

    IdentifyNetworkNodes.selectAll()
    IdentifyNetworkNodes_copy = processing.run("native:saveselectedfeatures", {'INPUT': IdentifyNetworkNodes, 
                                                                            'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']
    IdentifyNetworkNodes.removeSelection()

    # save output
    saving_gpkg(IdentifyNetworkNodes_copy, "IdentifyNetworkNodes_copy", wd + "work/work_reference_5m_rmc.gpkg", save_selected=False)

    # extract outlet by exutoire, we need final outlet to fix network connectivity
    outlet = processing.run('native:extractbylocation',
        {
            'INPUT' : IdentifyNetworkNodes, 
            'INTERSECT' : exutoire_layer,
            'PREDICATE' : [0],
            'OUTPUT' : 'TEMPORARY_OUTPUT'
        })['OUTPUT']
    
    # save output
    saving_gpkg(outlet, "outlet", wd + "work/work_reference_5m_rmc.gpkg", save_selected=False)
    
    # get only stream with % of their length inside the water surface => percent_stream_in_surface
    pc_length_in_surface_field = 'length_in_surface'

    IdentifyNetworkNodes.dataProvider().addAttributes([QgsField(pc_length_in_surface_field, QVariant.Double)])
    IdentifyNetworkNodes.updateFields()

    IdentifyNetworkNodes.startEditing()

    for linestring_feature in IdentifyNetworkNodes.getFeatures():
            linestring_geometry = linestring_feature.geometry()
            total_length = linestring_geometry.length()

            # Initialize length_within_polygon as -1 to indicate no intersection and remove it
            pc_length_in_surface = -1

            # Iterate over polygon features
            for polygon_feature in surface_hydro_merge.getFeatures():
                polygon_geometry = polygon_feature.geometry()

                # Check if linestring intersects with the polygon
                if linestring_geometry.intersects(polygon_geometry):
                    # Calculate the length of the intersection
                    intersection_geometry = linestring_geometry.intersection(polygon_geometry)
                    length_in_polygon = intersection_geometry.length()
                    pc_length_in_surface = length_in_polygon/total_length*100

                    # Update the length attribute in the linestring layer
                    IdentifyNetworkNodes.dataProvider().changeAttributeValues({linestring_feature.id(): {IdentifyNetworkNodes.fields().indexFromName(pc_length_in_surface_field): pc_length_in_surface}})

                    break  # Exit the inner loop after finding the first intersecting polygon

            # remove if the length inside the water surface is below the setted %
            if pc_length_in_surface < percent_stream_in_surface:
                IdentifyNetworkNodes.dataProvider().deleteFeatures([linestring_feature.id()])

    # Commit changes
    IdentifyNetworkNodes.commitChanges()

    # save output
    saving_gpkg(IdentifyNetworkNodes, "IdentifyNetworkNodes", wd + "work/work_reference_5m_rmc.gpkg", save_selected=False)

    # merge outlet and IdentifyNetworkNodes
    processing.run('etl_load:appendfeaturestolayer',
        { 'ACTION_ON_DUPLICATE' : 1, 
        'SOURCE_FIELD' : 'fid', 
        'SOURCE_LAYER' : outlet,
        'TARGET_FIELD' : 'fid', 
        'TARGET_LAYER' : IdentifyNetworkNodes})
    
    # fix network connectivity
    fixed_network = processing.run('fct:fixnetworkconnectivity', 
        {
            'INPUT' : IdentifyNetworkNodes_copy, 
            'SUBSET' : IdentifyNetworkNodes, 
            'FROM_NODE_FIELD' : 'NODEA', 
            'TO_NODE_FIELD' : 'NODEB',
            'OUTPUT' : 'TEMPORARY_OUTPUT', 
        })['OUTPUT']
    
    # save output
    saving_gpkg(fixed_network, "fixed_network", wd + "work/work_reference_5m_rmc.gpkg", save_selected=False)

    # Measure network from outlet
    print('Measure network from outlet')
    networkMeasureFromOutlet = processing.run('fct:measurenetworkfromoutlet',
        {
            'FROM_NODE_FIELD' : 'NODEA',
            'TO_NODE_FIELD' : 'NODEB',
            'INPUT' : fixed_network, 
            'OUTPUT' : 'TEMPORARY_OUTPUT', 
        })['OUTPUT']

    # save output
    saving_gpkg(networkMeasureFromOutlet, "networkMeasureFromOutlet", wd + "work/work_reference_5m_rmc.gpkg", save_selected=False)
    
    # Hack order
    print('Compute Hack order')
    networkHack = processing.run('fct:hackorder',
        {
            'FROM_NODE_FIELD' : 'NODEA',
            'TO_NODE_FIELD' : 'NODEB',
            'INPUT' : networkMeasureFromOutlet, 
            'IS_DOWNSTREAM_MEAS' : True, 
            'MEASURE_FIELD' : 'MEASURE', 
            'OUTPUT' : 'TEMPORARY_OUTPUT', 
        })['OUTPUT']
    
    # save output
    saving_gpkg(networkHack, "networkHack", wd + "work/work_reference_5m_rmc.gpkg", save_selected=False)
    
    # Strahler order
    print('Compute Strahler order')
    networkStrahler = processing.run('fct:strahlerorder',
        {
            'AXIS_FIELD' : 'HACK', 
            'FROM_NODE_FIELD' : 'NODEA', 
            'TO_NODE_FIELD' : 'NODEB',
            'INPUT' : networkHack, 
            'OUTPUT' : 'TEMPORARY_OUTPUT', 
        })['OUTPUT']
    
    # remove the small strahler rank 1 affluents in strahler rang 3 to avoid small stream in the middle of bigger streams valley bottoms 
    nodea_field = 'NODEA'
    nodeb_field = 'NODEB'
    field_strahler = 'STRAHLER'

    # get strahler 1 streams
    filter_expression_strahler_1 = QgsExpression(f"{field_strahler} = 1")
    filter_strahler_1 = QgsFeatureRequest(filter_expression_strahler_1)
    strahler_1 = networkStrahler.getFeatures(filter_strahler_1)

    # get strahler 3 streams
    filter_expression_strahler_3 = QgsExpression(f"{field_strahler} > 2")
    filter_strahler_3 = QgsFeatureRequest(filter_expression_strahler_3)
    strahler_3 = networkStrahler.getFeatures(filter_strahler_3)

    # create list of feature attributs
    nodeb_list = [(feature[nodeb_field], feature.id(), feature.geometry().length()) for feature in strahler_1]
    nodea_list = [(feature[nodea_field], feature.id(), feature.geometry().length()) for feature in strahler_3]

    # compare the list to get only the connect nodes and strahler stream 1 below the threshold set
    matching_pairs = [(nodeb, id_b, length_b, nodea, id_a, length_a) 
                    for nodeb, id_b, length_b in nodeb_list 
                    for nodea, id_a, length_a in nodea_list 
                    if nodeb == nodea and length_b <= small_segment_filter]

    # keep only the strahler stream 1 id, select and delete them
    matching_ids = set(id_b for _, id_b, _, _, _, _ in matching_pairs)
    networkStrahler.selectByIds(list(matching_ids))
    networkStrahler.startEditing()
    networkStrahler.deleteSelectedFeatures()
    networkStrahler.commitChanges()

    # save output
    saving_gpkg(networkStrahler, "networkStrahler", wd + "work/work_reference_5m_rmc.gpkg", save_selected=False)

    # reaggregate stream after sliver stream  removed
    print('Aggregate reaches to intersection')
    AggregateSegment = processing.run('fct:aggregatestreamsegments',
                                        {
                                        'INPUT': networkStrahler,
                                        'CATEGORY_FIELD' : '',
                                        'COPY_FIELDS' : 'fid',
                                        'FROM_NODE_FIELD' : 'NODEA',
                                        'TO_NODE_FIELD' : 'NODEB',
                                        'OUTPUT' : 'TEMPORARY_OUTPUT'
                                        })['OUTPUT']
    
    # save output
    saving_gpkg(AggregateSegment, "AggregateSegment", wd + "work/work_reference_5m_rmc.gpkg", save_selected=False)
    
    join_aggregate = processing.run('native:joinattributestable',
                                { 
                                    'DISCARD_NONMATCHING' : False, 
                                    'FIELD' : 'fid', 
                                    'FIELDS_TO_COPY' : [], 
                                    'FIELD_2' : 'fid', 
                                    'INPUT' : AggregateSegment, 
                                    'INPUT_2' : networkStrahler, 
                                    'METHOD' : 1, 
                                    'OUTPUT' : 'TEMPORARY_OUTPUT', 
                                    'PREFIX' : 'join_' 
                                    })['OUTPUT']
    
    # save output
    saving_gpkg(join_aggregate, "join_aggregate", wd + "work/work_reference_5m_rmc.gpkg", save_selected=False)
    
    # rename fields
    with edit(join_aggregate):
        for field in join_aggregate.fields():
            # Check if the field name starts with "join_"
            if field.name().startswith('join_'):
                new_field_name = field.name()[5:]  # Remove the first 5 characters ("join_")
                idx = join_aggregate.fields().indexFromName(field.name())
                join_aggregate.renameAttribute(idx, new_field_name)

    fields_to_remove = ["fid", "join_fid", 
                        "NODEA", "join_NODEA", 
                        "NODEB", "join_NODEB",
                        "MEASURE", "length_in_surface",
                        "LENGTH", "join_LENGTH",
                        "GID",
                        "CATEGORY",
                    "AXIS", "LAXIS"]

    # remove fields
    field_indexes = {field_name: join_aggregate.fields().indexFromName(field_name) for field_name in fields_to_remove}

    with edit(join_aggregate):
        # Delete the attributes (fields) using the field indexes
        join_aggregate.dataProvider().deleteAttributes(list(field_indexes.values()))
        
        # Update the fields to apply the changes
        join_aggregate.updateFields()

    # add a new length field
    with edit(join_aggregate):
        new_field = QgsField("length", QVariant.Double)
        join_aggregate.dataProvider().addAttributes([new_field])
        join_aggregate.updateFields()

        length_index = join_aggregate.fields().indexFromName("length")

        for feature in join_aggregate.getFeatures():
            length = feature.geometry().length()
            
            join_aggregate.dataProvider().changeAttributeValues({feature.id(): {length_index: length}})

    join_aggregate.commitChanges()

    # save output
    saving_gpkg(join_aggregate, reference_hydrographique_5m_layername, reference_hydrographique_5m_gpkg_path, save_selected=False)

    print('End : hydrological reference network 5m from hydrographic surface created')

    return

create_5m_width_hydro_network(surface_hydrographique_gpkg = 'surface_hydrographique_naturel_retenue.gpkg',
                              surface_hydrographique_layername = 'surface_hydrographique_naturel_retenue',
                              reference_hydrographique_gpkg = 'reference_hydrographique.gpkg',
                              reference_hydrographique_layername = 'reference_hydrographique_segment',
                              reference_hydrographique_5m_gpkg = 'reference_hydrographique_5m.gpkg',
                              reference_hydrographique_5m_layername = 'reference_hydrographique_segment_5m',
                              exutoire_gpkg = 'exutoire.gpkg', 
                              exutoire_buffer_layername = 'exutoire_buffer50',
                              zone_gpkg = 'zone.gpkg',
                              zone_layername = 'rmc',
                              small_segment_filter = 500,
                              percent_stream_in_surface = 30)
