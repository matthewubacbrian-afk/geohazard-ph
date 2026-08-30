import type { ReactNode } from 'react';
import { useRevealOnScroll } from '../../../hooks/useRevealOnScroll';
import styles from './Reveal.module.css';

type RevealProps = {
  children: ReactNode;
  delayMs?: number;
  className?: string;
};

export default function Reveal({ children, delayMs = 0, className }: RevealProps) {
  const { ref, visible } = useRevealOnScroll<HTMLDivElement>();

  const classes = [styles.reveal, visible ? styles.visible : '', className ?? '']
    .filter(Boolean)
    .join(' ');

  return (
    <div ref={ref} className={classes} style={{ transitionDelay: `${delayMs}ms` }}>
      {children}
    </div>
  );
}
