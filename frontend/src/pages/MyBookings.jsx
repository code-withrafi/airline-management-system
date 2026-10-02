// src/pages/MyBookings.jsx

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  FiInbox,
  FiX,
  FiAlertCircle,
  FiArrowRight,
  FiRefreshCw,
  FiClock,
} from "react-icons/fi";

import { api } from "../api/client";
import RefundModal from "../components/RefundModal";
import DownloadTicketButton from "../components/DownloadTicketButton";

const REFUNDABLE = ["CONFIRMED", "CHECKED_IN"];
const NON_CANCELLABLE = [
  "CANCELLED",
  "REFUNDED",
  "COMPLETED",
  "REFUND_REQUESTED",
];
const TICKET_AVAILABLE = [
  "CONFIRMED",
  "CHECKED_IN",
  "COMPLETED",
  "REFUND_REQUESTED",
  "REFUNDED",
];

function fmtDate(iso) {
  return new Date(iso).toLocaleDateString([], {
    weekday: "short",
    day: "numeric",
    month: "short",
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

function statusStyle(status) {
  const styles = {
    UNPAID: ["#fff7df", "#9a6700"],
    CONFIRMED: ["#eaf9f0", "#087443"],
    CHECKED_IN: ["#eaf3ff", "#175cd3"],
    COMPLETED: ["#eef0ff", "#42389d"],
    CANCELLED: ["#fff0ef", "#b42318"],
    REFUND_REQUESTED: ["#fff7df", "#9a6700"],
    REFUNDED: ["#f7edff", "#7a2e9b"],
  };

  const [bg, fg] = styles[status] || ["#f2f4f7", "#475467"];
  return { bg, fg };
}

export default function MyBookings() {
  const [bookings, setBookings] = useState([]);
  const [state, setState] = useState({ loading: true, error: null });
  const [refundTarget, setRefundTarget] = useState(null);

  useEffect(() => {
    let cancelled = false;

    api
      .get("/api/bookings/my")
      .then(({ data }) => {
        if (cancelled) return;
        setBookings(data || []);
        setState({ loading: false, error: null });
      })
      .catch((err) => {
        if (cancelled) return;

        setState({
          loading: false,
          error:
            err.response?.data?.detail || "Could not load bookings.",
        });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const handleCancel = async (booking) => {
    if (!window.confirm(`Cancel booking ${booking.booking_reference}?`)) return;

    try {
      const { data } = await api.delete(`/api/bookings/${booking.id}`);
      setBookings((list) =>
        list.map((item) => (item.id === data.id ? data : item))
      );
    } catch (err) {
      alert(err.response?.data?.detail || "Could not cancel booking.");
    }
  };

  const handleRefundSuccess = (updated) => {
    setBookings((list) =>
      list.map((item) =>
        item.id === updated.id
          ? {
              ...item,
              status: updated.status,
              refund_amount: updated.refund_amount,
            }
          : item
      )
    );
    setRefundTarget(null);
  };

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 900 }}>
        <motion.header
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          style={{ marginBottom: 32 }}
        >
          <div
            style={{
              color: "var(--primary)",
              fontFamily: '"Manrope", sans-serif',
              fontSize: 12,
              fontWeight: 700,
              letterSpacing: ".08em",
              textTransform: "uppercase",
              marginBottom: 8,
            }}
          >
            Your travel
          </div>

          <h1
            style={{
              fontSize: "clamp(28px, 4vw, 38px)",
              letterSpacing: "-.03em",
              marginBottom: 7,
            }}
          >
            My bookings
          </h1>

          <p style={{ color: "var(--muted)", fontSize: 15 }}>
            {state.loading
              ? "Loading your trips…"
              : `${bookings.length} booking${
                  bookings.length === 1 ? "" : "s"
                }`}
          </p>
        </motion.header>

        {state.error && <ErrorState message={state.error} />}

        {!state.loading && !state.error && !bookings.length && (
          <EmptyState />
        )}

        <AnimatePresence mode="popLayout">
          {bookings.map((booking, index) => (
            <BookingRow
              key={booking.id}
              booking={booking}
              index={index}
              onCancel={() => handleCancel(booking)}
              onRefund={() => setRefundTarget(booking)}
            />
          ))}
        </AnimatePresence>

        <AnimatePresence>
          {refundTarget && (
            <RefundModal
              booking={refundTarget}
              onClose={() => setRefundTarget(null)}
              onSuccess={handleRefundSuccess}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function BookingRow({ booking, index, onCancel, onRefund }) {
  const colors = statusStyle(booking.status);
  const canCancel = !NON_CANCELLABLE.includes(booking.status);
  const canRefund = REFUNDABLE.includes(booking.status);
  const canDownload = TICKET_AVAILABLE.includes(booking.status);
  const refundPending = booking.status === "REFUND_REQUESTED";
  const refunded = booking.status === "REFUNDED";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -40 }}
      transition={{
        duration: 0.35,
        delay: index * 0.05,
      }}
      className="card"
      style={{
        padding: 24,
        marginBottom: 16,
        display: "grid",
        gridTemplateColumns: "minmax(0, 1.5fr) auto auto",
        gap: 24,
        alignItems: "center",
      }}
    >
      <div style={{ minWidth: 0 }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            flexWrap: "wrap",
            marginBottom: 10,
          }}
        >
          <span
            style={{
              color: "var(--primary)",
              fontFamily: '"Manrope", sans-serif',
              fontSize: 16,
              fontWeight: 800,
              letterSpacing: ".04em",
            }}
          >
            {booking.booking_reference}
          </span>

          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 5,
              padding: "5px 10px",
              borderRadius: 999,
              background: colors.bg,
              color: colors.fg,
              fontFamily: '"Manrope", sans-serif',
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: ".03em",
            }}
          >
            {refundPending && <FiClock size={11} />}
            {booking.status.replace(/_/g, " ")}
          </span>
        </div>

        <div
          style={{
            color: "var(--muted)",
            fontSize: 13,
            lineHeight: 1.7,
          }}
        >
          Flight #{booking.flight_id} · Seat #{booking.seat_id}
          <br />
          Booked {fmtDate(booking.booked_at)} at{" "}
          {fmtTime(booking.booked_at)}
        </div>
      </div>

      <div style={{ textAlign: "right", whiteSpace: "nowrap" }}>
        <div
          style={{
            color: "#98a2b3",
            fontSize: 12,
            marginBottom: 3,
          }}
        >
          Total paid
        </div>

        <div
          style={{
            fontSize: 23,
            fontWeight: 800,
            letterSpacing: "-.03em",
          }}
        >
          ${Number(booking.fare_amount).toFixed(2)}
        </div>

        {refunded && booking.refund_amount && (
          <div
            style={{
              color: "#7a2e9b",
              fontSize: 12,
              fontWeight: 600,
              marginTop: 4,
            }}
          >
            Refunded ${Number(booking.refund_amount).toFixed(2)}
          </div>
        )}
      </div>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 8,
          minWidth: 145,
        }}
      >
        <Link
          to={`/bookings/${booking.id}`}
          className="btn-outline"
          style={actionStyle}
        >
          Details <FiArrowRight size={13} />
        </Link>

        {canDownload && (
          <DownloadTicketButton
            bookingId={booking.id}
            reference={booking.booking_reference}
            variant="small"
            label="Ticket"
          />
        )}

        {canRefund && (
          <motion.button
            whileHover={{ y: -1 }}
            whileTap={{ scale: 0.98 }}
            onClick={onRefund}
            style={{
              ...actionStyle,
              background: "#fff",
              color: "var(--primary)",
              border: "1px solid #bfd7ff",
            }}
          >
            <FiRefreshCw size={12} /> Refund
          </motion.button>
        )}

        {canCancel && (
          <motion.button
            whileHover={{ y: -1 }}
            whileTap={{ scale: 0.98 }}
            onClick={onCancel}
            style={{
              ...actionStyle,
              background: "#fff",
              color: "var(--danger)",
              border: "1px solid #f5c2c0",
            }}
          >
            <FiX size={12} /> Cancel
          </motion.button>
        )}
      </div>
    </motion.div>
  );
}

