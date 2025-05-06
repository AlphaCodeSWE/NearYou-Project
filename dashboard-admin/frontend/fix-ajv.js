#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

// Trova la root di AJV
const ajvPkg = require.resolve('ajv/package.json');
const ajvDir = path.dirname(ajvPkg);
const compileDir = path.join(ajvDir, 'dist', 'compile');

// Se non esiste la cartella compile, esci silenzioso
if (!fs.existsSync(compileDir)) {
  console.warn('⚠ ajv compile dir non trovato:', compileDir);
  process.exit(0);
}

// Stub da creare
const stubs = {
  'codegen.js': `// Auto-generated stub per ajv/dist/compile/codegen
module.exports = function compile() { return {}; };
`,
  'context.js': `// Auto-generated stub per ajv/dist/compile/context
module.exports = require('./codegen');
`
};

for (const [fname, content] of Object.entries(stubs)) {
  const filePath = path.join(compileDir, fname);
  if (!fs.existsSync(filePath)) {
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(\`✔ Created stub: ajv/dist/compile/\${fname}\`);
  }
}
