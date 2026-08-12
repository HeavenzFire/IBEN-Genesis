/**
 * CRDT Document Store - Persists document operations to IndexedDB
 * 
 * Listens to OPERATION_APPLIED events and automatically persists documents.
 * Provides race-condition-free distributed state sync across devices/tabs.
 */

class CRDTDocumentStore {
  /**
   * @param {EventBus} bus - Omni-Mesh event bus to listen for operations
   * @param {string} dbName - IndexedDB database name
   */
  constructor(bus, dbName = 'OmniMesh-CRDT') {
    this.bus = bus;
    this.dbName = dbName;
    this.db = null;
    this.init();
  }

  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        console.log(`[Omni-Mesh] CRDT store initialized: ${this.dbName}`);
        
        // Subscribe to operation events for auto-persistence
        this.bus.on("OPERATION_APPLIED", async ({ documentId }) => {
          await this.persistDocument(documentId);
        });
        
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Create object store for documents
        if (!db.objectStoreNames.contains('documents')) {
          const store = db.createObjectStore('documents', { keyPath: 'id' });
          store.createIndex('updatedAt', 'updatedAt', { unique: false });
          store.createIndex('revision', 'revision', { unique: false });
        }

        // Create object store for operations (append-only log)
        if (!db.objectStoreNames.contains('operations')) {
          const store = db.createObjectStore('operations', { keyPath: 'id' });
          store.createIndex('documentId', 'documentId', { unique: false });
          store.createIndex('revision', 'revision', { unique: false });
        }
      };
    });
  }

  /**
   * Persist a document to IndexedDB
   * @param {string|object} documentIdOrDoc - Document ID or full document object
   */
  async persistDocument(documentIdOrDoc) {
    if (!this.db) {
      throw new Error("IndexedDB not initialized");
    }

    const document = typeof documentIdOrDoc === 'string'
      ? window.OmniMesh.documents.get(documentIdOrDoc)
      : documentIdOrDoc;

    if (!document) {
      console.warn(`[Omni-Mesh] Document not found for persistence: ${documentIdOrDoc}`);
      return;
    }

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(['documents'], 'readwrite');
      const store = tx.objectStore('documents');
      
      const request = store.put({
        id: document.id,
        source: document.source,
        layers: document.layers,
        operations: document.operations,
        metadata: document.metadata,
        revision: document.revision,
        createdAt: document.createdAt,
        updatedAt: document.updatedAt
      });

      request.onsuccess = () => {
        console.log(`[Omni-Mesh] Document persisted: ${document.id} (rev ${document.revision})`);
        resolve(document);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Load a document from IndexedDB
   * @param {string} documentId - Document ID to load
   */
  async loadDocument(documentId) {
    if (!this.db) {
      throw new Error("IndexedDB not initialized");
    }

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(['documents'], 'readonly');
      const store = tx.objectStore('documents');
      const request = store.get(documentId);

      request.onsuccess = () => {
        const doc = request.result;
        if (doc && window.OmniMesh) {
          window.OmniMesh.documents.documents.set(documentId, doc);
        }
        resolve(doc || null);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Get all documents sorted by revision
   */
  async getAllDocuments() {
    if (!this.db) {
      throw new Error("IndexedDB not initialized");
    }

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(['documents'], 'readonly');
      const store = tx.objectStore('documents');
      const index = store.index('updatedAt');
      const request = index.openCursor(null, 'prev');

      const documents = [];
      request.onsuccess = (event) => {
        const cursor = event.target.result;
        if (cursor) {
          documents.push(cursor.value);
          cursor.continue();
        } else {
          resolve(documents);
        }
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Clear all stored documents (use with caution)
   */
  async clear() {
    if (!this.db) {
      throw new Error("IndexedDB not initialized");
    }

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(['documents'], 'readwrite');
      const store = tx.objectStore('documents');
      const request = store.clear();

      request.onsuccess = () => {
        console.log("[Omni-Mesh] CRDT store cleared");
        resolve();
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }
}

// Auto-initialize if running in browser
if (typeof window !== 'undefined' && typeof indexedDB !== 'undefined') {
  console.log("[Omni-Mesh] CRDTDocumentStore loaded - instantiate with: new CRDTDocumentStore(OmniMesh.bus)");
}
