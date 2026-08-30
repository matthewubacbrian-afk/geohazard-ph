import styles from "./Skeleton.module.css";

type SkeletonProps = {
  width?: string | number;
  height?: string | number;
  className?: string;
};

export default function Skeleton({ width, height, className }: SkeletonProps) {
  return (
    <span
      className={`${styles.skeleton} ${className ?? ""}`}
      style={{ width: width ?? "100%", height: height ?? 12 }}
      aria-hidden="true"
    />
  );
}
