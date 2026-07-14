const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("boardroomDesktop", {
  platform: process.platform,
  versions: {
    electron: process.versions.electron,
    chrome: process.versions.chrome,
    node: process.versions.node
  },
  showAbout: () => ipcRenderer.invoke("boardroom:about")
});
