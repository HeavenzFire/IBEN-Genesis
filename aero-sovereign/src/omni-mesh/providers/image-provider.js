/**
 * Local Image Provider - Connects to diffusion backends (ComfyUI, Stable Diffusion, etc.)
 * 
 * Provider-neutral adapter for image generation capabilities.
 * Endpoint can be swapped without changing Omni-Mesh core.
 */

class LocalImageProvider {
  /**
   * @param {string} endpoint - Base URL of image generation backend (e.g., "http://127.0.0.1:8188")
   */
  constructor(endpoint) {
    this.endpoint = endpoint.replace(/\/$/, "");
  }

  /**
   * Execute image generation request
   * @param {object} request - Request with payload: { prompt, width, height, steps, seed }
   * @returns {Promise<object>} Generated image result
   */
  async execute(request) {
    const { prompt, width = 1024, height = 1024, steps = 30, seed = -1 } = request.payload || {};

    if (!prompt) {
      throw new Error("Prompt required for image generation");
    }

    const response = await fetch(`${this.endpoint}/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        prompt,
        width,
        height,
        steps,
        seed
      })
    });

    if (!response.ok) {
      throw new Error(`Image backend HTTP ${response.status}`);
    }

    return response.json();
  }
}

// Auto-register if running in browser with default endpoint
if (typeof window !== 'undefined' && window.OmniMesh) {
  console.log("[Omni-Mesh] LocalImageProvider loaded - register with: OmniMesh.capability('image-generation', new LocalImageProvider('http://127.0.0.1:8188'))");
}
