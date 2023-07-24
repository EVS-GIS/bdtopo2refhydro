# coding: utf-8

"""
From plan_d_eau, frontiere and limite_terre_mer prepared layers, create the plan_d_eau_line, the exutoire reference 
layer and the exutoire reference with buffer.

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

wd = 'C:/Users/lmanie01/Documents/Gitlab/bdtopo2refhydro/'

# variables
buffer_distance = 50
# EPSG
crs = 'EPSG:2154'

### names
# inputs
plan_d_eau_name = 'plan_d_eau_selected'
frontiere_name = 'frontiere'
limite_terre_mer_name = 'limite_terre_mer'
# outputs
plan_d_eau_line_name = 'plan_d_eau_line'
exutoire_name = 'exutoire'
exutoire_buffer_name = f"{'exutoire_buffer'}{buffer_distance}"

# pgkg file exutoire
referentiel_exutoire_gpkg = wd + 'correction_files/reference_exutoire.gpkg'
output_gpkg = wd + 'reference_correction/exutoire.gpkg'

### gpkg layers
# inputs
plan_d_eau_layer = f"{referentiel_exutoire_gpkg}|layername={plan_d_eau_name}"
frontiere_layer = f"{referentiel_exutoire_gpkg}|layername={frontiere_name}"
limite_terre_mer_layer = f"{referentiel_exutoire_gpkg}|layername={limite_terre_mer_name}"
# outputs
plan_d_eau_line_layer = f"{output_gpkg}|layername={plan_d_eau_line_name}"
exutoire_layer = f"{output_gpkg}|layername={exutoire_name}"
exutoire_buffer50_layer = f"{output_gpkg}|layername={exutoire_buffer_name}"

### processing

# load layers
plan_d_eau = QgsVectorLayer(plan_d_eau_layer, plan_d_eau_name, 'ogr')
frontiere = QgsVectorLayer(frontiere_layer, frontiere_name, 'ogr')
limite_terre_mer = QgsVectorLayer(limite_terre_mer_layer, limite_terre_mer_name, 'ogr')

# Check if layers are valid
if not plan_d_eau.isValid() or not frontiere.isValid() or not limite_terre_mer.isValid():
    print('Une des couches n\'a pas été chargée correctement')

# Function to save a layer in an existing gpkg
def saving_gpkg(layer, name, out_path):
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    options.EditionCapability = QgsVectorFileWriter.CanAddNewLayer 
    options.layerName = name
    options.fileEncoding = layer.dataProvider().encoding()
    options.driverName = "GPKG"
    _writer = QgsVectorFileWriter.writeAsVectorFormat(layer, out_path, options)
    print("Update mode")
    if _writer:
            print(name, _writer)
    if _writer[0] == QgsVectorFileWriter.ErrCreateDataSource :
        print("Create mode")
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile #Create mode
        _writer= QgsVectorFileWriter.writeAsVectorFormat(layer, out_path, options)
        if _writer:
                print(name, _writer)

# fix geometries plan_d_eau
plan_d_eau_fix = processing.run('native:fixgeometries',
                        {'INPUT' : plan_d_eau,
                         'OUTPUT' : 'TEMPORARY_OUTPUT'})['OUTPUT']

# plan_d_eau to line
plan_d_eau_line = processing.run('native:polygonstolines',
               { 'INPUT' : plan_d_eau_fix, 
                'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']

# save plan_d_eau_line
saving_gpkg(plan_d_eau_line, plan_d_eau_line_name, output_gpkg)

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
saving_gpkg(exutoire, exutoire_name, output_gpkg)

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
saving_gpkg(exutoire_buffer_fix, exutoire_buffer_name, output_gpkg)

# script end
print('exutoire created')