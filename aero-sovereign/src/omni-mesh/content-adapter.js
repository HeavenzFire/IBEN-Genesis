/**
 * Content Script Adapter - Omni-Mesh browser extension adapter
 * 
 * Makes ChatGPT's DOM just an external adapter. If the page changes its React structure,
 * the document engine doesn't care. Dispatches OMNI_MESH_COMMAND and listens for results.
 */

(() => {
  if (window.__OMNI_MESH_LOADED__) {
    return;
  }

  window.__OMNI_MESH_LOADED__ = true;
  console.log("[Omni-Mesh] Content adapter initialized - DOM decoupled from Document Engine");

  /**
   * Listen for commands from extension popup or other sources
   */
  window.addEventListener("OMNI_MESH_COMMAND", async (event) => {
    const command = event.detail;
    if (!command) return;

    const requestId = command.request?.id || crypto.randomUUID();

    try {
      // Ensure OmniMesh is available
      if (!window.OmniMesh) {
        throw new Error("OmniMesh not initialized - load omni-mesh-core.js first");
      }

      const result = await window.OmniMesh.execute(
        command.capability,
        {
          id: requestId,
          type: command.type,
          payload: command.request.payload
        }
      );

      window.dispatchEvent(
        new CustomEvent("OMNI_MESH_RESULT", {
          detail: {
            requestId,
            result
          }
        })
      );
    } catch (error) {
      window.dispatchEvent(
        new CustomEvent("OMNI_MESH_ERROR", {
          detail: {
            requestId,
            error: String(error)
          }
        })
      );
    }
  });

  /**
   * Helper: Send command to Omni-Mesh from page context
   */
  window.sendOmniCommand = (capability, type, payload) => {
    return new Promise((resolve, reject) => {
      const requestId = crypto.randomUUID();

      const resultHandler = (event) => {
        if (event.detail.requestId === requestId) {
          window.removeEventListener("OMNI_MESH_RESULT", resultHandler);
          window.removeEventListener("OMNI_MESH_ERROR", errorHandler);
          resolve(event.detail.result);
        }
      };

      const errorHandler = (event) => {
        if (event.detail.requestId === requestId) {
          window.removeEventListener("OMNI_MESH_RESULT", resultHandler);
          window.removeEventListener("OMNI_MESH_ERROR", errorHandler);
          reject(new Error(event.detail.error));
        }
      };

      window.addEventListener("OMNI_MESH_RESULT", resultHandler);
      window.addEventListener("OMNI_MESH_ERROR", errorHandler);

      window.dispatchEvent(
        new CustomEvent("OMNI_MESH_COMMAND", {
          detail: {
            capability,
            type,
            request: {
              id: requestId,
              payload
            }
          }
        })
      );
    });
  };

  console.log("[Omni-Mesh] window.sendOmniCommand() available for direct invocation");
})();
