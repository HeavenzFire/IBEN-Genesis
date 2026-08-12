/**
 * HeavenzFire Omni-Mesh - CRDT Synchronized Memory Layer
 * 
 * Implements Conflict-Free Replicated Data Types for distributed state synchronization
 * across mesh nodes without race conditions. Local-first storage with 1/729 syntropic compression.
 */

import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';
import { SyntropicCompressor } from './ImageDocument.js';

/**
 * LWW (Last-Writer-Wins) Register CRDT
 * Simplest CRDT for single-value state synchronization
 */
export class LWWRegister {
  constructor(nodeId, initialValue = null) {
    this.nodeId = nodeId;
    this.value = initialValue;
    this.timestamp = Date.now();
  }

  set(newValue) {
    const newTimestamp = Date.now();
    if (newTimestamp > this.timestamp) {
      this.value = newValue;
      this.timestamp = newTimestamp;
      return true;
    }
    return false;
  }

  merge(remote) {
    if (remote.timestamp > this.timestamp) {
      this.value = remote.value;
      this.timestamp = remote.timestamp;
      return true;
    }
    return false;
  }

  toJSON() {
    return {
      nodeId: this.nodeId,
      value: this.value,
      timestamp: this.timestamp
    };
  }

  static fromJSON(json) {
    const register = new LWWRegister(json.nodeId, json.value);
    register.timestamp = json.timestamp;
    return register;
  }
}

/**
 * G-Set (Grow-only Set) CRDT
 * For append-only collections like operation logs
 */
export class GSet {
  constructor() {
    this.elements = new Set();
  }

  add(element) {
    this.elements.add(element);
  }

  has(element) {
    return this.elements.has(element);
  }

  merge(remote) {
    let changed = false;
    for (const element of remote.elements) {
      if (!this.elements.has(element)) {
        this.elements.add(element);
        changed = true;
      }
    }
    return changed;
  }

  toArray() {
    return Array.from(this.elements);
  }

  toJSON() {
    return { elements: this.toArray() };
  }

  static fromJSON(json) {
    const gset = new GSet();
    json.elements.forEach(el => gset.add(el));
    return gset;
  }
}

/**
 * OR-Set (Observed-Remove Set) CRDT
 * Supports both add and remove operations with proper conflict resolution
 */
export class ORSet {
  constructor(nodeId) {
    this.nodeId = nodeId;
    this.elements = new Map(); // element → Set<uniqueTag>
    this.tombstones = new Map(); // element → Set<uniqueTag>
  }

  add(element) {
    const uniqueTag = `${this.nodeId}:${Date.now()}:${Math.random()}`;
    
    if (!this.elements.has(element)) {
      this.elements.set(element, new Set());
    }
    this.elements.get(element).add(uniqueTag);
    
    // Clear any tombstones for this element
    if (this.tombstones.has(element)) {
      this.tombstones.delete(element);
    }
    
    return uniqueTag;
  }

  remove(element) {
    if (!this.elements.has(element)) return false;
    
    // Move all tags to tombstones
    const tags = this.elements.get(element);
    this.elements.delete(element);
    
    if (!this.tombstones.has(element)) {
      this.tombstones.set(element, new Set());
    }
    tags.forEach(tag => this.tombstones.get(element).add(tag));
    
    return true;
  }

  has(element) {
    return this.elements.has(element) && this.elements.get(element).size > 0;
  }

  merge(remote) {
    let changed = false;
    
    // Merge remote elements
    for (const [element, remoteTags] of remote.elements) {
      if (!this.elements.has(element)) {
        this.elements.set(element, new Set());
      }
      
      const localTags = this.elements.get(element);
      for (const tag of remoteTags) {
        if (!localTags.has(tag)) {
          localTags.add(tag);
          changed = true;
        }
      }
    }
    
    // Merge tombstones
    for (const [element, remoteTombstones] of remote.tombstones) {
      if (!this.tombstones.has(element)) {
        this.tombstones.set(element, new Set());
      }
      
      const localTombstones = this.tombstones.get(element);
      for (const tag of remoteTombstones) {
        if (!localTombstones.has(tag)) {
          localTombstones.add(tag);
          
          // Remove from elements if present
          if (this.elements.has(element)) {
            this.elements.get(element).delete(tag);
            if (this.elements.get(element).size === 0) {
              this.elements.delete(element);
            }
          }
          changed = true;
        }
      }
    }
    
    return changed;
  }

  toArray() {
    return Array.from(this.elements.keys());
  }

  toJSON() {
    return {
      nodeId: this.nodeId,
      elements: Array.from(this.elements.entries()).map(([k, v]) => [k, Array.from(v)]),
      tombstones: Array.from(this.tombstones.entries()).map(([k, v]) => [k, Array.from(v)])
    };
  }

  static fromJSON(json) {
    const orset = new ORSet(json.nodeId);
    json.elements.forEach(([k, v]) => orset.elements.set(k, new Set(v)));
    json.tombstones.forEach(([k, v]) => orset.tombstones.set(k, new Set(v)));
    return orset;
  }
}

/**
 * Distributed Operation Log with Syntropic Compression
 * Stores differential strokes using Bowen-York curvature principles
 */
export class OperationLog {
  constructor(nodeId) {
    this.nodeId = nodeId;
    this.operations = [];
    this.compressor = SyntropicCompressor;
    this.eventBus = new EventEmitter();
  }

