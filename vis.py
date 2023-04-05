import numpy as np
from open3d import *    

def main():
    cloud = io.read_point_cloud("C:/Users/rteklewold/Desktop/env/materials/panther/patchmatchnet_output/fused.ply") # Read the point cloud
    visualization.draw_geometries([cloud]) # Visualize the point cloud     

if __name__ == "__main__":
    main()