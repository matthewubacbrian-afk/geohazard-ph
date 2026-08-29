# GeoHazard PH - Web Application Structure

This document explains the structure and components of the GeoHazard PH web dashboard, a React-based geologic hazard monitoring platform for the Philippines.

---

## 📁 Folder Structure Overview

```
web/
├── src/                          # Source code
│   ├── App.tsx                   # Root component (entry point)
│   ├── main.tsx                  # React DOM bootstrap
│   ├── vite-env.d.ts             # Vite environment types
│   ├── api/                      # API client layer
│   ├── components/               # Reusable UI components
│   ├── hooks/                    # Custom React hooks
│   ├── pages/                    # Page-level components
│   ├── styles/                   # Global CSS/Tailwind
│   └── types/                    # TypeScript type definitions
├── tests/                        # Test files
├── package.json                  # Dependencies and scripts
├── tsconfig.json                 # TypeScript configuration
├── vite.config.ts                # Vite bundler configuration
├── tailwind.config.ts            # Tailwind CSS configuration
└── index.html                    # HTML entry point
```

---

## 🏗️ Application Architecture

### Entry Point: `src/App.tsx`

```typescript
import Dashboard from './pages/Dashboard';

export default function App() {
  return <Dashboard />;
}
```

**What it does:**
- Simple root component that renders the main Dashboard page
- Serves as the entry point for the entire application
- No routing logic at this level (single-page dashboard)

---

### Bootstrap: `src/main.tsx`

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './styles/index.css';

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
);
```

**What it does:**
- Mounts React to the DOM (`#root` element in `index.html`)
- Sets up **React Query** (TanStack Query) for server state management
  - Handles data fetching, caching, and synchronization
  - Configured with a `QueryClient` instance
- Wraps app in `QueryClientProvider` to enable all child components to use React Query hooks
- Imports global styles from `styles/index.css`

---

## 📄 Pages

### `src/pages/Dashboard.tsx`

```typescript
import EventList from '../components/events/EventList';
import Header from '../components/layout/Header';
import Sidebar from '../components/layout/Sidebar';
import MapView from '../components/map/MapView';
import { useEvents } from '../hooks/useEvents';
import RiskProfileExplorer from './RiskProfileExplorer';

export default function Dashboard() {
  const { data: events = [] } = useEvents();

  return (
    <main>
      <Header />
      <div className="workspace">
        <Sidebar />
        <MapView events={events} />
        <EventList events={events} />
        <RiskProfileExplorer />
      </div>
    </main>
  );
}
```

**What it does:**
- Main dashboard layout combining all major UI sections
- **Data fetching:** Uses `useEvents()` hook to fetch hazard events from backend API
- **Layout structure:**
  - `<Header>` - Top navigation bar
  - `<Sidebar>` - Left panel with filters and controls
  - `<MapView>` - Interactive map area (center)
  - `<EventList>` - Event listing panel
  - `<RiskProfileExplorer>` - Risk analysis section
- Passes `events` data to `MapView` and `EventList` components

---

## 🧩 Components

Components are organized by feature/functionality:

### Layout Components (`components/layout/`)

#### **Header.tsx**
```typescript
export default function Header() {
  return (
    <header className="header">
      <h1>GeoHazard PH</h1>
      <span>Public geologic hazard awareness</span>
    </header>
  );
}
```
- Top banner with application title and tagline
- Simple presentational component

#### **Sidebar.tsx**
```typescript
import EventFilterBar from '../events/EventFilterBar';
import LayerControls from '../map/LayerControls';
import VolcanoAlertCard from '../volcano/VolcanoAlertCard';

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <EventFilterBar />
      <LayerControls />
      <VolcanoAlertCard />
    </aside>
  );
}
```
- Left sidebar container
- Houses three sub-sections:
  - **EventFilterBar** - Filter hazard events by type/date
  - **LayerControls** - Toggle map layers (faults, volcanoes, etc.)
  - **VolcanoAlertCard** - Current volcano alert status

---

