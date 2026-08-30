import styles from "./RiskMeter.module.css";

type RiskMeterProps = {
  label: string;
  level: "high" | "medium" | "low";
  value: number;
};

export default function RiskMeter({ label, level, value }: RiskMeterProps) {
  return (
    <div className={styles.row}>
      <span className={`${styles.label} ${styles[`label--${level}`]}`}>
        {label}
      </span>
      <div className={styles.bar}>
        <span
          className={`${styles.fill} ${styles[`fill--${level}`]}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}
