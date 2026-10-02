// src/pages/Booking.jsx

import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FiArrowLeft,
  FiAlertCircle,
  FiCalendar,
  FiCheck,
  FiInfo,
  FiMapPin,
  FiShield,
} from "react-icons/fi";
import { MdFlightTakeoff } from "react-icons/md";

import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import SeatMap from "../components/SeatMap";

function fmtTime(iso) {
  return new Date(iso).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function fmtShortDate(iso) {
  return new Date(iso).toLocaleDateString([], {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

export default function Booking() {
  const { flightId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [flight, setFlight] = useState(null);
  const [seats, setSeats] = useState([]);
  const [selectedSeat, setSelectedSeat] = useState(null);
  const [state, setState] = useState({
    loading: true,
    error: null,
  });
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  useEffect(() => {
    let cancelled = false;

    Promise.all([
      api.get(`/api/flights/${flightId}`),
      api.get(`/api/flights/${flightId}/seats`),
    ])
      .then(([flightRes, seatsRes]) => {
        if (cancelled) return;

        setFlight(flightRes.data);
        setSeats(seatsRes.data || []);
        setState({
          loading: false,
          error: null,
        });
      })
      .catch((err) => {
        if (cancelled) return;

        setState({
          loading: false,
          error:
            err.response?.data?.detail ||
            "Could not load flight details.",
        });
      });

    return () => {
      cancelled = true;
    };
  }, [flightId]);

  const baseFare = useMemo(
    () => (flight ? Number(flight.base_fare) : 0),
    [flight]
  );

  const selectedPrice = useMemo(() => {
    if (!selectedSeat || selectedSeat.price == null) return null;
    return Number(selectedSeat.price);
  }, [selectedSeat]);

  const total = selectedPrice ?? baseFare;

  const surcharge = useMemo(() => {
    if (selectedPrice == null) return 0;
    return Math.max(0, selectedPrice - baseFare);
  }, [selectedPrice, baseFare]);

  const isBusiness = selectedSeat?.seat_class === "BUSINESS";

  const availableSeats = seats.filter((seat) => seat.is_available).length;

  const handleContinue = async () => {
    if (!selectedSeat) return;

    setSubmitting(true);
    setSubmitError("");

    try {
      const { data: booking } = await api.post("/api/bookings", {
        flight_id: Number(flightId),
        seat_id: selectedSeat.id,
      });

      navigate(`/payment/${booking.id}`);
    } catch (err) {
      const detail = err.response?.data?.detail;

      setSubmitError(
        typeof detail === "string"
          ? detail
          : "Could not create the booking."
      );

      setSubmitting(false);
    }
  };

  if (state.loading) return <Loading />;
  if (state.error) return <ErrorBlock message={state.error} />;
  if (!flight) return null;

  const route = flight.route;
  const from = route.origin_airport;
  const to = route.destination_airport;

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 1120 }}>
        <Link
          to={`/flights/${flightId}`}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 7,
            color: "var(--muted)",
            fontFamily: '"Manrope", sans-serif',
            fontSize: 14,
            fontWeight: 600,
            marginBottom: 24,
          }}
        >
          <FiArrowLeft size={15} />
          Back to flight details
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.4,
            ease: [0.22, 1, 0.36, 1],
          }}
          className="card"
          style={{
            padding: "20px 24px",
            marginBottom: 24,
            display: "flex",
            alignItems: "center",
            gap: 20,
            flexWrap: "wrap",
          }}
        >
          <div
            style={{
              width: 42,
              height: 42,
              display: "grid",
              placeItems: "center",
              borderRadius: 12,
              background: "#eaf3ff",
              color: "var(--primary)",
              flexShrink: 0,
            }}
          >
            <MdFlightTakeoff size={22} />
          </div>

          <div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                marginBottom: 5,
              }}
            >
              <span
                style={{
                  color: "var(--primary)",
                  fontFamily: '"Manrope", sans-serif',
                  fontSize: 13,
                  fontWeight: 700,
                }}
              >
                {flight.flight_number}
              </span>

              <span style={{ color: "var(--line)" }}>/</span>

              <span
                style={{
                  color: "var(--muted)",
                  fontSize: 13,
                }}
              >
                {flight.aircraft?.manufacturer}{" "}
                {flight.aircraft?.model}
              </span>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 9,
                fontSize: 15,
              }}
            >
              <strong>{from.iata_code}</strong>

              <span style={{ color: "var(--muted)" }}>
                {fmtTime(flight.departure_time)}
              </span>

              <span style={{ color: "#98a2b3" }}>→</span>

              <span style={{ color: "var(--muted)" }}>
                {fmtTime(flight.arrival_time)}
              </span>

              <strong>{to.iata_code}</strong>
            </div>
          </div>

          <div
            style={{
              marginLeft: "auto",
              display: "flex",
              alignItems: "center",
              gap: 8,
              color: "var(--muted)",
              fontSize: 13,
            }}
          >
            <FiCalendar size={14} />
            {fmtShortDate(flight.departure_time)}
          </div>
        </motion.div>

        <div
          className="booking-layout"
          style={{
            display: "grid",
            gridTemplateColumns:
              "minmax(0, 1.65fr) minmax(300px, .85fr)",
            gap: 24,
            alignItems: "start",
          }}
        >
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.4,
              delay: 0.1,
              ease: [0.22, 1, 0.36, 1],
            }}
            className="card"
            style={{
              padding: 32,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: 20,
                marginBottom: 28,
              }}
            >
              <div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 9,
                    marginBottom: 7,
                  }}
                >
                  <span
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      background: "var(--success)",
                      boxShadow:
                        "0 0 0 4px rgba(18,183,106,.1)",
                    }}
                  />

                  <span
                    style={{
                      color: "var(--success)",
                      fontFamily: '"Manrope", sans-serif',
                      fontSize: 12,
                      fontWeight: 700,
                    }}
                  >
                    {availableSeats} seats available
                  </span>
                </div>

                <h2
                  style={{
                    fontSize: 22,
                    marginBottom: 6,
                  }}
                >
                  Choose your seat
                </h2>

                <p
                  style={{
                    color: "var(--muted)",
                    fontSize: 14,
                    lineHeight: 1.5,
                  }}
                >
                  Select an available seat to continue your booking.
                </p>
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 7,
                  padding: "8px 11px",
                  borderRadius: 10,
                  background: "#f6f8fc",
                  color: "var(--muted)",
                  fontSize: 12,
                  whiteSpace: "nowrap",
                }}
              >
                <FiInfo size={14} />
                Seat selection
              </div>
            </div>

            <div
              style={{
                padding: "18px 16px",
                borderRadius: 16,
                background:
                  "linear-gradient(180deg, #f8fbff 0%, #f5f8fc 100%)",
                border: "1px solid var(--line)",
              }}
            >
              <SeatMap
                seats={seats}
                selectedId={selectedSeat?.id || null}
                onSelect={setSelectedSeat}
              />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.4,
              delay: 0.2,
              ease: [0.22, 1, 0.36, 1],
            }}
            className="card"
            style={{
              padding: 28,
              position: "sticky",
              top: 92,
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 12,
                marginBottom: 22,
              }}
            >
              <h2 style={{ fontSize: 19 }}>Booking summary</h2>

              <div
                style={{
                  width: 36,
                  height: 36,
                  display: "grid",
                  placeItems: "center",
                  borderRadius: 10,
                  background: "#eaf3ff",
                  color: "var(--primary)",
                }}
              >
                <FiCheck size={17} />
              </div>
            </div>

            <div
              style={{
                padding: "14px 15px",
                marginBottom: 14,
                borderRadius: 12,
                background: "#f8fafc",
                border: "1px solid var(--line)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  marginBottom: 8,
                  color: "var(--primary)",
                  fontFamily: '"Manrope", sans-serif',
                  fontSize: 12,
                  fontWeight: 700,
                }}
              >
                <FiMapPin size={13} />
                YOUR JOURNEY
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 10,
                }}
              >
                <div>
                  <strong style={{ fontSize: 18 }}>
                    {from.iata_code}
                  </strong>

                  <div
                    style={{
                      marginTop: 2,
                      color: "var(--muted)",
                      fontSize: 12,
                    }}
                  >
                    {from.city}
                  </div>
                </div>

                <div
                  style={{
                    flex: 1,
                    height: 1,
                    background: "var(--line)",
                    position: "relative",
                  }}
                >
                  <MdFlightTakeoff
                    size={16}
                    style={{
                      position: "absolute",
                      left: "50%",
                      top: "50%",
                      transform:
                        "translate(-50%, -50%) rotate(90deg)",
                      background: "#f8fafc",
                      padding: 1,
                    }}
                  />
                </div>

                <div style={{ textAlign: "right" }}>
                  <strong style={{ fontSize: 18 }}>
                    {to.iata_code}
                  </strong>

                  <div
                    style={{
                      marginTop: 2,
                      color: "var(--muted)",
                      fontSize: 12,
                    }}
                  >
                    {to.city}
                  </div>
                </div>
              </div>
            </div>

            <SummaryRow
              label="Passenger"
              value={user?.email || "Passenger"}
            />

            <SummaryRow
              label="Flight"
              value={flight.flight_number}
            />

            <SummaryRow
              label="Date"
              value={fmtShortDate(flight.departure_time)}
            />

            <SummaryRow
              label="Seat"
              value={
                selectedSeat ? (
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    <strong>{selectedSeat.seat_number}</strong>

                    <span
                      style={{
                        color: "var(--muted)",
                        fontSize: 11,
                      }}
                    >
                      {selectedSeat.seat_class}
                    </span>
                  </span>
                ) : (
                  <span style={{ color: "#98a2b3" }}>
                    Not selected
                  </span>
                )
              }
            />

            <div
              style={{
                height: 1,
                background: "var(--line)",
                margin: "18px 0",
              }}
            />

            <div style={{ marginBottom: 20 }}>
              <PriceRow
                label="Base fare"
                value={baseFare}
                muted
              />

              {isBusiness && surcharge > 0 && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{
                    opacity: 1,
                    height: "auto",
                  }}
                  transition={{ duration: 0.25 }}
                  style={{ overflow: "hidden" }}
                >
                  <PriceRow
                    label="Business class surcharge"
                    value={surcharge}
                    prefix="+"
                    accent="var(--warning)"
                  />
                </motion.div>
              )}

              <div
                style={{
                  height: 1,
                  background: "var(--line)",
                  margin: "12px 0",
                }}
              />

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: 16,
                }}
              >
                <div>
                  <div
                    style={{
                      color: "var(--ink)",
                      fontFamily: '"Manrope", sans-serif',
                      fontSize: 14,
                      fontWeight: 700,
                    }}
                  >
                    Total
                  </div>

                  <div
                    style={{
                      color: "var(--muted)",
                      fontSize: 11,
                      marginTop: 2,
                    }}
                  >
                    Per passenger
                  </div>
                </div>

                <div
                  style={{
                    color: "var(--ink)",
                    fontFamily: '"Plus Jakarta Sans", sans-serif',
                    fontSize: 30,
                    fontWeight: 800,
                    letterSpacing: "-.04em",
                  }}
                >
                  ${total.toFixed(2)}
                </div>
              </div>
            </div>

            {isBusiness && (
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 8,
                  padding: "9px 11px",
                  marginBottom: 16,
                  borderRadius: 10,
                  background: "#fff8eb",
                  border: "1px solid #fde3b0",
                  color: "#a15c00",
                  fontSize: 12,
                  lineHeight: 1.45,
                }}
              >
                <FiInfo
                  size={14}
                  style={{ flexShrink: 0, marginTop: 1 }}
                />
                Business class fare includes priority boarding.
              </div>
            )}

            {submitError && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                role="alert"
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 8,
                  padding: "11px 12px",
                  marginBottom: 16,
                  borderRadius: 10,
                  background: "#fef2f2",
                  border: "1px solid #fecaca",
                  color: "#b42318",
                  fontSize: 13,
                  lineHeight: 1.45,
                }}
              >
                <FiAlertCircle
                  size={15}
                  style={{
                    flexShrink: 0,
                    marginTop: 1,
                  }}
                />
                {submitError}
              </motion.div>
            )}

            <button
              type="button"
              onClick={handleContinue}
              disabled={!selectedSeat || submitting}
              className="btn-primary"
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 8,
                padding: "14px 20px",
                fontSize: 15,
              }}
            >
              {submitting
                ? "Creating booking…"
                : "Continue to payment"}

              {!submitting && <FiArrowRightIcon />}
            </button>

            {!selectedSeat && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 7,
                  marginTop: 12,
                  color: "#98a2b3",
                  fontSize: 12,
                }}
              >
                <FiInfo size={13} />
                Select a seat to continue
              </div>
            )}

            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 7,
                marginTop: 18,
                paddingTop: 16,
                borderTop: "1px solid var(--line)",
                color: "var(--muted)",
                fontSize: 11,
              }}
            >
              <FiShield size={14} />
              Secure booking & payment
            </div>
          </motion.div>
        </div>
      </div>

      <style>{`
        @media (max-width: 900px) {
          .booking-layout {
            grid-template-columns: 1fr !important;
          }

          .booking-layout > .card:last-child {
            position: static !important;
          }
        }

        @media (max-width: 600px) {
          .booking-layout > .card {
            padding: 22px !important;
          }
        }
      `}</style>
    </div>
  );
}

