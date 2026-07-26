const { app, BrowserWindow, Menu, dialog, ipcMain, shell } = require("electron");
const { spawn } = require("node:child_process");
const http = require("node:http");
const path = require("node:path");

const APP_NAME = "Boardroom AI";
const DEFAULT_PORT = "3010";
const HOST = "127.0.0.1";

let mainWindow = null;
let splashWindow = null;
let nextProcess = null;

const isPackaged = app.isPackaged;

function getAssetPath(...segments) {
  if (isPackaged) {
    return path.join(process.resourcesPath, "assets", ...segments);
  }

  return path.join(__dirname, "build", ...segments);
}

function getNextRoot() {
  if (isPackaged) {
    return path.join(process.resourcesPath, "app");
  }

  return path.join(__dirname, "..");
}

function getNextEntry() {
  if (isPackaged) {
    return path.join(getNextRoot(), "server.js");
  }

  return path.join(getNextRoot(), "node_modules", "next", "dist", "bin", "next");
}

function getServerUrl() {
  return `http://${HOST}:${process.env.BOARDROOM_DESKTOP_PORT || DEFAULT_PORT}`;
}

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 520,
    height: 360,
    frame: false,
    resizable: false,
    movable: true,
    show: false,
    backgroundColor: "#07090d",
    icon: getAssetPath("icon.png"),
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs")
    }
  });

  splashWindow.loadFile(path.join(__dirname, "splash.html"));
  splashWindow.once("ready-to-show", () => splashWindow?.show());
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 1180,
    minHeight: 760,
    title: APP_NAME,
    show: false,
    backgroundColor: "#07090d",
    icon: getAssetPath("icon.png"),
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true
    }
  });

  mainWindow.once("ready-to-show", () => {
    splashWindow?.close();
    splashWindow = null;
    mainWindow?.show();
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  if (isPackaged) {
    mainWindow.webContents.on("before-input-event", (event, input) => {
      const key = input.key.toLowerCase();
      if ((input.control || input.meta) && input.shift && key === "i") {
        event.preventDefault();
      }
    });

    mainWindow.webContents.on("devtools-opened", () => {
      mainWindow?.webContents.closeDevTools();
    });
  }

  mainWindow.loadURL(`${getServerUrl()}/workspace`);
}

function createMenu() {
  const template = [
    {
      label: APP_NAME,
      submenu: [
        {
          label: `About ${APP_NAME}`,
          click: showAboutDialog
        },
        { type: "separator" },
        { role: "quit" }
      ]
    },
    {
      label: "View",
      submenu: isPackaged
        ? [{ role: "reload" }, { role: "resetZoom" }, { role: "zoomIn" }, { role: "zoomOut" }]
        : [{ role: "reload" }, { role: "toggleDevTools" }, { role: "resetZoom" }, { role: "zoomIn" }, { role: "zoomOut" }]
    }
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

function showAboutDialog() {
  const version = app.getVersion();
  dialog.showMessageBox(mainWindow, {
    type: "info",
    title: `About ${APP_NAME}`,
    message: APP_NAME,
    detail: `Version ${version}\nRelease channel RC1\n\nExecutive AI operating system for founders.`,
    buttons: ["OK"],
    icon: getAssetPath("icon.png")
  });
}

function startNextServer() {
  const port = process.env.BOARDROOM_DESKTOP_PORT || DEFAULT_PORT;
  const env = {
    ...process.env,
    NODE_ENV: isPackaged ? "production" : "development",
    PORT: port,
    HOSTNAME: HOST,
    NEXT_TELEMETRY_DISABLED: "1",
    ELECTRON_RUN_AS_NODE: "1"
  };

  const args = isPackaged
    ? [getNextEntry()]
    : [getNextEntry(), "dev", "--hostname", HOST, "--port", port];

  nextProcess = spawn(process.execPath, args, {
    cwd: getNextRoot(),
    env,
    stdio: isPackaged ? "ignore" : "inherit",
    windowsHide: true
  });

  nextProcess.once("exit", (code) => {
    nextProcess = null;
    if (code !== 0 && mainWindow) {
      dialog.showErrorBox(APP_NAME, "The local application server stopped unexpectedly.");
      app.quit();
    }
  });
}

function waitForServer(url, attempts = 90) {
  return new Promise((resolve, reject) => {
    let remaining = attempts;

    const check = () => {
      const request = http.get(url, (response) => {
        response.resume();
        resolve();
      });

      request.on("error", () => {
        remaining -= 1;
        if (remaining <= 0) {
          reject(new Error(`Timed out waiting for ${url}`));
          return;
        }
        setTimeout(check, 500);
      });

      request.setTimeout(1500, () => {
        request.destroy();
      });
    };

    check();
  });
}

app.whenReady().then(async () => {
  app.setAppUserModelId("com.boardroomai.desktop");
  ipcMain.handle("boardroom:about", () => showAboutDialog());
  createMenu();
  createSplashWindow();
  startNextServer();

  try {
    await waitForServer(getServerUrl());
    createMainWindow();
  } catch (error) {
    splashWindow?.close();
    dialog.showErrorBox(APP_NAME, error instanceof Error ? error.message : "Desktop startup failed.");
    app.quit();
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow();
  }
});

app.on("before-quit", () => {
  if (nextProcess) {
    nextProcess.kill();
    nextProcess = null;
  }
});
