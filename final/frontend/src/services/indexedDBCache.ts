/**
 * NarrAI Neural Cache Manager (IndexedDB)
 * Feature 28: IndexedDB Cache Manager for TensorFlow.js Hybrid Architecture
 *
 * Provides persistent offline client storage for:
 * 1. 128-dimensional concept vectors and story metadata.
 * 2. Quantized neural model weights and architecture configurations.
 *
 * Enforces a strict 10-20MB cache budget (default: 15MB) with automated
 * Least Recently Used (LRU) eviction and graceful in-memory SSR/private mode fallback.
 */

export interface ConceptVectorRecord {
  post_id: number;
  title: string;
  genre: string;
  author_id: number;
  concept_vector: number[];
  created_at: string | null;
  views_count: number;
  likes_count: number;
  completion_count: number;
  last_accessed_at: number;
  byte_size: number;
}

export interface NeuralWeightsRecord {
  model_name: string;
  version: string;
  format?: string;
  total_params?: number;
  input_dim: number;
  output_dim: number;
  architecture: any;
  weights_manifest: any[];
  weights?: any;
  weights_base64?: string;
  last_accessed_at: number;
  byte_size: number;
}

export interface CacheStorageStats {
  usedBytes: number;
  maxBytes: number;
  vectorCount: number;
  weightsCached: boolean;
  budgetUtilizationPct: number;
}

const DB_NAME = "NarrAINeuralCacheDB";
const DB_VERSION = 1;
const STORE_VECTORS = "concept_vectors";
const STORE_WEIGHTS = "neural_weights";
const STORE_META = "cache_metadata";

// Budget: 15 MB (within 10-20 MB specification)
export const DEFAULT_CACHE_BUDGET_BYTES = 15 * 1024 * 1024;

/**
 * Calculates approximate JSON byte size of an object.
 */
function estimateByteSize(obj: any): number {
  try {
    return new Blob([JSON.stringify(obj)]).size;
  } catch {
    const str = JSON.stringify(obj);
    return str ? str.length * 2 : 1024;
  }
}

class IndexedDBCacheManager {
  private dbPromise: Promise<IDBDatabase | null> | null = null;
  private maxBytes: number = DEFAULT_CACHE_BUDGET_BYTES;

  // In-memory fallback when IndexedDB is unavailable (SSR, test runner, strict privacy)
  private memoryVectors: Map<number, ConceptVectorRecord> = new Map();
  private memoryWeights: Map<string, NeuralWeightsRecord> = new Map();
  private memoryMeta: Map<string, any> = new Map();

  constructor(maxBytes: number = DEFAULT_CACHE_BUDGET_BYTES) {
    this.maxBytes = maxBytes;
  }

  /**
   * Check if running in browser environment with IndexedDB support.
   */
  private isSupported(): boolean {
    return typeof window !== "undefined" && !!window.indexedDB;
  }

  /**
   * Opens or initializes IndexedDB schema.
   */
  private async getDB(): Promise<IDBDatabase | null> {
    if (!this.isSupported()) return null;
    if (this.dbPromise) return this.dbPromise;

    this.dbPromise = new Promise((resolve) => {
      try {
        const req = window.indexedDB.open(DB_NAME, DB_VERSION);

        req.onupgradeneeded = () => {
          const db = req.result;

          // 1. Concept Vectors Store
          if (!db.objectStoreNames.contains(STORE_VECTORS)) {
            const vecStore = db.createObjectStore(STORE_VECTORS, { keyPath: "post_id" });
            vecStore.createIndex("last_accessed_at", "last_accessed_at", { unique: false });
            vecStore.createIndex("genre", "genre", { unique: false });
            vecStore.createIndex("created_at", "created_at", { unique: false });
          }

          // 2. Neural Weights Store
          if (!db.objectStoreNames.contains(STORE_WEIGHTS)) {
            const weightsStore = db.createObjectStore(STORE_WEIGHTS, { keyPath: "model_name" });
            weightsStore.createIndex("last_accessed_at", "last_accessed_at", { unique: false });
          }

          // 3. Cache Metadata Store
          if (!db.objectStoreNames.contains(STORE_META)) {
            db.createObjectStore(STORE_META, { keyPath: "key" });
          }
        };

        req.onsuccess = () => resolve(req.result);
        req.onerror = () => {
          console.warn("[IndexedDBCache] Failed to open IndexedDB, falling back to memory cache.");
          resolve(null);
        };
      } catch (err) {
        console.warn("[IndexedDBCache] Exception opening IndexedDB:", err);
        resolve(null);
      }
    });

    return this.dbPromise;
  }

