/**
 * HeavenzFire Omni-Mesh - Main Orchestrator
 * 
 * Unifies Image Document Engine, Capability-Based Node Router, and CRDT Memory
 * into a single provider-neutral orchestration layer.
 * 
 * Routes work according to capability rather than hard-coded provider names.
 */

import { ImageDocument, SyntropicCompressor } from './ImageDocument.js';
import { NodeRegistry, TaskQueue } from './NodeRouter.js';
import { CRDTDocumentStore } from './CRDTMemory.js';
import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';

export class OmniMeshOrchestrator {
  constructor(nodeId = null) {
    this.nodeId = nodeId || `node_${uuidv4().slice(0, 8)}`;
    
    // Core subsystems
    this.documents = new Map(); // docId → ImageDocument
    this.nodeRegistry = new NodeRegistry();
    this.taskQueue = new TaskQueue(this.nodeRegistry);
    this.memory = new CRDTDocumentStore(this.nodeId);
    
    // Event bus for cross-system coordination
    this.eventBus = new EventEmitter();
    
    // Mesh state
    this.isInitialized = false;
    this.startedAt = null;
    
    // Bind internal event handlers
    this._bindEventHandlers();
  }

  _bindEventHandlers() {
    // Forward node registry events
    this.nodeRegistry.on('node:register', (data) => {
      this.eventBus.emit('mesh:node:register', data);
      this.memory.updateCapabilities(this._aggregateCapabilities());
    });

    this.nodeRegistry.on('node:unregister', (data) => {
      this.eventBus.emit('mesh:node:unregister', data);
      this.memory.updateCapabilities(this._aggregateCapabilities());
    });

    this.nodeRegistry.on('route:success', (data) => {
      this.eventBus.emit('mesh:route:success', data);
    });

    this.nodeRegistry.on('route:fail', (data) => {
      this.eventBus.emit('mesh:route:fail', data);
    });

    // Forward task queue events
    this.taskQueue.on('task:submit', (data) => {
      this.eventBus.emit('mesh:task:submit', data);
    });

    this.taskQueue.on('task:complete', (data) => {
      this.eventBus.emit('mesh:task:complete', data);
      this._storeTaskResult(data.task);
    });

    this.taskQueue.on('task:fail', (data) => {
      this.eventBus.emit('mesh:task:fail', data);
    });

    // Forward memory events
    this.memory.on('slice:add', (data) => {
      this.eventBus.emit('mesh:memory:slice:add', data);
    });

    this.memory.on('slice:update', (data) => {
      this.eventBus.emit('mesh:memory:slice:update', data);
    });

    this.memory.on('state:merge', (data) => {
      this.eventBus.emit('mesh:memory:merge', data);
    });
  }

  /**
   * Initialize the orchestrator
   */
  initialize() {
    if (this.isInitialized) return;

    // Register self as a node with local capabilities
    this.nodeRegistry.registerNode(this.nodeId, {
      image: {
        rasterEdit: true,
        crop: true,
        segmentation: true,
        tiling: true
      },
      inference: {
        localLLM: false,
        vision: false,
        embedding: false
      },
      transport: {
        webRTC: false,
        websocket: true
      },
      storage: {
        indexedDB: true,
        crdt: true
      }
    });

    this.isInitialized = true;
    this.startedAt = Date.now();
    
    this.eventBus.emit('mesh:initialize', {
      nodeId: this.nodeId,
      timestamp: this.startedAt
    });

    console.log(`[Omni-Mesh] Initialized node ${this.nodeId}`);
  }

  /**
   * Create or open an image document
   * @param {string} docId 
   * @returns {ImageDocument}
   */
  createDocument(docId = null) {
    const doc = new ImageDocument(docId);
    this.documents.set(doc.id, doc);
    
    // Track in CRDT memory
    this.memory.addSlice(doc.id);
    
    this.eventBus.emit('mesh:document:create', { docId: doc.id });
    
    return doc;
  }

  getDocument(docId) {
    return this.documents.get(docId);
  }

  /**
   * Register a remote node with capabilities
   * @param {string} nodeId 
   * @param {Object} capabilities 
   * @param {Object} metadata - endpoint, transport, etc.
   * @returns {Node}
   */
  registerNode(nodeId, capabilities, metadata = {}) {
    const node = this.nodeRegistry.registerNode(nodeId, capabilities);
    
    if (metadata.endpoint) {
      node.setEndpoint(metadata.endpoint, metadata.transport || 'websocket');
    }
    
    return node;
  }

