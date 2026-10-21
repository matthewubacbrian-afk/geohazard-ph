const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const test = require('node:test');

const root = path.resolve(__dirname, '..', '..');
const mobile = path.join(root, 'mobile');
const observer = path.join(root, 'scripts', 'mobile_image_input_observer.cjs');
const image = path.join(mobile, 'android', 'app', 'src', 'main', 'res', 'mipmap-mdpi', 'ic_launcher.png');

function runObserved(code) {
  const traceDir = fs.mkdtempSync(path.join(os.tmpdir(), 'geohazard-image-input-test-'));
  const child = spawnSync(process.execPath, ['--require', observer, '-e', code, image], {
    cwd: mobile,
    encoding: 'utf8',
    env: { ...process.env, GEOHAZARD_IMAGE_INPUT_TRACE_DIR: traceDir },
  });
  const records = fs.readdirSync(traceDir)
    .filter((name) => name.endsWith('.jsonl'))
    .flatMap((name) => fs.readFileSync(path.join(traceDir, name), 'utf8').trim().split('\n'))
    .filter(Boolean)
    .map((line) => JSON.parse(line));
  fs.rmSync(traceDir, { recursive: true, force: true });
  return { child, records };
}

test('records a supplied buffer without storing its bytes', () => {
  const { child, records } = runObserved(`
    const fs = require('node:fs');
    const imageSize = require('image-size');
    const input = fs.readFileSync(process.argv[1]);
    const result = imageSize(input);
    if (result.width <= 0 || !imageSize.types.includes('png')) process.exit(2);
  `);
  assert.equal(child.status, 0, child.stderr);
  assert.deepEqual(records.map((record) => record.event), ['activation', 'module_load', 'call']);
  const call = records[2];
  const bytes = fs.readFileSync(image);
  assert.equal(call.input_kind, 'buffer');
  assert.equal(call.byte_count, bytes.length);
  assert.equal(call.sha256, crypto.createHash('sha256').update(bytes).digest('hex'));
  assert.equal(call.signature_class, 'other');
  assert.equal(call.origin_class, 'buffer_unknown');
  assert.equal(JSON.stringify(call).includes(bytes.toString('base64')), false);
});

test('records a workspace path and preserves the parser result', () => {
  const { child, records } = runObserved(`
    const imageSize = require('image-size');
    const result = imageSize(process.argv[1]);
    if (result.width <= 0) process.exit(2);
  `);
  assert.equal(child.status, 0, child.stderr);
  const call = records.find((record) => record.event === 'call');
  assert.equal(call.input_kind, 'path');
  assert.equal(call.origin_class, 'workspace');
  assert.equal(call.signature_class, 'other');
  assert.equal(JSON.stringify(call).includes(image), false);
});

test('keeps CommonJS export identity and observes both function aliases', () => {
  const { child, records } = runObserved(`
    const fs = require('node:fs');
    const imageSize = require('image-size');
    if (imageSize !== require('image-size') || imageSize !== imageSize.default ||
        imageSize !== imageSize.imageSize) process.exit(2);
    const bytes = fs.readFileSync(process.argv[1]);
    imageSize(bytes);
    imageSize.default(bytes);
    imageSize.imageSize(bytes);
  `);
  assert.equal(child.status, 0, child.stderr);
  assert.equal(records.filter((record) => record.event === 'call').length, 3);
});

test('records advisory-relevant byte prefixes without claiming parser dispatch', () => {
  const { child, records } = runObserved(`
    const imageSize = require('image-size');
    const inputs = [
      Buffer.from('69636e7300000008', 'hex'),
      Buffer.from('0000000c4a584c2000000000', 'hex'),
      Buffer.from('00000010667479706865696300000000', 'hex'),
      Buffer.from('00000010667479706176696600000000', 'hex'),
    ];
    for (const input of inputs) { try { imageSize(input); } catch {} }
  `);
  assert.equal(child.status, 0, child.stderr);
  assert.deepEqual(records.filter((record) => record.event === 'call')
    .map((record) => record.signature_class), ['icns', 'jxl', 'heif', 'heif']);
});

test('preserves parser errors while recording the attempted call', () => {
  const { child, records } = runObserved(`
    const imageSize = require('image-size');
    try { imageSize(Buffer.from([1, 2, 3])); process.exit(2); }
    catch (error) { if (!(error instanceof TypeError)) process.exit(3); }
  `);
  assert.equal(child.status, 0, child.stderr);
  assert.equal(records.filter((record) => record.event === 'call').length, 1);
});

test('fails closed when the trace directory cannot be written', () => {
  const missing = path.join(os.tmpdir(), `geohazard-missing-${process.pid}-${Date.now()}`, 'trace');
  const child = spawnSync(process.execPath, ['--require', observer, '-e', 'process.exit(0)'], {
    cwd: mobile,
    encoding: 'utf8',
    env: { ...process.env, GEOHAZARD_IMAGE_INPUT_TRACE_DIR: missing },
  });
  assert.notEqual(child.status, 0);
  assert.match(child.stderr, /ENOENT/);
});