### Map Components (`components/map/`)

#### **MapView.tsx**
```typescript
import type { HazardEvent } from '../../types/hazard';

type MapViewProps = {
  events: HazardEvent[];
};

export default function MapView({ events }: MapViewProps) {
  return (
    <section className="map-shell" aria-label="Hazard map">
      <div className="map-placeholder">
        <span>MapLibre map area</span>
        <strong>{events.length}</strong>
        <span>events loaded</span>
      </div>
    </section>
  );
}
```
- Central interactive map display
- **Props:** Takes array of `HazardEvent` objects
- **Current state:** Placeholder UI (MapLibre integration in progress)
- Displays event count at the top

#### **EventMarker.tsx**
- Renders individual event markers on the map
- Color-coded by hazard type (earthquake, volcanic, landslide)

#### **FaultLineLayer.tsx**
- Displays tectonic fault lines as a map layer
- Sourced from geohazard data

#### **LayerControls.tsx**
- UI to toggle visibility of map layers:
  - Fault lines
  - Volcano zones
  - Hazard events
  - Base layer options

---

### Event Components (`components/events/`)

#### **EventList.tsx**
```typescript
import type { HazardEvent } from '../../types/hazard';

type EventListProps = {
  events: HazardEvent[];
};

export default function EventList({ events }: EventListProps) {
  return (
    <div className="panel">
      <h2>Recent Events</h2>
      <ul>
        {events.map((event) => (
          <li key={event.id}>
            <strong>{event.place_name}</strong>
            <span>{event.source.toUpperCase()}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
```
- Displays list of recent hazard events
- **Props:** Array of `HazardEvent` objects
- Renders event location and data source
- Key prop ensures efficient list rendering

#### **EventDetailPanel.tsx**
- Shows detailed information for selected event
- Triggered when user clicks on an event marker or list item

#### **EventFilterBar.tsx**
- Sidebar controls to filter events by:
  - Hazard type (earthquake, volcanic, landslide)
  - Date range
  - Magnitude/severity

---

### Risk Profile Components (`components/risk/`)

#### **RiskProfileCard.tsx**
- Displays statistical risk profile for a region
- Shows:
  - Cluster classification
  - Confidence score
  - Feature importances (factors contributing to risk)
  - Model version and generation date

#### **RegionLookup.tsx**
- Search interface to find regions by name
- Returns matching risk profiles

---

### Volcano Components (`components/volcano/`)

#### **VolcanoAlertCard.tsx**
- Card showing current volcano alert statuses
- Color-coded by alert level
- Displays active volcanoes in the Philippines

---

## 🎯 Custom Hooks (`src/hooks/`)

### **useEvents.ts**
```typescript
import { useQuery } from '@tanstack/react-query';
import { fetchEvents } from '../api/client';

export function useEvents() {
  return useQuery({
    queryKey: ['events'],
    queryFn: fetchEvents
  });
}
```
- Fetches all hazard events from backend API
- Returns: `{ data, isLoading, error, ...queryStatus }`
- Caches results with `queryKey: ['events']`

### **useFaultLines.ts**
- Fetches tectonic fault line data
- Used by `FaultLineLayer` component

### **useRealtimeAlerts.ts**
- Subscribes to real-time alerts via WebSocket/polling
- Updates UI with new hazard events as they occur

### **useRiskProfiles.ts**
- Fetches ML-generated risk profiles by region
- Used by `RiskProfileExplorer` page

---

## 🔗 API Client (`src/api/client.ts`)

```typescript
import type { HazardEvent, RiskProfile } from '../types/hazard';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export async function fetchEvents(): Promise<HazardEvent[]> {
  const response = await fetch(`${API_BASE_URL}/events`);
  if (!response.ok) {
    throw new Error('Failed to fetch events');
  }
  return response.json();
}

export async function fetchRiskProfiles(): Promise<RiskProfile[]> {
  const response = await fetch(`${API_BASE_URL}/risk-profile/clusters`);
  if (!response.ok) {
    throw new Error('Failed to fetch risk profiles');
  }
  return response.json();
}

export async function fetchRiskProfile(regionName: string): Promise<RiskProfile> {
  const response = await fetch(`${API_BASE_URL}/risk-profile/${encodeURIComponent(regionName)}`);
  if (!response.ok) {
    throw new Error('Failed to fetch risk profile');
  }
  return response.json();
}
```