  unregisterNode(nodeId) {
    return this.nodeRegistry.unregisterNode(nodeId);
  }

  /**
   * Submit a task to be routed to capable nodes
   * @param {string} requiredCapability - e.g., 'inference.vision'
   * @param {Object} payload 
   * @param {Object} options 
   * @returns {string} taskId
   */
  submitTask(requiredCapability, payload, options = {}) {
    return this.taskQueue.submit(requiredCapability, payload, options);
  }

  /**
   * Process a spatial slice through the mesh
   * @param {string} docId 
   * @param {Object} regionParams - x, y, width, height
   * @param {string} targetType - embedding|vision|inference
   * @param {Object} options 
   * @returns {Promise<Object>}
   */
  async processSlice(docId, regionParams, targetType, options = {}) {
    const doc = this.documents.get(docId);
    if (!doc) {
      throw new Error(`Document ${docId} not found`);
    }

    // Create slice
    const slice = doc.createSlice(regionParams);
    
    // Tile if region is large
    if (regionParams.width > 512 || regionParams.height > 512) {
      slice.tile(256);
    }

    // Export for target type
    const exportData = await doc.exportRegion(slice.id, targetType);
    
    // Determine required capability
    const capabilityMap = {
      embedding: 'inference.embedding',
      vision: 'inference.vision',
      inference: 'inference.localLLM'
    };
    
    const requiredCapability = capabilityMap[targetType] || 'inference.localLLM';
    
    // Submit as task
    const taskId = this.submitTask(requiredCapability, {
      type: 'SLICE_PROCESSING',
      docId,
      sliceId: slice.id,
      targetType,
      exportData
    }, options);

    this.eventBus.emit('mesh:slice:process', {
      docId,
      sliceId: slice.id,
      taskId,
      targetType
    });

    return { sliceId: slice.id, taskId };
  }

  /**
   * Merge state from a remote node (CRDT synchronization)
   * @param {Object} remoteState 
   */
  syncWithRemote(remoteState) {
    const changed = this.memory.merge(remoteState);
    
    if (changed) {
      this.eventBus.emit('mesh:sync:complete', {
        remoteNodeId: remoteState.nodeId
      });
    }
    
    return changed;
  }

  /**
   * Get current mesh state for synchronization
   * @returns {Object}
   */
  getState() {
    return {
      nodeId: this.nodeId,
      isInitialized: this.isInitialized,
      startedAt: this.startedAt,
      documents: Array.from(this.documents.keys()),
      nodes: this.nodeRegistry.getAllNodes().map(n => ({
        id: n.id,
        capabilities: n.capabilities,
        status: n.status,
        latency: n.latency,
        load: n.load
      })),
      memory: this.memory.getState(),
      pendingTasks: this.taskQueue.pendingTasks.length,
      capabilities: this._aggregateCapabilities()
    };
  }

  /**
   * Aggregate capabilities across all registered nodes
   * @returns {Object}
   */
  _aggregateCapabilities() {
    const aggregated = {
      image: {},
      inference: {},
      transport: {},
      storage: {}
    };

    const nodes = this.nodeRegistry.getAllNodes();
    
    for (const node of nodes) {
      for (const [category, caps] of Object.entries(node.capabilities)) {
        for (const [cap, enabled] of Object.entries(caps)) {
          if (enabled) {
            if (!aggregated[category][cap]) {
              aggregated[category][cap] = [];
            }
            aggregated[category][cap].push(node.id);
          }
        }
      }
    }

    return aggregated;
  }

  _storeTaskResult(task) {
    // Store completed task result in CRDT memory
    this.memory.updateSliceData(task.payload?.sliceId, {
      lastTaskId: task.id,
      lastTaskResult: task.result,
      lastTaskCompletedAt: task.completedAt
    });
  }

  /**
   * Compress operation log using syntropic compression (1/729 ratio)
   * @returns {Object} Compressed representation
   */
  compressOperations() {
    return this.memory.compress();
  }

  on(event, listener) {
    this.eventBus.on(event, listener);
  }

  off(event, listener) {
    this.eventBus.off(event, listener);
  }

  once(event, listener) {
    this.eventBus.once(event, listener);
  }
}

export default OmniMeshOrchestrator;
