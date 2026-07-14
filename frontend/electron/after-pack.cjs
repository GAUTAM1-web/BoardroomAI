const fs = require("node:fs");
const path = require("node:path");

exports.default = async function afterPack(context) {
  const projectDir = context.projectDir || context.packager?.projectDir || process.cwd();
  const source = path.join(projectDir, ".next", "standalone", "node_modules");
  const destination = path.join(context.appOutDir, "resources", "app", "node_modules");

  if (!fs.existsSync(source)) {
    throw new Error(`Next standalone dependencies were not found at ${source}`);
  }

  fs.rmSync(destination, { recursive: true, force: true });
  fs.cpSync(source, destination, { recursive: true, force: true });
};
