# HeavenzFire Omni-Mesh Architecture

## Provider-Neutral Document Engine + Event Bus

The Omni-Mesh decouples the browser, model provider, renderer, persistence layer, and image-generation backend into **replaceable components** connected by capability-based routing.

```
                     OMNI-MESH
                         │
             ┌───────────┴───────────┐
             │                       │
       DOCUMENT ENGINE          EVENT BUS
             │                       │
             └───────────┬───────────┘
                         │
                  CAPABILITY ROUTER
                         │
       ┌─────────────────┼──────────────────┐
       │                 │                  │
       ▼                 ▼                  ▼
 IMAGE GENERATION    4D MANIFOLD        LOCAL LLM
       │                 │                  │
       ▼                 ▼                  ▼
 Diffusion API       Canvas/WebGPU       Ollama
       │                 │                  │
       └─────────────────┼──────────────────┘
                         │
                         ▼
                    CRDT STORE
                         │
                         ▼
                      IndexedDB
                         │
                    ┌────┴────┐
                    ▼         ▼
                  WebRTC   Browser Nodes
```

---

## Core Components

### 1. `omni-mesh-core.js` - Main Orchestrator

Three subsystems unified:

| Class | Purpose |
|-------|---------|
| `EventBus` | Reactive middleware interceptors, autonomous swarm loops |
| `CapabilityRouter` | Discovers nodes by capability (vision, embedding, webRTC), not provider name |
| `DocumentEngine` | Image Document Engine (SLICE → crop → tile → export) with CRDT-style operations |

**Usage:**
```js
// Register a capability
OmniMesh.capability("image-generation", new LocalImageProvider("http://127.0.0.1:8188"));

// Execute through router
const result = await OmniMesh.execute("image-generation", {
  id: crypto.randomUUID(),
  type: "IMAGE_GENERATION_REQUEST",
  payload: { prompt: "cyberpunk city", width: 1024 }
});

// Create and operate on documents
const doc = OmniMesh.documents.createDocument({ type: "image" });
OmniMesh.documents.apply(doc.id, { type: "GENERATE", payload: {...} });
```

---

### 2. Providers (`/providers/`)

#### `image-provider.js` - Local Diffusion Backend

Connects to ComfyUI, Stable Diffusion, or any HTTP-based image generation API.

```js
const provider = new LocalImageProvider("http://127.0.0.1:8188");
OmniMesh.capability("image-generation", provider);
```

**Note:** Ollama is primarily a local LLM/vision endpoint, NOT a diffusion image generator. This architecture keeps them separate.

#### `manifold-provider.js` - 4D Hyper-Manifold Renderer

Transforms visualization from isolated animation to routed capability.

**Supported operations:**
- `ROTATE_4D` - Set xw, yz rotation angles
- `ADD_NODE` - Add node to manifold graph
- `SET_METRIC` - Update spacetime metric
- `UPDATE_SLICING` - Configure maximal slicing (K=0)

```js
OmniMesh.capability("4d-manifold", new ManifoldRendererProvider(hyperManifoldRenderer));

// Usage
await OmniMesh.execute("4d-manifold", {
  id: crypto.randomUUID(),
  type: "ROTATE_4D",
  payload: { xw: Math.PI/4, yz: Math.PI/6 }
});
```

---

### 3. `content-adapter.js` - Browser Extension Adapter

Makes ChatGPT's DOM just an external adapter. If the page changes its React structure, the document engine doesn't care.

**Events:**
- `OMNI_MESH_COMMAND` - Send commands to Omni-Mesh
- `OMNI_MESH_RESULT` / `OMNI_MESH_ERROR` - Receive responses

**Helper function:**
```js
const result = await window.sendOmniCommand(
  "4d-manifold",
  "ROTATE_4D",
  { xw: Math.PI/4, yz: Math.PI/6 }
);
```

---

### 4. `crdt-store.js` - Persistent CRDT Memory

Listens to `OPERATION_APPLIED` events and automatically persists documents to IndexedDB.

**Features:**
- Race-condition-free sync across devices/tabs
- Append-only operation log
- Revision tracking
- Auto-persistence on every mutation

```js
const store = new CRDTDocumentStore(OmniMesh.bus);
await store.init();

// Auto-persists on every OPERATION_APPLIED event
const doc = OmniMesh.documents.createDocument({...});
OmniMesh.documents.apply(doc.id, {...}); // → automatically saved to IndexedDB
```

---

### 5. `examples.js` - Complete Integration Patterns

Six fully-worked examples:

1. **generateOmniImage()** - End-to-end image generation with document tracking
2. **set4DRotation()** - Manifold rotation through capability routing
3. **initializeOmniMesh()** - Provider registration + CRDT setup
4. **setupEventListeners()** - Telemetry/middleware interceptors
5. **useContentAdapter()** - Browser extension usage patterns
6. **bootOmniMesh()** - Complete initialization sequence

**Quick start:**
```js
// Load all scripts, then run:
await bootOmniMesh();

// Now available:
generateOmniImage("black hole accretion disk");
set4DRotation(Math.PI/4, Math.PI/6);
```

---

## Data Flow Example

```text
PROMPT: "cyberpunk cityscape"
  │
  ▼
IMAGE_GENERATION_REQUEST (operation created)
  │
  ▼
DocumentEngine.apply() 
  ├── revision++
  ├── emits OPERATION_APPLIED → CRDT Store persists
  │
  ▼
CapabilityRouter.execute("image-generation")
  ├── emits CAPABILITY_EXECUTION_STARTED
  │
  ▼
LocalImageProvider.fetch("http://127.0.0.1:8188/generate")
  │
  ▼
Diffusion Backend (ComfyUI, etc.)
  │
  ▼
IMAGE_GENERATION_RESULT returned
  │
  ▼
DocumentEngine.apply() - records result
  ├── emits OPERATION_APPLIED → CRDT Store persists
  │
  ▼
IndexedDB (persistent, syncable via WebRTC)
```

---

## Key Architectural Wins

| Before | After |
|--------|-------|
| Coupled to Grok/ChatGPT DOM | Provider-neutral Document Engine |
| Hardcoded provider names | Capability-based routing |
| Isolated renderer | Routed capability with event bus |
| No persistence | CRDT-backed IndexedDB store |
| Single-purpose script | Extensible multi-provider system |

---

## File Structure

```
src/omni-mesh/
├── omni-mesh-core.js        # EventBus + CapabilityRouter + DocumentEngine
├── providers/
│   ├── image-provider.js    # Local diffusion backend adapter
│   └── manifold-provider.js # 4D renderer capability
├── content-adapter.js       # Browser extension adapter
├── crdt-store.js            # IndexedDB persistence layer
├── examples.js              # Complete usage patterns
└── README.md                # This file
```

---

## Next Steps

1. **Load scripts in order:**
   ```html
   <script src="omni-mesh-core.js"></script>
   <script src="providers/image-provider.js"></script>
   <script src="providers/manifold-provider.js"></script>
   <script src="crdt-store.js"></script>
   <script src="content-adapter.js"></script>
   <script src="examples.js"></script>
   ```

2. **Run initialization:**
   ```js
   await bootOmniMesh();
   ```

3. **Add your diffusion backend** at `http://127.0.0.1:8188/generate` (or update endpoint)

4. **Extend with new capabilities:**
   - Local LLM (Ollama)
   - Embedding model (Xenova/transformers.js)
   - WebRTC peer connections
   - Vision models

The system is now **provider-neutral, extensible, and under your control**.
