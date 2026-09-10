import type { StaticLayer } from "../../types/staticLayer";
import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { HazardEvent } from "../../types/hazard";
import { BASEMAPS, type BasemapId } from "./basemaps";
import styles from "./MapView.module.css";
import {
  isVolcanoOverlay,
  removeVolcanoOverlays,
  syncVolcanoOverlays,
  VOLCANO_OVERLAYS,
  type VolcanoOverlayState,
} from "./volcanoOverlays";

type MapViewProps = {
  events: HazardEvent[];
  faults?: StaticLayer[];
  volcanoZones?: StaticLayer[];
  showFaults?: boolean;
  showVolcanoZones?: boolean;
  volcanoOverlayRevision?: number;
  onVolcanoOverlayState?: (state: VolcanoOverlayState) => void;
  basemap?: BasemapId;
  selectedEvent?: HazardEvent | null;
  showEvents?: boolean;
};

const PH_CENTER: [number, number] = [121.774, 12.8797]; // Philippines

// Resolve a CSS custom property from :root (single source of truth for tokens).
// MapLibre paints need literal values, so we read the token at runtime instead
// of duplicating the color in source.
function cssVar(name: string, fallback = ""): string {
  if (typeof window === "undefined") return fallback;
  return (
    window
      .getComputedStyle(document.documentElement)
      .getPropertyValue(name)
      .trim() || fallback
  );
}

function toFeatureCollection(events: HazardEvent[]) {
  return {
    type: "FeatureCollection" as const,
    features: events.map((event) => ({
      type: "Feature" as const,
      geometry: {
        type: "Point" as const,
        coordinates: [event.longitude, event.latitude],
      },
      properties: {
        place: event.place_name,
        magnitude: event.magnitude ?? null,
      },
    })),
  };
}