function FiArrowRightIcon() {
  return (
    <span
      style={{
        display: "inline-flex",
        fontSize: 17,
      }}
    >
      →
    </span>
  );
}

function SummaryRow({ label, value }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: 16,
        padding: "8px 0",
        fontSize: 13,
      }}
    >
      <span style={{ color: "var(--muted)" }}>{label}</span>

      <span
        style={{
          color: "var(--ink)",
          fontWeight: 600,
          textAlign: "right",
          maxWidth: "65%",
          overflowWrap: "anywhere",
        }}
      >
        {value}
      </span>
    </div>
  );
}

function PriceRow({
  label,
  value,
  prefix = "",
  accent,
  muted,
}) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        gap: 16,
        padding: "6px 0",
        color:
          accent || (muted ? "var(--muted)" : "var(--ink)"),
        fontSize: 13,
        fontWeight: accent ? 600 : 400,
      }}
    >
      <span>{label}</span>

      <span
        style={{
          fontVariantNumeric: "tabular-nums",
          whiteSpace: "nowrap",
        }}
      >
        {prefix}${Number(value).toFixed(2)}
      </span>
    </div>
  );
}

function Loading() {
  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 1120 }}>
        <div
          className="card"
          style={{
            height: 460,
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
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
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
              fontSize: 22,
              marginBottom: 8,
            }}
          >
            Could not start booking
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
            <FiArrowLeft size={15} />
            Back to home
          </Link>
        </motion.div>
      </div>
    </div>
  );
}