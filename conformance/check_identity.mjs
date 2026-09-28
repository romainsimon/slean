// Independent encoding/hash check only. This is not a scientific module reader.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';

const root = path.dirname(fileURLToPath(import.meta.url));
const read = file => JSON.parse(fs.readFileSync(path.join(root, file), 'utf8'));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');

function unicode(text) {
  for (let i = 0; i < text.length; i++) {
    const code = text.charCodeAt(i);
    if (code >= 0xd800 && code <= 0xdbff) {
      const next = text.charCodeAt(++i);
      assert.ok(next >= 0xdc00 && next <= 0xdfff, 'Lone high surrogate');
    } else assert.ok(code < 0xdc00 || code > 0xdfff, 'Lone low surrogate');
  }
}

function canonical(value) {
  if (typeof value === 'number') assert.ok(Number.isFinite(value));
  if (typeof value === 'string') unicode(value);
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  return '{' + Object.keys(value).sort().map(key => {
    unicode(key);
    return JSON.stringify(key) + ':' + canonical(value[key]);
  }).join(',') + '}';
}

const vectors = read('identity-vectors.json');
for (const vector of vectors.jcs) {
  const bytes = canonical(JSON.parse(vector.input_json));
  assert.equal(bytes, vector.canonical);
  assert.equal(hash(bytes), vector.sha256);
}
for (const vector of vectors.modules) {
  const value = read(`fixtures/${vector.fixture}/slean-module.json`);
  assert.equal(value.id, vector.id);
  delete value.id;
  assert.equal('sha256:' + hash('slean-module/0.1-draft.1\n' + canonical(value)), vector.id);
}
assert.throws(() => canonical('\ud800'));
assert.throws(() => canonical(Infinity));
console.log(JSON.stringify({jcs_vectors: vectors.jcs.length, module_vectors: vectors.modules.length,
  status: 'passed', scope: 'JCS serialization and module hash only; no raw-input or scientific validation'}));
