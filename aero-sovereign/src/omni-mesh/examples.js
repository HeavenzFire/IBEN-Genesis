/**
 * Omni-Mesh Integration Examples - Complete usage patterns
 * 
 * Demonstrates end-to-end data flow:
 * PROMPT → IMAGE_GENERATION_REQUEST → DocumentEngine → CapabilityRouter → Local Diffusion Node → CRDT Store
 */

// ============================================================================
// EXAMPLE 1: Generate an image through the Omni-Mesh
// ============================================================================

async function generateOmniImage(prompt, options = {}) {
  const { width = 1536, height = 1024, steps = 30, seed = -1 } = options;

  // Create document to track the operation
  const document = window.OmniMesh.documents.createDocument({
    type: "image",
    prompt
  });

  console.log(`[Example] Document created: ${document.id}`);

  // Create generation request operation
  const request = {
    id: crypto.randomUUID(),
    type: "IMAGE_GENERATION_REQUEST",
    payload: {
      prompt,
      width,
      height,
      steps,
      seed
    }
  };

  // Apply operation to document (triggers revision++, emits OPERATION_APPLIED)
  window.OmniMesh.documents.apply(document.id, request);

  // Execute through capability router (routes to registered image-generation provider)
  const result = await window.OmniMesh.execute("image-generation", request);

  // Record result in document
  window.OmniMesh.documents.apply(document.id, {
    id: crypto.randomUUID(),
    actor: "local-image-node",
    type: "IMAGE_GENERATION_RESULT",
    payload: result
  });

  console.log(`[Example] Image generated and stored in document ${document.id}`);
  return { document: window.OmniMesh.documents.get(document.id), result };
}

// ============================================================================
// EXAMPLE 2: Rotate 4D manifold through capability routing
// ============================================================================

function set4DRotation(xw, yz) {
  const request = {
    id: crypto.randomUUID(),
    type: "ROTATE_4D",
    payload: { xw, yz }
  };

  return window.OmniMesh.execute("4d-manifold", request);
}

// Usage: set4DRotation(Math.PI / 4, Math.PI / 6);

// ============================================================================
// EXAMPLE 3: Register providers and initialize CRDT store
// ============================================================================

function initializeOmniMesh() {
  // Register image generation provider (ComfyUI-style backend at port 8188)
  const imageProvider = new LocalImageProvider("http://127.0.0.1:8188");
  window.OmniMesh.capability("image-generation", imageProvider);

  // Register 4D manifold renderer provider
  // Assumes hyperManifoldRenderer is available globally
  if (typeof hyperManifoldRenderer !== 'undefined') {
    const manifoldProvider = new ManifoldRendererProvider(hyperManifoldRenderer);
    window.OmniMesh.capability("4d-manifold", manifoldProvider);
  }

  // Initialize CRDT persistence layer (auto-persists on every operation)
  const crdtStore = new CRDTDocumentStore(window.OmniMesh.bus);

  console.log("[Example] Omni-Mesh initialized with providers:", window.OmniMesh.getCapabilities());
  
  return { imageProvider, crdtStore };
}

// ============================================================================
// EXAMPLE 4: Listen to event bus for telemetry/middleware interceptors
// ============================================================================

function setupEventListeners() {
  // Track all capability executions
  window.OmniMesh.bus.on("CAPABILITY_EXECUTION_STARTED", ({ capability, requestId }) => {
    console.log(`[Telemetry] Executing ${capability} [${requestId.slice(0, 8)}...]`);
  });

  window.OmniMesh.bus.on("CAPABILITY_EXECUTION_COMPLETE", ({ capability, requestId, result }) => {
    console.log(`[Telemetry] ${capability} completed successfully`);
  });

  window.OmniMesh.bus.on("CAPABILITY_EXECUTION_FAILED", ({ capability, requestId, error }) => {
    console.error(`[Telemetry] ${capability} failed: ${error}`);
  });

  // Auto-log document operations
  window.OmniMesh.bus.on("OPERATION_APPLIED", ({ documentId, operation }) => {
    console.log(`[Document] ${operation.type} applied to ${documentId} (rev ${operation.revision})`);
  });

  // Track document creation
  window.OmniMesh.bus.on("DOCUMENT_CREATED", (doc) => {
    console.log(`[Document] Created ${doc.id} with source:`, doc.source);
  });
}

// ============================================================================
// EXAMPLE 5: Use content adapter from browser console or extension
// ============================================================================

async function useContentAdapter() {
  // Method 1: Dispatch custom event
  window.dispatchEvent(new CustomEvent("OMNI_MESH_COMMAND", {
    detail: {
      capability: "image-generation",
      type: "IMAGE_GENERATION_REQUEST",
      request: {
        id: crypto.randomUUID(),
        payload: {
          prompt: "A black hole accretion disk with gravitational lensing",
          width: 1024,
          height: 1024,
          steps: 50
        }
      }
    }
  }));

  // Method 2: Use helper function (returns Promise)
  try {
    const result = await window.sendOmniCommand(
      "4d-manifold",
      "ROTATE_4D",
      { xw: Math.PI / 4, yz: Math.PI / 6 }
    );
    console.log("[Adapter] Rotation applied:", result);
  } catch (error) {
    console.error("[Adapter] Error:", error);
  }
}

// ============================================================================
// EXAMPLE 6: Complete initialization sequence (drop into console)
// ============================================================================

async function bootOmniMesh() {
  console.log("[Boot] Initializing Omni-Mesh system...");

  // Wait for core to load
  if (!window.OmniMesh) {
    throw new Error("OmniMesh core not loaded - include omni-mesh-core.js first");
  }

  // Setup event listeners
  setupEventListeners();

  // Initialize providers
  const { imageProvider, crdtStore } = initializeOmniMesh();

  // Wait for CRDT store to initialize
  await crdtStore.init();

  console.log("[Boot] Omni-Mesh ready. Available capabilities:", window.OmniMesh.getCapabilities());
  console.log("[Boot] Usage examples:");
  console.log("  - generateOmniImage('cyberpunk cityscape')");
  console.log("  - set4DRotation(Math.PI/4, Math.PI/6)");
  console.log("  - window.sendOmniCommand('image-generation', 'IMAGE_GENERATION_REQUEST', {...})");

  return { imageProvider, crdtStore };
}

// Auto-expose examples globally
if (typeof window !== 'undefined') {
  window.generateOmniImage = generateOmniImage;
  window.set4DRotation = set4DRotation;
  window.initializeOmniMesh = initializeOmniMesh;
  window.setupEventListeners = setupEventListeners;
  window.useContentAdapter = useContentAdapter;
  window.bootOmniMesh = bootOmniMesh;
  
  console.log("[Omni-Mesh] Examples loaded. Run bootOmniMesh() to initialize full system.");
}
