/**
 * Omni-Mesh Core - Provider-Neutral Document Engine + Event Bus
 * 
 * Decouples the system from any specific UI or model provider DOM.
 * Routes work by capability, not hardcoded provider names.
 */

(() => {
  /**
   * EventBus - Reactive middleware interceptors and autonomous swarm loops
   * Emits lifecycle events: CAPABILITY_REGISTERED, EXECUTION_STARTED/COMPLETE/FAILED,
   * DOCUMENT_CREATED, OPERATION_APPLIED
   */
  class EventBus {
    constructor() {
      this.listeners = new Map();
    }

    on(type, handler) {
      if (!this.listeners.has(type)) {
        this.listeners.set(type, new Set());
      }
      this.listeners.get(type).add(handler);
      return () => this.listeners.get(type)?.delete(handler);
    }

    emit(type, payload = {}) {
      const handlers = this.listeners.get(type) || [];
      for (const handler of handlers) {
        try {
          handler(payload);
        } catch (err) {
          console.error(`[OmniMesh:${type}]`, err);
        }
      }
    }
  }

  /**
   * CapabilityRouter - Discovers nodes by capability, not provider name
   * Routes tasks to nodes with matching capabilities (vision, embedding, webRTC, etc.)
   */
  class CapabilityRouter {
    constructor(bus) {
      this.bus = bus;
      this.providers = new Map();
    }

    register(capability, provider) {
      this.providers.set(capability, provider);
      this.bus.emit("CAPABILITY_REGISTERED", { capability });
    }

    has(capability) {
      return this.providers.has(capability);
    }

    async execute(capability, request) {
      const provider = this.providers.get(capability);
      if (!provider) {
        throw new Error(`Capability unavailable: ${capability}`);
      }

      this.bus.emit("CAPABILITY_EXECUTION_STARTED", {
        capability,
        requestId: request.id
      });

      try {
        const result = await provider.execute(request);
        this.bus.emit("CAPABILITY_EXECUTION_COMPLETE", {
          capability,
          requestId: request.id,
          result
        });
        return result;
      } catch (error) {
        this.bus.emit("CAPABILITY_EXECUTION_FAILED", {
          capability,
          requestId: request.id,
          error: String(error)
        });
        throw error;
      }
    }
  }

  /**
   * DocumentEngine - Image Document Engine (SLICE → crop → tile → export)
   * Manages documents with CRDT-style operations, revisions, and metadata
   */
  class DocumentEngine {
    constructor(bus) {
      this.bus = bus;
      this.documents = new Map();
    }

    createDocument(source = {}) {
      const document = {
        id: crypto.randomUUID(),
        source,
        layers: [],
        operations: [],
        metadata: {},
        revision: 0,
        createdAt: Date.now(),
        updatedAt: Date.now()
      };

      this.documents.set(document.id, document);
      this.bus.emit("DOCUMENT_CREATED", document);
      return document;
    }

    get(documentId) {
      return this.documents.get(documentId);
    }

    apply(documentId, operation) {
      const document = this.documents.get(documentId);
      if (!document) {
        throw new Error(`Document not found: ${documentId}`);
      }

      operation.revision = document.revision + 1;
      document.operations.push(operation);
      document.revision = operation.revision;
      document.updatedAt = Date.now();

      this.bus.emit("OPERATION_APPLIED", {
        documentId,
        operation
      });

      return document;
    }
  }

  /**
   * OmniMesh - Main orchestrator unifying all subsystems
   * Exposes: .capability(), .execute(), .documents, .bus
   */
  class OmniMesh {
    constructor() {
      this.bus = new EventBus();
      this.router = new CapabilityRouter(this.bus);
      this.documents = new DocumentEngine(this.bus);
    }

    /**
     * Register a capability provider
     * @param {string} name - Capability name (e.g., "image-generation", "4d-manifold")
     * @param {object} provider - Provider with execute(request) method
     */
    capability(name, provider) {
      this.router.register(name, provider);
      return this;
    }

    /**
     * Execute a capability request
     * @param {string} capability - Capability name
     * @param {object} request - Request with id, type, payload
     */
    async execute(capability, request) {
      return this.router.execute(capability, request);
    }

    /**
     * Get registered capabilities
     */
    getCapabilities() {
      return Array.from(this.router.providers.keys());
    }
  }

  // Initialize global instance
  window.OmniMesh = new OmniMesh();
  console.log("[Omni-Mesh] Core initialized - provider-neutral Document Engine + Event Bus ready");
})();
