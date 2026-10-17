/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Backend base URL as seen by the browser. Empty string means same-origin (proxy mode). */
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_REQUEST_TIMEOUT_MS?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
