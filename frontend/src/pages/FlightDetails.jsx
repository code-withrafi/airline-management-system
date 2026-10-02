import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FiAlertCircle,
  FiArrowLeft,
  FiArrowRight,
  FiClock,
} from "react-icons/fi";
import { MdFlightTakeoff } from "react-icons/md";

import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

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
    year: "numeric",
  });

const fmtDuration = (minutes) => {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h ? `${h}h${m ? ` ${m}m` : ""}` : `${m}m`;
};

export default function FlightDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const [state, setState] = useState({
    loading: true,
    error: null,
    flight: null,
  });

  useEffect(() => {
    let cancelled = false;

    api
      .get(`/api/flights/${id}`)
      .then(({ data }) => {
        if (!cancelled) {
          setState({ loading: false, error: null, flight: data });
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setState({
            loading: false,
            error: err.response?.data?.detail || "Flight not found.",
            flight: null,
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  const handleBook = () => {
    if (isAuthenticated) return navigate(`/booking/${id}`);
    navigate(`/login?next=${encodeURIComponent(`/booking/${id}`)}`);
  };

  if (state.loading) return <Loading />;
  if (state.error) return <ErrorBlock message={state.error} />;
  if (!state.flight) return null;

  const f = state.flight;
  const { route } = f;
  const from = route.origin_airport;
  const to = route.destination_airport;

  const economyFare = Number(f.economy_fare ?? f.base_fare);
  const businessFare = Number(f.business_fare ?? f.base_fare * 2.5);
  const hasBusiness = businessFare > economyFare;

  const backUrl = `/search?origin=${from.iata_code}&destination=${to.iata_code}&date=${f.departure_time.slice(
    0,
    10
  )}`;

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 1000 }}>
        <Link
          to={backUrl}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            marginBottom: 24,
            color: "var(--muted)",
            fontFamily: '"Manrope", sans-serif',
            fontSize: 14,
            fontWeight: 600,
          }}
        >
          <FiArrowLeft size={15} />
          Back to results
        </Link>

        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card"
          style={{
            position: "relative",
            overflow: "hidden",
            padding: 40,
            marginBottom: 24,
            color: "#fff",
            background:
              "linear-gradient(135deg, #071a33 0%, #0b3b78 60%, #1677ff 100%)",
          }}
        >
          <MdFlightTakeoff
            size={210}
            style={{
              position: "absolute",
              top: -35,
              right: -20,
              opacity: 0.06,
              transform: "rotate(-15deg)",
            }}
          />

          <div
            style={{
              position: "relative",
              display: "flex",
              alignItems: "center",
              gap: 12,
              marginBottom: 36,
            }}
          >
            <span
              style={{
                padding: "5px 11px",
                borderRadius: 8,
                background: "rgba(125,211,252,.14)",
                color: "#7dd3fc",
                fontFamily: '"Manrope", sans-serif',
                fontSize: 12,
                fontWeight: 700,
              }}
            >
              {f.flight_number}
            </span>

            <span style={{ color: "rgba(255,255,255,.65)", fontSize: 13 }}>
              {f.aircraft?.manufacturer} {f.aircraft?.model}
            </span>

            <span
              style={{
                marginLeft: "auto",
                padding: "5px 10px",
                borderRadius: 999,
                background: "rgba(18,183,106,.15)",
                color: "#6ee7b7",
                fontSize: 12,
                fontWeight: 700,
              }}
            >
              ● {f.status}
            </span>
          </div>

          <div
            style={{
              position: "relative",
              display: "grid",
              gridTemplateColumns: "1fr auto 1fr",
              alignItems: "center",
              gap: 24,
            }}
          >
            <Airport
              time={fmtTime(f.departure_time)}
              code={from.iata_code}
              city={from.city}
              date={fmtDate(f.departure_time)}
            />

            <div style={{ minWidth: 180, textAlign: "center" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  gap: 6,
                  marginBottom: 9,
                  color: "rgba(255,255,255,.6)",
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
                  gap: 6,
                }}
              >
                <span className="route-dot" />
                <span className="route-line" />
                <MdFlightTakeoff
                  size={18}
                  color="#7dd3fc"
                  style={{ transform: "rotate(90deg)" }}
                />
                <span className="route-line" />
                <span className="route-dot" />
              </div>

              <small
                style={{
                  display: "block",
                  marginTop: 9,
                  color: "rgba(255,255,255,.5)",
                }}
              >
                {route.distance_km} km
              </small>
            </div>

            <Airport
              align="right"
              time={fmtTime(f.arrival_time)}
              code={to.iata_code}
              city={to.city}
              date={fmtDate(f.arrival_time)}
            />
          </div>

          <style>{`
            .route-dot {
              width: 7px;
              height: 7px;
              flex-shrink: 0;
              border-radius: 50%;
              background: #7dd3fc;
            }

            .route-line {
              flex: 1;
              height: 1px;
              background: rgba(125,211,252,.4);
            }
          `}</style>
        </motion.section>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.55fr 1fr",
            gap: 24,
            alignItems: "start",
          }}
        >
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="card"
            style={{ padding: 30 }}
          >
            <h2 style={{ marginBottom: 20, fontSize: 20 }}>
              Flight details
            </h2>

            <DetailRow
              label="Airline code"
              value={f.flight_number.slice(0, 2)}
            />
            <DetailRow
              label="Aircraft"
              value={`${f.aircraft?.manufacturer || ""} ${
                f.aircraft?.model || ""
              }`}
            />
            <DetailRow
              label="Registration"
              value={f.aircraft?.registration_number || "—"}
            />
            <DetailRow
              label="Seats"
              value={`${f.aircraft?.seat_capacity || "—"} seats`}
            />
            <DetailRow
              label="Boarding gate"
              value={f.boarding_gate || "TBD"}
            />
            <DetailRow
              label="Origin"
              value={`${from.iata_code} · ${from.name}`}
              sub={`${from.icao_code} · ${from.timezone}`}
            />
            <DetailRow
              label="Destination"
              value={`${to.iata_code} · ${to.name}`}
              sub={`${to.icao_code} · ${to.timezone}`}
            />
          </motion.section>

          <motion.aside
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="card"
            style={{
              position: "sticky",
              top: 92,
              padding: 30,
            }}
          >
            <small
              style={{
                color: "var(--muted)",
                fontFamily: '"Manrope", sans-serif',
                fontWeight: 700,
                letterSpacing: ".05em",
              }}
            >
              ECONOMY FROM
            </small>

            <div
              style={{
                margin: "6px 0",
                fontSize: 42,
                fontWeight: 700,
                letterSpacing: "-.04em",
              }}
            >
              ${economyFare.toFixed(2)}
            </div>

            <p
              style={{
                marginBottom: 20,
                color: "var(--muted)",
                fontSize: 13,
              }}
            >
              Per passenger · taxes included
            </p>

            {hasBusiness && (
              <div
                style={{
                  marginBottom: 20,
                  padding: "9px 12px",
                  borderRadius: 10,
                  background: "#fff7e6",
                  color: "#b54708",
                  fontSize: 13,
                  fontWeight: 600,
                }}
              >
                Business from ${businessFare.toFixed(2)}
              </div>
            )}

            <button
              onClick={handleBook}
              className="btn-primary"
              style={{
                width: "100%",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                gap: 8,
                padding: "14px 20px",
                fontSize: 15,
              }}
            >
              Book this flight
              <FiArrowRight size={16} />
            </button>

            {!isAuthenticated && (
              <p
                style={{
                  marginTop: 14,
                  color: "var(--muted)",
                  textAlign: "center",
                  fontSize: 12,
                  lineHeight: 1.5,
                }}
              >
                Sign in is required to complete your booking.
              </p>
            )}
          </motion.aside>
        </div>
      </div>
    </div>
  );
}

