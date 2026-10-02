import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { fadeUpOnView } from "../../animations/variants";

export default function DestinationCard({
  code,
  city,
  country,
  color,
  image,
  delay = 0,
}) {
  return (
    <motion.div
      {...fadeUpOnView(delay)}
      whileHover={{ y: -6 }}
      className="card"
      style={{ overflow: "hidden" }}
    >
      <Link
        to={`/search?destination=${code}`}
        style={{ display: "block", color: "inherit" }}
      >
        <div style={{ position: "relative", height: 190, overflow: "hidden" }}>
          <img
            src={image}
            alt={`${city}, ${country}`}
            loading="lazy"
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transition: "transform .5s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "scale(1.06)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "scale(1)";
            }}
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />

          <div
            style={{
              position: "absolute",
              inset: 0,
              background: `linear-gradient(180deg, transparent 35%, ${color || "#0b1f3a"}dd)`,
            }}
          />

          <span
            style={{
              position: "absolute",
              top: 14,
              left: 14,
              padding: "5px 10px",
              borderRadius: 999,
              background: "rgba(7,26,51,.6)",
              backdropFilter: "blur(8px)",
              color: "#fff",
              fontFamily: '"Manrope", sans-serif',
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: ".08em",
            }}
          >
            {code}
          </span>
        </div>

        <div style={{ padding: "18px 20px 20px" }}>
          <h3 style={{ marginBottom: 5, fontSize: 18 }}>{city}</h3>
          <p style={{ color: "var(--muted)", fontSize: 14 }}>{country}</p>
        </div>
      </Link>
    </motion.div>
  );
}