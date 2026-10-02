import { motion } from "framer-motion";
import { Link } from "react-router-dom";

export default function CTASection() {
  return (
    <section style={{ padding: "80px 0 110px", background: "var(--bg)" }}>
      <motion.div
        className="container"
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
        style={{
          padding: "64px 32px",
          textAlign: "center",
          color: "#fff",
          borderRadius: "var(--radius-lg)",
          background:
            "linear-gradient(135deg, #032241 0%, #273856 55%, #1F5885 100%)",
          boxShadow: "var(--shadow-hover)",
        }}
      >
        <h2
          style={{
            marginBottom: 12,
            fontSize: "clamp(28px, 4vw, 44px)",
            letterSpacing: "-.03em",
          }}
        >
          Ready for takeoff?
        </h2>

        <p
          style={{
            marginBottom: 30,
            color: "rgba(255,255,255,.72)",
            fontSize: 17,
          }}
        >
          Create your free account and start booking flights today.
        </p>

        <Link
          to="/register"
          className="btn-primary"
          style={{
            display: "inline-block",
            padding: "14px 28px",
            background: "#fff",
            color: "var(--primary)",
          }}
        >
          Create free account
        </Link>
      </motion.div>
    </section>
  );
}