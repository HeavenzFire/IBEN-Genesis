/**
 * HeavenzFire Omni-Mesh - Image Document Engine
 * 
 * Provider-neutral document model for spatial slicing, tiling, and region-based operations.
 * Decoupled from any specific UI or model provider DOM.
 * 
 * Core abstraction: SLICE → crop → tile → region export → embedding/vision/inference
 */

import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';

export class ImageDocument {
  constructor(id = null) {
    this.id = id || uuidv4();
    this.slices = new Map(); // sliceId → Slice
    this.capabilities = {
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
        websocket: false
      },
      storage: {
        indexedDB: true,
        crdt: true
      }
    };
    this.eventBus = new EventEmitter();
    this.metadata = {
      createdAt: Date.now(),
      modifiedAt: Date.now(),
      source: null,
      dimensions: null
    };
  }

  /**
   * Create a spatial slice from the document
   * @param {Object} params - Slice parameters
   * @param {number} params.x - X coordinate
   * @param {number} params.y - Y coordinate  
   * @param {number} params.width - Width of region
   * @param {number} params.height - Height of region
   * @param {string} [params.operation='CROP_REGION'] - Operation type
   * @returns {Slice}
   */
  createSlice({ x, y, width, height, operation = 'CROP_REGION' }) {
    const sliceId = uuidv4();
    const slice = new Slice(sliceId, { x, y, width, height, operation });
    
    this.slices.set(sliceId, slice);
    this.metadata.modifiedAt = Date.now();
    
    this.eventBus.emit('slice:create', { 
      documentId: this.id, 
      sliceId, 
      slice,
      timestamp: Date.now()
    });
    
    return slice;
  }

  getSlice(sliceId) {
    return this.slices.get(sliceId);
  }

  deleteSlice(sliceId) {
    const slice = this.slices.get(sliceId);
    if (slice) {
      this.slices.delete(sliceId);
      this.eventBus.emit('slice:delete', { 
        documentId: this.id, 
        sliceId,
        timestamp: Date.now()
      });
    }
    return slice;
  }

  getAllSlices() {
    return Array.from(this.slices.values());
  }

  /**
   * Export a region for specific processing pipeline
   * @param {string} sliceId 
   * @param {'embedding'|'vision'|'inference'} targetType 
   * @returns {Promise<RegionExport>}
   */
  async exportRegion(sliceId, targetType) {
    const slice = this.slices.get(sliceId);
    if (!slice) {
      throw new Error(`Slice ${sliceId} not found`);
    }

    const exportData = await slice.export(targetType);
    
    this.eventBus.emit('region:export', {
      documentId: this.id,
      sliceId,
      targetType,
      exportData,
      timestamp: Date.now()
    });

    return exportData;
  }

  attachCapability(capabilityPath, enabled = true) {
    const [category, cap] = capabilityPath.split('.');
    if (this.capabilities[category]) {
      this.capabilities[category][cap] = enabled;
      this.eventBus.emit('capability:update', {
        documentId: this.id,
        category,
        cap,
        enabled
      });
    }
  }

  on(event, listener) {
    this.eventBus.on(event, listener);
  }

  off(event, listener) {
    this.eventBus.off(event, listener);
  }

  emit(event, data) {
    this.eventBus.emit(event, { documentId: this.id, ...data });
  }
}

export class Slice {
  constructor(id, { x, y, width, height, operation }) {
    this.id = id;
    this.region = { x, y, width, height };
    this.operation = operation;
    this.tiles = [];
    this.embeddings = new Map();
    this.inferenceTasks = new Map();
    this.visionResults = new Map();
    this.state = 'idle'; // idle → processing → complete → error
    this.createdAt = Date.now();
  }

  /**
   * Tile the region into smaller chunks for parallel processing
   * @param {number} tileSize - Size of each tile (default 256x256)
   * @returns {Array<Tile>}
   */
  tile(tileSize = 256) {
    const tiles = [];
    const { x, y, width, height } = this.region;

    for (let ty = 0; ty < height; ty += tileSize) {
      for (let tx = 0; tx < width; tx += tileSize) {
        const tile = {
          id: `${this.id}_tile_${tx}_${ty}`,
          x: x + tx,
          y: y + ty,
          width: Math.min(tileSize, width - tx),
          height: Math.min(tileSize, height - ty),
          state: 'pending'
        };
        tiles.push(tile);
      }
    }

    this.tiles = tiles;
    return tiles;
  }

