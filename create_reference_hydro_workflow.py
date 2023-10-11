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

def create_reference_hydro(workdir, script_folder, inputs_folder, outputs_folder) :
    """
    Creates a reference hydrographic network from IGN BD TOPO.

    Parameters:
        workdir (str): The main working directory path.
        script_folder (str): The path to the folder containing the scripts to run.
        inputs_folder (str): The path to the folder containing the input data.
        outputs_folder (str): The path to the folder where the outputs will be saved.

    Returns:
        None

    Raises:
        IOError: If an error occurs while executing any of the scripts.

    Description:
        This function executes a series of scripts in the specified script_folder
        to create a hydrographic network. The function runs the following scripts
        in order:
        - 'fix_connection_and_direction.py'
        - 'fix_connection.py'
        - 'fix_direction.py'
        - 'fix_modified_geom.py'
        - 'fix_suppr_canal.py'
        - 'create_exutoire.py'
        - 'create_connected_reference_hydro.py'

        If any script execution raises an exception, the function will raise an IOError.

        Note: The function assumes that the data file name are not changed and follow the original repository ones.

    Usage:
        >>> create_reference_hydro('/path/to/workdir/', 'scripts/', 'input_data/', 'output_data/')
    """
    # def all global variables to set all the the paths in the script.py file below
    global wd, inputs, outputs, crs

    global troncon_hydrographique_cours_d_eau_corr_gpkg
    global troncon_hydrographique_cours_d_eau_corr
    
    global corr_reseau_hydrographique_gpkg
    global troncon_hydrographique_corr_connection_and_dir_ecoulement
    global troncon_hydrographique_corr_connection
    global troncon_hydrographique_corr_dir_ecoulement
    global troncon_hydrographique_corr_geom
    global troncon_hydrographique_corr_suppr_canal

    global creation_exutoire_gpkg, plan_d_eau_layername, frontiere_layername, limite_terre_mer_layername, plan_d_eau_line_layername

    global exutoire_gpkg, exutoire_layername, exutoire_buffer_layername, buffer_distance
    global reference_hydrographique_gpkg, reference_hydrographique_troncon_layername, reference_hydrographique_segment_layername

    # set folder and crs
    wd = workdir # function params
    inputs = inputs_folder # function params
    outputs = outputs_folder # function params
    crs = 'EPSG:2154'

    # input files and layers
    corr_reseau_hydrographique_gpkg = 'corr_reseau_hydrographique.gpkg'
    troncon_hydrographique_corr_connection_and_dir_ecoulement = 'troncon_hydrographique_corr_connection_and_dir_ecoulement'
    troncon_hydrographique_corr_connection = 'troncon_hydrographique_corr_connection'
    troncon_hydrographique_corr_dir_ecoulement = 'troncon_hydrographique_corr_dir_ecoulement'
    troncon_hydrographique_corr_geom = 'troncon_hydrographique_corr_geom'
    troncon_hydrographique_corr_suppr_canal = 'troncon_hydrographique_corr_suppr_canal'

    creation_exutoire_gpkg = 'creation_exutoire.gpkg'
    plan_d_eau_layername = 'plan_d_eau_selected'
    frontiere_layername = 'frontiere'
    limite_terre_mer_layername = 'limite_terre_mer'
    
    # output file 
    troncon_hydrographique_cours_d_eau_corr_gpkg = 'troncon_hydrographique_cours_d_eau_corr.gpkg' # file created by user to save correction, set the name used.
    troncon_hydrographique_cours_d_eau_corr = 'troncon_hydrographique_cours_d_eau_corr' # layer created by user to save correction, set the name used.

    exutoire_gpkg = 'exutoire.gpkg' # no need to change exutoire
    plan_d_eau_line_layername = 'plan_d_eau_line'
    exutoire_layername = 'exutoire'
    exutoire_buffer_layername = 'exutoire_buffer50'
    buffer_distance = 50

    reference_hydrographique_gpkg = 'reference_hydrographique.gpkg' # change this name to create new output file
    reference_hydrographique_troncon_layername = 'reference_hydrographique_troncon'
    reference_hydrographique_segment_layername = 'reference_hydrographique_segment'


    def run_script(script_name):
        try:
            script_path = workdir + script_folder + script_name
            exec(open(script_path.encode('utf-8')).read())
        except Exception as e:
            error_message = f"Error executing {script_name}: {str(e)}"
            raise IOError(error_message)

    try:
        # fix_connection_and_direction
        print('fix_connection_and_direction')
        run_script('fix_connection_and_direction.py')

        # fix_connection
        print('fix_connection')
        run_script('fix_connection.py')

        # fix_direction
        print('fix_direction')
        run_script('fix_direction.py')

        # fix_modified_geom
        print('fix_modified_geom')
        run_script('fix_modified_geom.py')

        # fix_suppr_canal
        print('fix_suppr_canal')
        run_script('fix_suppr_canal.py')

        # create_exutoire to selected connected reaches to upstream
        print('create_exutoire')
        run_script('create_exutoire.py')

        # create_connected_reference_hydro to create the final reference fixed hydrographic network with connected reaches
        print('create_connected_reference_hydro')
        run_script('create_connected_reference_hydro.py')

    except Exception as e:
        raise IOError(e)

    print("Reference hydrographique successfully created")
    return

create_reference_hydro('C:/Users/lmanie01/Documents/Gitlab/bdtopo2refhydro/',
                       'pyqgis_scripts/',
                       'inputs/',
                       'outputs/')