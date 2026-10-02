// src/pages/BookingDetail.jsx

import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FiArrowLeft,
  FiAlertCircle,
  FiMapPin,
  FiClock,
  FiUser,
  FiMail,
  FiPhone,
  FiCreditCard,
  FiCalendar,
  FiX,
  FiRefreshCw,
  FiCheck,
  FiShare2,
  FiCopy,
} from "react-icons/fi";
import { MdFlightTakeoff } from "react-icons/md";

import { api } from "../api/client";
import DownloadTicketButton from "../components/DownloadTicketButton";
import RefundModal from "../components/RefundModal";

// ---------- helpers ----------

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
    year: "numeric",
  });
}

function fmtDateTime(iso) {
  if (!iso) return "—";

  const d = new Date(iso);

  return `${d.toLocaleDateString([], {
    day: "numeric",
    month: "short",
    year: "numeric",
  })}, ${d.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  })}`;
}

function fmtDuration(minutes) {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;

  return h && m ? `${h}h ${m}m` : h ? `${h}h` : `${m}m`;
}

function statusStyle(status) {
  const map = {
    UNPAID: {
      bg: "#fef3c7",
      fg: "#92400e",
      label: "Unpaid",
    },
    CONFIRMED: {
      bg: "#dcfce7",
      fg: "#166534",
      label: "Confirmed",
    },
    CHECKED_IN: {
      bg: "#dbeafe",
      fg: "#1e40af",
      label: "Checked in",
    },
    COMPLETED: {
      bg: "#e0e7ff",
      fg: "#3730a3",
      label: "Completed",
    },
    CANCELLED: {
      bg: "#fee2e2",
      fg: "#991b1b",
      label: "Cancelled",
    },
    REFUND_REQUESTED: {
      bg: "#fef3c7",
      fg: "#92400e",
      label: "Refund pending",
    },
    REFUNDED: {
      bg: "#f3e8ff",
      fg: "#6b21a8",
      label: "Refunded",
    },
  };

  return (
    map[status] || {
      bg: "#f1f5f9",
      fg: "#475569",
      label: status,
    }
  );
}

const REFUNDABLE = ["CONFIRMED", "CHECKED_IN"];

const CANCELLABLE = ["UNPAID", "CONFIRMED"];

const TICKET_OK = [
  "CONFIRMED",
  "CHECKED_IN",
  "COMPLETED",
  "REFUND_REQUESTED",
  "REFUNDED",
];

const BOARDING_PASS_OK = ["CHECKED_IN", "COMPLETED"];

// ---------- component ----------

