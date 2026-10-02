import { motion } from "framer-motion";
import { fadeUpOnView } from "../../animations/variants";

export default function FeatureCard({ icon: Icon, title, text, delay = 0 }) {
  return (
    <motion.div
      {...fadeUpOnView(delay)}
      whileHover={{ y: -5 }}
      className="card"
      style={{
        padding: 28,
        transition: "box-shadow .25s ease",
      }}
    >
      <div
        style={{
          width: 52,
          height: 52,
          display: "grid",
          placeItems: "center",
          marginBottom: 20,
          borderRadius: 14,
          background: "#eaf3ff",
          color: "var(--primary)",
        }}
      >
        <Icon size={24} />
      </div>

      <h3 style={{ marginBottom: 8, fontSize: 19 }}>{title}</h3>

      <p
        style={{
          color: "var(--muted)",
          fontSize: 14,
          lineHeight: 1.7,
        }}
      >
        {text}
      </p>
    </motion.div>
  );
}