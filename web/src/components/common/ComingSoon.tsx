import styles from "./ComingSoon.module.css";

type ComingSoonProps = {
  title: string;
  description: string;
  note?: string;
};

export default function ComingSoon({ title, description, note }: ComingSoonProps) {
  return (
    <section className={styles.section} aria-labelledby="coming-soon-heading">
      <div className={styles.badge}>Coming Soon</div>
      <h1 id="coming-soon-heading" className={styles.title}>
        {title}
      </h1>
      <p className={styles.description}>{description}</p>
      {note ? <p className={styles.note}>{note}</p> : null}
    </section>
  );
}
