const layers = ['Earthquakes', 'Volcanoes', 'Faults', 'Landslides'];

export default function LayerControls() {
  return (
    <div className="panel">
      <h2>Layers</h2>
      {layers.map((layer) => (
        <label key={layer} className="toggle-row">
          <input type="checkbox" defaultChecked={layer !== 'Landslides'} />
          <span>{layer}</span>
        </label>
      ))}
    </div>
  );
}
