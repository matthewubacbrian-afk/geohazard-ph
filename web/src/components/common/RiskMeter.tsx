type RiskMeterProps = {
  label: string;
  level: "high" | "medium" | "low";
  value: number;
};

export default function RiskMeter({ label, level, value }: RiskMeterProps) {
  return (
    <div className="risk-row">
      <span className={`risk-label risk-label--${level}`}>{label}</span>
      <div className="risk-bar">
        <span className={`risk-fill risk-fill--${level}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
