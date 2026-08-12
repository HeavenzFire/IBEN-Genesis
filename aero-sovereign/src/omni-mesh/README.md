# HeavenzFire Omni-Mesh

Provider-neutral orchestration layer for distributed AI inference, image processing, and CRDT-synchronized memory.

## Architecture

The Omni-Mesh decouples the **Image Document Engine** from specific model providers, enabling capability-based routing across a dynamic mesh of nodes (local browser tabs, Ollama workers, cloud endpoints, etc.).

```
SLICE
├── crop
├── tile
├── region export
│   ├── region → embedding
│   ├── region → vision model
│   └── region → inference task
```

## Core Components

### 1. Image Document Engine (`ImageDocument.js`)

Provider-neutral document model for spatial slicing, tiling, and region-based operations:

```js
import { ImageDocument } from './omni-mesh/ImageDocument.js';

const doc = new ImageDocument();

// Create spatial slice
const slice = doc.createSlice({
  x: 800,
  y: 400,
  width: 1024,
  height: 768,
  operation: 'CROP_REGION'
});

// Tile for parallel processing
const tiles = slice.tile(256);

// Export for specific pipeline
const exportData = await doc.exportRegion(slice.id, 'vision');
```

**Syntropic Compression**: Implements 1/729 compression ratio using Bowen-York curvature principles for differential operation strokes.

### 2. Capability-Based Node Router (`NodeRouter.js`)

Discovers and routes work to nodes based on capabilities rather than hardcoded providers:

```js
import { NodeRegistry, TaskQueue } from './omni-mesh/NodeRouter.js';

const registry = new NodeRegistry();

// Register nodes with capabilities
registry.registerNode('node-01', {
  image: { rasterEdit: true, vision: true },
  inference: { localLLM: true },
  transport: { webRTC: true }
});

registry.registerNode('node-02', {
  inference: { embedding: true, vision: true },
  storage: { indexedDB: true }
});

// Route by capability, not provider name
const node = registry.routeTask('inference.vision', myTask, 'latency');
```

**Node Discovery Example**:
```
NODE 01
├─ Gemma
├─ Vision
├─ ImageEdit
└─ WebRTC

NODE 02
├─ Coding LLM
├─ Embeddings
└─ WebGPU

NODE 03
├─ Cloud model
└─ High-bandwidth GPU
```

### 3. CRDT Synchronized Memory (`CRDTMemory.js`)

Conflict-Free Replicated Data Types for distributed state synchronization without race conditions:

```js
import { CRDTDocumentStore } from './omni-mesh/CRDTMemory.js';

const store = new CRDTDocumentStore('my-node-id');

// Add slices (OR-Set CRDT)
store.addSlice('slice-123');

// Update data (LWW Register CRDT)
store.updateSliceData('slice-123', { processed: true });

// Merge with remote node state
store.merge(remoteState); // No conflicts, guaranteed convergence
```

**CRDT Types Implemented**:
- **LWW Register**: Last-Writer-Wins for single values
- **G-Set**: Grow-only sets for append-only logs
- **OR-Set**: Observed-Remove Set for add/remove collections

### 4. Main Orchestrator (`OmniMeshOrchestrator.js`)

Unifies all subsystems into a single coordination layer:

```js
import { OmniMeshOrchestrator } from './omni-mesh/OmniMeshOrchestrator.js';

const mesh = new OmniMeshOrchestrator('my-node');
mesh.initialize();

// Create document
const doc = mesh.createDocument('doc-1');

// Register remote nodes
mesh.registerNode('ollama-worker', {
  inference: { localLLM: true, vision: true },
  transport: { websocket: true }
}, {
  endpoint: 'ws://localhost:8080',
  transport: 'websocket'
});

// Process slice through mesh
const { sliceId, taskId } = await mesh.processSlice(
  'doc-1',
  { x: 0, y: 0, width: 512, height: 512 },
  'vision',
  { priority: 'high' }
);

// Listen for events
mesh.on('mesh:task:complete', ({ task, result }) => {
  console.log(`Task ${task.id} completed on node ${task.dispatchedTo}`);
});

// Sync with remote nodes
const localState = mesh.getState();
// ... transmit state via WebSocket/WebRTC ...
mesh.syncWithRemote(remoteState);
```

## Event Bus

All components emit events for reactive integration:

| Event | Description |
|-------|-------------|
| `mesh:initialize` | Orchestrator initialized |
| `mesh:node:register` | New node joined mesh |
| `mesh:node:unregister` | Node left mesh |
| `mesh:route:success` | Task successfully routed |
| `mesh:route:fail` | No capable nodes available |
| `mesh:task:submit` | Task submitted to queue |
| `mesh:task:complete` | Task completed |
| `mesh:task:fail` | Task failed after retries |
| `mesh:document:create` | New document created |
| `mesh:slice:process` | Slice processing started |
| `mesh:memory:slice:add` | Slice added to CRDT store |
| `mesh:memory:merge` | State merged with remote |
| `mesh:sync:complete` | CRDT sync completed |

## Installation

```bash
npm install uuid
```

## Usage Pattern

1. **Initialize** orchestrator with unique node ID
2. **Register** local and remote nodes with their capabilities
3. **Create** documents and spatial slices
4. **Submit** tasks requiring specific capabilities
5. **Listen** for completion events
6. **Sync** state across mesh using CRDT merge

## Syntropic Compression

The system implements 1/729 syntropic compression for operation logs:

- **Invariant Mass**: Total operation weight (ADM mass equivalent)
- **Momentum (P_z)**: Directional change rate
- **Spin (S_z)**: Rotational/cyclical pattern detection
- **Differential Strokes**: Only stores changes from baseline (K=0 maximal slicing)

```js
const compressed = mesh.compressOperations();
// Returns: { invariantMass, momentum, spin, differentialStrokes, checksum }
```

## License

MIT
