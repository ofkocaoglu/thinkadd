# analyzer.py
import trimesh
import numpy as np
from scipy.spatial.transform import Rotation as R

def generate_orientations(n=100):
    """Uniform sphere sampling"""
    phi = np.random.uniform(0, 2*np.pi, n)
    costheta = np.random.uniform(-1, 1, n)
    theta = np.arccos(costheta)
    x = np.sin(theta) * np.cos(phi)
    y = np.sin(theta) * np.sin(phi)
    z = np.cos(theta)
    return np.vstack([x, y, z]).T

def rotate_mesh(mesh, direction):
    """Rotate mesh to align Z axis with the given direction"""
    z_axis = np.array([0, 0, 1])
    direction = direction / np.linalg.norm(direction)
    rot_axis = np.cross(direction, z_axis)
    
    if np.linalg.norm(rot_axis) < 1e-6:
        return mesh.copy()
    
    rot_angle = np.arccos(np.dot(direction, z_axis))
    rot = R.from_rotvec(rot_axis / np.linalg.norm(rot_axis) * rot_angle)
    rot_matrix_3x3 = rot.as_matrix()

    # Convert 3x3 to 4x4 homogeneous transform
    rot_matrix_4x4 = np.eye(4)
    rot_matrix_4x4[:3, :3] = rot_matrix_3x3

    new_mesh = mesh.copy()
    new_mesh.apply_transform(rot_matrix_4x4)
    return new_mesh


def compute_support_metric(mesh):
    """Approximate support volume using lowest-facing triangles"""
    z_threshold = 0.5  # overhang threshold
    normals = mesh.face_normals
    overhang_faces = normals[:, 2] < z_threshold
    overhang_area = mesh.area_faces[overhang_faces].sum()
    return overhang_area
