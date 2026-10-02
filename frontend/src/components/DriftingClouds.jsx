// src/components/DriftingClouds.jsx

import { motion } from "framer-motion";

const clouds = [
  {
    top: "10%",
    left: "-15%",
    width: 520,
    opacity: 0.16,
    duration: 75,
    delay: 0,
  },
  {
    top: "28%",
    left: "68%",
    width: 600,
    opacity: 0.12,
    duration: 90,
    delay: -30,
  },
  {
    top: "50%",
    left: "-18%",
    width: 650,
    opacity: 0.1,
    duration: 100,
    delay: -55,
  },
  {
    top: "70%",
    left: "65%",
    width: 500,
    opacity: 0.09,
    duration: 85,
    delay: -20,
  },
];

function Cloud({ width, opacity }) {
  return (
    <div
      style={{
        position: "relative",
        width,
        height: width * 0.22,
        opacity,
      }}
    >
      {/* Main continuous cloud body */}
      <div
        style={{
          position: "absolute",
          inset: "35% 0 0",
          borderRadius: "50% 50% 42% 38%",
          background:
            "linear-gradient(180deg, rgba(255,255,255,.82), rgba(255,255,255,.5))",
          filter: "blur(9px)",
        }}
      />

      {/* Soft upper cloud mass */}
      <div
        style={{
          position: "absolute",
          left: "10%",
          top: "22%",
          width: "48%",
          height: "55%",
          borderRadius: "58% 42% 45% 50%",
          background: "rgba(255,255,255,.72)",
          filter: "blur(10px)",
        }}
      />

      {/* Irregular central mass */}
      <div
        style={{
          position: "absolute",
          left: "30%",
          top: "5%",
          width: "42%",
          height: "72%",
          borderRadius: "45% 55% 48% 52%",
          background: "rgba(255,255,255,.76)",
          filter: "blur(11px)",
        }}
      />

      {/* Long soft right side */}
      <div
        style={{
          position: "absolute",
          right: "4%",
          top: "30%",
          width: "42%",
          height: "48%",
          borderRadius: "50% 45% 55% 40%",
          background: "rgba(255,255,255,.66)",
          filter: "blur(12px)",
        }}
      />

      {/* Soft edge haze */}
      <div
        style={{
          position: "absolute",
          inset: "10% -5% -5%",
          borderRadius: "50%",
          background: "rgba(255,255,255,.28)",
          filter: "blur(20px)",
        }}
      />
    </div>
  );
}

export default function DriftingClouds() {
  return (
    <div
      aria-hidden="true"
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        pointerEvents: "none",
        zIndex: 0,
      }}
    >
      {clouds.map((cloud, index) => (
        <motion.div
          key={index}
          initial={{ x: "-20vw" }}
          animate={{
            x: ["-20vw", "120vw"],
            y: [0, -4, 3, 0],
          }}
          transition={{
            duration: cloud.duration,
            delay: cloud.delay,
            repeat: Infinity,
            ease: "linear",
          }}
          style={{
            position: "absolute",
            top: cloud.top,
            left: cloud.left,
          }}
        >
          <Cloud
            width={cloud.width}
            opacity={cloud.opacity}
          />
        </motion.div>
      ))}
    </div>
  );
}