const actionStyle = {
  width: "100%",
  padding: "9px 14px",
  fontSize: 13,
  fontWeight: 600,
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 6,
};

function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
      className="card"
      style={{
        padding: "64px 32px",
        textAlign: "center",
      }}
    >
      <div
        style={{
          width: 64,
          height: 64,
          margin: "0 auto 18px",
          display: "grid",
          placeItems: "center",
          borderRadius: 18,
          background: "#eaf3ff",
          color: "var(--primary)",
        }}
      >
        <FiInbox size={30} />
      </div>

      <h2
        style={{
          fontSize: 22,
          marginBottom: 8,
        }}
      >
        No bookings yet
      </h2>

      <p
        style={{
          maxWidth: 400,
          margin: "0 auto 24px",
          color: "var(--muted)",
          fontSize: 14,
          lineHeight: 1.6,
        }}
      >
        You haven't booked any flights yet. Search a route and book
        your first trip.
      </p>

      <Link
        to="/search"
        className="btn-primary"
        style={{
          display: "inline-flex",
          padding: "12px 24px",
          fontSize: 14,
        }}
      >
        Search flights
      </Link>
    </motion.div>
  );
}

function ErrorState({ message }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
      style={{
        padding: 36,
        textAlign: "center",
        background: "#fff8f7",
        border: "1px solid #f5c2c0",
      }}
    >
      <FiAlertCircle
        size={40}
        color="var(--danger)"
        style={{ marginBottom: 12 }}
      />

      <h3 style={{ fontSize: 18, marginBottom: 6 }}>
        Couldn't load bookings
      </h3>

      <p style={{ color: "#b42318", fontSize: 14 }}>
        {message}
      </p>
    </motion.div>
  );
}