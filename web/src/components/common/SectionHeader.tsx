type SectionHeaderProps = {
  title: string;
  subtitle: string;
};

import styles from "./SectionHeader.module.css";

export default function SectionHeader({ title, subtitle }: SectionHeaderProps) {
  return (
    <div className={styles.header}>
      <h2 className={styles.title}>{title}</h2>
      <p className={styles.subtitle}>{subtitle}</p>
    </div>
  );
}
