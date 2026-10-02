export default function Stat({ number, label }) {
  return (
    <div style={{ textAlign: "center" }}>
      <div
        style={{
          marginBottom: 3,
          color: "#fff",
          fontFamily: '"Plus Jakarta Sans", sans-serif',
          fontSize: 26,
          fontWeight: 700,
          letterSpacing: "-.03em",
        }}
      >
        {number}
      </div>

      <div
        style={{
          color: "rgba(255,255,255,.62)",
          fontFamily: '"Manrope", sans-serif',
          fontSize: 12,
          fontWeight: 600,
        }}
      >
        {label}
      </div>
    </div>
  );
}