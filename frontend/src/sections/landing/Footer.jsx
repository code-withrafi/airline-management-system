export default function Footer() {
  return (
    <footer
      style={{
        padding: "36px 0",
        background: "#071a33",
        color: "rgba(255,255,255,.6)",
        textAlign: "center",
        fontFamily: '"Manrope", sans-serif',
        fontSize: 13,
      }}
    >
      <div className="container">
        <strong style={{ color: "#fff" }}>Aeriva</strong>
        <span style={{ margin: "0 8px", opacity: 0.4 }}>·</span>
        © {new Date().getFullYear()}
        <span style={{ margin: "0 8px", opacity: 0.4 }}>·</span>
        Iftekhar Rafi
      </div>
    </footer>
  );
}