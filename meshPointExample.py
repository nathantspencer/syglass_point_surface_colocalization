import syglass as sy
import trimesh
import time
import os
import csv
import numpy as np

#              ________________________________________________              #
#/=============| Mesh / Counting Point Colocalization Example |=============\#
#|             ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾             |#
#|  Compares the counting points and meshes for a given project and         |#
#|  reports how many points are contained within each mesh.                 |#
#|                                                                          |#
#|  Note that for now the project must NOT be opened in syGlass when this   |#
#|  script runs. This can later be built into a syGlass plugin, which will  |#
#|  not suffer from this issue.                                             |#
#|                                                                          |#
#\==========================================================================/#

# constants: modify as needed before running the script
EXPERIMENT_NAME = 'test'
#PROJECT_PATH = 'D:/127 dmso MII O_N pb-02-Airyscan Processing-06_project127 dmso MII O_N pb-02-Airyscan Processing-06_project127 dmso MII O_N pb-02-Airyscan Processing-06_project.syg'
PROJECT_PATH = 'C:/Users/emmak/Downloads/HighResMRI_WithMeshes/HighResMRI_WithMeshes/HighResMRISkull_wMeshes.syg'

if __name__ == '__main__':
    
    # get the project object, list of mesh names, list of counting points
    project = sy.get_project(PROJECT_PATH)
    mesh_names = project.impl.GetMeshNamesAndSizes(EXPERIMENT_NAME)
    # TODO: get_counting_points exports the x,y,z coordinates in voxel units from the bottom left corner
    counting_points = project.get_counting_points(EXPERIMENT_NAME)
    num_points = project.get_number_of_counting_points(EXPERIMENT_NAME)
    transformation_matrix = project.get_mesh_transformation_matrix(EXPERIMENT_NAME)
    identity = np.identity(4)
    is_identity = False
    if np.array_equal(transformation_matrix, identity):
        is_identity = True
    inverse_transform_matrix = np.linalg.pinv(transformation_matrix)
    
    # iterate through list of meshes
    for mesh_name in mesh_names:
        print('\nProcessing mesh: ' + mesh_name)
        project.impl.ExportMeshOBJs(EXPERIMENT_NAME, mesh_name, 'temp_mesh.obj')
       
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
                if not is_identity:
                    counting_point_array = np.array([[point[2], point[1], point[0], 1.0]])
                    transposed = np.transpose(counting_point_array)
                    tcounting_point_array = np.dot(inverse_transform_matrix, transposed)
                    x_array = tcounting_point_array[0]
                    y_array = tcounting_point_array[1]
                    z_array = tcounting_point_array[2]
                    xyz_point = [x_array[0], y_array[0], z_array[0]]
                
                # check to see whether the point is contained within the current mesh
                if mesh.contains([xyz_point]):
                    points_in_mesh_list.append([series, xyz_point[0], xyz_point[1], xyz_point[2]])
                    points_contained = points_contained + 1
            
            # print the results for each series/mesh pair
            print(mesh_name + ' contains ' + str(points_contained) + ' ' + series.lower() + ' counting points.')
        
        if len(points_in_mesh_list) > 0:
            filename = mesh_name + '.csv'
            with open(filename, 'w', newline = '') as f:
                writer = csv.writer(f)
                writer.writerow(['color', 'x', 'y', 'z'])
                writer.writerows(points_in_mesh_list)
    
    # remove this temporary file that was written earlier
    os.remove('temp_mesh.obj')