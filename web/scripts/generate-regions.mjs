import { readFile, rename, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

export const API_URL = 'https://www.geoboundaries.org/api/current/gbOpen/PHL/ADM1/';
export const DEFAULT_SOURCE_URL = 'https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/41af8f1/releaseData/gbOpen/PHL/ADM1/geoBoundaries-PHL-ADM1.geojson';
export const DEFAULT_TOLERANCE = 0.01;
export const QUANTIZATION_DECIMALS = 3;
export const DEFAULT_WARNING_BYTES = 220 * 1024;
export const ATTRIBUTION = 'Philippine administrative boundaries © geoBoundaries, sourced from NAMRIA, PSA, and OCHA Philippines, licensed under CC BY 3.0 IGO.';

const FEATURE_COUNT = 17;
const SOURCE_BOUNDARY_ID = 'PHL-ADM1-36201628';
const OUTPUT_PATH = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../src/data/philippine-regions.json');
const DOCS_PATH = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../docs/data-sources.md');
const PROVENANCE_START = '<!-- REGION_BOUNDARY_PROVENANCE:START -->';
const PROVENANCE_END = '<!-- REGION_BOUNDARY_PROVENANCE:END -->';

function assertTolerance(tolerance) {
  if (!Number.isFinite(tolerance) || tolerance <= 0) {
    throw new Error('Simplification tolerance must be a positive finite number.');
  }
}

function isPosition(value) {
  return Array.isArray(value) && value.length >= 2 && value.every(Number.isFinite);
}

function squaredDistanceToSegment(point, start, end) {
  const dx = end[0] - start[0];
  const dy = end[1] - start[1];
  if (dx === 0 && dy === 0) {
    return (point[0] - start[0]) ** 2 + (point[1] - start[1]) ** 2;
  }
  const projection = ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / (dx * dx + dy * dy);
  const factor = Math.max(0, Math.min(1, projection));
  const closestX = start[0] + factor * dx;
  const closestY = start[1] + factor * dy;
  return (point[0] - closestX) ** 2 + (point[1] - closestY) ** 2;
}

function simplifyLine(points, tolerance) {
  if (points.length <= 2) {
    return points;
  }
  const squaredTolerance = tolerance ** 2;
  const keep = new Set([0, points.length - 1]);
  const pending = [[0, points.length - 1]];

  while (pending.length > 0) {
    const [startIndex, endIndex] = pending.pop();
    let furthestIndex = -1;
    let furthestDistance = squaredTolerance;
    for (let index = startIndex + 1; index < endIndex; index += 1) {
      const distance = squaredDistanceToSegment(points[index], points[startIndex], points[endIndex]);
      if (distance > furthestDistance) {
        furthestDistance = distance;
        furthestIndex = index;
      }
    }
    if (furthestIndex !== -1) {
      keep.add(furthestIndex);
      pending.push([startIndex, furthestIndex], [furthestIndex, endIndex]);
    }
  }

  return points.filter((_, index) => keep.has(index));
}

function simplifyRing(ring, tolerance) {
  if (!Array.isArray(ring) || ring.length < 4 || !ring.every(isPosition)) {
    throw new Error('Polygon rings must contain at least four finite coordinate pairs.');
  }
  const closed = ring[0][0] === ring.at(-1)[0] && ring[0][1] === ring.at(-1)[1];
  if (!closed) {
    throw new Error('Polygon rings must be closed.');
  }
  const simplified = simplifyLine(ring.slice(0, -1), tolerance);
  const unique = simplified.length >= 3
    ? simplified
    : [ring[0], ring[Math.floor((ring.length - 1) / 2)], ring.at(-2)];
  const factor = 10 ** QUANTIZATION_DECIMALS;
  const quantized = unique.map(([longitude, latitude]) => [
    Math.round(longitude * factor) / factor,
    Math.round(latitude * factor) / factor
  ]);
  const deduplicated = quantized.filter((position, index) => (
    index === 0 || position[0] !== quantized[index - 1][0] || position[1] !== quantized[index - 1][1]
  ));
  const valid = deduplicated.length >= 3 ? deduplicated : quantized;
  return [...valid, valid[0]];
}

function simplifyGeometry(geometry, tolerance) {
  if (!geometry || !['Polygon', 'MultiPolygon'].includes(geometry.type)) {
    throw new Error(`Unsupported geometry type: ${geometry?.type ?? 'missing'}.`);
  }
  if (geometry.type === 'Polygon') {
    return { type: geometry.type, coordinates: geometry.coordinates.map((ring) => simplifyRing(ring, tolerance)) };
  }
  return {
    type: geometry.type,
    coordinates: geometry.coordinates.map((polygon) => polygon.map((ring) => simplifyRing(ring, tolerance)))
  };
}

function validateSource(source) {
  if (!source || source.type !== 'FeatureCollection' || !Array.isArray(source.features)) {
    throw new Error('Source must be a GeoJSON FeatureCollection.');
  }
  if (source.features.length !== FEATURE_COUNT) {
    throw new Error(`Expected ${FEATURE_COUNT} region features, received ${source.features.length}.`);
  }
}

export function simplifyGeoJson(source, tolerance) {
  assertTolerance(tolerance);
  validateSource(source);
  return {
    type: 'FeatureCollection',
    features: source.features.map((feature) => {
      const name = feature?.properties?.shapeName;
      if (typeof name !== 'string' || name.length === 0) {
        throw new Error('Every region feature must have a shapeName property.');
      }
      return {
        type: 'Feature',
        properties: { region_name: name },
        geometry: simplifyGeometry(feature.geometry, tolerance)
      };
    })
  };
}

export function countFeatureVertices(feature) {
  const count = (coordinates) => {
    if (isPosition(coordinates)) {
      return 1;
    }
    if (!Array.isArray(coordinates)) {
      return 0;
    }
    return coordinates.reduce((total, child) => total + count(child), 0);
  };
  return count(feature.geometry.coordinates);
}

export function serializeGeoJson(collection) {
  return `${JSON.stringify(collection)}\n`;
}

function formatBytes(bytes) {
  return new Intl.NumberFormat('en-US').format(bytes);
}

export function buildProvenance({ sourceMetadata, sourceUrl, tolerance, outputBytes, features, generatedAt }) {
  const rows = features.map((feature) => `| ${feature.properties.region_name} | ${countFeatureVertices(feature)} |`);
  const totalVertices = features.reduce((total, feature) => total + countFeatureVertices(feature), 0);
  return [
    PROVENANCE_START,
    '### Generated Philippine region boundary asset',
    '',
    `- Boundary ID: ${sourceMetadata.boundaryID}`,
    `- Represented year: ${sourceMetadata.boundaryYearRepresented}`,
    `- Source build date: ${sourceMetadata.buildDate}`,
    `- Source providers: ${sourceMetadata.boundarySource}`,
    `- Source GeoJSON: ${sourceUrl}`,
    `- Metadata API: ${API_URL}`,
    `- License: ${sourceMetadata.boundaryLicense}`,
    `- Attribution: ${ATTRIBUTION}`,
    `- Generated at: ${generatedAt}`,
    `- Simplification tolerance: ${tolerance}`,
    `- Coordinate quantization: ${QUANTIZATION_DECIMALS} decimal places`,
    `- Output bytes: ${formatBytes(outputBytes)}`,
    `- Feature count: ${features.length}`,
    `- Total vertex count: ${formatBytes(totalVertices)}`,
    '',
    '| Region | Vertices |',
    '| --- | ---: |',
    ...rows,
    '',
    PROVENANCE_END,
    ''
  ].join('\n');
}

function parseArgs(args) {
  const options = { source: DEFAULT_SOURCE_URL, tolerance: DEFAULT_TOLERANCE };
  for (const argument of args) {
    const [key, value] = argument.split('=');
    if (key === '--source' && value) {
      options.source = value;
    } else if (key === '--tolerance' && value) {
      options.tolerance = Number(value);
    } else {
      throw new Error(`Unknown or malformed argument: ${argument}`);
    }
  }
  new URL(options.source);
  assertTolerance(options.tolerance);
  return options;
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed with ${response.status} ${response.statusText}: ${url}`);
  }
  return response.json();
}

async function writeAtomically(filePath, contents) {
  const temporaryPath = `${filePath}.tmp-${process.pid}`;
  await writeFile(temporaryPath, contents, 'utf8');
  await rename(temporaryPath, filePath);
}

async function updateProvenance(provenance) {
  const existing = await readFile(DOCS_PATH, 'utf8');
  const block = `${PROVENANCE_START}\n${provenance.slice(provenance.indexOf('\n') + 1)}`;
  const pattern = new RegExp(`${PROVENANCE_START}[\\s\\S]*?${PROVENANCE_END}\\r?\\n?`);
  const updated = pattern.test(existing)
    ? existing.replace(pattern, block)
    : `${existing.trimEnd()}\n\n${block}`;
  await writeAtomically(DOCS_PATH, updated);
}

async function run() {
  const options = parseArgs(process.argv.slice(2));
  const metadata = options.source === DEFAULT_SOURCE_URL
    ? await fetchJson(API_URL)
    : {
        boundaryID: SOURCE_BOUNDARY_ID,
        boundaryYearRepresented: '2020',
        buildDate: 'Jul 05, 2023',
        boundarySource: 'NAMRIA, PSA, and OCHA Philippines',
        boundaryLicense: 'CC BY 3.0 IGO'
      };
  if (metadata.boundaryID !== SOURCE_BOUNDARY_ID) {
    throw new Error(`Unexpected geoBoundaries dataset: ${metadata.boundaryID ?? 'missing boundary ID'}.`);
  }
  const source = await fetchJson(options.source);
  const collection = simplifyGeoJson(source, options.tolerance);
  const serialized = serializeGeoJson(collection);
  const outputBytes = Buffer.byteLength(serialized);
  const warningBytes = Number(process.env.REGION_ASSET_WARNING_BYTES ?? DEFAULT_WARNING_BYTES);
  if (outputBytes > warningBytes) {
    console.warn(`Warning: generated region asset is ${formatBytes(outputBytes)} bytes, above ${formatBytes(warningBytes)} bytes.`);
  }
  await writeAtomically(OUTPUT_PATH, serialized);
  await updateProvenance(buildProvenance({
    sourceMetadata: metadata,
    sourceUrl: options.source,
    tolerance: options.tolerance,
    outputBytes,
    features: collection.features,
    generatedAt: new Date().toISOString()
  }));
  console.log(`Generated ${collection.features.length} regions (${formatBytes(outputBytes)} bytes).`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  run().catch((error) => {
    console.error(`Region generation failed: ${error.message}`);
    process.exitCode = 1;
  });
}