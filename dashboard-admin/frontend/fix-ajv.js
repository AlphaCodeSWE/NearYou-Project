#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

try {
  // Risolvi il percorso di codegen.js e ricava la cartella compile
  const codegenPath = require.resolve('ajv/dist/compile/codegen');
  const compileDir = path.dirname(codegenPath); // es. node_modules/ajv/dist/compile
  const contextFile = path.join(compileDir, 'context.js');
  if (!fs.existsSync(contextFile)) {
    fs.writeFileSync(
      contextFile,
      `// Auto-generated stub per ajv/dist/compile/context\nmodule.exports = require('./codegen');\n`,
      'utf8'
    );
    console.log(' Created stub: ajv/dist/compile/context.js');
  }
} catch (e) {
  console.warn(' Could not create ajv context stub:', e);
}