export default function MapView({
  events,
  faults = [],
  volcanoZones = [],
  showFaults = false,
  showVolcanoZones = false,
  volcanoOverlayRevision = 0,
  onVolcanoOverlayState,
  basemap = "streets",
  selectedEvent,
  showEvents = true,
}: MapViewProps) {
  const referenceLayers = useRef({
    faults,
    volcanoZones,
    showFaults,
    showVolcanoZones,
    showEvents,
  });
  referenceLayers.current = {
    faults,
    volcanoZones,
    showFaults,
    showVolcanoZones,
    showEvents,
  };
  const overlayCallback = useRef(onVolcanoOverlayState);
  overlayCallback.current = onVolcanoOverlayState;
  const overlayFailed = useRef(false);
  const appliedOverlayRevision = useRef(volcanoOverlayRevision);
  const remoteOverlaysEnabled = () =>
    referenceLayers.current.showVolcanoZones &&
    referenceLayers.current.volcanoZones.length === 0;

  function syncReferenceLayers(map: maplibregl.Map) {
    const current = referenceLayers.current;
    for (const [id, rows, visible] of [
      ["faults", current.faults, current.showFaults],
      ["volcano-zones", current.volcanoZones, current.showVolcanoZones],
    ] as const) {
      const data = {
        type: "FeatureCollection" as const,
        features: rows.map((row) => ({
          type: "Feature" as const,
          id: row.id,
          geometry: row.geometry,
          properties: { name: row.name, source: row.source },
        })),
      };
      const existing = map.getSource(id) as
        | maplibregl.GeoJSONSource
        | undefined;
      if (existing) existing.setData(data);
      else map.addSource(id, { type: "geojson", data });
      if (!map.getLayer(id)) {
        const before = map.getLayer("event-circles")
          ? "event-circles"
          : undefined;
        if (id === "faults")
          map.addLayer(
            {
              id,
              type: "line",
              source: id,
              paint: {
                "line-color": cssVar("--hazard-fault"),
                "line-width": 2,
              },
            },
            before,
          );
        else
          map.addLayer(
            {
              id,
              type: "fill",
              source: id,
              paint: {
                "fill-color": cssVar("--hazard-volcano"),
                "fill-opacity": 0.25,
                "fill-outline-color": cssVar("--hazard-volcano"),
              },
            },
            map.getLayer("faults") ? "faults" : before,
          );
      }
      map.setLayoutProperty(id, "visibility", visible ? "visible" : "none");
    }
    syncVolcanoOverlays(map, remoteOverlaysEnabled());
  }

  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const appliedBasemap = useRef(basemap);

  // Always-current events, readable from inside event handlers that were
  // registered once at mount (those closures would otherwise see whatever
  // `events` was on the render that registered them, not later updates).
  const eventsRef = useRef(events);
  eventsRef.current = events;

  // Setup the events source and event-circles layer.
  // Must run after initial map load AND after every style change
  // because setStyle() wipes custom sources/layers. Reads from eventsRef so
  // it always uses the latest data, even though it's registered once.
  const setupEventLayers = (map: maplibregl.Map) => {
    // Check if source already exists and remove it to avoid duplication
    if (map.getSource("events")) {
      if (map.getLayer("event-circles")) {
        map.removeLayer("event-circles");
      }
      map.removeSource("events");
    }

    map.addSource("events", {
      type: "geojson",
      data: toFeatureCollection(eventsRef.current),
    });

    const markerColor = cssVar("--accent");
    const markerStroke = cssVar("--white") || "var(--white)";

    map.addLayer({
      id: "event-circles",
      type: "circle",
      source: "events",
      paint: {
        "circle-radius": [
          "interpolate",
          ["linear"],
          ["coalesce", ["get", "magnitude"], 0],
          0,
          8,
          9,
          22,
        ],
        "circle-color": markerColor,
        "circle-stroke-width": 1.5,
        "circle-stroke-color": markerStroke,
        "circle-opacity": 0.9,
      },
    });

    map.setLayoutProperty(
      "event-circles",
      "visibility",
      referenceLayers.current.showEvents ? "visible" : "none",
    );

    if (map.getLayer("label_country")) {
      map.setLayoutProperty("label_country", "text-field", [
        "format",
        ["get", "name_en"],
        { "font-scale": 1.2 },
        "\n",
        {},
        ["get", "name"],
        {
          "font-scale": 0.8,
          "text-font": ["literal", ["Noto Sans Regular"]],
        },
      ]);
    }
  };

  // Keep the map and camera while replacing only its style.
  useEffect(() => {
    if (!mapContainer.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: BASEMAPS[basemap].style,
      center: PH_CENTER,
      zoom: 5,
    });
    mapRef.current = map;

    map.addControl(new maplibregl.NavigationControl(), "top-right");

    const restoreEvents = () => {
      overlayFailed.current = false;
      if (remoteOverlaysEnabled()) overlayCallback.current?.("loading");
      syncReferenceLayers(map);
      setupEventLayers(map);
    };
    const overlayError = (event: { sourceId?: string; error?: unknown }) => {
      if (remoteOverlaysEnabled() && isVolcanoOverlay(event.sourceId)) {
        overlayFailed.current = true;
        overlayCallback.current?.("error");
      }
    };
    const overlayIdle = () => {
      if (
        remoteOverlaysEnabled() &&
        !overlayFailed.current &&
        VOLCANO_OVERLAYS.every(
          (layer) => map.getSource(layer.id) && map.isSourceLoaded(layer.id),
        )
      )
        overlayCallback.current?.("ready");
    };
    const overlayLoading = (event: maplibregl.MapSourceDataEvent) => {
      if (
        remoteOverlaysEnabled() &&
        !overlayFailed.current &&
        isVolcanoOverlay(event.sourceId)
      ) {
        overlayCallback.current?.("loading");
      }
    };
    map.on("style.load", restoreEvents);
    map.on("error", overlayError);
    map.on("idle", overlayIdle);
    map.on("sourcedataloading", overlayLoading);
    appliedBasemap.current = basemap;

    return () => {
      map.off("style.load", restoreEvents);
      map.off("error", overlayError);
      map.off("idle", overlayIdle);
      map.off("sourcedataloading", overlayLoading);
      map.remove();
      mapRef.current = null;
    };
    // Mount-only intentionally: see comment above. `basemap`'s initial value
    // is captured here; later changes are handled by the basemap effect.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (map?.getLayer("event-circles")) syncReferenceLayers(map);
  }, [faults, volcanoZones, showFaults, showVolcanoZones]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || appliedOverlayRevision.current === volcanoOverlayRevision)
      return;
    appliedOverlayRevision.current = volcanoOverlayRevision;
    overlayFailed.current = false;
    overlayCallback.current?.("loading");
    removeVolcanoOverlays(map);
    if (map.getLayer("event-circles"))
      syncVolcanoOverlays(map, remoteOverlaysEnabled());
  }, [volcanoOverlayRevision]);

  // Sync updated event data into the already-existing source. This runs on
  // every `events` change WITHOUT touching the map instance or camera.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const source = map.getSource("events") as
      | maplibregl.GeoJSONSource
      | undefined;
    // If the source isn't there yet (map/style still loading), the 'load' /
    // 'style.load' handlers will pick up eventsRef.current when they run.
    if (!source) return;
    source.setData(toFeatureCollection(events));
  }, [events]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getLayer("event-circles")) return;
    map.setLayoutProperty(
      "event-circles",
      "visibility",
      showEvents ? "visible" : "none",
    );
  }, [showEvents]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || appliedBasemap.current === basemap) return;
    appliedBasemap.current = basemap;
    // Diff updates can remove custom layers without emitting style.load.
    // Full replacement guarantees our persistent listener restores markers.
    map.setStyle(BASEMAPS[basemap].style, { diff: false });
  }, [basemap]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !selectedEvent) return;
    const reducedMotion =
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
    map.flyTo({
      center: [selectedEvent.longitude, selectedEvent.latitude],
      zoom: Math.max(map.getZoom(), 8),
      duration: reducedMotion ? 0 : 800,
    });
    mapContainer.current?.scrollIntoView?.({
      block: "nearest",
      behavior: reducedMotion ? "auto" : "smooth",
    });
  }, [selectedEvent]);

  return (
    <div className={styles.canvas} aria-label="Hazard map">
      <div ref={mapContainer} className={styles.container} />
      <span className="sr-only">{events.length} events loaded</span>
      {events.length === 0 && (
        <div className={styles.empty}>No events to display.</div>
      )}
    </div>
  );
}
