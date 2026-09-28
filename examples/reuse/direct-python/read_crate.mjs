// An existing RO-Crate library reads the envelope; it does not verify science.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import pkg from 'ro-crate';

const { ROCrate } = pkg;
const directory = process.argv[2];
if (!directory) throw new Error('Usage: node read_crate.mjs DIRECTORY');
const metadata = JSON.parse(fs.readFileSync(path.join(directory, 'ro-crate-metadata.json'), 'utf8'));
assert.equal(metadata['@context'], 'https://w3id.org/ro/crate/1.3/context');
const crate = new ROCrate(metadata);
assert.equal(crate.rootDataset['@id'], './');
assert.equal(crate.getEntity('ro-crate-metadata.json').conformsTo['@id'], 'https://w3id.org/ro/crate/1.3');
const manifest = JSON.parse(fs.readFileSync(path.join(directory, 'payload-sha256.json'), 'utf8'));
for (const [file, expected] of Object.entries(manifest)) {
  assert.ok(!path.isAbsolute(file) && file !== '' && !file.includes('\\') &&
    file.split('/').every(part => part !== '..' && part !== '.' && part !== ''),
    'Only explicit local payload paths are supported');
  assert.equal(crate.getEntity(file)['@id'], file);
  const bytes = fs.readFileSync(path.join(directory, file));
  assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'), expected);
}
const result = JSON.parse(fs.readFileSync(path.join(directory, 'result.json'), 'utf8'));
const investigation = JSON.parse(fs.readFileSync(path.join(directory, 'investigation.json'), 'utf8'));
assert.equal(crate.getEntity('#research-cycle').result['@id'], 'investigation.json');
assert.equal(result.displacement.value, '4');
assert.equal(result.status, 'conditional');
assert.equal(investigation.assessments[0].outcome, 'failed_prediction');
assert.equal(investigation.assessments[1].outcome, 'within_bound');
assert.equal(investigation.follow_up.status, 'unresolved');
assert.equal(investigation.alternative.status, 'unresolved');
assert.equal(investigation.blocked_question.attempts[0].result.status, 'incompatible');
assert.equal(investigation.blocked_question.attempts[1].result.status, 'conditional');
const [before, after] = investigation.blocked_question.attempts;
assert.equal(before.input_sha256, after.input_sha256);
assert.equal(before.input_sha256, investigation.blocked_question.input_sha256);
assert.equal(before.method_sha256, after.method_sha256);
assert.notEqual(before.model, after.model);
assert.equal(after.assessment, investigation.assessments[1].protocol);
assert.equal(crate.getEntity('formal/DirectReuse.lean')['@type'], 'File');
const formal = JSON.parse(fs.readFileSync(path.join(directory, 'formal/observed-calibration.json'), 'utf8'));
assert.equal(formal.physical_applicability, 'not_verified');
console.log(JSON.stringify({reader: 'ro-crate@3.7.2', files_read: Object.keys(manifest).length,
  status: 'envelope_read_and_payloads_checked', scientific_validity: 'not_evaluated',
  formal_reports: 'preserved_not_recomputed_by_this_reader', profile_conformance: 'not_evaluated'}));
