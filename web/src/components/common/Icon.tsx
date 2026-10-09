export type IconName = 'assessment' | 'close' | 'filter' | 'history' | 'layers' | 'map' | 'volcano';

type IconProps = {
  className?: string;
  name: IconName;
};

export default function Icon({ className, name }: IconProps) {
  return (
    <svg
      className={className}
      aria-hidden="true"
      focusable="false"
      viewBox="0 0 24 24"
      width="18"
      height="18"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {name === 'map' && (
        <>
          <path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Z" />
          <path d="M9 3v15m6-12v15" />
        </>
      )}
      {name === 'filter' && <path d="M4 5h16l-6.5 7.5V19l-3 1v-7.5L4 5Z" />}
      {name === 'history' && (
        <>
          <path d="M3 11a9 9 0 1 1 2.2 6" />
          <path d="M3 4v7h7m2-5v6l4 2" />
        </>
      )}
      {name === 'volcano' && (
        <>
          <path d="m3 20 6-11 3 4 3-6 6 13H3Z" />
          <path d="M10 5c-1-1 1-2 0-3m5 4c-1-1 1-2 0-3" />
        </>
      )}
      {name === 'assessment' && (
        <>
          <path d="M4 20V4m0 16h17" />
          <path d="m7 15 4-4 3 2 5-6" />
          <path d="M7 8v.01M11 11v.01M14 13v.01M19 7v.01" />
        </>
      )}
      {name === 'layers' && (
        <>
          <path d="m12 3 9 5-9 5-9-5 9-5Z" />
          <path d="m3 12 9 5 9-5M3 16l9 5 9-5" />
        </>
      )}
      {name === 'close' && <path d="m6 6 12 12M18 6 6 18" />}
    </svg>
  );
}
