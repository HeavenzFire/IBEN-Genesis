# IBEN-Genesis: Peer-to-Peer Mesh Framework

## Quaternary Logic Architecture Implementation

A decentralized peer-to-peer mesh framework implementing **quaternary logic encoding** (-2, -1, +1, +2) with **gyroidal tensor routing** on non-Euclidean minimal surfaces for enhanced information density and fault-tolerant data transmission.

---

## Core Features

### 🔷 Quaternary State Encoding
- **Symmetric Bipolar States**: `-2, -1, +1, +2` (eliminates neutral zero)
- **2x Information Density**: 2 bits per quaternary symbol vs 1 bit binary
- **Balanced Vector Loads**: Equal positive/negative state distribution
- **Native Error Detection**: Quaternary checksums with single-error correction

### 🔷 Gyroidal Tensor Topology
- **Non-Euclidean Routing**: Nodes positioned on gyroid minimal surfaces
- **Four Orthogonal Streams**: Quaternary states map to independent tensor pathways
- **Curvature-Aware Distance**: Geodesic routing accounting for surface geometry
- **Dynamic Path Optimization**: A* search with gyroidal heuristics

### 🔷 Self-Healing Protocols
- **Congestion Detection**: Real-time node health monitoring
- **Automatic Re-routing**: Dynamic path reconstruction around degraded nodes
- **Zero Single Points of Failure**: Fully distributed mesh topology

---

## Module Structure

```
/workspace/
├── quaternary_core.py      # Quaternary logic encoding/decoding
├── gyroid_topology.py      # Gyroidal surface routing & mesh management
└── IBEN_GENESIS_README.md  # This documentation
```

---

## Quick Start

### Prerequisites
```bash
pip install numpy
```

### Run Quaternary Core Demo
```bash
python quaternary_core.py
```

**Demonstrates:**
- Byte-to-quaternary encoding
- Round-trip encoding/decoding
- Tensor transformations
- Checksum-based error correction

### Run Gyroidal Topology Demo
```bash
python gyroid_topology.py
```

**Demonstrates:**
- Mesh node generation on gyroid surface
- Neighbor connection establishment
- Tensor stream assignment
- Optimal path finding
- Congestion detection & re-balancing

---

## API Reference

### QuaternaryCore Module

#### `QuaternaryState` Enum
```python
from quaternary_core import QuaternaryState

# Valid states
state = QuaternaryState.NEG_TWO    # -2
state = QuaternaryState.NEG_ONE    # -1
state = QuaternaryState.POS_ONE    # +1
state = QuaternaryState.POS_TWO    # +2

# Convert from binary pair (0/1, 0/1) -> (-2,-1,+1,+2)
state = QuaternaryState.from_binary_pair(1, 0)  # POS_ONE

# Properties
state.polarity   # -1 or +1
state.magnitude  # 1 or 2
```

#### `QuaternaryVector` Class
```python
from quaternary_core import QuaternaryVector, QuaternaryState

vector = QuaternaryVector([
    QuaternaryState.NEG_TWO,
    QuaternaryState.POS_ONE,
    QuaternaryState.POS_TWO
])

# Operations
length = len(vector)
dot = vector.dot_product(other_vector)
transformed = vector.tensor_transform(matrix)
density = vector.information_density()  # bits
checksum = vector.checksum()
```

#### `QuaternaryEncoder` Class
```python
from quaternary_core import QuaternaryEncoder

encoder = QuaternaryEncoder()

# Encode bytes to quaternary
data = b"IBEN"
encoded = encoder.encode_bytes(data)

# Decode back to bytes
decoded = encoder.decode_bytes(encoded)

# Error correction
corrected, success = encoder.apply_error_correction(
    corrupted_vector, 
    expected_checksum
)
```

### GyroidTopology Module

#### `GyroidalTopology` Class
```python
from gyroid_topology import GyroidalTopology

# Initialize topology
topology = GyroidalTopology(grid_size=10, gyroid_scale=2*np.pi)

# Generate mesh nodes
nodes = topology.generate_mesh_nodes(num_nodes=100)

# Assign tensor streams (quaternary state -> stream 0-3)
stream = topology.assign_tensor_stream("node_0001", quaternary_state=-2)

# Find optimal routing path
path = topology.find_optimal_path(source_id, target_id, tensor_stream=2)

# Access path properties
print(f"Latency: {path.latency}")
print(f"Bandwidth: {path.bandwidth}")
print(f"Nodes: {path.nodes}")
```

#### Self-Healing Operations
```python
# Detect congested nodes
congested = topology.detect_congestion(threshold=0.7)

# Re-route around congestion
new_paths = topology.rebalance_routing(congested_nodes)
```

#### Gyroid Surface Functions
```python
# Evaluate gyroid implicit function
value = GyroidalTopology.gyroid_function(x, y, z)

# Get surface normal (gradient)
normal = GyroidalTopology.gyroid_gradient(x, y, z)

# Project point to nearest surface location
surface_point = topology.project_to_gyroid_surface(initial_point)
```

---

## Mathematical Foundations

### Quaternary Logic Mapping
| Binary Pair | Quaternary State | Tensor Stream |
|-------------|------------------|---------------|
| 00          | -2               | 0             |
| 01          | -1               | 1             |
| 10          | +1               | 2             |
| 11          | +2               | 3             |

### Gyroid Minimal Surface
The gyroid surface is defined by the implicit equation:

```
sin(x)·cos(y) + sin(y)·cos(z) + sin(z)·cos(x) = 0
```

This triply-periodic minimal surface provides:
- **Zero mean curvature** at all points
- **Three-fold symmetry** for isotropic routing
- **Infinite genus** for complex pathway topologies

### Information Density
- **Binary**: log₂(2) = 1 bit/symbol
- **Quaternary**: log₂(4) = 2 bits/symbol
- **Throughput Gain**: 2× improvement per clock cycle

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    IBEN-Genesis Mesh                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐               │
│  │ Node A  │────▶│ Node B  │────▶│ Node C  │               │
│  │Stream 0 │     │Stream 2 │     │Stream 1 │               │
│  └────┬────┘     └────┬────┘     └────┬────┘               │
│       │               │               │                     │
│       ▼               ▼               ▼                     │
│  ┌─────────────────────────────────────────┐               │
│  │      Gyroidal Tensor Routing Layer      │               │
│  │  sin(x)cos(y) + sin(y)cos(z) + ... = 0  │               │
│  └─────────────────────────────────────────┘               │
│                                                             │
│  Quaternary States: [-2, -1, +1, +2]                       │
│  Information Density: 2 bits/symbol                        │
│  Self-Healing: Automatic congestion avoidance              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Quantum-Resistant Cryptography**: Implement lattice-based encryption layer
2. **Immutable Forensic Logging**: Integrate ZYLPHA-16 audit framework
3. **Localized Core Engine**: Develop autonomous runtime modules
4. **Network Simulation**: Scale testing with 1000+ nodes

---

## License

MIT License - Decentralized Framework Initiative

---

**Status**: ✅ Core modules implemented and validated  
**Version**: 0.1.0-alpha
