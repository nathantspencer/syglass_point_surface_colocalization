import syglass as sy
import trimesh
import time
import os
import csv
import subprocess
import pathlib

#              ________________________________________________              #
#/=============| Mesh / Counting Point Colocalization Example |=============\#
#|             ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾             |#
#|  Compares the counting points and meshes for a given project and         |#
#|  reports how many points are contained within each mesh.                 |#
#|                                                                          |#
#\==========================================================================/#


def count_points(project):
    
    EXPERIMENT_NAME = project.get_current_experiment()
    projectPath = project.get_path_to_syg_file().string()
    print('')
    print("Extracting project from: " + projectPath)
    # get the list of mesh names, list of counting points
    mesh_names = project.impl.GetMeshNamesAndSizes(EXPERIMENT_NAME)
    counting_points = project.get_counting_points(EXPERIMENT_NAME)

    # iterate through list of meshes
    for mesh_name in mesh_names:
        print('\nProcessing mesh: ' + mesh_name)
        project.impl.ExportMeshOBJs(EXPERIMENT_NAME, mesh_name, 'temp_mesh.obj')
        has_points = False

        # meshes take a second to export—here we wait for them
        while project.impl.GetMeshIOPercentage() != 100.0:
            time.sleep(0.1)
        mesh = trimesh.load('temp_mesh.obj', force='mesh')

        points_in_mesh_list = []
        # check the mesh against each point in each color series
        for series in counting_points:
            points_contained = 0
            for point in counting_points[series]:

                # mesh coordinates are in physical units, so we'll apply the voxel dimensions
                voxel_dimensions = project.get_voxel_dimensions()
                point[0] = point[0] * voxel_dimensions[0]
                point[1] = point[1] * voxel_dimensions[1]
                point[2] = point[2] * voxel_dimensions[2]

                # trimesh expects XYZ points, not ZYX, so we'll swap these axes
                xyz_point = [point[2], point[1], point[0]] 
        
                # check to see whether the point is contained within the current mesh
                if mesh.contains([xyz_point]):
                    points_in_mesh_list.append([series, xyz_point[0], xyz_point[1], xyz_point[2]])
                    points_contained = points_contained + 1

            # print the results for each series/mesh pair
            if points_contained > 0:
                has_points = True
                print(mesh_name + ' contains ' + str(points_contained) + ' ' + series.lower() + ' counting points.')

        # determine if mesh contains points
        if not (has_points):
            print("No counting points found.")
        # if there are points, add to .csv file for mesh from list
        if len(points_in_mesh_list) > 0:
            filename = mesh_name + '.csv'
            project_folder_path = pathlib.Path(projectPath).parent.resolve()
            with open(str(project_folder_path) + '\\' + filename, 'w', newline = '') as f:
                writer = csv.writer(f)
                writer.writerow(['color', 'x', 'y', 'z'])
                writer.writerows(points_in_mesh_list)

    # remove this temporary file that was written earlier
    os.remove('temp_mesh.obj')
    subprocess.run(['explorer', str(project_folder_path)])


def main(args):
    print("Point Surface Colocalization")
    print("-----------------------------")
    print("Compares the counting points and meshes for a given project")
    print("and reports how many points are contained within each mesh.")
    print("-----------------------------")

    projectList = args["selected_projects"]
    if len(projectList) < 1:
        print("Highlight a project before running to select a project!")
    
    if len(projectList) >= 1:
        for project in projectList:
            count_points(project)