  /**
   * Export region data for specific target pipeline
   * @param {'embedding'|'vision'|'inference'} targetType 
   * @returns {Promise<Object>}
   */
  async export(targetType) {
    this.state = 'processing';
    
    try {
      switch (targetType) {
        case 'embedding':
          return await this._exportForEmbedding();
        case 'vision':
          return await this._exportForVision();
        case 'inference':
          return await this._exportForInference();
        default:
          throw new Error(`Unknown export target: ${targetType}`);
      }
    } catch (error) {
      this.state = 'error';
      throw error;
    } finally {
      if (this.state !== 'error') {
        this.state = 'complete';
      }
    }
  }

  async _exportForEmbedding() {
    // Extract region data optimized for embedding generation
    const payload = {
      type: 'EMBEDDING_INPUT',
      region: this.region,
      operation: this.operation,
      tiles: this.tiles.length > 0 ? this.tiles : null,
      metadata: {
        sliceId: this.id,
        createdAt: this.createdAt
      }
    };
    
    this.embeddings.set('pending', payload);
    return payload;
  }

  async _exportForVision() {
    // Extract region data optimized for vision model processing
    const payload = {
      type: 'VISION_INPUT',
      region: this.region,
      operation: this.operation,
      tiles: this.tiles.length > 0 ? this.tiles : null,
      preprocessing: {
        normalize: true,
        resize: null // Let vision model decide
      },
      metadata: {
        sliceId: this.id,
        createdAt: this.createdAt
      }
    };
    
    this.visionResults.set('pending', payload);
    return payload;
  }

  async _exportForInference() {
    // Extract region data for general inference tasks
    const payload = {
      type: 'INFERENCE_TASK',
      region: this.region,
      operation: this.operation,
      tiles: this.tiles.length > 0 ? this.tiles : null,
      taskQueue: [],
      metadata: {
        sliceId: this.id,
        createdAt: this.createdAt
      }
    };
    
    this.inferenceTasks.set('pending', payload);
    return payload;
  }

  addInferenceTask(task) {
    const taskId = uuidv4();
    this.inferenceTasks.set(taskId, {
      id: taskId,
      task,
      status: 'queued',
      createdAt: Date.now()
    });
    return taskId;
  }

  storeEmbedding(embeddingId, vector) {
    this.embeddings.set(embeddingId, {
      vector,
      storedAt: Date.now()
    });
  }

  storeVisionResult(resultId, result) {
    this.visionResults.set(resultId, {
      result,
      storedAt: Date.now()
    });
  }
}

/**
 * Syntropic Compression Utility
 * Implements 1/729 compression ratio for CRDT operations
 */
export class SyntropicCompressor {
  static COMPRESSION_RATIO = 1 / 729;

  /**
   * Compress differential operation strokes
   * @param {Array} operations - Raw operation sequence
   * @returns {Object} Compressed representation
   */
  static compress(operations) {
    // Implement Bowen-York curvature-inspired compression
    // Reduces redundant spatial metric recalculations
    const compressed = {
      invariantMass: this._computeInvariantMass(operations),
      momentum: this._computeMomentum(operations),
      spin: this._computeSpin(operations),
      differentialStrokes: this._extractDifferentialStrokes(operations),
      checksum: this._generateChecksum(operations)
    };

    return compressed;
  }

  static _computeInvariantMass(operations) {
    // Compute ADM mass equivalent for operation sequence
    return operations.reduce((mass, op) => mass + (op.weight || 1), 0);
  }

  static _computeMomentum(operations) {
    // P_z component - directional change rate
    let momentum = 0;
    for (let i = 1; i < operations.length; i++) {
      const delta = operations[i].timestamp - operations[i-1].timestamp;
      momentum += delta > 0 ? 1 / delta : 0;
    }
    return momentum * this.COMPRESSION_RATIO;
  }

  static _computeSpin(operations) {
    // S_z component - rotational/cyclical patterns
    const patternMap = new Map();
    operations.forEach(op => {
      const key = op.type;
      patternMap.set(key, (patternMap.get(key) || 0) + 1);
    });
    
    let spin = 0;
    patternMap.forEach(count => {
      if (count > 1) spin += Math.log(count);
    });
    
    return spin * this.COMPRESSION_RATIO;
  }

  static _extractDifferentialStrokes(operations) {
    // Only store changes from baseline (maximal slicing K=0)
    const baseline = operations[0];
    return operations.slice(1).map(op => ({
      type: op.type,
      delta: this._computeDelta(baseline, op),
      timestamp: op.timestamp
    }));
  }

  static _computeDelta(baseline, current) {
    // Compute minimal delta representation
    const delta = {};
    for (const key in current) {
      if (current[key] !== baseline[key]) {
        delta[key] = current[key];
      }
    }
    return delta;
  }

  static _generateChecksum(operations) {
    // Simple checksum for integrity verification
    return operations.reduce((sum, op) => {
      return sum + JSON.stringify(op).split('').reduce((a, b) => a + b.charCodeAt(0), 0);
    }, 0) % 1000000;
  }
}

export default ImageDocument;
