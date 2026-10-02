// src/sections/landing/HeroSection.jsx

import { motion } from "framer-motion";
import AnimatedPlane from "../../components/AnimatedPlane";
import DriftingClouds from "../../components/DriftingClouds";
import SearchWidget from "../../components/SearchWidget";
import Stat from "../../components/ui/Stat";
import { fadeUp } from "../../animations/variants";
import { HERO_STATS } from "../../constants/landing";

export default function HeroSection() {
  return (
    <section
      style={{
        position: "relative",
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        overflow: "hidden",
        padding: "100px 0 80px",
        color: "#fff",
        background: `
          radial-gradient(
            ellipse at 50% 100%,
            rgba(56,189,248,.28) 0%,
            rgba(56,189,248,.08) 28%,
            transparent 58%
          ),
          linear-gradient(
            160deg,
            #06152b 0%,
            #092b57 38%,
            #0b4f91 70%,
            #1677ff 100%
          )
        `,
      }}
    >
      {/* Atmospheric glow */}
      <div
        aria-hidden="true"
        style={{
          position: "absolute",
          width: 600,
          height: 600,
          top: "-280px",
          right: "-180px",
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(56,189,248,.18), transparent 68%)",
          filter: "blur(20px)",
          pointerEvents: "none",
        }}
      />

      {/* Drifting clouds */}
      <DriftingClouds />

      {/* Animated aircraft */}
      <AnimatedPlane />

      <div
        className="container hero-content"
        style={{
          position: "relative",
          zIndex: 3,
          width: "min(1200px, calc(100% - 48px))",
          margin: "0 auto",
          textAlign: "center",
        }}
      >
        <motion.span
          {...fadeUp(0)}
          style={{
            display: "inline-block",
            marginBottom: 18,
            padding: "7px 14px",
            borderRadius: 999,
            background: "rgba(56,189,248,.14)",
            border: "1px solid rgba(125,211,252,.12)",
            color: "#7dd3fc",
            fontFamily: '"Manrope", sans-serif',
            fontSize: 13,
            fontWeight: 700,
            backdropFilter: "blur(8px)",
          }}
        >
          Fly smarter with Aeriva
        </motion.span>

        <motion.h1
          {...fadeUp(0.1)}
          style={{
            maxWidth: 900,
            margin: "0 auto 20px",
            fontSize: "clamp(42px, 7vw, 82px)",
            lineHeight: 1.04,
            letterSpacing: "-.045em",
            textShadow: "0 8px 35px rgba(0,0,0,.18)",
          }}
        >
          Fly anywhere.
          <br />
          Book in <span style={{ color: "#7dd3fc" }}>seconds.</span>
        </motion.h1>

        <motion.p
          {...fadeUp(0.2)}
          style={{
            maxWidth: 620,
            margin: "0 auto 44px",
            color: "rgba(255,255,255,.78)",
            fontSize: "clamp(16px, 1.7vw, 20px)",
            lineHeight: 1.6,
          }}
        >
          Compare fares, choose your seat, and get your ticket. All in one
          seamless experience.
        </motion.p>

        <SearchWidget />

        <motion.div
          {...fadeUp(0.7)}
          className="hero-stats"
          style={{
            display: "flex",
            justifyContent: "center",
            gap: 36,
            flexWrap: "wrap",
            marginTop: 42,
          }}
        >
          {HERO_STATS.map((stat) => (
            <Stat key={stat.label} {...stat} />
          ))}
        </motion.div>
      </div>

      {/* Bottom horizon glow */}
      <div
        aria-hidden="true"
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 0,
          height: 180,
          background:
            "linear-gradient(to top, rgba(255,255,255,.07), transparent)",
          pointerEvents: "none",
          zIndex: 1,
        }}
      />

      {/* Scroll indicator */}
      <motion.div
        animate={{ y: [0, 8, 0], opacity: [0.35, 0.65, 0.35] }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        style={{
          position: "absolute",
          bottom: 22,
          left: "50%",
          color: "rgba(255,255,255,.45)",
          fontSize: 22,
          zIndex: 4,
        }}
      >
        ↓
      </motion.div>

      <style>{`
        @media (max-width: 768px) {
          .hero-content {
            width: min(100% - 32px, 1200px) !important;
          }

          .hero-stats {
            gap: 20px !important;
            margin-top: 30px !important;
          }
        }

        @media (max-width: 480px) {
          .hero-content {
            width: min(100% - 24px, 1200px) !important;
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .hero-content * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
          }
        }
      `}</style>
    </section>
  );
}