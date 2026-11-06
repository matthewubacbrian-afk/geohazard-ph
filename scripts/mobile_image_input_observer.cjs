// Observe build-host image-size inputs without retaining paths or asset bytes.
const crypto = require('node:crypto');
const fs = require('node:fs');
const Module = require('node:module');
const path = require('node:path');
const { threadId } = require('node:worker_threads');

const traceDir = process.env.GEOHAZARD_IMAGE_INPUT_TRACE_DIR;
if (!traceDir) {
  throw new Error('GEOHAZARD_IMAGE_INPUT_TRACE_DIR is required');
}
const traceFile = path.join(traceDir, `${process.pid}.jsonl`);
const workspace = path.resolve(__dirname, '..');
const installRoot = path.join(workspace, 'mobile', 'node_modules');
const maxInputSize = 512 * 1024;

function record(event) {
  fs.appendFileSync(traceFile, JSON.stringify({ pid: process.pid, thread_id: threadId, ...event }) + '\n');
}

function within(root, candidate) {
  const relative = path.relative(root, candidate);
  return relative === '' || (relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative));
}

function signatureClass(bytes) {
  if (bytes.subarray(0, 4).toString() === 'icns') return 'icns';
  if (bytes.length >= 12 && bytes.subarray(4, 8).toString() === 'JXL ') return 'jxl';
  if (bytes.length >= 12 && bytes.subarray(4, 8).toString() === 'ftyp' &&
      ['avif', 'mif1', 'msf1', 'heic', 'heix', 'hevc', 'hevx'].includes(bytes.subarray(8, 12).toString())) {
    return 'heif';
  }
  return 'other';
}

function digest(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex');
}

function describe(input) {
  if (input instanceof Uint8Array) {
    const bytes = Buffer.from(input.buffer, input.byteOffset, input.byteLength);
    return { input_kind: 'buffer', origin_class: 'buffer_unknown', byte_count: bytes.length,
      sha256: digest(bytes), signature_class: signatureClass(bytes) };
  }
  if (typeof input !== 'string') {
    return { input_kind: 'invalid', origin_class: 'unknown' };
  }
  const resolved = path.resolve(input);
  const canonical = fs.realpathSync(resolved);
  let origin = 'outside_workspace';
  if (within(installRoot, canonical)) origin = 'installed_dependency';
  else if (within(workspace, canonical)) origin = 'workspace';
  const descriptor = fs.openSync(canonical, 'r');
  let size;
  let bytes;
  try {
    size = fs.fstatSync(descriptor).size;
    bytes = Buffer.alloc(Math.min(size, maxInputSize));
    const read = fs.readSync(descriptor, bytes, 0, bytes.length, 0);
    bytes = bytes.subarray(0, read);
  } finally {
    fs.closeSync(descriptor);
  }
  return { input_kind: 'path', origin_class: origin, file_size: size,
    byte_count: bytes.length, sha256: digest(bytes), signature_class: signatureClass(bytes) };
}

record({ event: 'activation' });
const originalLoad = Module._load;
const wrappedExports = new WeakMap();
Module._load = function observedLoad(request, parent, isMain) {
  const loaded = originalLoad.apply(this, arguments);
  if (typeof loaded !== 'function') return loaded;
  const resolved = Module._resolveFilename(request, parent, isMain);
  if (!path.isAbsolute(resolved)) return loaded;
  const canonical = fs.realpathSync(resolved);
  if (path.relative(installRoot, canonical).split(path.sep).join('/') !== 'image-size/dist/index.js') {
    return loaded;
  }
  if (wrappedExports.has(loaded)) return wrappedExports.get(loaded);
  record({ event: 'module_load', module_path: path.relative(installRoot, canonical).split(path.sep).join('/') });
  const wrapped = new Proxy(loaded, {
    get(target, property, receiver) {
      const value = Reflect.get(target, property, receiver);
      return (property === 'default' || property === 'imageSize') && value === target ? wrapped : value;
    },
    apply(target, thisArg, args) {
      let input;
      try {
        input = describe(args[0]);
      } catch (error) {
        input = { input_kind: typeof args[0] === 'string' ? 'path' : 'invalid',
          origin_class: 'unknown', observation_error: error.code || error.name };
      }
      record({ event: 'call', ...input, callback: typeof args[1] === 'function' });
      return Reflect.apply(target, thisArg, args);
    },
  });
  wrappedExports.set(loaded, wrapped);
  return wrapped;
};
