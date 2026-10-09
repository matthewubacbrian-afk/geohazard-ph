import type { StaticLayer } from "../../types/staticLayer";
import { useEffect, useId, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { HazardEvent } from "../../types/hazard";
import type { RiskProfile } from "../../types/hazard";
import { BASEMAPS, type BasemapId } from "./basemaps";
import styles from "./MapView.module.css";
import { PHILIPPINE_REGIONS } from "../../data/philippine-regions";
import { riskProfilesToFeatureCollection } from "./riskOverlay";
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
  onSelectEvent?: (event: HazardEvent) => void;
  showEvents?: boolean;
  riskProfiles?: RiskProfile[];
  showRiskLayer?: boolean;
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
        eventId: event.id,
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
  onSelectEvent,
  showEvents = true,
  riskProfiles = [],
  showRiskLayer = false,
}: MapViewProps) {
  const eventSummaryId = useId();
  const referenceLayers = useRef({
    faults,
    volcanoZones,
    showFaults,
    showVolcanoZones,
    showEvents,
    riskProfiles,
    showRiskLayer,
  });
  referenceLayers.current = {
    faults,
    volcanoZones,
    showFaults,
    showVolcanoZones,
    showEvents,
    riskProfiles,
    showRiskLayer,
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
                "line-color": cssVar("--accent"),
                "line-width": 2.75,
                "line-opacity": 0.95,
                "line-blur": 0.15,
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
                "fill-color": cssVar("--risk-moderate"),
                "fill-opacity": 0.28,
                "fill-outline-color": cssVar("--text"),
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
  const selectEventRef = useRef(onSelectEvent);
  selectEventRef.current = onSelectEvent;
  const selectedEventRef = useRef(selectedEvent);
  selectedEventRef.current = selectedEvent;
  const clickHandlerRef = useRef<
    ((event: maplibregl.MapLayerMouseEvent) => void) | null
  >(null);
  const animationFrameRef = useRef<number | null>(null);
  const animationRunningRef = useRef(false);

  const stopHaloAnimation = () => {
    animationRunningRef.current = false;
    if (animationFrameRef.current !== null)
      cancelAnimationFrame(animationFrameRef.current);
    animationFrameRef.current = null;
  };

  const animateHalo = (map: maplibregl.Map) => {
    if (animationRunningRef.current) return;
    animationRunningRef.current = true;
    const frame = (timestamp: number) => {
      if (!animationRunningRef.current) return;
      if (map.getLayer("selected-event-pulse")) {
        const phase = (timestamp % 1800) / 1800;
        const wave = 0.5 - 0.5 * Math.cos(phase * 2 * Math.PI);
        map.setPaintProperty("selected-event-pulse", "circle-radius", 13 + 7 * wave);
        map.setPaintProperty(
          "selected-event-pulse",
          "circle-opacity",
          0.22 + 0.3 * (1 - wave),
        );
      }
      animationFrameRef.current = requestAnimationFrame(frame);
    };
    animationFrameRef.current = requestAnimationFrame(frame);
  };

  const selectedFeatureCollection = (event: HazardEvent | null | undefined) => ({
    type: "FeatureCollection" as const,
    features: event
      ? [
          {
            type: "Feature" as const,
            geometry: {
              type: "Point" as const,
              coordinates: [event.longitude, event.latitude],
            },
            properties: { magnitude: event.magnitude ?? null },
          },
        ]
      : [],
  });
  const riskProfilesRef = useRef(riskProfiles);
  riskProfilesRef.current = riskProfiles;

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
    if (map.getLayer("selected-event-pulse"))
      map.removeLayer("selected-event-pulse");
    if (map.getSource("selected-event")) map.removeSource("selected-event");

    map.addSource("events", {
      type: "geojson",
      data: toFeatureCollection(eventsRef.current),
    });

    const markerStroke = cssVar("--surface-card", "#fffefa");

    map.addLayer({
      id: "event-circles",
      type: "circle",
      source: "events",
      paint: {
        "circle-radius": [
          "interpolate",
          ["linear"],
          ["max", 0, ["min", 9, ["coalesce", ["get", "magnitude"], 0]]],
          0,
          4,
          9,
          13,
        ],
        "circle-color": [
          "step",
          ["coalesce", ["get", "magnitude"], 0],
          cssVar("--magnitude-low"),
          3,
          cssVar("--magnitude-moderate"),
          5,
          cssVar("--magnitude-high"),
          7,
          cssVar("--magnitude-very-high"),
        ],
        "circle-stroke-width": 2.5,
        "circle-stroke-color": markerStroke,
        "circle-opacity": 0.9,
      },
    });

    const selectedData = selectedFeatureCollection(selectedEventRef.current);
    map.addSource("selected-event", { type: "geojson", data: selectedData });
    const reducedMotion =
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
    map.addLayer({
      id: "selected-event-pulse",
      type: "circle",
      source: "selected-event",
      paint: {
        "circle-radius": reducedMotion ? 17 : 13,
        "circle-color": [
          "step",
          ["coalesce", ["get", "magnitude"], 0],
          cssVar("--magnitude-low"),
          3,
          cssVar("--magnitude-moderate"),
          5,
          cssVar("--magnitude-high"),
          7,
          cssVar("--magnitude-very-high"),
        ],
        "circle-opacity": reducedMotion ? 0.4 : 0.52,
        "circle-stroke-width": 2,
        "circle-stroke-color": cssVar("--surface-card", "#fffefa"),
      },
    });
    if (selectedEventRef.current && !reducedMotion) animateHalo(map);

    if (clickHandlerRef.current) map.off("click", "event-circles", clickHandlerRef.current);
    const handleEventClick = (event: maplibregl.MapLayerMouseEvent) => {
      const eventId = event.features?.[0]?.properties?.eventId;
      if (typeof eventId !== "string") return;
      const selected = eventsRef.current.find((row) => row.id === eventId);
      if (selected) selectEventRef.current?.(selected);
    };
    clickHandlerRef.current = handleEventClick;
    map.on("click", "event-circles", handleEventClick);

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

  const syncRiskLayer = (map: maplibregl.Map) => {
    const data = riskProfilesToFeatureCollection(
      riskProfilesRef.current,
      PHILIPPINE_REGIONS,
    );
    const source = map.getSource("risk-regions") as
      | maplibregl.GeoJSONSource
      | undefined;
    if (source) source.setData(data);
    else map.addSource("risk-regions", { type: "geojson", data });

    if (!map.getLayer("risk-regions-fill")) {
      map.addLayer(
        {
          id: "risk-regions-fill",
          type: "fill",
          source: "risk-regions",
          paint: {
            "fill-color": [
              "match",
              ["get", "label"],
              "Very High",
              cssVar("--risk-very-high"),
              "High",
              cssVar("--risk-high"),
              "Moderate",
              cssVar("--risk-moderate"),
              "Low",
              cssVar("--risk-low"),
              cssVar("--text-faint"),
            ],
            "fill-opacity": [
              "match",
              ["get", "label"],
              "Very High",
              0.52,
              "High",
              0.45,
              "Moderate",
              0.38,
              0.32,
            ],
          },
        },
        map.getLayer("event-circles") ? "event-circles" : undefined,
      );
    }
    if (!map.getLayer("risk-regions-outline")) {
      map.addLayer({
        id: "risk-regions-outline",
        type: "line",
        source: "risk-regions",
        paint: {
          "line-color": cssVar("--surface-card"),
          "line-width": 3,
          "line-opacity": 0.95,
        },
      });
    }
    const riskPatterns = [
      { label: "Low", id: "risk-regions-outline-low", dash: [1, 0] },
      { label: "Moderate", id: "risk-regions-outline-moderate", dash: [2, 1] },
      { label: "High", id: "risk-regions-outline-high", dash: [1, 1] },
      { label: "Very High", id: "risk-regions-outline-very-high", dash: [3, 1, 1, 1] },
    ] as const;
    for (const pattern of riskPatterns) {
      if (!map.getLayer(pattern.id)) {
        map.addLayer({
          id: pattern.id,
          type: "line",
          source: "risk-regions",
          filter: ["==", ["get", "label"], pattern.label],
          paint: {
            "line-color": cssVar("--text"),
            "line-width": 1.5,
            "line-dasharray": [...pattern.dash],
          },
        });
      }
    }
    const visibility = referenceLayers.current.showRiskLayer ? "visible" : "none";
    map.setLayoutProperty("risk-regions-fill", "visibility", visibility);
    map.setLayoutProperty("risk-regions-outline", "visibility", visibility);
    for (const { id } of riskPatterns) map.setLayoutProperty(id, "visibility", visibility);
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
      syncRiskLayer(map);
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
      if (clickHandlerRef.current)
        map.off("click", "event-circles", clickHandlerRef.current);
      clickHandlerRef.current = null;
      stopHaloAnimation();
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
  }, [faults, volcanoZones, showFaults, showVolcanoZones, riskProfiles, showRiskLayer]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getLayer("event-circles")) return;
    syncRiskLayer(map);
  }, [riskProfiles, showRiskLayer]);

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
    if (!map) return;
    const selectedSource = map.getSource("selected-event") as maplibregl.GeoJSONSource | undefined;
    if (selectedSource)
      selectedSource.setData(selectedFeatureCollection(selectedEvent));
    if (!selectedEvent) stopHaloAnimation();
    else if (
      !(window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false)
    )
      animateHalo(map);
  }, [selectedEvent]);

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
    <div
      className={styles.canvas}
      role="region"
      aria-label="Hazard event map"
      aria-describedby={eventSummaryId}
    >
      <div ref={mapContainer} className={styles.container} />
      <span id={eventSummaryId} className="sr-only">
        {showEvents
          ? `${events.length} events shown on the map.`
          : `Event layer hidden. ${events.length} events are available.`}
      </span>
      <section className={styles.magnitudeLegend} aria-label="Magnitude legend">
        <h3 className={styles.legendTitle}>Magnitude</h3>
        <ul className={styles.legendList}>
          <li className={styles.legendRow}>
            <span className={`${styles.magnitudeKey} ${styles.magnitudeKeyLow}`} aria-hidden="true" />
            <span>0–2.9 · small</span>
          </li>
          <li className={styles.legendRow}>
            <span className={`${styles.magnitudeKey} ${styles.magnitudeKeyModerate}`} aria-hidden="true" />
            <span>3.0–4.9 · medium</span>
          </li>
          <li className={styles.legendRow}>
            <span className={`${styles.magnitudeKey} ${styles.magnitudeKeyHigh}`} aria-hidden="true" />
            <span>5.0–6.9 · large</span>
          </li>
          <li className={styles.legendRow}>
            <span className={`${styles.magnitudeKey} ${styles.magnitudeKeyVeryHigh}`} aria-hidden="true" />
            <span>7.0+ · largest</span>
          </li>
        </ul>
      </section>
      {events.length === 0 && (
        <div className={styles.empty}>No events to display.</div>
      )}
    </div>
  );
}
