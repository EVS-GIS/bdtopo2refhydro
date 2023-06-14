from vector_tools import FeatureInPolygonWithDistance
from config.config import paths_config, parameters_config

# parameters
paths = paths_config()
params = parameters_config()

FeatureInPolygonWithDistance(paths['reference_hydrographique_identified_nodes'], 
                           paths['surface_hydrographique_ecoulement_naturel'], 
                           paths['reference_hydrographique_identified_nodes_output'],
                           300)