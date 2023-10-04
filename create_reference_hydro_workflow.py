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
    global wd, inputs, outputs
    wd = workdir
    inputs = inputs_folder
    outputs = outputs_folder

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