  /**
   * Stores or updates a list of concept vectors with LRU tracking and budget eviction.
   */
  async saveVectors(
    vectors: Array<{
      post_id: number;
      title: string;
      genre: string;
      author_id: number;
      concept_vector: number[];
      created_at: string | null;
      views_count: number;
      likes_count: number;
      completion_count: number;
    }>
  ): Promise<number> {
    if (!vectors || vectors.length === 0) return 0;
    const now = Date.now();

    const prepared: ConceptVectorRecord[] = vectors.map((v) => ({
      ...v,
      last_accessed_at: now,
      byte_size: estimateByteSize(v) + 64,
    }));

    const totalNewBytes = prepared.reduce((sum, item) => sum + item.byte_size, 0);

    // Evict oldest entries if total would exceed budget
    await this.evictLRUIfNeeded(totalNewBytes);

    const db = await this.getDB();
    if (!db) {
      for (const rec of prepared) {
        this.memoryVectors.set(rec.post_id, rec);
      }
      return prepared.length;
    }

    return new Promise((resolve) => {
      try {
        const tx = db.transaction([STORE_VECTORS], "readwrite");
        const store = tx.objectStore(STORE_VECTORS);

        let savedCount = 0;
        for (const item of prepared) {
          store.put(item);
          savedCount++;
        }

        tx.oncomplete = () => resolve(savedCount);
        tx.onerror = () => {
          console.warn("[IndexedDBCache] Vector write failed, saving to memory fallback");
          for (const rec of prepared) {
            this.memoryVectors.set(rec.post_id, rec);
          }
          resolve(prepared.length);
        };
      } catch (err) {
        console.warn("[IndexedDBCache] Transaction error in saveVectors:", err);
        for (const rec of prepared) {
          this.memoryVectors.set(rec.post_id, rec);
        }
        resolve(prepared.length);
      }
    });
  }

  /**
   * Retrieves all cached concept vectors, updating their last accessed timestamp.
   */
  async getVectors(): Promise<ConceptVectorRecord[]> {
    const db = await this.getDB();
    if (!db) {
      return Array.from(this.memoryVectors.values());
    }

    return new Promise((resolve) => {
      try {
        const tx = db.transaction([STORE_VECTORS], "readonly");
        const store = tx.objectStore(STORE_VECTORS);
        const req = store.getAll();

        req.onsuccess = () => {
          const list = (req.result as ConceptVectorRecord[]) || [];
          resolve(list);
        };

        req.onerror = () => {
          resolve(Array.from(this.memoryVectors.values()));
        };
      } catch {
        resolve(Array.from(this.memoryVectors.values()));
      }
    });
  }

  /**
   * Retrieves a single concept vector by post_id.
   */
  async getVector(postId: number): Promise<ConceptVectorRecord | null> {
    const db = await this.getDB();
    if (!db) {
      return this.memoryVectors.get(postId) || null;
    }

    return new Promise((resolve) => {
      try {
        const tx = db.transaction([STORE_VECTORS], "readwrite");
        const store = tx.objectStore(STORE_VECTORS);
        const req = store.get(postId);

        req.onsuccess = () => {
          const item = req.result as ConceptVectorRecord | undefined;
          if (item) {
            item.last_accessed_at = Date.now();
            store.put(item);
            resolve(item);
          } else {
            resolve(null);
          }
        };

        req.onerror = () => {
          resolve(this.memoryVectors.get(postId) || null);
        };
      } catch {
        resolve(this.memoryVectors.get(postId) || null);
      }
    });
  }

