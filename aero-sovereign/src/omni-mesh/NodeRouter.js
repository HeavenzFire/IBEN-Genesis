/**
 * HeavenzFire Omni-Mesh - Capability-Based Node Router
 * 
 * Discovers and routes work to nodes based on capabilities rather than hardcoded providers.
 * Implements the actual Omni-Mesh: capability hyper-mesh routing under maximal slicing.
 */

import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';

export class NodeRegistry {
  constructor() {
    this.nodes = new Map(); // nodeId → Node
    this.capabilityIndex = new Map(); // capabilityPath → Set<nodeId>
    this.eventBus = new EventEmitter();
  }

  /**
   * Register a new node with its capabilities
   * @param {string} nodeId 
   * @param {Object} capabilities 
   * @returns {Node}
   */
  registerNode(nodeId, capabilities) {
    const node = new Node(nodeId, capabilities);
    this.nodes.set(nodeId, node);
    
    // Index capabilities for fast lookup
    this._indexCapabilities(nodeId, capabilities);
    
    this.eventBus.emit('node:register', { nodeId, capabilities });
    return node;
  }

  _indexCapabilities(nodeId, capabilities) {
    for (const [category, caps] of Object.entries(capabilities)) {
      for (const [cap, enabled] of Object.entries(caps)) {
        if (enabled) {
          const capPath = `${category}.${cap}`;
          if (!this.capabilityIndex.has(capPath)) {
            this.capabilityIndex.set(capPath, new Set());
          }
          this.capabilityIndex.get(capPath).add(nodeId);
        }
      }
    }
  }

  unregisterNode(nodeId) {
    const node = this.nodes.get(nodeId);
    if (node) {
      // Remove from capability index
      for (const [category, caps] of Object.entries(node.capabilities)) {
        for (const [cap, enabled] of Object.entries(caps)) {
          if (enabled) {
            const capPath = `${category}.${cap}`;
            const nodeSet = this.capabilityIndex.get(capPath);
            if (nodeSet) {
              nodeSet.delete(nodeId);
              if (nodeSet.size === 0) {
                this.capabilityIndex.delete(capPath);
              }
            }
          }
        }
      }
      
      this.nodes.delete(nodeId);
      this.eventBus.emit('node:unregister', { nodeId });
    }
    return node;
  }

  /**
   * Find nodes capable of handling a specific capability
   * @param {string} capabilityPath - e.g., 'inference.vision'
   * @returns {Array<Node>}
   */
  findNodesByCapability(capabilityPath) {
    const nodeIds = this.capabilityIndex.get(capabilityPath);
    if (!nodeIds) return [];
    
    return Array.from(nodeIds)
      .map(id => this.nodes.get(id))
      .filter(Boolean);
  }

  /**
   * Route a task to the best available node based on capability
   * @param {string} requiredCapability 
   * @param {Object} task 
   * @param {Object} [routingStrategy='latency'] - latency|load|roundrobin
   * @returns {Node|null}
   */
  routeTask(requiredCapability, task, routingStrategy = 'latency') {
    const candidates = this.findNodesByCapability(requiredCapability);
    
    if (candidates.length === 0) {
      this.eventBus.emit('route:fail', { 
        requiredCapability, 
        task,
        reason: 'no_capable_nodes'
      });
      return null;
    }

    let selectedNode;
    switch (routingStrategy) {
      case 'latency':
        selectedNode = this._selectByLatency(candidates);
        break;
      case 'load':
        selectedNode = this._selectByLoad(candidates);
        break;
      case 'roundrobin':
        selectedNode = this._selectRoundRobin(candidates);
        break;
      default:
        selectedNode = candidates[0];
    }

    this.eventBus.emit('route:success', {
      requiredCapability,
      task,
      selectedNodeId: selectedNode.id,
      strategy: routingStrategy
    });

    return selectedNode;
  }

  _selectByLatency(candidates) {
    return candidates.reduce((best, node) => {
      return node.latency < best.latency ? node : best;
    }, candidates[0]);
  }

  _selectByLoad(candidates) {
    return candidates.reduce((best, node) => {
      return node.load < best.load ? node : best;
    }, candidates[0]);
  }

  _selectRoundRobin(candidates) {
    // Simple round-robin using timestamp modulo
    const index = Date.now() % candidates.length;
    return candidates[index];
  }

  getAllNodes() {
    return Array.from(this.nodes.values());
  }

  getNode(nodeId) {
    return this.nodes.get(nodeId);
  }

  on(event, listener) {
    this.eventBus.on(event, listener);
  }

  off(event, listener) {
    this.eventBus.off(event, listener);
  }
}

