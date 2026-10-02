// src/components/AnimatedPlane.jsx

import { motion } from "framer-motion";
import { MdFlight } from "react-icons/md";

export default function AnimatedPlane() {
  const flightAnimation = {
    x: ["-20vw", "120vw"],
    y: [0, -18, 0, 18, 0],
    opacity: [0, 1, 1, 1, 0],
  };

  const flightTransition = {
    duration: 14,
    repeat: Infinity,
    ease: "easeInOut",
    times: [0, 0.05, 0.5, 0.95, 1],
  };

  return (
    <motion.div
      initial={{ x: "-20vw", y: 0, opacity: 0 }}
      animate={flightAnimation}
      transition={flightTransition}
      style={{
        position: "absolute",
        top: "18%",
        left: 0,
        zIndex: 2,
        width: 90,
        height: 44,
        pointerEvents: "none",
      }}
    >
      {/* Soft outer glow */}
      <motion.div
        animate={{
          opacity: [0, 0.35, 0.2, 0.35, 0],
          scaleX: [0.7, 1, 1.05, 1, 0.7],
        }}
        transition={{
          ...flightTransition,
          duration: 14,
        }}
        style={{
          position: "absolute",
          right: 38,
          top: "50%",
          width: 70,
          height: 10,
          transform: "translateY(-50%)",
          borderRadius: 999,
          background:
            "linear-gradient(90deg, transparent, rgba(56,189,248,.35), rgba(255,255,255,.5))",
          filter: "blur(8px)",
        }}
      />

      {/* Main aircraft trail */}
      <motion.div
        animate={{
          opacity: [0, 0.7, 0.45, 0.7, 0],
          width: [12, 54, 62, 54, 12],
        }}
        transition={{
          ...flightTransition,
          duration: 14,
        }}
        style={{
          position: "absolute",
          right: 38,
          top: "50%",
          height: 2,
          transform: "translateY(-50%)",
          borderRadius: 999,
          background:
            "linear-gradient(90deg, transparent, rgba(56,189,248,.35), rgba(255,255,255,.9))",
          boxShadow: "0 0 10px rgba(56,189,248,.55)",
        }}
      />

      {/* Aircraft */}
      <motion.div
        animate={{
          y: [0, -2, 0, 2, 0],
          rotate: [0, -1, 0, 1, 0],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        style={{
          position: "absolute",
          right: 0,
          top: 0,
          color: "#fbbf24",
          filter: "drop-shadow(0 0 18px rgba(251,191,36,.55))",
        }}
      >
        <MdFlight
          size={44}
          style={{
            transform: "rotate(90deg)",
          }}
        />
      </motion.div>
    </motion.div>
  );
}

