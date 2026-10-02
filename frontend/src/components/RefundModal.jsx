// src/components/RefundModal.jsx
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { FiX, FiAlertCircle, FiCheck, FiInfo, FiRefreshCw } from 'react-icons/fi';

import { api } from '../api/client';

// ---------- refund policy (matches backend TIERS) ----------
const POLICY_TIERS = [
  { days: '7+ days before', percent: 100 },
  { days: '5+ days before', percent: 80 },
  { days: '3+ days before', percent: 70 },
  { days: '2+ days before', percent: 60 },
  { days: '1+ day before',  percent: 40 },
  { days: 'Same day',       percent: 25 },
];

// ---------- component ----------

export default function RefundModal({ booking, onClose, onSuccess }) {
  const [preview, setPreview] = useState(null);
  const [state, setState] = useState({ loading: true, error: null });
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.get(
          `/api/bookings/${booking.id}/refund-preview`
        );
        if (cancelled) return;
        setPreview(data);
        setState({ loading: false, error: null });
      } catch (err) {
        if (cancelled) return;
        setState({
          loading: false,
          error: err.response?.data?.detail || 'Could not load refund info.',
        });
      }
    })();
    return () => { cancelled = true; };
  }, [booking.id]);

  const submit = async () => {
    setSubmitError('');
    setSubmitting(true);
    try {
      const { data } = await api.post(`/api/bookings/${booking.id}/refund`);
      onSuccess(data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setSubmitError(
        typeof detail === 'string'
          ? detail
          : 'Could not submit refund request.'
      );
      setSubmitting(false);
    }
  };

  // Close on ESC
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(15,23,42,.55)',
        backdropFilter: 'blur(4px)',
        zIndex: 1000,
        display: 'grid', placeItems: 'center',
        padding: 24,
        overflowY: 'auto',
      }}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.94, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.94, y: 10 }}
        transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
        onClick={(e) => e.stopPropagation()}
        className="card"
        style={{
          width: '100%', maxWidth: 540,
          padding: 32, position: 'relative',
          maxHeight: '90vh', overflowY: 'auto',
        }}
      >
        {/* Close */}
        <button
          onClick={onClose}
          aria-label="Close"
          style={{
            position: 'absolute', top: 14, right: 14,
            background: 'transparent', padding: 8,
            color: '#94a3b8', borderRadius: 8,
          }}
        >
          <FiX size={20} />
        </button>

        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12,
          marginBottom: 20,
        }}>
          <div style={{
            width: 46, height: 46, borderRadius: 12,
            background: '#dbeafe', color: '#2563eb',
            display: 'grid', placeItems: 'center',
          }}>
            <FiRefreshCw size={22} />
          </div>
          <div>
            <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 2 }}>
              Request a refund
            </h2>
            <div style={{ color: '#64748b', fontSize: 13 }}>
              Booking{' '}
              <strong style={{ color: '#0f172a' }}>
                {booking.booking_reference}
              </strong>
            </div>
          </div>
        </div>

        {/* Loading */}
        {state.loading && (
          <div style={{
            padding: '40px 20px', textAlign: 'center',
            color: '#94a3b8', fontSize: 14,
          }}>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              style={{
                display: 'inline-block', width: 24, height: 24,
                border: '3px solid #e2e8f0',
                borderTopColor: '#2563eb',
                borderRadius: '50%',
                marginBottom: 12,
              }}
            />
            <div>Checking eligibility…</div>
          </div>
        )}

        {/* Error */}
        {state.error && (
          <div style={{
            background: '#fee2e2', color: '#991b1b',
            padding: 16, borderRadius: 10, fontSize: 14,
            display: 'flex', alignItems: 'flex-start', gap: 10,
          }}>
            <FiAlertCircle size={18} style={{ flexShrink: 0, marginTop: 1 }} />
            <div>{state.error}</div>
          </div>
        )}

        {/* Preview */}
        {preview && (
          <>
            {preview.eligible ? <EligiblePanel preview={preview} /> : <IneligiblePanel preview={preview} />}

            {preview.eligible && (
              <>
                {/* Policy tiers */}
                <div style={{
                  background: '#f8fafc',
                  borderRadius: 10,
                  padding: 16,
                  marginBottom: 16,
                }}>
                  <div style={{
                    fontWeight: 700, color: '#475569',
                    marginBottom: 10, fontSize: 12,
                    letterSpacing: '.05em', textTransform: 'uppercase',
                  }}>
                    Refund policy
                  </div>
                  {POLICY_TIERS.map((t) => (
                    <div key={t.days} style={{
                      display: 'flex', justifyContent: 'space-between',
                      padding: '4px 0', color: '#64748b', fontSize: 13,
                    }}>
                      <span>{t.days}</span>
                      <span style={{ fontWeight: 600, color: '#0f172a' }}>
                        {t.percent}%
                      </span>
                    </div>
                  ))}
                </div>

                {/* Note */}
                <div style={{
                  display: 'flex', gap: 8,
                  fontSize: 13, color: '#64748b',
                  marginBottom: 24, lineHeight: 1.6,
                }}>
                  <FiInfo size={16} style={{ flexShrink: 0, marginTop: 2 }} />
                  <div>
                    Your request will be reviewed by an administrator.
                    You'll be notified once it's approved or rejected.
                  </div>
                </div>
              </>
            )}
          </>
        )}

        {/* Submit error */}
        {submitError && (
          <div style={{
            background: '#fee2e2', color: '#991b1b',
            padding: '10px 14px', borderRadius: 8,
            fontSize: 13, marginBottom: 16,
          }}>
            {submitError}
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            type="button"
            onClick={onClose}
            className="btn-outline"
            style={{ flex: 1, padding: '12px 20px', fontWeight: 600 }}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={!preview?.eligible || submitting}
            className="btn-primary"
            style={{ flex: 1, padding: '12px 20px', fontWeight: 600 }}
          >
            {submitting
              ? 'Submitting…'
              : preview?.eligible
                ? `Request $${Number(preview.refund_amount).toFixed(2)}`
                : 'Not eligible'}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ---------- subcomponents ----------

function EligiblePanel({ preview }) {
  const refundAmt = Number(preview.refund_amount).toFixed(2);
  const paidAmt = Number(preview.paid_amount).toFixed(2);

  return (
    <div style={{
      background: 'linear-gradient(135deg, #f0fdf4, #dcfce7)',
      border: '1px solid #bbf7d0',
      borderRadius: 12,
      padding: 20,
      marginBottom: 16,
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        color: '#166534', fontWeight: 700, marginBottom: 14,
        fontSize: 13, letterSpacing: '.02em',
      }}>
        <FiCheck size={16} />
        REFUND ELIGIBLE
      </div>

      <div style={{
        display: 'flex', justifyContent: 'space-between',
        alignItems: 'baseline', marginBottom: 4,
      }}>
        <span style={{ color: '#166534', fontSize: 14 }}>You'll receive</span>
        <span style={{
          fontSize: 34, fontWeight: 800,
          color: '#166534', letterSpacing: '-0.03em',
          lineHeight: 1,
        }}>
          ${refundAmt}
        </span>
      </div>

      <div style={{
        display: 'flex', justifyContent: 'space-between',
        marginTop: 8, fontSize: 13, color: '#16a34a',
      }}>
        <span>Refund rate</span>
        <span style={{ fontWeight: 600 }}>{preview.refund_percentage}%</span>
      </div>

      <div style={{
        display: 'flex', justifyContent: 'space-between',
        marginTop: 4, fontSize: 13, color: '#16a34a',
      }}>
        <span>Original amount paid</span>
        <span style={{ fontWeight: 600 }}>${paidAmt}</span>
      </div>
    </div>
  );
}

function IneligiblePanel({ preview }) {
  return (
    <div style={{
      background: '#fef2f2',
      border: '1px solid #fecaca',
      borderRadius: 12,
      padding: 20,
      marginBottom: 16,
      color: '#991b1b',
      fontSize: 14,
      display: 'flex', gap: 10,
    }}>
      <FiAlertCircle size={18} style={{ flexShrink: 0, marginTop: 1 }} />
      <div>
        <strong>Not eligible for a refund.</strong>
        {preview.reason && (
          <div style={{ marginTop: 6, lineHeight: 1.5 }}>{preview.reason}</div>
        )}
      </div>
    </div>
  );
}