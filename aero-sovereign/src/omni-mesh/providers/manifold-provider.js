/**
 * 4D Manifold Renderer Provider - Connects hyper-manifold renderer to Omni-Mesh
 * 
 * Transforms the visualization from isolated animation to routed capability.
 * Supports ROTATE_4D, ADD_NODE, and other manifold operations.
 */

class ManifoldRendererProvider {
  /**
   * @param {object} renderer - HyperManifoldRenderer instance with rotation and nodes properties
   */
  constructor(renderer) {
    this.renderer = renderer;
  }

  /**
   * Execute manifold operation
   * @param {object} request - Request with type and payload
   * @returns {Promise<object>} Operation result
   */
  async execute(request) {
    switch (request.type) {
      case "ROTATE_4D": {
        const { xw = 0, yz = 0 } = request.payload || {};
        
        if (this.renderer.rotation) {
          this.renderer.rotation.xw = xw;
          this.renderer.rotation.yz = yz;
        }

        return {
          applied: true,
          rotation: {
            xw: this.renderer.rotation?.xw ?? xw,
            yz: this.renderer.rotation?.yz ?? yz
          }
        };
      }

      case "ADD_NODE": {
        const node = request.payload?.node;
        
        if (!node) {
          throw new Error("Node required for ADD_NODE operation");
        }

        if (this.renderer.nodes) {
          this.renderer.nodes.push(node);
        }

        return {
          applied: true,
          nodeId: node.id
        };
      }

      case "SET_METRIC": {
        const { metric } = request.payload || {};
        
        if (this.renderer.metric) {
          this.renderer.metric = metric;
        }

        return {
          applied: true,
          metric
        };
      }

      case "UPDATE_SLICING": {
        const { K = 0, slicing = 'maximal' } = request.payload || {};
        
        if (this.renderer.slicing) {
          this.renderer.slicing.K = K;
          this.renderer.slicing.type = slicing;
        }

        return {
          applied: true,
          slicing: { K, type: slicing }
        };
      }

      default:
        throw new Error(`Unknown manifold operation: ${request.type}`);
    }
  }
}

// Auto-register if running in browser with renderer available
if (typeof window !== 'undefined' && window.OmniMesh) {
  console.log("[Omni-Mesh] ManifoldRendererProvider loaded - register with: OmniMesh.capability('4d-manifold', new ManifoldRendererProvider(hyperManifoldRenderer))");
}
