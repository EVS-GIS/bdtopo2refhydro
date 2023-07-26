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

from qgis.core import QgsVectorLayer, QgsVectorFileWriter
import processing

# uncomment if not runned by workflow
# wd = 'C:/Users/lmanie01/Documents/Gitlab/bdtopo2refhydro/'
# inputs = 'inputs/'
# outputs = 'outputs/'

def create_exutoire (creation_exutoire_gpkg, plan_d_eau_layername, frontiere_layername, limite_terre_mer_layername, 
                     output_exutoire_gpkg, plan_d_eau_line_layername, exutoire_layername,
                     buffer_distance: float = 50, crs: str = 'EPSG:2154'):
    """
    Create 'exutoire' layers and save them to a GeoPackage. From plan_d_eau, frontiere and limite_terre_mer prepared layers, 
    create the plan_d_eau_line, the exutoire reference layer and the exutoire reference with buffer.
    The exutoire with bufer is used to select the hydrographic network outlets.

    Parameters:
        creation_exutoire_gpkg (str): The input GeoPackage containing inputs layers.
        plan_d_eau_layername (str): The name of the 'plan_d_eau' layer in the input GeoPackage.
        frontiere_layername (str): The name of the 'frontiere' layer in the input GeoPackage.
        limite_terre_mer_layername (str): The name of the 'limite_terre_mer' layer in the input GeoPackage.
        output_exutoire_gpkg (str): The output GeoPackage.
        plan_d_eau_line_layername (str): The name of the converted 'plan_d_eau' line layer in the output GeoPackage.
        exutoire_layername (str): The name of the final 'exutoire' layer in the output GeoPackage.
        buffer_distance (float, optional): The distance for buffering the 'exutoire' layer. Default is 50.
        crs (str, optional): The Coordinate Reference System (CRS) of the output layers. Default is 'EPSG:2154'.

    Raises:
        IOError: If there is an error to load inputs layers.

    Notes:
        - The function requires QGIS libraries and processing tools to be available.

    Example:
        create_exutoire('input.gpkg', 'plan_d_eau', 'frontiere', 'limite_terre_mer', 'output.gpkg', 'plan_d_eau_line', 'exutoire')
    """

    ### Paths
    exutoire_buffer_layername = f"{exutoire_layername}_buffer{buffer_distance}"
    creation_exutoire_gpkg_path = wd + inputs + creation_exutoire_gpkg
    output_exutoire_gpkg_path = wd + outputs + output_exutoire_gpkg
    # inputs
    plan_d_eau_layer = f"{creation_exutoire_gpkg_path}|layername={plan_d_eau_layername}"
    frontiere_layer = f"{creation_exutoire_gpkg_path}|layername={frontiere_layername}"
    limite_terre_mer_layer = f"{creation_exutoire_gpkg_path}|layername={limite_terre_mer_layername}"
    #outputs
    plan_d_eau_line_layer = f"{output_exutoire_gpkg_path}|layername={plan_d_eau_line_layername}"

    # load layers
    plan_d_eau = QgsVectorLayer(plan_d_eau_layer, plan_d_eau_layername, 'ogr')
    frontiere = QgsVectorLayer(frontiere_layer, frontiere_layername, 'ogr')
    limite_terre_mer = QgsVectorLayer(limite_terre_mer_layer, limite_terre_mer_layername, 'ogr')

    # check inputs layers
    for layer in plan_d_eau, frontiere, limite_terre_mer:
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

    ### processing
    # fix geometries plan_d_eau
    plan_d_eau_fix = processing.run('native:fixgeometries',
                            {'INPUT' : plan_d_eau,
                            'OUTPUT' : 'TEMPORARY_OUTPUT'})['OUTPUT']

    # plan_d_eau to line
    plan_d_eau_line = processing.run('native:polygonstolines',
                { 'INPUT' : plan_d_eau_fix, 
                    'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']

    # save plan_d_eau_line
    saving_gpkg(plan_d_eau_line, plan_d_eau_line_layername, output_exutoire_gpkg, save_selected=False)

    # merge all three layers
    exutoire_no_fix = processing.run('native:mergevectorlayers',
                { 'CRS' : QgsCoordinateReferenceSystem(crs),
                    'LAYERS' : [limite_terre_mer_layer, plan_d_eau_line_layer, frontiere_layer],
                    'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']

    # reset fid field
    with edit(exutoire_no_fix):
        for f in exutoire_no_fix.getFeatures():
            f['fid'] = f.id()
            exutoire_no_fix.updateFeature(f)

    # fix geometries exutoire_no_fix
    exutoire = processing.run('native:fixgeometries',
                            {'INPUT' : exutoire_no_fix,
                            'OUTPUT' : 'TEMPORARY_OUTPUT'})['OUTPUT']

    # save exutoire
    saving_gpkg(exutoire, exutoire_layername, output_exutoire_gpkg_path, save_selected=False)

    # buffer on exutoire
    exutoire_buffer = processing.run('native:buffer',
                                    { 'DISSOLVE' : False, 
                                    'DISTANCE' : buffer_distance, 
                                    'END_CAP_STYLE' : 0, 
                                    'INPUT' : exutoire, 
                                    'JOIN_STYLE' : 0, 
                                    'MITER_LIMIT' : 2, 
                                    'OUTPUT' : 'TEMPORARY_OUTPUT', 
                                    'SEGMENTS' : 5 })['OUTPUT']

    # fix geometries exutoire_buffer
    exutoire_buffer_fix = processing.run('native:fixgeometries',
                            {'INPUT' : exutoire_buffer,
                            'OUTPUT' : 'TEMPORARY_OUTPUT'})['OUTPUT']

    # save exutoire_buffer
    saving_gpkg(exutoire_buffer_fix, exutoire_buffer_layername, output_exutoire_gpkg_path, save_selected=False)

    # script end
    print('exutoire created')
    return

create_exutoire(creation_exutoire_gpkg = 'creation_exutoire.gpkg', 
                plan_d_eau_layername = 'plan_d_eau_selected', 
                frontiere_layername = 'frontiere', 
                limite_terre_mer_layername = 'limite_terre_mer',
                output_exutoire_gpkg = 'exutoire.gpkg', 
                plan_d_eau_line_layername = 'plan_d_eau_line', 
                exutoire_layername = 'exutoire',
                buffer_distance = 50, 
                crs = 'EPSG:2154')