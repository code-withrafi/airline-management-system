import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { FiArrowRight, FiClock, FiMapPin } from "react-icons/fi";
import { MdFlightTakeoff } from "react-icons/md";

const fmtTime = (iso) =>
  new Date(iso).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });

const fmtDate = (iso) =>
  new Date(iso).toLocaleDateString([], {
    weekday: "short",
    day: "numeric",
    month: "short",
  });

const fmtDuration = (minutes) => {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h ? `${h}h${m ? ` ${m}m` : ""}` : `${m}m`;
};

export default function FlightCard({ flight, index = 0 }) {
  const { route } = flight;
  const from = route.origin_airport;

  return (
    <motion.article
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.4,
        delay: index * 0.06,
        ease: [0.22, 1, 0.36, 1],
      }}
      whileHover={{ y: -4 }}
      className="card"
      style={{
        display: "grid",
        gridTemplateColumns: "1.4fr 1fr 1fr auto",
        alignItems: "center",
        gap: 24,
        padding: 24,
        marginBottom: 16,
      }}
    >
      <div>
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 7,
            marginBottom: 9,
            padding: "5px 10px",
            borderRadius: 8,
            background: "#eaf3ff",
            color: "var(--primary)",
            fontFamily: '"Manrope", sans-serif',
            fontSize: 12,
            fontWeight: 700,
          }}
        >
          <MdFlightTakeoff size={14} />
          {flight.flight_number}
        </span>

        <p style={{ color: "var(--muted)", fontSize: 13 }}>
          {flight.aircraft?.manufacturer} {flight.aircraft?.model}
        </p>
      </div>

      <div>
        <strong
          style={{
            display: "block",
            marginBottom: 5,
            fontSize: 23,
            letterSpacing: "-.03em",
          }}
        >
          {fmtTime(flight.departure_time)}
        </strong>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            color: "var(--muted)",
            fontSize: 13,
          }}
        >
          <FiMapPin size={13} />
          <b style={{ color: "var(--ink)" }}>{from.iata_code}</b>
          <span>·</span>
          {from.city}
        </div>

        <small style={{ color: "#98a2b3" }}>
          {fmtDate(flight.departure_time)}
        </small>
      </div>

      <div style={{ textAlign: "center", color: "var(--muted)" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            gap: 5,
            marginBottom: 7,
            fontSize: 12,
          }}
        >
          <FiClock size={13} />
          {fmtDuration(route.estimated_duration_minutes)}
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 5,
            marginBottom: 6,
          }}
        >
          <span
            style={{
              flex: 1,
              height: 1,
              background: "var(--line)",
            }}
          />

          <FiArrowRight size={15} />

          <span
            style={{
              flex: 1,
              height: 1,
              background: "var(--line)",
            }}
          />
        </div>

        <small>{route.distance_km} km</small>
      </div>

      <div style={{ textAlign: "right" }}>
        <small style={{ color: "#98a2b3" }}>From</small>

        <div
          style={{
            margin: "2px 0 10px",
            fontSize: 25,
            fontWeight: 700,
            letterSpacing: "-.03em",
          }}
        >
          ${Number(flight.base_fare).toFixed(2)}
        </div>

        <Link
          to={`/flights/${flight.id}`}
          className="btn-primary"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            padding: "10px 18px",
            fontSize: 13,
          }}
        >
          Select
          <FiArrowRight size={14} />
        </Link>
      </div>
    </motion.article>
  );
}