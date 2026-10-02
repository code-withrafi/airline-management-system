// src/pages/Payment.jsx

import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FiAlertCircle,
  FiArrowLeft,
  FiCalendar,
  FiCheck,
  FiCreditCard,
  FiLock,
  FiMapPin,
  FiShield,
} from "react-icons/fi";
import { MdFlightTakeoff } from "react-icons/md";

import { api } from "../api/client";
import CountdownTimer from "../components/CountdownTimer";

const fmtAmount = (value) => Number(value).toFixed(2);

const fmtDate = (iso) =>
  new Date(iso).toLocaleDateString([], {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
  });

const fmtTime = (iso) =>
  new Date(iso).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });

export default function Payment() {
  const { bookingId } = useParams();
  const navigate = useNavigate();

  const [booking, setBooking] = useState(null);
  const [flight, setFlight] = useState(null);
  const [seat, setSeat] = useState(null);
  const [state, setState] = useState({ loading: true, error: null });

  const [card, setCard] = useState({
    card_number: "",
    card_number_display: "",
    expiry: "",
    expiry_display: "",
    cvv: "",
    cardholder_name: "",
  });

  const [submitting, setSubmitting] = useState(false);
  const [payError, setPayError] = useState("");
  const [expired, setExpired] = useState(false);

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
          seats.find((item) => item.id === bookingData.seat_id) || null
        );
        setState({ loading: false, error: null });
      } catch (err) {
        if (!cancelled) {
          setState({
            loading: false,
            error:
              err.response?.data?.detail || "Could not load booking.",
          });
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [bookingId]);

  const onCardNumber = (value) => {
    const digits = value.replace(/\D/g, "").slice(0, 19);
    setCard((current) => ({
      ...current,
      card_number: digits,
      card_number_display: digits.replace(/(.{4})/g, "$1 ").trim(),
    }));
  };

  const onExpiry = (value) => {
    const digits = value.replace(/\D/g, "").slice(0, 4);
    setCard((current) => ({
      ...current,
      expiry: digits,
      expiry_display:
        digits.length > 2
          ? `${digits.slice(0, 2)}/${digits.slice(2)}`
          : digits,
    }));
  };

  const onCvv = (value) => {
    setCard((current) => ({
      ...current,
      cvv: value.replace(/\D/g, "").slice(0, 4),
    }));
  };

  const handlePay = async (e) => {
    e.preventDefault();
    if (expired) {
      setPayError(
        "Payment window expired. Your seat has been released."
      );
      return;
    }
    setPayError("");
    setSubmitting(true);

    try {
      const { data } = await api.post("/api/payments", {
        booking_id: Number(bookingId),
        amount: Number(booking.fare_amount),
        card_number: card.card_number,
        expiry:
          card.expiry.length === 4
            ? `${card.expiry.slice(0, 2)}/${card.expiry.slice(2)}`
            : card.expiry,
        cvv: card.cvv,
        cardholder_name: card.cardholder_name.trim(),
      });

      if (data.success) {
        navigate(`/confirmation/${bookingId}`, { replace: true });
        return;
      }

      setPayError(data.message || "Payment declined.");
      setSubmitting(false);
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      let message = "Payment failed. Please try again.";

      if (typeof detail === "string") {
        message = detail;
      } else if (Array.isArray(detail)) {
        message = detail
          .map((item) => item.msg || JSON.stringify(item))
          .join(", ");
      } else if (detail) {
        message = JSON.stringify(detail);
      } else if (status === 401) {
        message = "Your session expired. Please sign in again.";
      } else if (status === 403) {
        message = "You are not authorized to pay for this booking.";
      } else if (status === 404) {
        message = "Booking not found.";
      } else if (status === 409) {
        message =
          "This booking cannot be paid because it is already paid or cancelled.";
      } else if (status === 422) {
        message =
          "Invalid payment details. Check your card number, expiry, and CVC.";
      } else if (status >= 500) {
        message =
          "Server error while processing payment. Please try again.";
      } else if (err.message) {
        message = err.message;
      }

      console.error("Payment error:", {
        status,
        data: err.response?.data,
        err,
      });

      setPayError(message);
      setSubmitting(false);
    }
  };

  if (state.loading) return <Loading />;
  if (state.error) return <ErrorBlock message={state.error} />;
  if (!booking || !flight) return null;

  const route = flight.route;
  const from = route.origin_airport;
  const to = route.destination_airport;

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 1080 }}>
        <Link
          to={`/booking/${flight.id}`}
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
          Back to seat selection
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          style={{ marginBottom: 28 }}
        >
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 7,
              marginBottom: 10,
              color: "var(--primary)",
              fontFamily: '"Manrope", sans-serif',
              fontSize: 12,
              fontWeight: 700,
              letterSpacing: ".04em",
              textTransform: "uppercase",
            }}
          >
            <FiLock size={13} />
            Secure checkout
          </div>

          <h1
            style={{
              fontSize: "clamp(28px, 4vw, 38px)",
              marginBottom: 8,
            }}
          >
            Complete your payment
          </h1>

          <p style={{ color: "var(--muted)", fontSize: 14 }}>
            Booking{" "}
            <strong style={{ color: "var(--ink)" }}>
              {booking.booking_reference}
            </strong>
            {" · "}Review your details before payment.
          </p>
        </motion.div>

        {booking.status === "UNPAID" && !expired && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "14px 18px",
              marginBottom: 24,
              borderRadius: 12,
              background: "#fff8eb",
              border: "1px solid #fde3b0",
              color: "#a15c00",
              fontSize: 14,
              lineHeight: 1.5,
            }}
          >
            <span style={{ fontSize: 18 }}>HOLD</span>
            <span>
              Your seat is held for{" "}
              <CountdownTimer
                secondsRemaining={booking.seconds_remaining}
                onExpire={() => {
                  setExpired(true);
                  setPayError(
                    "Payment window expired. Your seat has been released."
                  );
                }}
              />
              {" "}- pay before then, or it will be released.
            </span>
          </div>
        )}

        {expired && (
          <div
            role="alert"
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: 10,
              padding: "14px 18px",
              marginBottom: 24,
              borderRadius: 12,
              background: "#fef2f2",
              border: "1px solid #fecaca",
              color: "#b42318",
              fontSize: 14,
              lineHeight: 1.5,
            }}
          >
            <span style={{ fontSize: 18, flexShrink: 0 }}>EXPIRED</span>
            <div>
              <strong>Payment window expired.</strong>
              <div style={{ marginTop: 4, fontSize: 13 }}>
                Your seat has been released. Pick another seat to start a new booking.
              </div>
            </div>
          </div>
        )}

        <div
          className="payment-layout"
          style={{
            display: "grid",
            gridTemplateColumns:
              "minmax(0, 1.45fr) minmax(300px, .85fr)",
            gap: 24,
            alignItems: "start",
          }}
        >
          <motion.form
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.4,
              delay: 0.1,
              ease: [0.22, 1, 0.36, 1],
            }}
            onSubmit={handlePay}
            className="card"
            style={{ padding: 32 }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                paddingBottom: 22,
                marginBottom: 24,
                borderBottom: "1px solid var(--line)",
              }}
            >
              <div
                style={{
                  width: 46,
                  height: 46,
                  display: "grid",
                  placeItems: "center",
                  borderRadius: 13,
                  background: "#eaf3ff",
                  color: "var(--primary)",
                }}
              >
                <FiCreditCard size={22} />
              </div>

              <div>
                <h2 style={{ fontSize: 18, marginBottom: 3 }}>
                  Card payment
                </h2>
                <p style={{ color: "var(--muted)", fontSize: 13 }}>
                  Enter your card details below.
                </p>
              </div>
            </div>

            <Field
              label="Card number"
              type="text"
              inputMode="numeric"
              autoComplete="cc-number"
              placeholder="1234 5678 9012 3456"
              value={card.card_number_display}
              onChange={(e) => onCardNumber(e.target.value)}
              required
            />

            <Field
              label="Cardholder name"
              type="text"
              autoComplete="cc-name"
              placeholder="Name on card"
              value={card.cardholder_name}
              onChange={(e) =>
                setCard((current) => ({
                  ...current,
                  cardholder_name: e.target.value,
                }))
              }
              required
            />

            <div
              className="payment-fields"
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 16,
              }}
            >
              <Field
                label="Expiry date"
                type="text"
                inputMode="numeric"
                autoComplete="cc-exp"
                placeholder="MM/YY"
                value={card.expiry_display}
                onChange={(e) => onExpiry(e.target.value)}
                required
              />

              <Field
                label="CVC"
                type="password"
                inputMode="numeric"
                autoComplete="cc-csc"
                placeholder="•••"
                value={card.cvv}
                onChange={(e) => onCvv(e.target.value)}
                required
              />
            </div>

            {payError && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                role="alert"
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 9,
                  padding: "12px 13px",
                  marginTop: 4,
                  borderRadius: 10,
                  background: "#fef2f2",
                  border: "1px solid #fecaca",
                  color: "#b42318",
                  fontSize: 13,
                  lineHeight: 1.5,
                }}
              >
                <FiAlertCircle
                  size={16}
                  style={{ flexShrink: 0, marginTop: 1 }}
                />
                <span>{payError}</span>
              </motion.div>
            )}

            <button
              type="submit"
              disabled={submitting || expired}
              className="btn-primary"
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 9,
                padding: "14px 20px",
                marginTop: 20,
                fontSize: 15,
              }}
            >
              <FiLock size={16} />
              {submitting
                ? "Processing payment…"
                : `Pay $${fmtAmount(booking.fare_amount)}`}
            </button>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 7,
                marginTop: 15,
                color: "var(--muted)",
                fontSize: 11,
                lineHeight: 1.5,
                textAlign: "center",
              }}
            >
              <FiShield size={14} />
              <span>Demo payment — no real charge will be made.</span>
            </div>
          </motion.form>

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
                marginBottom: 20,
              }}
            >
              <h2 style={{ fontSize: 18 }}>Order summary</h2>

              <div
                style={{
                  width: 36,
                  height: 36,
                  display: "grid",
                  placeItems: "center",
                  borderRadius: 10,
                  background: "#eaf8f1",
                  color: "var(--success)",
                }}
              >
                <FiCheck size={17} />
              </div>
            </div>

            <div
              style={{
                padding: 15,
                marginBottom: 16,
                borderRadius: 13,
                background: "#f8fafc",
                border: "1px solid var(--line)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 7,
                  marginBottom: 12,
                  color: "var(--primary)",
                  fontFamily: '"Manrope", sans-serif',
                  fontSize: 11,
                  fontWeight: 700,
                  letterSpacing: ".05em",
                }}
              >
                <FiMapPin size={13} />
                JOURNEY
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                }}
              >
                <Airport code={from.iata_code} city={from.city} />

                <div
                  style={{
                    flex: 1,
                    height: 1,
                    background: "var(--line)",
                    position: "relative",
                  }}
                >
                  <MdFlightTakeoff
                    size={15}
                    style={{
                      position: "absolute",
                      left: "50%",
                      top: "50%",
                      transform:
                        "translate(-50%, -50%) rotate(90deg)",
                      padding: 1,
                      background: "#f8fafc",
                      color: "var(--primary)",
                    }}
                  />
                </div>

                <Airport
                  code={to.iata_code}
                  city={to.city}
                  align="right"
                />
              </div>
            </div>

            <SummaryRow label="Flight" value={flight.flight_number} />
            <SummaryRow
              label="Date"
              value={fmtDate(flight.departure_time)}
            />
            <SummaryRow
              label="Departure"
              value={fmtTime(flight.departure_time)}
            />
            <SummaryRow
              label="Seat"
              value={
                seat ? (
                  <span>
                    <strong>{seat.seat_number}</strong>{" "}
                    <span
                      style={{
                        color: "var(--muted)",
                        fontSize: 11,
                      }}
                    >
                      {seat.seat_class}
                    </span>
                  </span>
                ) : (
                  "—"
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
                  fontFamily: '"Plus Jakarta Sans", sans-serif',
                  fontSize: 30,
                  fontWeight: 800,
                  letterSpacing: "-.04em",
                }}
              >
                ${fmtAmount(booking.fare_amount)}
              </div>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 7,
                marginTop: 18,
                paddingTop: 16,
                borderTop: "1px solid var(--line)",
                color: "var(--muted)",
                fontSize: 11,
              }}
            >
              <FiCalendar size={13} />
              <span>{fmtDate(flight.departure_time)}</span>
            </div>
          </motion.div>
        </div>
      </div>

      <style>{`
        @media (max-width: 850px) {
          .payment-layout {
            grid-template-columns: 1fr !important;
          }

          .payment-layout > .card:last-child {
            position: static !important;
          }
        }

        @media (max-width: 520px) {
          .payment-fields {
            grid-template-columns: 1fr !important;
          }

          .payment-layout > .card {
            padding: 22px !important;
          }
        }
      `}</style>
    </div>
  );
}

