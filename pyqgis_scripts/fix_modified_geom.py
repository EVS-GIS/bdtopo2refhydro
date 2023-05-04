"""
 The script iterates through the features in the target layer with a filter expression to match the 
 identifiers in the source layer. For each matching feature, it extracts its unique identifier, 
 finds the corresponding feature in the source layer, and updates the geometry of the target 
 feature with the geometry of the source feature.
"""

from qgis.core import QgsVectorLayer, QgsFeatureRequest

# Paths to GPKG files
source_gpkg = './correction_files/reference_hydrographique.gpkg|layername=troncon_hydrographique_corr_geom'
cible_gpkg = './correction_files/reference_hydrographique.gpkg|layername=troncon_hydrographique_cours_d_eau_corr'
# Load source and target layers
source_layer = QgsVectorLayer(source_gpkg, 'troncon_hydrographique_corr_geom', 'ogr')
cible_layer = QgsVectorLayer(cible_gpkg, 'troncon_hydrographique_cours_d_eau_corr', 'ogr')

# Check if layers are valid
if not source_layer.isValid() or not cible_layer.isValid():
    print('One or more layers could not be loaded correctly')

# Get identifiers of features in source layer
identifiants = []
for feature in source_layer.getFeatures():
    identifiants.append("'" + feature['cleabs'] + "'")

# Update geometry of target layer using source layer
with edit(cible_layer):
    for feature in cible_layer.getFeatures(QgsFeatureRequest().setFilterExpression('"cleabs" IN ({})'.format(','.join(identifiants)))):
        # Get and modify identifier of the current feature in the target layer
        id = "'" + feature['cleabs'] +"'"
        # Get geometry from source layer that matches the identifier of the current feature in the target layer
        geom = next(source_layer.getFeatures(QgsFeatureRequest().setFilterExpression('"cleabs" IN ({})'.format(id)))).geometry()
        # Update the geometry of the feature
        cible_layer.changeGeometry(feature.id(), geom)
        print(feature['cleabs'] + ' line modified')