function Airport({ time, code, city, date, align }) {
  return (
    <div style={{ textAlign: align || "left" }}>
      <div
        style={{
          fontSize: 46,
          fontWeight: 700,
          letterSpacing: "-.04em",
        }}
      >
        {time}
      </div>

      <strong style={{ display: "block", marginTop: 9, fontSize: 19 }}>
        {code}
      </strong>

      <div
        style={{
          marginTop: 2,
          color: "rgba(255,255,255,.7)",
          fontSize: 14,
        }}
      >
        {city}
      </div>

      <small
        style={{
          display: "block",
          marginTop: 7,
          color: "rgba(255,255,255,.5)",
        }}
      >
        {date}
      </small>
    </div>
  );
}

function DetailRow({ label, value, sub }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "130px 1fr",
        gap: 18,
        padding: "13px 0",
        borderBottom: "1px solid var(--line)",
        fontSize: 14,
      }}
    >
      <span style={{ color: "var(--muted)" }}>{label}</span>

      <span style={{ fontWeight: 600 }}>
        {value}

        {sub && (
          <small
            style={{
              display: "block",
              marginTop: 3,
              color: "#98a2b3",
              fontWeight: 400,
            }}
          >
            {sub}
          </small>
        )}
      </span>
    </div>
  );
}

function Loading() {
  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 1000 }}>
        <div
          className="card"
          style={{
            height: 300,
            background:
              "linear-gradient(90deg, #f1f5f9, #e2e8f0, #f1f5f9)",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.4s infinite",
          }}
        />

        <style>{`
          @keyframes shimmer {
            from {
              background-position: 200% 0;
            }

            to {
              background-position: -200% 0;
            }
          }
        `}</style>
      </div>
    </div>
  );
}

function ErrorBlock({ message }) {
  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 650 }}>
        <div className="card" style={{ padding: 48, textAlign: "center" }}>
          <FiAlertCircle
            size={44}
            color="var(--danger)"
            style={{ marginBottom: 14 }}
          />

          <h2 style={{ marginBottom: 8, fontSize: 20 }}>
            Flight not available
          </h2>

          <p style={{ marginBottom: 24, color: "var(--muted)" }}>
            {message}
          </p>

          <Link
            to="/"
            className="btn-primary"
            style={{ display: "inline-block" }}
          >
            Back to home
          </Link>
        </div>
      </div>
    </div>
  );
}