function Field({
  label,
  type = "text",
  inputMode,
  autoComplete,
  placeholder,
  value,
  onChange,
  required,
}) {
  return (
    <div style={{ marginBottom: 18 }}>
      <label>{label}</label>
      <input
        type={type}
        inputMode={inputMode}
        autoComplete={autoComplete}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        required={required}
      />
    </div>
  );
}

function Airport({ code, city, align = "left" }) {
  return (
    <div style={{ textAlign: align, minWidth: 65 }}>
      <div
        style={{
          fontFamily: '"Plus Jakarta Sans", sans-serif',
          fontSize: 18,
          fontWeight: 800,
          letterSpacing: "-.03em",
        }}
      >
        {code}
      </div>

      <div
        style={{
          color: "var(--muted)",
          fontSize: 11,
          marginTop: 2,
        }}
      >
        {city}
      </div>
    </div>
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

function Loading() {
  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 1080 }}>
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
      <div className="container" style={{ maxWidth: 700 }}>
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

          <h2 style={{ fontSize: 22, marginBottom: 8 }}>
            Could not open payment
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
            to="/bookings"
            className="btn-primary"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 7,
              padding: "12px 22px",
            }}
          >
            View my bookings
          </Link>
        </motion.div>
      </div>
    </div>
  );
}