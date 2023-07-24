# coding: utf-8

"""
Workflow to run directly from pyqgis console.
The file 'reference_correction/troncon_hydrographique_cours_d_eau_corr.gpkg|layername=troncon_hydrographique_cours_d_eau_corr' need to be created first with BD TOPO
SELECT * FROM troncon_hydrographique WHERE liens_vers_cours_d_eau IS NOT NULL AND liens_vers_cours_d_eau != '';

Update wd parameter in each script and in this file before running

***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

wd = 'C:/Users/lmanie01/Documents/Gitlab/bdtopo2refhydro/pyqgis_scripts/'

# fix_connection_and_direction
exec(open(wd + 'fix_connection_and_direction.py'.encode('utf-8')).read())

# fix_connection
exec(open(wd + 'fix_connection.py'.encode('utf-8')).read())

# fix_direction
exec(open(wd + 'fix_direction.py'.encode('utf-8')).read())

# fix_modified_geom
exec(open(wd + 'fix_modified_geom.py'.encode('utf-8')).read())

# fix_suppr_canal
exec(open(wd + 'fix_suppr_canal.py'.encode('utf-8')).read())