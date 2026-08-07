// Small hand-rolled SVG icon set — keeps the bundle light, no icon
// library dependency needed for a handful of glyphs.

const base = {
  width: 20,
  height: 20,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round",
};

export function IconLeaf(props) {
  return (
    <svg {...base} {...props}>
      <path d="M11 20A7 7 0 0 1 4 13c0-4.5 4-8 12-9 1 8-3 12-9 12" />
      <path d="M4 13c3-1 6-2 10-6" />
    </svg>
  );
}

export function IconPlate(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="4" />
    </svg>
  );
}

export function IconClock(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 3" />
    </svg>
  );
}

export function IconUpload(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 16V4M12 4l-4 4M12 4l4 4" />
      <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
    </svg>
  );
}

export function IconSparkles(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3l1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6L12 3z" />
      <path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15z" />
    </svg>
  );
}

export function IconRecycle(props) {
  return (
    <svg {...base} {...props}>
      <path d="M7 19H5.5a2.5 2.5 0 0 1-2.2-3.7l1-1.8" />
      <path d="M10.5 4.5 12 2l3 5.2" />
      <path d="M18 19h2a2.5 2.5 0 0 0 2-4l-.9-1.6" />
      <path d="M8 19h8" />
      <path d="M14 2 12 5.5" />
    </svg>
  );
}

export function IconArrowRight(props) {
  return (
    <svg {...base} {...props}>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}
