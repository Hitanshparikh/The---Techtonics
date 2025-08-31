/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_REACT_APP_GEMINI_API_KEY?: string;
  // add other env variables here if needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}