export class Node {
  constructor(id, capabilities) {
    this.id = id;
    this.capabilities = capabilities;
    this.status = 'active'; // active|inactive|degraded
    this.latency = Math.random() * 100 + 10; // ms, would be measured in real impl
    this.load = 0; // 0-1 scale
    this.lastHeartbeat = Date.now();
    this.metadata = {
      registeredAt: Date.now(),
      endpoint: null,
      transport: null
    };
  }

  updateHealth({ latency, load, status }) {
    if (latency !== undefined) this.latency = latency;
    if (load !== undefined) this.load = load;
    if (status !== undefined) this.status = status;
    this.lastHeartbeat = Date.now();
  }

  hasCapability(capabilityPath) {
    const [category, cap] = capabilityPath.split('.');
    return this.capabilities[category]?.[cap] === true;
  }

  setEndpoint(endpoint, transport = 'websocket') {
    this.metadata.endpoint = endpoint;
    this.metadata.transport = transport;
  }

  isHealthy() {
    const now = Date.now();
    const heartbeatAge = now - this.lastHeartbeat;
    return this.status === 'active' && heartbeatAge < 30000; // 30s timeout
  }
}

/**
 * Task Queue for Omni-Mesh routing
 * Manages task distribution across capable nodes
 */
export class TaskQueue {
  constructor(nodeRegistry) {
    this.registry = nodeRegistry;
    this.tasks = new Map(); // taskId → Task
    this.pendingTasks = [];
    this.eventBus = new EventEmitter();
  }

  /**
   * Submit a task requiring specific capabilities
   * @param {string} requiredCapability 
   * @param {Object} payload 
   * @param {Object} options 
   * @returns {string} taskId
   */
  submit(requiredCapability, payload, options = {}) {
    const taskId = uuidv4();
    const task = {
      id: taskId,
      requiredCapability,
      payload,
      status: 'pending',
      priority: options.priority || 'normal',
      createdAt: Date.now(),
      attempts: 0,
      maxAttempts: options.maxAttempts || 3,
      result: null,
      error: null
    };

    this.tasks.set(taskId, task);
    this.pendingTasks.push(task);

    this.eventBus.emit('task:submit', { taskId, task });

    // Attempt immediate routing
    this._processPendingTasks();

    return taskId;
  }

  _processPendingTasks() {
    // Sort by priority then timestamp
    this.pendingTasks.sort((a, b) => {
      const priorityOrder = { high: 0, normal: 1, low: 2 };
      if (priorityOrder[a.priority] !== priorityOrder[b.priority]) {
        return priorityOrder[a.priority] - priorityOrder[b.priority];
      }
      return a.createdAt - b.createdAt;
    });

    // Process tasks while we have capacity
    while (this.pendingTasks.length > 0) {
      const task = this.pendingTasks[0];
      const node = this.registry.routeTask(task.requiredCapability, task.payload);

      if (!node) {
        // No capable node available, leave in queue
        break;
      }

      this.pendingTasks.shift();
      this._dispatchTask(task, node);
    }
  }

  async _dispatchTask(task, node) {
    task.status = 'dispatched';
    task.attempts++;
    task.dispatchedTo = node.id;
    task.dispatchedAt = Date.now();

    this.eventBus.emit('task:dispatch', { task, nodeId: node.id });

    try {
      // In real implementation, this would call the node's endpoint
      const result = await this._executeOnNode(node, task.payload);
      
      task.status = 'complete';
      task.result = result;
      task.completedAt = Date.now();

      this.eventBus.emit('task:complete', { task, result });
    } catch (error) {
      task.status = 'failed';
      task.error = error.message;

      if (task.attempts < task.maxAttempts) {
        // Retry
        task.status = 'pending';
        this.pendingTasks.push(task);
        this.eventBus.emit('task:retry', { task, attempt: task.attempts });
      } else {
        this.eventBus.emit('task:fail', { task, error });
      }
    }
  }

  async _executeOnNode(node, payload) {
    // Placeholder for actual node communication
    // Would use WebSocket, WebRTC, or HTTP based on node metadata
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ 
          nodeId: node.id, 
          processed: true, 
          timestamp: Date.now(),
          data: payload 
        });
      }, node.latency);
    });
  }

  getTask(taskId) {
    return this.tasks.get(taskId);
  }

  cancelTask(taskId) {
    const task = this.tasks.get(taskId);
    if (task && task.status === 'pending') {
      task.status = 'cancelled';
      const index = this.pendingTasks.findIndex(t => t.id === taskId);
      if (index !== -1) {
        this.pendingTasks.splice(index, 1);
      }
      this.eventBus.emit('task:cancel', { taskId });
      return true;
    }
    return false;
  }

  on(event, listener) {
    this.eventBus.on(event, listener);
  }

  off(event, listener) {
    this.eventBus.off(event, listener);
  }
}

export default NodeRegistry;
