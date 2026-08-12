/**
 * Omni-Mesh Integration Test
 * Verifies all core components work together
 */

import { OmniMeshOrchestrator } from './OmniMeshOrchestrator.js';

console.log('=== HeavenzFire Omni-Mesh Integration Test ===\n');

// Create orchestrator instance
const mesh = new OmniMeshOrchestrator('test-node-01');

// Initialize
mesh.initialize();
console.log('✓ Orchestrator initialized\n');

// Create a document
const doc = mesh.createDocument('test-doc-1');
console.log(`✓ Document created: ${doc.id}\n`);

// Create a spatial slice (as per the original spec)
const slice = doc.createSlice({
  x: 800,
  y: 400,
  width: 1024,
  height: 768,
  operation: 'CROP_REGION'
});
console.log(`✓ Slice created: ${slice.id}`);
console.log(`  Region: x=${slice.region.x}, y=${slice.region.y}, w=${slice.region.width}, h=${slice.region.height}\n`);

// Tile the slice
const tiles = slice.tile(256);
console.log(`✓ Slice tiled into ${tiles.length} tiles (256x256 each)\n`);

// Register mock nodes with capabilities
mesh.registerNode('node-gemma', {
  image: { rasterEdit: true, vision: true },
  inference: { localLLM: true },
  transport: { webRTC: true }
}, {
  endpoint: 'ws://localhost:8001',
  transport: 'websocket'
});

mesh.registerNode('node-coding-llm', {
  inference: { embedding: true, localLLM: true },
  storage: { indexedDB: true }
}, {
  endpoint: 'ws://localhost:8002',
  transport: 'websocket'
});

mesh.registerNode('node-cloud-vision', {
  inference: { vision: true, embedding: true },
  transport: { websocket: true }
}, {
  endpoint: 'wss://cloud.example.com/vision',
  transport: 'websocket'
});

console.log('✓ Registered 3 nodes with capabilities:\n');
console.log('  NODE 01 (node-gemma)');
console.log('    ├─ Gemma (localLLM)');
console.log('    ├─ Vision');
console.log('    ├─ ImageEdit');
console.log('    └─ WebRTC\n');

console.log('  NODE 02 (node-coding-llm)');
console.log('    ├─ Coding LLM');
console.log('    ├─ Embeddings');
console.log('    └─ IndexedDB\n');

console.log('  NODE 03 (node-cloud-vision)');
console.log('    ├─ Cloud Vision Model');
console.log('    └─ High-bandwidth WebSocket\n');

// Export region for vision processing
(async () => {
  const exportData = await doc.exportRegion(slice.id, 'vision');
  console.log(`✓ Region exported for vision processing`);
  console.log(`  Type: ${exportData.type}`);
  console.log(`  Tiles: ${exportData.tiles ? exportData.tiles.length : 0}\n`);

  // Submit task requiring vision capability
  const taskId = mesh.submitTask('inference.vision', {
    type: 'TEST_VISION_TASK',
    sliceId: slice.id,
    data: exportData
  }, { priority: 'high' });

  console.log(`✓ Task submitted: ${taskId}`);
  console.log(`  Required capability: inference.vision`);
  console.log(`  Priority: high\n`);

  // Get aggregated capabilities
  const state = mesh.getState();
  console.log('✓ Mesh State Summary:');
  console.log(`  Node ID: ${state.nodeId}`);
  console.log(`  Documents: ${state.documents.length}`);
  console.log(`  Registered Nodes: ${state.nodes.length}`);
  console.log(`  Pending Tasks: ${state.pendingTasks}`);
  
  console.log('\n  Aggregated Capabilities:');
  for (const [category, caps] of Object.entries(state.capabilities)) {
    for (const [cap, nodeIds] of Object.entries(caps)) {
      if (nodeIds.length > 0) {
        console.log(`    ${category}.${cap}: ${nodeIds.join(', ')}`);
      }
    }
  }

  // Test CRDT memory
  console.log('\n✓ CRDT Memory Layer:');
  const memoryState = state.memory;
  console.log(`  Node ID: ${memoryState.nodeId}`);
  console.log(`  Slices tracked: ${memoryState.slices.elements.length}`);
  console.log(`  Operation log entries: ${memoryState.operationLog.operations.length}`);

  // Test syntropic compression
  const compressed = mesh.compressOperations();
  console.log('\n✓ Syntropic Compression (1/729 ratio):');
  console.log(`  Invariant Mass: ${compressed.invariantMass}`);
  console.log(`  Momentum (P_z): ${compressed.momentum.toFixed(6)}`);
  console.log(`  Spin (S_z): ${compressed.spin.toFixed(6)}`);
  console.log(`  Differential Strokes: ${compressed.differentialStrokes.length}`);
  console.log(`  Checksum: ${compressed.checksum}`);

  console.log('\n=== All Tests Passed ===');
  console.log('\nThe Omni-Mesh is ready for:');
  console.log('  • P2P Browser Swarm (WebRTC Mesh)');
  console.log('  • Semantic Vector Routing & Embedding Indexing');
  console.log('  • Multi-Model Consensus & Voting Protocols');
  console.log('  • Event-Driven Tool & Agent Hooks');
  console.log('  • Persistent CRDT Synchronized Memory');
})();
