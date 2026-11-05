/// <reference types="vite/client" />

interface Window {
  __RESILAI_BUILD__: {
    commit: string;
    buildTime: string;
    environment: string;
    api: string;
    version: string;
  };
}
