const CACHE_DB = "ocr-browser-models";

export async function clearBrowserModelCache(): Promise<void> {
  if (typeof caches !== "undefined") {
    const keys = await caches.keys();
    await Promise.all(
      keys.filter((k) => k.includes("transformers") || k.includes("huggingface")).map((k) => caches.delete(k))
    );
  }

  if (typeof indexedDB !== "undefined") {
    const dbs = [CACHE_DB, "transformers-cache", "hf-transformers"];
    await Promise.all(
      dbs.map(
        (name) =>
          new Promise<void>((resolve) => {
            const req = indexedDB.deleteDatabase(name);
            req.onsuccess = () => resolve();
            req.onerror = () => resolve();
            req.onblocked = () => resolve();
          })
      )
    );
  }

  localStorage.removeItem("browser-ocr-cache-cleared-at");
  localStorage.setItem("browser-ocr-cache-cleared-at", new Date().toISOString());
}

export function getCacheClearedAt(): string | null {
  return localStorage.getItem("browser-ocr-cache-cleared-at");
}