export default function BookingDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [booking, setBooking] = useState(null);
  const [flight, setFlight] = useState(null);
  const [seat, setSeat] = useState(null);
  const [passenger, setPassenger] = useState(null);

  const [state, setState] = useState({
    loading: true,
    error: null,
  });

  const [refundOpen, setRefundOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  // ---------- load ----------

  useEffect(() => {
    let cancelled = false;

    const loadAll = async () => {
      try {
        await Promise.resolve();

        if (cancelled) return;

        setState({
          loading: true,
          error: null,
        });

        const { data: bookingData } = await api.get(
          `/api/bookings/${id}`
        );

        const [
          { data: flightData },
          { data: seats },
          { data: passengerData },
        ] = await Promise.all([
          api.get(`/api/flights/${bookingData.flight_id}`),
          api.get(`/api/flights/${bookingData.flight_id}/seats`),
          api.get("/api/passengers/me"),
        ]);

        if (cancelled) return;

        setBooking(bookingData);
        setFlight(flightData);
        setSeat(
          seats.find((s) => s.id === bookingData.seat_id) || null
        );
        setPassenger(passengerData);

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
    };

    loadAll();

    return () => {
      cancelled = true;
    };
  }, [id]);

  // ---------- actions ----------

  const handleCancel = async () => {
    if (!window.confirm(`Cancel booking ${booking.booking_reference}?`)) {
      return;
    }

    try {
      const { data } = await api.delete(`/api/bookings/${id}`);
      setBooking(data);
    } catch (err) {
      alert(
        err.response?.data?.detail ||
          "Could not cancel booking."
      );
    }
  };

  const handleCopyRef = async () => {
    try {
      await navigator.clipboard.writeText(
        booking.booking_reference
      );

      setCopied(true);

      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* ignore */
    }
  };

  const handleRefundSuccess = (updated) => {
    setBooking((b) => ({
      ...b,
      status: updated.status,
      refund_amount: updated.refund_amount,
    }));

    setRefundOpen(false);
  };

  // ---------- states ----------

  if (state.loading) return <Loading />;

  if (state.error) {
    return (
      <ErrorBlock
        message={state.error}
        onBack={() => navigate("/bookings")}
      />
    );
  }

  if (!booking || !flight || !passenger) return null;

  const route = flight.route;
  const from = route.origin_airport;
  const to = route.destination_airport;
  const style = statusStyle(booking.status);

  const canRefund = REFUNDABLE.includes(booking.status);
  const canCancel = CANCELLABLE.includes(booking.status);
  const canTicket = TICKET_OK.includes(booking.status);
  const canBoardingPass = BOARDING_PASS_OK.includes(
    booking.status
  );

  // Timeline steps

  const steps = [
    {
      key: "booked",
      label: "Booked",
      at: booking.booked_at,
      done: true,
    },
    {
      key: "paid",
      label: "Paid",
      at: [
        "CONFIRMED",
        "CHECKED_IN",
        "COMPLETED",
        "REFUND_REQUESTED",
        "REFUNDED",
      ].includes(booking.status)
        ? booking.booked_at
        : null,
      done: [
        "CONFIRMED",
        "CHECKED_IN",
        "COMPLETED",
        "REFUND_REQUESTED",
        "REFUNDED",
      ].includes(booking.status),
    },
    {
      key: "refund",
      label: "Refund requested",
      at:
        booking.status === "REFUND_REQUESTED" ||
        booking.status === "REFUNDED"
          ? booking.booked_at
          : null,
      done:
        booking.status === "REFUND_REQUESTED" ||
        booking.status === "REFUNDED",
      hidden: !["REFUND_REQUESTED", "REFUNDED"].includes(
        booking.status
      ),
    },
    {
      key: "checked_in",
      label: "Checked in",
      at: null,
      done: ["CHECKED_IN", "COMPLETED"].includes(
        booking.status
      ),
      pending: !["CHECKED_IN", "COMPLETED"].includes(
        booking.status
      ),
    },
    {
      key: "departed",
      label: "Flight departed",
      at: flight.departure_time,
      done: ["COMPLETED"].includes(booking.status),
      pending: !["COMPLETED"].includes(booking.status),
    },
    {
      key: "cancelled",
      label: "Cancelled",
      at: booking.cancelled_at,
      done: booking.status === "CANCELLED",
      hidden: booking.status !== "CANCELLED",
      danger: true,
    },
  ].filter((s) => !s.hidden);

  return (
    <div className="page">
      <div
        className="container"
        style={{ maxWidth: 1000 }}
      >
        {/* Back link */}

        <Link
          to="/bookings"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            color: "#64748b",
            fontSize: 14,
            marginBottom: 24,
          }}
        >
          <FiArrowLeft size={14} />
          Back to my bookings
        </Link>

        {/* ============ Hero ticket card ============ */}

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="card"
          style={{
            padding: 40,
            background:
              "linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%)",
            color: "#fff",
            marginBottom: 24,
            position: "relative",
            overflow: "hidden",
          }}
        >
          <MdFlightTakeoff
            size={240}
            style={{
              position: "absolute",
              right: -40,
              top: -40,
              opacity: 0.05,
              transform: "rotate(-15deg)",
              pointerEvents: "none",
            }}
          />

          {/* Top row: E-ticket label + status */}

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              marginBottom: 32,
              position: "relative",
              zIndex: 1,
            }}
          >
            <div>
              <div
                style={{
                  fontSize: 11,
                  letterSpacing: ".15em",
                  color: "rgba(255,255,255,.5)",
                  fontWeight: 700,
                  marginBottom: 6,
                }}
              >
                E-TICKET
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                }}
              >
                <span
                  style={{
                    fontSize: 22,
                    fontWeight: 800,
                    letterSpacing: "-0.01em",
                  }}
                >
                  {flight.flight_number}
                </span>

                <button
                  onClick={handleCopyRef}
                  title="Copy booking reference"
                  style={{
                    background: "rgba(255,255,255,.1)",
                    color: "#fff",
                    border:
                      "1px solid rgba(255,255,255,.2)",
                    padding: "3px 8px",
                    borderRadius: 6,
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: ".08em",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 4,
                    cursor: "pointer",
                  }}
                >
                  {copied ? (
                    <FiCheck size={11} />
                  ) : (
                    <FiCopy size={11} />
                  )}

                  {booking.booking_reference}
                </button>
              </div>
            </div>

            <span
              style={{
                padding: "6px 14px",
                borderRadius: 999,
                background: style.bg,
                color: style.fg,
                fontWeight: 700,
                fontSize: 12,
                letterSpacing: ".03em",
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              ● {style.label.toUpperCase()}
            </span>
          </div>

          {/* Middle: big route */}

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr auto 1fr",
              gap: 24,
              alignItems: "center",
              position: "relative",
              zIndex: 1,
            }}
          >
            <div>
              <div
                style={{
                  fontSize: 44,
                  fontWeight: 800,
                  letterSpacing: "-0.03em",
                  lineHeight: 1,
                }}
              >
                {fmtTime(flight.departure_time)}
              </div>

              <div
                style={{
                  fontSize: 20,
                  fontWeight: 700,
                  marginTop: 10,
                }}
              >
                {from.iata_code}
              </div>

              <div
                style={{
                  color: "rgba(255,255,255,.7)",
                  fontSize: 14,
                  marginTop: 2,
                }}
              >
                {from.city}
              </div>
            </div>

            <div
              style={{
                textAlign: "center",
                minWidth: 160,
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  color: "rgba(255,255,255,.6)",
                  fontSize: 12,
                  justifyContent: "center",
                  marginBottom: 10,
                }}
              >
                <FiClock size={13} />

                <span>
                  {fmtDuration(
                    route.estimated_duration_minutes
                  )}
                </span>
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: "#fbbf24",
                  }}
                />

                <div
                  style={{
                    flex: 1,
                    height: 2,
                    background:
                      "linear-gradient(90deg, #fbbf24, rgba(251,191,36,.3))",
                  }}
                />

                <MdFlightTakeoff
                  size={18}
                  color="#fbbf24"
                  style={{
                    transform: "rotate(90deg)",
                  }}
                />

                <div
                  style={{
                    flex: 1,
                    height: 2,
                    background:
                      "linear-gradient(90deg, rgba(251,191,36,.3), #fbbf24)",
                  }}
                />

                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: "#fbbf24",
                  }}
                />
              </div>

              <div
                style={{
                  color: "rgba(255,255,255,.5)",
                  fontSize: 12,
                  marginTop: 10,
                }}
              >
                {fmtShortDate(flight.departure_time)}
              </div>
            </div>

            <div style={{ textAlign: "right" }}>
              <div
                style={{
                  fontSize: 44,
                  fontWeight: 800,
                  letterSpacing: "-0.03em",
                  lineHeight: 1,
                }}
              >
                {fmtTime(flight.arrival_time)}
              </div>

              <div
                style={{
                  fontSize: 20,
                  fontWeight: 700,
                  marginTop: 10,
                }}
              >
                {to.iata_code}
              </div>

              <div
                style={{
                  color: "rgba(255,255,255,.7)",
                  fontSize: 14,
                  marginTop: 2,
                }}
              >
                {to.city}
              </div>
            </div>
          </div>

          {/* Bottom: quick facts */}

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(120px, 1fr))",
              gap: 20,
              marginTop: 36,
              paddingTop: 24,
              borderTop:
                "1px solid rgba(255,255,255,.1)",
              position: "relative",
              zIndex: 1,
            }}
          >
            <Fact
              label="Seat"
              value={
                seat
                  ? `${seat.seat_number} · ${seat.seat_class}`
                  : "—"
              }
            />

            <Fact
              label="Gate"
              value={flight.boarding_gate || "TBD"}
            />

            <Fact
              label="Aircraft"
              value={flight.aircraft?.model || "—"}
            />

            <Fact
              label="Registration"
              value={
                flight.aircraft?.registration_number || "—"
              }
            />
          </div>
        </motion.div>

        {/* ============ Info grid: Passenger + Payment ============ */}

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(320px, 1fr))",
            gap: 24,
            marginBottom: 24,
          }}
        >
          {/* Passenger */}

          <InfoCard
            title="Passenger"
            icon={FiUser}
            delay={0.1}
          >
            <Row
              label="Name"
              value={`${passenger.first_name} ${passenger.last_name}`}
            />

            <Row
              label="Email"
              value={passenger.email}
              icon={FiMail}
            />

            <Row
              label="Phone"
              value={passenger.phone}
              icon={FiPhone}
            />

            <Row
              label="Passport"
              value={passenger.passport_number}
              icon={FiCreditCard}
            />

            {passenger.date_of_birth && (
              <Row
                label="Date of birth"
                value={passenger.date_of_birth}
                icon={FiCalendar}
              />
            )}

            {passenger.address && (
              <Row
                label="Address"
                value={passenger.address}
                icon={FiMapPin}
              />
            )}
          </InfoCard>

          {/* Payment */}

          <InfoCard
            title="Payment"
            icon={FiCreditCard}
            delay={0.15}
          >
            <Row
              label="Base fare"
              value={`$${Number(
                booking.fare_amount
              ).toFixed(2)}`}
            />

            <Row
              label="Taxes & fees"
              value="$0.00"
            />

            {booking.refund_amount != null && (
              <Row
                label="Refund"
                value={
                  <span
                    style={{
                      color: "#6b21a8",
                      fontWeight: 700,
                    }}
                  >
                    −$
                    {Number(
                      booking.refund_amount
                    ).toFixed(2)}
                  </span>
                }
              />
            )}

            <div
              style={{
                borderTop: "1px solid #e2e8f0",
                margin: "14px 0",
              }}
            />

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "baseline",
              }}
            >
              <span
                style={{
                  color: "#64748b",
                  fontWeight: 600,
                }}
              >
                Total paid
              </span>

              <span
                style={{
                  fontSize: 24,
                  fontWeight: 800,
                  letterSpacing: "-0.02em",
                }}
              >
                $
                {Number(
                  booking.fare_amount
                ).toFixed(2)}
              </span>
            </div>
          </InfoCard>
        </div>

        {/* ============ Timeline ============ */}

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.5,
            delay: 0.2,
          }}
          className="card"
          style={{
            padding: 32,
            marginBottom: 24,
          }}
        >
          <h3
            style={{
              fontSize: 16,
              fontWeight: 700,
              marginBottom: 24,
            }}
          >
            Booking timeline
          </h3>

          <div
            style={{
              display: "grid",
              gap: 0,
            }}
          >
            {steps.map((step, i) => (
              <TimelineStep
                key={step.key}
                {...step}
                last={i === steps.length - 1}
              />
            ))}
          </div>
        </motion.div>

        {/* ============ Actions toolbar ============ */}

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.5,
            delay: 0.25,
          }}
          className="card"
          style={{
            padding: 20,
            display: "flex",
            gap: 12,
            flexWrap: "wrap",
            alignItems: "center",
          }}
        >
          {canTicket && (
            <DownloadTicketButton
              bookingId={booking.id}
              reference={booking.booking_reference}
              variant="primary"
            />
          )}

          {canBoardingPass && (
            <DownloadTicketButton
              bookingId={booking.id}
              reference={booking.booking_reference}
              variant="outline"
              label="Boarding pass"
            />
          )}

          {canRefund && (
            <button
              onClick={() => setRefundOpen(true)}
              className="btn-outline"
              style={{
                padding: "14px 20px",
                fontSize: 15,
                fontWeight: 600,
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <FiRefreshCw size={15} />
              Request refund
            </button>
          )}

          {canCancel && (
            <button
              onClick={handleCancel}
              style={{
                padding: "14px 20px",
                fontSize: 15,
                fontWeight: 600,
                background: "#fff",
                color: "#dc2626",
                border: "1px solid #fecaca",
                borderRadius: 8,
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <FiX size={15} />
              Cancel booking
            </button>
          )}

          <button
            onClick={() => {
              const url = window.location.href;

              navigator.clipboard?.writeText(url);

              alert(
                "Booking link copied to clipboard."
              );
            }}
            className="btn-outline"
            style={{
              padding: "14px 20px",
              fontSize: 15,
              fontWeight: 600,
              marginLeft: "auto",
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <FiShare2 size={15} />
            Share
          </button>
        </motion.div>

        {/* ============ Refund status banners ============ */}

        {booking.status === "REFUND_REQUESTED" && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="card"
            style={{
              padding: 20,
              marginTop: 24,
              background: "#fef3c7",
              border: "1px solid #fcd34d",
              color: "#92400e",
            }}
          >
            <strong>Refund pending review</strong>

            <div
              style={{
                fontSize: 13,
                marginTop: 4,
                opacity: 0.85,
              }}
            >
              Your refund request is being reviewed by an
              administrator.
            </div>
          </motion.div>
        )}
      </div>

      {/* Refund modal */}

      {refundOpen && (
        <RefundModal
          booking={booking}
          onClose={() => setRefundOpen(false)}
          onSuccess={handleRefundSuccess}
        />
      )}
    </div>
  );
}

// ---------- subcomponents ----------

function Fact({ label, value }) {
  return (
    <div>
      <div
        style={{
          fontSize: 10,
          letterSpacing: ".1em",
          color: "rgba(255,255,255,.5)",
          fontWeight: 700,
          marginBottom: 4,
        }}
      >
        {label.toUpperCase()}
      </div>

      <div
        style={{
          fontSize: 15,
          fontWeight: 600,
        }}
      >
        {value}
      </div>
    </div>
  );
}

function InfoCard({
  title,
  icon: Icon,
  children,
  delay = 0,
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.5,
        delay,
      }}
      className="card"
      style={{
        padding: 32,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          marginBottom: 20,
        }}
      >
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            background: "#eff6ff",
            color: "#2563eb",
            display: "grid",
            placeItems: "center",
          }}
        >
          <Icon size={18} />
        </div>

        <h3
          style={{
            fontSize: 16,
            fontWeight: 700,
          }}
        >
          {title}
        </h3>
      </div>

      <div
        style={{
          display: "grid",
          gap: 10,
        }}
      >
        {children}
      </div>
    </motion.div>
  );
}

