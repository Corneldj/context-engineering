// Validates every ```mermaid block in the course: it must parse against the
// real mermaid parser, and it must carry accTitle/accDescr (alt text).
//
//   cd tools/mermaid && npm install     # once
//   node tools/mermaid/validate.mjs     # from anywhere

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { JSDOM } from 'jsdom';

const dom = new JSDOM('<!DOCTYPE html><body></body>', { pretendToBeVisual: true });
global.window = dom.window;
global.document = dom.window.document;
Object.defineProperty(global, 'navigator', { value: dom.window.navigator, configurable: true });
for (const k of ['Node', 'Element', 'HTMLElement', 'DOMParser', 'SVGElement', 'getComputedStyle']) {
  global[k] = dom.window[k];
}

const mermaid = (await import('mermaid')).default;
mermaid.initialize({ startOnLoad: false });

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === '.git' || entry.name === 'node_modules') continue;
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(p, out);
    else if (entry.name.endsWith('.md')) out.push(p);
  }
  return out;
}

let total = 0, failed = 0, noAlt = 0;
for (const file of walk(root)) {
  const text = fs.readFileSync(file, 'utf8');
  const re = /```mermaid\n([\s\S]*?)```/g;
  let match, index = 0;
  while ((match = re.exec(text))) {
    index++; total++;
    const rel = path.relative(root, file);
    if (!match[1].includes('accDescr')) {
      noAlt++;
      console.log(`NO ALT TEXT  ${rel} block ${index}`);
    }
    try {
      await mermaid.parse(match[1]);
    } catch (err) {
      failed++;
      console.log(`PARSE FAIL   ${rel} block ${index}: ${String(err.message || err).split('\n')[0]}`);
    }
  }
}
console.log(`mermaid: ${total} blocks, ${failed} parse failures, ${noAlt} missing alt text`);
process.exit(failed || noAlt ? 1 : 0);
