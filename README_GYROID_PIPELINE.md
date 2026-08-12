# AERO-SOVEREIGN GYROID ASSET PIPELINE

## Overview

This package provides production-ready tools for generating **Triply Periodic Minimal Surface (TPMS)** gyroid structures for advanced garment and material design workflows.

---

## Files Included

| File | Purpose | Target Application |
|------|---------|-------------------|
| `gyroid_geometry_blender.py` | Procedural mesh generation via Marching Cubes | Blender 3.x+ |
| `gyroid_shader_osl.osl` | OSL shader for procedural texturing | Blender Cycles, Houdini, Arnold |
| `README.md` | This documentation | All |

---

## Mathematical Foundation

**Gyroid Implicit Equation:**

```
f(x,y,z) = sin(x)cos(y) + sin(y)cos(z) + sin(z)cos(x) = 0
```

**Threshold Control:**

```
|f(x,y,z)| ≤ t
```

Where `t` controls fabric thickness and porosity:
- **Lower values** (0.3–0.4): Fine lattice, high porosity
- **Higher values** (0.5–0.6): Thick struts, low porosity

---

## Quick Start

### Option 1: Python Geometry Generation (Blender)

**Prerequisites:**
```bash
# Install required Python packages in Blender's environment
pip install numpy scikit-image
```

**Usage:**
1. Open Blender
2. Navigate to **Scripting** workspace
3. Create new script → Paste `gyroid_geometry_blender.py`
4. Adjust `CONFIG` dictionary parameters
5. Press **Alt+P** or click ▶ Run Script

**Key Parameters:**
```python
CONFIG = {
    "threshold": 0.45,        # Lattice thickness
    "resolution": 100,        # Voxel resolution (higher = detailed but slower)
    "x_min": -5.0,            # Domain bounds
    "x_max": 5.0,
    "decimate_ratio": 0.5,    # Polygon reduction (1.0 = no reduction)
    "apply_material": True,   # Auto-apply PBR material
}
```

---

### Option 2: OSL Shader (Procedural Texturing)

**Prerequisites:**
- Enable **Open Shading Language** in renderer settings
- Blender: Render Properties → Cycles → Features → Open Shading Language ✓

**Usage:**
1. Add **Script** node to shader editor
2. Load `gyroid_shader_osl.osl`
3. Connect output to Material Output
4. Adjust shader parameters

**Key Parameters:**
| Parameter | Description | Recommended Range |
|-----------|-------------|-------------------|
| `Scale` | Pattern frequency | 3.0 – 10.0 |
| `Threshold` | Surface cutoff | 0.3 – 0.6 |
| `Thickness_Gradient` | Edge softness | 0.05 – 0.2 |
| `Output_Mode` | 0=Solid, 1=Wireframe, 2=Porosity Map | 0 – 2 |

---

## Asset Prompts

### Micro-Lattice Swimwear

**Geometry Settings:**
```python
threshold = 0.4
resolution = 120
scale = 5.0
```

**Material Settings (OSL):**
```
Scale: 5.0
Threshold: 0.4
Base_Color: (0.02, 0.12, 0.40)
Roughness: 0.25
Subsurface: 0.2
```

**Render:** 8K turnaround, rim lighting, elastomer PBR mapping

---

### Tensor Monokini (Dual-Substrate)

**Geometry Settings:**
```python
threshold = 0.55
resolution = 100
scale = 4.0
```

**Material Settings (OSL):**
```
Scale: 4.0
Threshold: 0.55
Base_Color: (0.05, 0.15, 0.35)      # Cobalt nylon
Secondary_Color: (0.85, 0.85, 0.90)  # Platinum overlay
Thickness_Gradient: 0.15
```

**Pipeline:** V-Ray or Cycles with stress-adaptive porosity simulation

---

## Advanced Workflows

### Stress-Adaptive Fabric Simulation

Use the included `Gyroid_Stress_Adaptive` shader variant (commented in OSL file) for tension-responsive materials:

```osl
// Uncomment Gyroid_Stress_Adaptive shader block
Stress_Vector: vector(0, 0, 1)  // Primary stress direction
Stress_Sensitivity: 0.3          // Porosity response factor
```

### Macro Close-Up Analysis

For material R&D and physics validation:

```python
# Python script config
threshold = 0.3
resolution = 150  # High detail for close-ups
```

```osl
// OSL shader config
Scale: 10.0
Threshold: 0.3
Output_Mode: 2  // Porosity visualization mode
```

---

## Performance Optimization

| Task | Recommendation |
|------|----------------|
| **High-resolution meshes** | Use `resolution ≤ 80` for interactive, `100–150` for final render |
| **Real-time preview** | Set `decimate_ratio = 0.3` and disable subsurface |
| **Animation** | Animate `Offset_X/Y/Z` parameters for dynamic patterns |
| **Memory usage** | Reduce domain bounds (`x_min/max`, etc.) for smaller volumes |

---

## Troubleshooting

### "scikit-image not installed" (Python)
```bash
# Locate Blender's Python executable
/path/to/blender/python/bin/python -m pip install scikit-image numpy
```

### OSL shader not rendering
- Verify Open Shading Language is enabled in renderer
- Ensure script node is set to **Text** mode (not **Internal**)
- Check that material output uses **Surface** input

### Mesh too dense/sparse
- Adjust `threshold`: lower = finer, higher = coarser
- Modify `Scale` parameter in OSL or domain bounds in Python
- Apply **Decimate** modifier post-generation

---

## Integration Notes

### Tauri + Aero-Sovereign Core

This gyroid pipeline integrates with the broader Aero-Sovereign architecture:

- **Zero-Copy Memory Bus**: Stream vertex data directly to WebGPU renderers
- **WASM Execution**: Run lightweight gyroid generators in sandboxed contexts
- **P2P Mesh Sync**: Share parametric presets across distributed nodes

---

## License & Attribution

Part of the **Aero-Sovereign** production framework.  
Designed for next-generation garment pipelines and parametric material systems.

---

## Support

For advanced customization or integration queries, reference the full Aero-Sovereign architectural documentation.