function Row({ label, value, icon: Icon }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
        padding: "8px 0",
        fontSize: 14,
        gap: 12,
      }}
    >
      <span
        style={{
          color: "#64748b",
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          flexShrink: 0,
        }}
      >
        {Icon && <Icon size={12} />}
        {label}
      </span>

      <span
        style={{
          color: "#0f172a",
          fontWeight: 500,
          textAlign: "right",
          wordBreak: "break-word",
        }}
      >
        {value}
      </span>
    </div>
  );
}

function TimelineStep({
  label,
  at,
  done,
  pending,
  danger,
  last,
}) {
  const color = done
    ? danger
      ? "#dc2626"
      : "#16a34a"
    : pending
      ? "#94a3b8"
      : "#cbd5e0";

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "20px 1fr auto",
        gap: 16,
        alignItems: "flex-start",
        position: "relative",
        paddingBottom: last ? 0 : 20,
      }}
    >
      {/* Node + vertical line */}

      <div
        style={{
          position: "relative",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          height: "100%",
        }}
      >
        <div
          style={{
            width: 14,
            height: 14,
            borderRadius: "50%",
            background: done ? color : "#fff",
            border: `2px solid ${color}`,
            flexShrink: 0,
            marginTop: 3,
            position: "relative",
            zIndex: 2,
          }}
        />

        {!last && (
          <div
            style={{
              position: "absolute",
              top: 20,
              bottom: -20,
              left: "50%",
              transform: "translateX(-50%)",
              width: 2,
              background: done
                ? color
                : "#e2e8f0",
              opacity: done ? 0.3 : 1,
              zIndex: 1,
            }}
          />
        )}
      </div>

      {/* Label */}

      <div>
        <div
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: done
              ? "#0f172a"
              : "#94a3b8",
          }}
        >
          {label}
        </div>
      </div>

      {/* Timestamp */}

      <div
        style={{
          fontSize: 13,
          color: "#94a3b8",
          textAlign: "right",
        }}
      >
        {at
          ? fmtDateTime(at)
          : pending
            ? "Pending"
            : "—"}
      </div>
    </div>
  );
}

function Loading() {
  return (
    <div className="page">
      <div
        className="container"
        style={{ maxWidth: 1000 }}
      >
        <div
          className="card"
          style={{
            height: 400,
            background:
              "linear-gradient(90deg, #f1f5f9 0%, #e2e8f0 50%, #f1f5f9 100%)",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.4s infinite",
          }}
        />

        <style>{`
          @keyframes shimmer {
            0% {
              background-position: 200% 0;
            }

            100% {
              background-position: -200% 0;
            }
          }
        `}</style>
      </div>
    </div>
  );
}

function ErrorBlock({ message, onBack }) {
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
          <FiAlertCircle
            size={48}
            color="#dc2626"
            style={{ marginBottom: 16 }}
          />

          <h2
            style={{
              fontSize: 20,
              fontWeight: 700,
              marginBottom: 8,
            }}
          >
            Could not load booking
          </h2>

          <p
            style={{
              color: "#64748b",
              marginBottom: 24,
            }}
          >
            {message}
          </p>

          <button
            onClick={onBack}
            className="btn-primary"
            style={{
              padding: "12px 24px",
            }}
          >
            Back to my bookings
          </button>
        </div>
      </div>
    </div>
  );
}