import { motion } from "framer-motion";

export default function SectionHeader({ eyebrow, title }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      style={{ textAlign: "center" }}
    >
      <span
        style={{
          display: "inline-block",
          marginBottom: 10,
          color: "var(--primary)",
          fontFamily: '"Manrope", sans-serif',
          fontSize: 12,
          fontWeight: 700,
          letterSpacing: ".12em",
          textTransform: "uppercase",
        }}
      >
        {eyebrow}
      </span>

      <h2
        style={{
          fontSize: "clamp(28px, 4vw, 44px)",
          letterSpacing: "-.035em",
        }}
      >
        {title}
      </h2>
    </motion.div>
  );
}