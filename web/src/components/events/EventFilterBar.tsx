export default function EventFilterBar() {
  return (
    <div className="filter-bar">
      <select aria-label="Hazard type" defaultValue="earthquake">
        <option value="earthquake">Earthquakes</option>
        <option value="volcanic">Volcanoes</option>
        <option value="landslide">Landslides</option>
      </select>
      <select aria-label="Time range" defaultValue="7d">
        <option value="24h">Last 24 hours</option>
        <option value="7d">Last 7 days</option>
        <option value="30d">Last 30 days</option>
      </select>
    </div>
  );
}