**What it does:**
- Central API client with all backend requests
- **Base URL:** Reads from `VITE_API_BASE_URL` environment variable (defaults to `http://localhost:8000/api/v1`)
- **Functions:**
  - `fetchEvents()` - GET `/events`
  - `fetchRiskProfiles()` - GET `/risk-profile/clusters`
  - `fetchRiskProfile(regionName)` - GET `/risk-profile/{region}`

---

## 📋 Type Definitions (`src/types/hazard.ts`)

```typescript
export type HazardEvent = {
  id: string;
  hazard_type: 'earthquake' | 'volcanic' | 'landslide';
  source: string;
  external_id?: string | null;
  magnitude?: number | null;
  depth_km?: number | null;
  latitude: number;
  longitude: number;
  place_name: string;
  occurred_at: string;
  alert_level?: string | null;
};

export type RiskProfile = {
  region_name: string;
  cluster: number;
  label: string;
  confidence: number;
  feature_importances: Record<string, number>;
  model_version: string;
  generated_at: string;
  dataset_snapshot: string;
};
```

**HazardEvent fields:**
- `id` - Unique identifier
- `hazard_type` - Type of geologic hazard
- `source` - Data source (PHIVOLCS, USGS, etc.)
- `magnitude` - Earthquake magnitude
- `depth_km` - Depth in kilometers
- `latitude, longitude` - Coordinates for map display
- `place_name` - Human-readable location
- `occurred_at` - ISO timestamp
- `alert_level` - Optional alert severity

**RiskProfile fields:**
- `region_name` - Region identifier
- `cluster` - ML cluster classification
- `label` - Descriptive label (e.g., "Very High Risk")
- `confidence` - Model confidence score
- `feature_importances` - Feature weights from Random Forest model
- `model_version` - ML model version
- `generated_at` - When profile was generated
- `dataset_snapshot` - Which dataset was used

---

## 🛠️ Tech Stack

| Technology | Purpose |
|-----------|---------|
| **React** | UI framework |
| **TypeScript** | Type-safe JavaScript |
| **Vite** | Fast build tool and dev server |
| **Tailwind CSS** | Utility-first CSS framework |
| **React Query (TanStack)** | Server state management, caching, sync |
| **MapLibre GL** | Interactive maps |
| **Vitest** | Unit testing framework |

---

## 🚀 Running the Web App

```bash
cd web
npm run dev
```

Starts development server at `http://localhost:5173`

```bash
npm run build
```

Builds optimized production bundle to `dist/`

```bash
npm test
```

Runs test suite with Vitest

---

## 🔄 Data Flow

```
API Backend (FastAPI)
        ↓
src/api/client.ts (HTTP calls)
        ↓
src/hooks/ (useEvents, useRiskProfiles, etc.)
        ↓
React Query QueryClient (caching, sync)
        ↓
Components (consume hooks)
        ↓
UI Rendered (MapView, EventList, etc.)
```

1. **Backend** serves geohazard data via REST API
2. **API Client** makes HTTP requests
3. **Custom Hooks** wrap React Query for specific data domains
4. **React Query** manages caching, loading states, errors
5. **Components** display data using hooks
6. **User interactions** trigger refetches or mutations

---

## 📝 Notes

- **Map integration:** `MapView.tsx` currently has a placeholder; MapLibre GL integration in progress
- **Environment config:** Set `VITE_API_BASE_URL` in `.env` to point to backend (e.g., `http://localhost:8000/api/v1`)
- **Mobile responsive:** Built with Tailwind utility classes for all screen sizes
- **Accessibility:** Components use semantic HTML and ARIA labels

