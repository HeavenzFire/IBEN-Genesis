"""
AERO-SOVEREIGN GYROID GEOMETRY GENERATOR
========================================
Procedural Triply Periodic Minimal Surface (TPMS) mesh generation for Blender.

Equation: sin(x)cos(y) + sin(y)cos(z) + sin(z)cos(x) = 0
Threshold: |f(x,y,z)| ≤ t controls fabric thickness and porosity.

Usage:
    1. Open Blender
    2. Go to Scripting tab → New
    3. Paste this code
    4. Adjust parameters in CONFIG
    5. Run script (Alt+P or Play button)
"""

import bpy
import bmesh
import math
from math import sin, cos
import numpy as np


# =============================================================================
# CONFIGURATION - Adjust for your garment requirements
# =============================================================================

CONFIG = {
    # Gyroid equation threshold (controls thickness/porosity)
    # Lower = finer lattice, Higher = thicker struts
    "threshold": 0.45,
    
    # Domain bounds (x, y, z ranges)
    "x_min": -5.0,
    "x_max": 5.0,
    "y_min": -5.0,
    "y_max": 5.0,
    "z_min": -5.0,
    "z_max": 5.0,
    
    # Resolution (higher = more detailed but slower)
    "resolution": 100,  # Number of samples per axis
    
    # Mesh refinement
    "smooth_iterations": 2,
    "decimate_ratio": 0.5,  # Reduce polygon count (1.0 = no reduction)
    
    # Output settings
    "object_name": "Gyroid_Lattice",
    "apply_material": True,
}


# =============================================================================
# GYROID EQUATION
# =============================================================================

def gyroid_function(x, y, z):
    """
    Evaluate the gyroid implicit surface function.
    
    f(x,y,z) = sin(x)cos(y) + sin(y)cos(z) + sin(z)cos(x)
    
    Returns value where f=0 defines the minimal surface.
    """
    return sin(x) * cos(y) + sin(y) * cos(z) + sin(z) * cos(x)


# =============================================================================
# MESH GENERATION USING MARCHING CUBES
# =============================================================================

def generate_gyroid_mesh(config):
    """
    Generate gyroid mesh using volumetric sampling and marching cubes.
    """
    print(f"[AERO-SOVEREIGN] Generating gyroid lattice...")
    print(f"[AERO-SOVEREIGN] Threshold: {config['threshold']}")
    print(f"[AERO-SOVEREIGN] Resolution: {config['resolution']}³ voxels")
    
    # Create coordinate grids
    x = np.linspace(config["x_min"], config["x_max"], config["resolution"])
    y = np.linspace(config["y_min"], config["y_max"], config["resolution"])
    z = np.linspace(config["z_min"], config["z_max"], config["resolution"])
    
    # Create 3D grid
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    # Evaluate gyroid function across volume
    V = gyroid_function(X, Y, Z)
    
    # Extract isosurface using marching cubes
    try:
        from skimage import measure
        verts, faces, normals, values = measure.marching_cubes(
            V, 
            level=config["threshold"],
            spacing=(
                (config["x_max"] - config["x_min"]) / config["resolution"],
                (config["y_max"] - config["y_min"]) / config["resolution"],
                (config["z_max"] - config["z_min"]) / config["resolution"]
            )
        )
    except ImportError:
        print("[ERROR] scikit-image not installed. Install with: pip install scikit-image")
        return None
    
    print(f"[AERO-SOVEREIGN] Extracted {len(verts)} vertices, {len(faces)} faces")
    
    return verts, faces


# =============================================================================
# BLENDER INTEGRATION
# =============================================================================

def create_blender_object(verts, faces, config):
    """
    Create a Blender mesh object from vertices and faces.
    """
    # Create new mesh
    mesh = bpy.data.meshes.new(f"{config['object_name']}_Mesh")
    obj = bpy.data.objects.new(config["object_name"], mesh)
    
    # Link to scene
    bpy.context.collection.objects.link(obj)
    
    # Build mesh from data
    bm = bmesh.new()
    
    # Add vertices
    for v in verts:
        bm.verts.new(v)
    
    bm.verts.ensure_lookup_table()
    
    # Add faces
    for f in faces:
        try:
            bm.faces.new([bm.verts[i] for i in f])
        except ValueError:
            # Skip degenerate faces
            continue
    
    # Smooth the mesh
    if config["smooth_iterations"] > 0:
        bmesh.ops.smooth_vert(
            bm,
            verts=bm.verts,
            factor=0.5,
            iterations=config["smooth_iterations"]
        )
    
    # Write to mesh
    bm.to_mesh(mesh)
    bm.free()
    
    # Apply decimation modifier
    if config["decimate_ratio"] < 1.0:
        decimate = obj.modifiers.new(name="Decimate", type='DECIMATE')
        decimate.ratio = config["decimate_ratio"]
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=decimate.name)
    
    # Enable smooth shading
    bpy.ops.object.shade_smooth()
    
    # Apply material if requested
    if config["apply_material"]:
        apply_gyroid_material(obj)
    
    print(f"[AERO-SOVEREIGN] Created object: {config['object_name']}")
    return obj


def apply_gyroid_material(obj):
    """
    Create and apply a PBR material optimized for gyroid lattices.
    """
    mat = bpy.data.materials.new(name="Gyroid_Elastomer")
    mat.use_nodes = True
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create principled BSDF
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = (0.05, 0.15, 0.35, 1.0)  # Cobalt blue
    bsdf.inputs["Subsurface"].default_value = 0.15
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.5, 0.3)
    bsdf.inputs["Metallic"].default_value = 0.1
    bsdf.inputs["Roughness"].default_value = 0.35
    bsdf.inputs["Clearcoat"].default_value = 0.8
    bsdf.inputs["Clearcoat Roughness"].default_value = 0.2
    
    # Output node
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Link nodes
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    
    # Assign material to object
    obj.data.materials.append(mat)
    
    print(f"[AERO-SOVEREIGN] Applied PBR material: Gyroid_Elastomer")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """
    Main execution entry point.
    """
    print("=" * 60)
    print("AERO-SOVEREIGN GYROID GEOMETRY GENERATOR")
    print("=" * 60)
    
    # Generate mesh data
    result = generate_gyroid_mesh(CONFIG)
    
    if result is None:
        print("[ERROR] Mesh generation failed.")
        return
    
    verts, faces = result
    
    # Create Blender object
    obj = create_blender_object(verts, faces, CONFIG)
    
    # Set active object
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
    print("=" * 60)
    print("[SUCCESS] Gyroid lattice generation complete!")
    print(f"[INFO] Object: {obj.name}")
    print(f"[INFO] Vertices: {len(obj.data.vertices)}")
    print(f"[INFO] Faces: {len(obj.data.polygons)}")
    print("=" * 60)


# Run if executed directly
if __name__ == "__main__":
    main()