  append(operation) {
    const op = {
      id: uuidv4(),
      nodeId: this.nodeId,
      timestamp: Date.now(),
      ...operation
    };
    
    this.operations.push(op);
    this.eventBus.emit('operation:append', { op });
    
    // Apply compression when log grows large
    if (this.operations.length % 100 === 0) {
      this.compress();
    }
    
    return op;
  }

  compress() {
    const compressed = this.compressor.compress(this.operations);
    this.eventBus.emit('log:compress', { 
      originalSize: this.operations.length,
      compressed,
      ratio: this.compressor.COMPRESSION_RATIO
    });
    return compressed;
  }

  getSince(timestamp) {
    return this.operations.filter(op => op.timestamp > timestamp);
  }

  merge(remoteOperations) {
    // Merge remote operations maintaining causal order
    const merged = [...this.operations, ...remoteOperations];
    merged.sort((a, b) => a.timestamp - b.timestamp);
    
    // Remove duplicates by id
    const seen = new Set();
    this.operations = merged.filter(op => {
      if (seen.has(op.id)) return false;
      seen.add(op.id);
      return true;
    });
    
    this.eventBus.emit('log:merge', { count: remoteOperations.length });
  }

  toJSON() {
    return {
      nodeId: this.nodeId,
      operations: this.operations
    };
  }

  static fromJSON(json) {
    const log = new OperationLog(json.nodeId);
    log.operations = json.operations;
    return log;
  }

  on(event, listener) {
    this.eventBus.on(event, listener);
  }

  off(event, listener) {
    this.eventBus.off(event, listener);
  }
}

/**
 * CRDT Document Store
 * Combines multiple CRDT types for full document state synchronization
 */
export class CRDTDocumentStore {
  constructor(nodeId) {
    this.nodeId = nodeId;
    this.slices = new ORSet(nodeId); // Slice IDs
    this.sliceData = new Map(); // sliceId → LWWRegister
    this.operationLog = new OperationLog(nodeId);
    this.capabilities = new LWWRegister(nodeId, {});
    this.eventBus = new EventEmitter();
  }

  addSlice(sliceId) {
    const tag = this.slices.add(sliceId);
    
    // Initialize slice data register
    if (!this.sliceData.has(sliceId)) {
      this.sliceData.set(sliceId, new LWWRegister(this.nodeId, null));
    }
    
    this.operationLog.append({
      type: 'SLICE_ADD',
      sliceId,
      tag
    });
    
    this.eventBus.emit('slice:add', { sliceId, tag });
    return tag;
  }

  removeSlice(sliceId) {
    this.slices.remove(sliceId);
    
    this.operationLog.append({
      type: 'SLICE_REMOVE',
      sliceId
    });
    
    this.eventBus.emit('slice:remove', { sliceId });
  }

  updateSliceData(sliceId, data) {
    if (!this.sliceData.has(sliceId)) {
      this.sliceData.set(sliceId, new LWWRegister(this.nodeId));
    }
    
    const register = this.sliceData.get(sliceId);
    const updated = register.set(data);
    
    if (updated) {
      this.operationLog.append({
        type: 'SLICE_UPDATE',
        sliceId,
        timestamp: register.timestamp
      });
      
      this.eventBus.emit('slice:update', { sliceId, data });
    }
    
    return updated;
  }

  getSliceData(sliceId) {
    const register = this.sliceData.get(sliceId);
    return register ? register.value : null;
  }

  updateCapabilities(capabilities) {
    const updated = this.capabilities.set(capabilities);
    
    if (updated) {
      this.operationLog.append({
        type: 'CAPABILITIES_UPDATE',
        capabilities,
        timestamp: this.capabilities.timestamp
      });
      
      this.eventBus.emit('capabilities:update', { capabilities });
    }
    
    return updated;
  }

  merge(remoteState) {
    let changed = false;
    
    // Merge slices
    if (this.slices.merge(remoteState.slices)) {
      changed = true;
    }
    
    // Merge slice data
    for (const [sliceId, remoteRegister] of Object.entries(remoteState.sliceData || {})) {
      if (!this.sliceData.has(sliceId)) {
        this.sliceData.set(sliceId, LWWRegister.fromJSON(remoteRegister));
        changed = true;
      } else {
        if (this.sliceData.get(sliceId).merge(remoteRegister)) {
          changed = true;
        }
      }
    }
    
    // Merge capabilities
    if (this.capabilities.merge(remoteState.capabilities)) {
      changed = true;
    }
    
    // Merge operation logs
    if (remoteState.operationLog?.operations) {
      this.operationLog.merge(remoteState.operationLog.operations);
      changed = true;
    }
    
    if (changed) {
      this.eventBus.emit('state:merge', { remoteNodeId: remoteState.nodeId });
    }
    
    return changed;
  }

  getState() {
    return {
      nodeId: this.nodeId,
      slices: this.slices.toJSON(),
      sliceData: Object.fromEntries(
        Array.from(this.sliceData.entries()).map(([k, v]) => [k, v.toJSON()])
      ),
      capabilities: this.capabilities.toJSON(),
      operationLog: this.operationLog.toJSON()
    };
  }

  compress() {
    return this.operationLog.compress();
  }

  on(event, listener) {
    this.eventBus.on(event, listener);
  }

  off(event, listener) {
    this.eventBus.off(event, listener);
  }
}

export default CRDTDocumentStore;
