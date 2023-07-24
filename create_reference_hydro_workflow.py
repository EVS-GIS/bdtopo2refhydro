# coding: utf-8

"""
Workflow to run directly from pyqgis console.
The file 'reference_correction/troncon_hydrographique_cours_d_eau_corr.gpkg|layername=troncon_hydrographique_cours_d_eau_corr' need to be created first with BD TOPO
SELECT * FROM troncon_hydrographique WHERE liens_vers_cours_d_eau IS NOT NULL AND liens_vers_cours_d_eau != '';

Update wd parameter in this file to change all wd param in each file

***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

wd = 'C:/Users/lmanie01/Documents/Gitlab/bdtopo2refhydro/'

# fix_connection_and_direction
fix_connection_and_direction = wd + 'pyqgis_scripts/fix_connection_and_direction.py'
exec(open(fix_connection_and_direction.encode('utf-8')).read())

# fix_connection
fix_connection = wd + 'pyqgis_scripts/fix_connection.py'
exec(open(fix_connection.encode('utf-8')).read())

# fix_direction
fix_direction = wd + 'pyqgis_scripts/fix_direction.py'
exec(open(fix_direction.encode('utf-8')).read())

# fix_modified_geom
fix_modified_geom = wd + 'pyqgis_scripts/fix_modified_geom.py'
exec(open(fix_modified_geom.encode('utf-8')).read())

# fix_suppr_canal
fix_suppr_canal = wd + 'pyqgis_scripts/fix_suppr_canal.py'
exec(open(fix_suppr_canal.encode('utf-8')).read())

# create_exutoire
create_exutoire = wd + 'pyqgis_scripts/create_exutoire.py'
exec(open(create_exutoire.encode('utf-8')).read())