// src/pages/Confirmation.jsx

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FiAlertCircle,
  FiArrowRight,
  FiCheck,
  FiClock,
  FiRefreshCw,
  FiShield,
} from "react-icons/fi";

import { api } from "../api/client";
import DownloadTicketButton from "../components/DownloadTicketButton";

function fmtDate(iso) {
  return new Date(iso).toLocaleDateString([], {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function fmtTime(iso) {
  return new Date(iso).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export default function Confirmation() {
  const { bookingId } = useParams();

  const [booking, setBooking] = useState(null);
  const [flight, setFlight] = useState(null);
  const [seat, setSeat] = useState(null);
  const [state, setState] = useState({
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const { data: bookingData } = await api.get(
          `/api/bookings/${bookingId}`
        );

        if (cancelled) return;

        const [{ data: flightData }, { data: seats }] =
          await Promise.all([
            api.get(`/api/flights/${bookingData.flight_id}`),
            api.get(`/api/flights/${bookingData.flight_id}/seats`),
          ]);

        if (cancelled) return;

        setBooking(bookingData);
        setFlight(flightData);
        setSeat(
          seats.find((item) => item.id === bookingData.seat_id) ||
            null
        );

        setState({
          loading: false,
          error: null,
        });
      } catch (err) {
        if (cancelled) return;

        setState({
          loading: false,
          error:
            err.response?.data?.detail ||
            "Could not load booking.",
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [bookingId]);

  if (state.loading) return <Loading />;
  if (state.error) return <ErrorBlock message={state.error} />;

  if (!booking || !flight) return null;

  const route = flight.route;
  const isRefundPending = booking.status === "REFUND_REQUESTED";
  const isRefunded = booking.status === "REFUNDED";
  const isCheckedIn = ["CHECKED_IN", "COMPLETED"].includes(
    booking.status
  );
  const canDownloadTicket = !["UNPAID", "CANCELLED"].includes(
    booking.status
  );

  const statusStyle = isRefundPending
    ? {
        background: "#fff8eb",
        border: "1px solid #fde3b0",
        color: "#a15c00",
      }
    : isRefunded
      ? {
          background: "#f6efff",
          border: "1px solid #dfc7f5",
          color: "#6b21a8",
        }
      : {
          background: "#eaf8f1",
          border: "1px solid #b7e5cd",
          color: "#087443",
        };

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 760 }}>
        {(isRefundPending || isRefunded) && (
          <StatusBanner
            pending={isRefundPending}
            refunded={isRefunded}
            amount={booking.refund_amount}
          />
        )}

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.45,
            ease: [0.22, 1, 0.36, 1],
          }}
          className="card"
          style={{
            padding: "44px 32px",
            marginBottom: 24,
            textAlign: "center",
            background:
              "linear-gradient(135deg, #0b5ed7 0%, #1677ff 60%, #38bdf8 100%)",
            color: "#fff",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{
              delay: 0.15,
              type: "spring",
              stiffness: 200,
              damping: 14,
            }}
            style={{
              width: 72,
              height: 72,
              display: "grid",
              placeItems: "center",
              margin: "0 auto 20px",
              borderRadius: "50%",
              background: "rgba(255,255,255,.16)",
              border: "1px solid rgba(255,255,255,.22)",
            }}
          >
            <FiCheck size={38} strokeWidth={3} />
          </motion.div>

          <h1
            style={{
              fontSize: "clamp(28px, 4vw, 40px)",
              marginBottom: 8,
            }}
          >
            Booking confirmed!
          </h1>

          <p
            style={{
              color: "rgba(255,255,255,.82)",
              fontSize: 15,
            }}
          >
            Have a great flight,{" "}
            {route.origin_airport.city} →{" "}
            {route.destination_airport.city}
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.45,
            delay: 0.1,
          }}
          className="card"
          style={{ padding: 30 }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 16,
              paddingBottom: 20,
              marginBottom: 20,
              borderBottom: "1px solid var(--line)",
            }}
          >
            <div>
              <div
                style={{
                  color: "var(--muted)",
                  fontFamily: '"Manrope", sans-serif',
                  fontSize: 11,
                  fontWeight: 700,
                  letterSpacing: ".08em",
                }}
              >
                BOOKING REFERENCE
              </div>

              <div
                style={{
                  color: "var(--primary)",
                  fontFamily: '"Plus Jakarta Sans", sans-serif',
                  fontSize: 23,
                  fontWeight: 800,
                  letterSpacing: ".04em",
                  marginTop: 4,
                }}
              >
                {booking.booking_reference}
              </div>
            </div>

            <span
              style={{
                ...statusStyle,
                padding: "7px 12px",
                borderRadius: 999,
                fontFamily: '"Manrope", sans-serif',
                fontSize: 11,
                fontWeight: 700,
                whiteSpace: "nowrap",
              }}
            >
              ● {booking.status.replace(/_/g, " ")}
            </span>
          </div>

          <div style={{ display: "grid", gap: 0 }}>
            <Row
              label="Flight"
              value={flight.flight_number}
            />

            <Row
              label="Route"
              value={`${route.origin_airport.city} (${route.origin_airport.iata_code}) → ${route.destination_airport.city} (${route.destination_airport.iata_code})`}
            />

            <Row
              label="Date"
              value={fmtDate(flight.departure_time)}
            />

            <Row
              label="Departure"
              value={`${fmtTime(flight.departure_time)} · ${route.origin_airport.timezone}`}
            />

            <Row
              label="Arrival"
              value={`${fmtTime(flight.arrival_time)} · ${route.destination_airport.timezone}`}
            />

            <Row
              label="Aircraft"
              value={`${flight.aircraft?.manufacturer} ${flight.aircraft?.model}`}
            />

            <Row
              label="Seat"
              value={
                seat
                  ? `${seat.seat_number} · ${seat.seat_class}`
                  : "—"
              }
            />

            <Row
              label="Amount paid"
              value={
                <strong style={{ color: "var(--success)" }}>
                  ${Number(booking.fare_amount).toFixed(2)}
                </strong>
              }
            />

            {isRefunded && booking.refund_amount && (
              <Row
                label="Refunded"
                value={
                  <strong style={{ color: "#6b21a8" }}>
                    ${Number(booking.refund_amount).toFixed(2)}
                  </strong>
                }
              />
            )}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.45,
            delay: 0.2,
          }}
          className="confirmation-actions"
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(200px, 1fr))",
            gap: 12,
            marginTop: 20,
          }}
        >
          {canDownloadTicket && (
            <DownloadTicketButton
              bookingId={booking.id}
              reference={booking.booking_reference}
              variant="primary"
            />
          )}

          <Link
            to="/bookings"
            className="btn-outline"
            style={actionStyle}
          >
            View my bookings
            <FiArrowRight size={14} />
          </Link>

          <Link
            to="/search"
            className="btn-outline"
            style={actionStyle}
          >
            Book another flight
          </Link>
        </motion.div>

        {isCheckedIn && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            style={{
              marginTop: 20,
              padding: 18,
              borderRadius: 14,
              background: "#eef6ff",
              border: "1px solid #cfe2ff",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 16,
              flexWrap: "wrap",
            }}
          >
            <div>
              <div
                style={{
                  color: "var(--primary-dark)",
                  fontFamily: '"Manrope", sans-serif',
                  fontSize: 14,
                  fontWeight: 700,
                }}
              >
                You're checked in
              </div>

              <div
                style={{
                  color: "#4774a8",
                  fontSize: 12,
                  marginTop: 3,
                }}
              >
                Download your boarding pass before heading to
                the airport.
              </div>
            </div>

            <DownloadTicketButton
              bookingId={booking.id}
              reference={booking.booking_reference}
              variant="primary"
              label="Boarding pass"
            />
          </motion.div>
        )}

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 6,
            marginTop: 22,
            color: "var(--muted)",
            fontSize: 12,
          }}
        >
          <FiShield size={13} />
          Confirmation email sent — demo only.
        </div>
      </div>

      <style>{`
        @media (max-width: 520px) {
          .confirmation-actions {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}

function StatusBanner({ pending, amount }) {
  const config = pending
    ? {
        icon: <FiClock size={19} />,
        title: "Refund pending review",
        text: "Your refund request is being reviewed by an administrator.",
        background: "#fff8eb",
        border: "#fde3b0",
        color: "#a15c00",
      }
    : {
        icon: <FiRefreshCw size={19} />,
        title: `Refunded $${Number(amount || 0).toFixed(2)}`,
        text: "The refund has been processed back to your original payment method.",
        background: "#f6efff",
        border: "#dfc7f5",
        color: "#6b21a8",
      };

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
      style={{
        padding: 16,
        marginBottom: 20,
        display: "flex",
        alignItems: "center",
        gap: 12,
        background: config.background,
        border: `1px solid ${config.border}`,
        color: config.color,
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          display: "grid",
          placeItems: "center",
          flexShrink: 0,
          borderRadius: 11,
          background: "rgba(0,0,0,.05)",
        }}
      >
        {config.icon}
      </div>

      <div>
        <strong
          style={{
            fontFamily: '"Manrope", sans-serif',
            fontSize: 13,
          }}
        >
          {config.title}
        </strong>

        <div
          style={{
            fontSize: 12,
            opacity: 0.82,
            marginTop: 2,
          }}
        >
          {config.text}
        </div>
      </div>
    </motion.div>
  );
}

function Row({ label, value }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "150px 1fr",
        gap: 18,
        padding: "11px 0",
        borderBottom: "1px solid #f0f2f5",
        fontSize: 13,
      }}
    >
      <span style={{ color: "var(--muted)" }}>
        {label}
      </span>

      <span
        style={{
          color: "var(--ink)",
          fontWeight: 500,
          overflowWrap: "anywhere",
        }}
      >
        {value}
      </span>
    </div>
  );
}

const actionStyle = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 8,
  padding: "13px 18px",
  fontSize: 14,
  fontWeight: 600,
};

function Loading() {
  return (
    <div className="page">
      <div
        className="container"
        style={{ maxWidth: 760 }}
      >
        <div
          className="card"
          style={{
            height: 400,
            background:
              "linear-gradient(90deg, #f6f8fc 0%, #e9eef5 50%, #f6f8fc 100%)",
            backgroundSize: "200% 100%",
            animation: "aeriva-shimmer 1.4s infinite",
          }}
        />
      </div>

      <style>{`
        @keyframes aeriva-shimmer {
          0% {
            background-position: 200% 0;
          }

          100% {
            background-position: -200% 0;
          }
        }
      `}</style>
    </div>
  );
}

function ErrorBlock({ message }) {
  return (
    <div className="page">
      <div
        className="container"
        style={{ maxWidth: 700 }}
      >
        <div
          className="card"
          style={{
            padding: 48,
            textAlign: "center",
          }}
        >
          <div
            style={{
              width: 58,
              height: 58,
              display: "grid",
              placeItems: "center",
              margin: "0 auto 18px",
              borderRadius: 16,
              background: "#fef2f2",
              color: "var(--danger)",
            }}
          >
            <FiAlertCircle size={28} />
          </div>

          <h2
            style={{
              fontSize: 21,
              marginBottom: 8,
            }}
          >
            Booking not found
          </h2>

          <p
            style={{
              color: "var(--muted)",
              fontSize: 14,
              lineHeight: 1.6,
              marginBottom: 24,
            }}
          >
            {message}
          </p>

          <Link
            to="/"
            className="btn-primary"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 7,
              padding: "12px 22px",
            }}
          >
            Back to home
          </Link>
        </div>
      </div>
    </div>
  );
}