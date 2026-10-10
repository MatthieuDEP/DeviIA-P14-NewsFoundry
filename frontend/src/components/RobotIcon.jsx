export default function RobotIcon({ size = 22 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M12 8V4H9" />
      <rect x="4" y="8" width="16" height="12" rx="3" />
      <path d="M1 14h3m16 0h3M9 13v3m6-3v3" />
    </svg>
  );
}
