import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { FiAlertCircle, FiArrowLeft, FiInbox } from "react-icons/fi";

import { api } from "../api/client";
import SearchWidget from "../components/SearchWidget";
import FlightCard from "../components/FlightCard";

const fmtDate = (date) =>
  new Date(`${date}T00:00:00`).toLocaleDateString([], {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

export default function SearchResults() {
  const [params] = useSearchParams();
  const origin = (params.get("origin") || "").toUpperCase();
  const destination = (params.get("destination") || "").toUpperCase();
  const date = params.get("date") || "";

  const [state, setState] = useState({
    loading: false,
    error: null,
    flights: [],
    query: null,
  });

  useEffect(() => {
    if (!origin || !destination || !date) return;

    let cancelled = false;

    Promise.resolve().then(() => {
      if (!cancelled) {
        setState((s) => ({ ...s, loading: true, error: null }));
      }
    });

    api
      .get("/api/flights/search", {
        params: { origin, destination, date },
      })
      .then(({ data }) => {
        if (cancelled) return;

        setState({
          loading: false,
          error: null,
          flights: data.results || [],
          query: { origin, destination, date },
        });
      })
      .catch((err) => {
        if (cancelled) return;

        setState({
          loading: false,
          error:
            err.response?.data?.detail ||
            "Could not load flights. Please try again.",
          flights: [],
          query: null,
        });
      });

    return () => {
      cancelled = true;
    };
  }, [origin, destination, date]);

  const from = state.flights[0]?.route?.origin_airport?.city;
  const to = state.flights[0]?.route?.destination_airport?.city;

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 1000 }}>
        <Link
          to="/"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            marginBottom: 24,
            color: "var(--muted)",
            fontSize: 14,
            fontFamily: '"Manrope", sans-serif',
            fontWeight: 600,
          }}
        >
          <FiArrowLeft size={15} />
          Back to home
        </Link>

        <motion.header
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          style={{ marginBottom: 30 }}
        >
          <h1
            style={{
              marginBottom: 7,
              fontSize: "clamp(26px, 3.5vw, 38px)",
              letterSpacing: "-.04em",
            }}
          >
            {from && to
              ? `${from} → ${to}`
              : `${origin || "Origin"} → ${
                  destination || "Destination"
                }`}
          </h1>

          {date && (
            <p style={{ color: "var(--muted)", fontSize: 15 }}>
              {fmtDate(date)}
              {state.query && (
                <>
                  {" · "}
                  <strong style={{ color: "var(--ink)" }}>
                    {state.flights.length}
                  </strong>{" "}
                  {state.flights.length === 1 ? "flight" : "flights"}
                </>
              )}
            </p>
          )}
        </motion.header>

        <div style={{ marginBottom: 36 }}>
          <SearchWidget
            compact
            initial={{ origin, destination, date }}
          />
        </div>

        {state.loading && <LoadingSkeleton />}
        {state.error && <ErrorBox message={state.error} />}

        {!state.loading &&
          !state.error &&
          state.query &&
          state.flights.length === 0 && <EmptyState />}

        {!state.loading &&
          !state.error &&
          state.flights.length > 0 && (
            <div>
              {state.flights.map((flight, index) => (
                <FlightCard
                  key={flight.id}
                  flight={flight}
                  index={index}
                />
              ))}
            </div>
          )}
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div>
      {[1, 2, 3].map((item) => (
        <motion.div
          key={item}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: item * 0.08 }}
          className="card"
          style={{
            height: 120,
            marginBottom: 16,
            background:
              "linear-gradient(90deg, #f1f5f9, #e2e8f0, #f1f5f9)",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.4s infinite",
          }}
        />
      ))}

      <style>{`
        @keyframes shimmer {
          from { background-position: 200% 0; }
          to { background-position: -200% 0; }
        }
      `}</style>
    </div>
  );
}

function ErrorBox({ message }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
      style={{
        padding: 36,
        textAlign: "center",
        borderColor: "#fecaca",
        background: "#fff7f7",
      }}
    >
      <FiAlertCircle
        size={38}
        color="var(--danger)"
        style={{ marginBottom: 12 }}
      />

      <h3 style={{ marginBottom: 6, fontSize: 18 }}>
        Something went wrong
      </h3>

      <p style={{ color: "#991b1b", fontSize: 14 }}>{message}</p>
    </motion.div>
  );
}

function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
      style={{
        padding: "56px 28px",
        textAlign: "center",
      }}
    >
      <FiInbox
        size={44}
        color="#98a2b3"
        style={{ marginBottom: 16 }}
      />

      <h3 style={{ marginBottom: 8, fontSize: 20 }}>
        No flights found
      </h3>

      <p
        style={{
          maxWidth: 420,
          margin: "0 auto",
          color: "var(--muted)",
          fontSize: 14,
          lineHeight: 1.7,
        }}
      >
        We couldn't find scheduled flights for this route and date.
        Try another date or route.
      </p>
    </motion.div>
  );
}