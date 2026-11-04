// src/components/RecommendedRoutes.jsx
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  FiArrowRight, FiCompass, FiTrendingUp, FiAlertCircle,
} from 'react-icons/fi';
import { MdFlightTakeoff } from 'react-icons/md';

import { getRecommendations } from '../api/recommendations';
import { useAuth } from '../context/AuthContext';

/**
 * Renders recommended routes on the landing page.
 * Personalised for logged-in passengers, popular for anonymous visitors.
 */
export default function RecommendedRoutes() {
  const { isAuthenticated } = useAuth();
  const [state, setState] = useState({
    loading: true,
    error: null,
    data: null,
  });

  useEffect(() => {
    let cancelled = false;

    setState({ loading: true, error: null, data: null });

    getRecommendations(3)
      .then((data) => {
        if (cancelled) return;
        setState({ loading: false, error: null, data });
      })
      .catch((err) => {
        if (cancelled) return;
        // 503 = model not trained yet — treat as a soft failure
        const detail = err.response?.data?.detail || 'Could not load recommendations.';
        setState({ loading: false, error: detail, data: null });
      });

    return () => { cancelled = true; };
  }, [isAuthenticated]);   // refetch when login state changes

  // ---------- Section header ----------
  const isPersonal = state.data?.personalized;
  const Icon = isPersonal ? FiCompass : FiTrendingUp;
  const eyebrow = isPersonal ? 'For you' : 'Trending';
  const title = isPersonal ? 'Picked for your next trip' : 'Popular right now';

  return (
    <section style={{ padding: '100px 0', background: '#fff' }}>
      <div className="container">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.6 }}
          style={{ textAlign: 'center', marginBottom: 48 }}
        >
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            color: '#2563eb', fontWeight: 700, fontSize: 13,
            letterSpacing: '.1em', textTransform: 'uppercase',
            marginBottom: 12,
          }}>
            <Icon size={14} />
            {eyebrow}
          </div>
          <h2 style={{
            fontSize: 'clamp(28px, 4vw, 44px)',
            fontWeight: 800, letterSpacing: '-0.02em',
            marginBottom: 8,
          }}>
            {title}
          </h2>
          {isPersonal && state.data.based_on?.length > 0 && (
            <p style={{ color: '#64748b', fontSize: 15 }}>
              Based on your trips to{' '}
              <strong style={{ color: '#0f172a' }}>
                {state.data.based_on.join(' · ')}
              </strong>
            </p>
          )}
          {!isPersonal && !state.loading && !state.error && (
            <p style={{ color: '#64748b', fontSize: 15 }}>
              The most booked routes across our network.
            </p>
          )}
        </motion.div>

        {/* ---------- States ---------- */}
        {state.loading && <LoadingSkeleton />}
        {state.error && <ErrorBox message={state.error} />}
        {state.data && !state.error && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: 20,
          }}>
            {state.data.recommendations.map((rec, i) => (
              <RouteCard key={rec.route_id} route={rec} index={i} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

// ---------- Route card ----------

function RouteCard({ route, index }) {
  const today = new Date().toISOString().slice(0, 10);
  const searchUrl = `/search?origin=${route.origin}&destination=${route.destination}&date=${today}`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ duration: 0.5, delay: index * 0.08 }}
      whileHover={{ y: -4, boxShadow: '0 12px 40px rgba(15,23,42,.12)' }}
      className="card"
      style={{ padding: 0, overflow: 'hidden' }}
    >
      {/* Top: route codes */}
      <div style={{
        background: 'linear-gradient(135deg, #1e3a8a, #2563eb)',
        color: '#fff',
        padding: '28px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 12,
        position: 'relative',
      }}>
        <MdFlightTakeoff
          size={90}
          style={{
            position: 'absolute', right: -16, bottom: -16,
            opacity: 0.08, transform: 'rotate(-15deg)',
          }}
        />
        <div>
          <div style={{ fontSize: 26, fontWeight: 800, letterSpacing: '-0.02em' }}>
            {route.origin}
          </div>
          <div style={{ fontSize: 11, opacity: 0.7, marginTop: 2 }}>FROM</div>
        </div>
        <FiArrowRight size={20} style={{ opacity: 0.6, flexShrink: 0 }} />
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 26, fontWeight: 800, letterSpacing: '-0.02em' }}>
            {route.destination}
          </div>
          <div style={{ fontSize: 11, opacity: 0.7, marginTop: 2 }}>TO</div>
        </div>
      </div>

      {/* Bottom: action */}
      <div style={{ padding: '20px 24px' }}>
        <div style={{ fontSize: 13, color: '#94a3b8', marginBottom: 12 }}>
          Search flights on this route
        </div>
        <Link
          to={searchUrl}
          className="btn-primary"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            width: '100%',
            padding: '11px 18px',
            fontSize: 14,
            fontWeight: 600,
          }}
        >
          View flights <FiArrowRight size={14} />
        </Link>
      </div>
    </motion.div>
  );
}

// ---------- States ----------

function LoadingSkeleton() {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
      gap: 20,
    }}>
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: i * 0.1 }}
          className="card"
          style={{
            height: 240,
            background: 'linear-gradient(90deg, #f1f5f9 0%, #e2e8f0 50%, #f1f5f9 100%)',
            backgroundSize: '200% 100%',
            animation: 'shimmer 1.4s infinite',
          }}
        />
      ))}
      <style>{`@keyframes shimmer {0%{background-position:200% 0}100%{background-position:-200% 0}}`}</style>
    </div>
  );
}

function ErrorBox({ message }) {
  return (
    <div style={{
      padding: 32,
      borderRadius: 12,
      background: '#f8fafc',
      border: '1px solid #e2e8f0',
      textAlign: 'center',
      color: '#64748b',
      fontSize: 14,
    }}>
      <FiAlertCircle size={28} color="#94a3b8" style={{ marginBottom: 10 }} />
      <div>{message}</div>
    </div>
  );
}