  /**
   * Stores quantized neural model weights in IndexedDB.
   */
  async saveWeights(weightsData: Omit<NeuralWeightsRecord, "last_accessed_at" | "byte_size">): Promise<void> {
    const record: NeuralWeightsRecord = {
      ...weightsData,
      last_accessed_at: Date.now(),
      byte_size: estimateByteSize(weightsData),
    };

    await this.evictLRUIfNeeded(record.byte_size, true);

    const db = await this.getDB();
    if (!db) {
      this.memoryWeights.set(record.model_name, record);
      return;
    }

    return new Promise((resolve) => {
      try {
        const tx = db.transaction([STORE_WEIGHTS], "readwrite");
        const store = tx.objectStore(STORE_WEIGHTS);
        store.put(record);

        tx.oncomplete = () => resolve();
        tx.onerror = () => {
          this.memoryWeights.set(record.model_name, record);
          resolve();
        };
      } catch {
        this.memoryWeights.set(record.model_name, record);
        resolve();
      }
    });
  }

  /**
   * Retrieves cached neural model weights.
   */
  async getWeights(modelName: string = "NarrAI-Recommender-TwoTower-Lite"): Promise<NeuralWeightsRecord | null> {
    const db = await this.getDB();
    if (!db) {
      return this.memoryWeights.get(modelName) || null;
    }

    return new Promise((resolve) => {
      try {
        const tx = db.transaction([STORE_WEIGHTS], "readwrite");
        const store = tx.objectStore(STORE_WEIGHTS);
        const req = store.get(modelName);

        req.onsuccess = () => {
          const item = req.result as NeuralWeightsRecord | undefined;
          if (item) {
            item.last_accessed_at = Date.now();
            store.put(item);
            resolve(item);
          } else {
            resolve(null);
          }
        };

        req.onerror = () => resolve(this.memoryWeights.get(modelName) || null);
      } catch {
        resolve(this.memoryWeights.get(modelName) || null);
      }
    });
  }

  /**
   * Stores sync metadata for delta synchronization.
   */
  async setSyncMeta(key: string, value: any): Promise<void> {
    const metaRecord = { key, value, updated_at: Date.now() };
    const db = await this.getDB();
    if (!db) {
      this.memoryMeta.set(key, metaRecord);
      return;
    }

    return new Promise((resolve) => {
      try {
        const tx = db.transaction([STORE_META], "readwrite");
        const store = tx.objectStore(STORE_META);
        store.put(metaRecord);
        tx.oncomplete = () => resolve();
        tx.onerror = () => resolve();
      } catch {
        resolve();
      }
    });
  }

  /**
   * Retrieves sync metadata by key.
   */
  async getSyncMeta(key: string): Promise<any | null> {
    const db = await this.getDB();
    if (!db) {
      const item = this.memoryMeta.get(key);
      return item ? item.value : null;
    }

    return new Promise((resolve) => {
      try {
        const tx = db.transaction([STORE_META], "readonly");
        const store = tx.objectStore(STORE_META);
        const req = store.get(key);
        req.onsuccess = () => {
          resolve(req.result ? req.result.value : null);
        };
        req.onerror = () => resolve(null);
      } catch {
        resolve(null);
      }
    });
  }

  /**
   * Computes current storage usage and stats against budget.
   */
  async getStorageStats(): Promise<CacheStorageStats> {
    const db = await this.getDB();
    if (!db) {
      let used = 0;
      this.memoryVectors.forEach((v) => { used += v.byte_size; });
      this.memoryWeights.forEach((w) => { used += w.byte_size; });

      return {
        usedBytes: used,
        maxBytes: this.maxBytes,
        vectorCount: this.memoryVectors.size,
        weightsCached: this.memoryWeights.size > 0,
        budgetUtilizationPct: Math.min(100, (used / this.maxBytes) * 100),
      };
    }

    return new Promise((resolve) => {
      try {
        const tx = db.transaction([STORE_VECTORS, STORE_WEIGHTS], "readonly");
        const vecStore = tx.objectStore(STORE_VECTORS);
        const weightsStore = tx.objectStore(STORE_WEIGHTS);

        let used = 0;
        let vecCount = 0;

        const vecReq = vecStore.getAll();
        vecReq.onsuccess = () => {
          const vecs = (vecReq.result as ConceptVectorRecord[]) || [];
          vecCount = vecs.length;
          for (const v of vecs) {
            used += v.byte_size || 512;
          }

          const weightReq = weightsStore.getAll();
          weightReq.onsuccess = () => {
            const weights = (weightReq.result as NeuralWeightsRecord[]) || [];
            const weightsFound = weights.length > 0;
            for (const w of weights) {
              used += w.byte_size || 50000;
            }

            resolve({
              usedBytes: used,
              maxBytes: this.maxBytes,
              vectorCount: vecCount,
              weightsCached: weightsFound,
              budgetUtilizationPct: Math.min(100, (used / this.maxBytes) * 100),
            });
          };

          weightReq.onerror = () => resolve({
            usedBytes: used,
            maxBytes: this.maxBytes,
            vectorCount: vecCount,
            weightsCached: false,
            budgetUtilizationPct: (used / this.maxBytes) * 100,
          });
        };

        vecReq.onerror = () => resolve({
          usedBytes: 0,
          maxBytes: this.maxBytes,
          vectorCount: 0,
          weightsCached: false,
          budgetUtilizationPct: 0,
        });
      } catch {
        resolve({
          usedBytes: 0,
          maxBytes: this.maxBytes,
          vectorCount: 0,
          weightsCached: false,
          budgetUtilizationPct: 0,
        });
      }
    });
  }

  /**
   * LRU Eviction Policy:
   * Evicts the oldest accessed concept vectors until current usage + incomingBytes <= maxBytes.
   */
  async evictLRUIfNeeded(incomingBytes: number, _preserveWeights: boolean = true): Promise<number> {
    const stats = await this.getStorageStats();
    if (stats.usedBytes + incomingBytes <= this.maxBytes) {
      return 0; // Budget is sufficient
    }

    const bytesToFree = stats.usedBytes + incomingBytes - this.maxBytes;
    let freedBytes = 0;

    const db = await this.getDB();
    if (!db) {
      const sorted = Array.from(this.memoryVectors.values()).sort(
        (a, b) => a.last_accessed_at - b.last_accessed_at
      );
      for (const item of sorted) {
        if (freedBytes >= bytesToFree) break;
        this.memoryVectors.delete(item.post_id);
        freedBytes += item.byte_size;
      }
      return freedBytes;
    }

    return new Promise((resolve) => {
      try {
        const tx = db.transaction([STORE_VECTORS], "readwrite");
        const store = tx.objectStore(STORE_VECTORS);
        const index = store.index("last_accessed_at");
        const cursorReq = index.openCursor();

        cursorReq.onsuccess = () => {
          const cursor = cursorReq.result;
          if (cursor && freedBytes < bytesToFree) {
            const val = cursor.value as ConceptVectorRecord;
            freedBytes += val.byte_size || 512;
            cursor.delete();
            cursor.continue();
          } else {
            resolve(freedBytes);
          }
        };

        cursorReq.onerror = () => resolve(freedBytes);
        tx.oncomplete = () => resolve(freedBytes);
      } catch {
        resolve(freedBytes);
      }
    });
  }

  /**
   * Clears all cached records from all stores.
   */
  async clearCache(): Promise<void> {
    this.memoryVectors.clear();
    this.memoryWeights.clear();
    this.memoryMeta.clear();

    const db = await this.getDB();
    if (!db) return;

    return new Promise((resolve) => {
      try {
        const tx = db.transaction([STORE_VECTORS, STORE_WEIGHTS, STORE_META], "readwrite");
        tx.objectStore(STORE_VECTORS).clear();
        tx.objectStore(STORE_WEIGHTS).clear();
        tx.objectStore(STORE_META).clear();
        tx.oncomplete = () => resolve();
        tx.onerror = () => resolve();
      } catch {
        resolve();
      }
    });
  }
}

// Singleton cache instance
export const indexedDBCache = new IndexedDBCacheManager(DEFAULT_CACHE_BUDGET_BYTES);
