// src/components/SeatMap.jsx
import { useMemo } from 'react';
import { motion } from 'framer-motion';

const COLS = ['A', 'B', 'C', 'D', 'E', 'F'];   // 3 + aisle + 3
const AISLE_AFTER = 'C';                        // gap between C and D

/**
 * Renders an interactive seat map.
 *
 * @param {Array} seats         - from GET /api/flights/:id/seats
 * @param {number|null} selectedId
 * @param {(seat) => void} onSelect
 */
export default function SeatMap({ seats, selectedId, onSelect }) {
  // Group seats by row, sorted ascending
  const rows = useMemo(() => {
    const map = new Map();
    for (const s of seats) {
      if (!map.has(s.row_number)) map.set(s.row_number, {});
      map.get(s.row_number)[s.seat_number.replace(/\d+/g, '')] = s;
    }
    return Array.from(map.entries())
      .sort((a, b) => a[0] - b[0])
      .map(([row, cols]) => ({ row, cols }));
  }, [seats]);

  // Detect the business/economy split (business rows come first)
  const firstEconomyRow = useMemo(() => {
    const econ = seats.find((s) => s.seat_class === 'ECONOMY');
    return econ?.row_number ?? Infinity;
  }, [seats]);

  // Derive prices per class straight from the seat data (no extra API call)
  const economyPrice = useMemo(() => {
    const s = seats.find((x) => x.seat_class === 'ECONOMY');
    return s ? Number(s.price) : null;
  }, [seats]);

  const businessPrice = useMemo(() => {
    const s = seats.find((x) => x.seat_class === 'BUSINESS');
    return s ? Number(s.price) : null;
  }, [seats]);

  return (
    <div>
      {/* ---------- Cabin head ---------- */}
      <div style={{
        display: 'flex', justifyContent: 'center', marginBottom: 24,
      }}>
        <div style={{
          background: '#f1f5f9',
          color: '#64748b',
          padding: '8px 24px',
          borderRadius: '999px 999px 8px 8px',
          fontSize: 12,
          fontWeight: 700,
          letterSpacing: '.08em',
        }}>
          ✈️ FRONT OF AIRCRAFT
        </div>
      </div>

      {/* ---------- Column letters ---------- */}
      <div style={gridStyles}>
        {COLS.map((c) => (
          <div key={c} style={{
            textAlign: 'center',
            fontSize: 12,
            fontWeight: 700,
            color: '#94a3b8',
            paddingBottom: 8,
          }}>
            {c}
          </div>
        ))}
      </div>

      {/* ---------- Rows ---------- */}
      {rows.map(({ row, cols }, i) => {
        const isBusiness = row < firstEconomyRow;
        return (
          <div key={row}>
            {/* Cabin divider between business and economy */}
            {row === firstEconomyRow && i > 0 && (
              <div style={{
                textAlign: 'center',
                margin: '12px 0',
                fontSize: 11,
                color: '#94a3b8',
                letterSpacing: '.1em',
                fontWeight: 600,
              }}>
                ───── ECONOMY ─────
              </div>
            )}

            <div style={gridStyles}>
              <div style={{
                display: 'grid',
                placeItems: 'center',
                fontSize: 12,
                color: '#94a3b8',
                fontWeight: 600,
              }}>
                {row}
              </div>

              {COLS.map((c) => {
                const seat = cols[c];
                const isSelected = seat && seat.id === selectedId;
                const taken = !seat || !seat.is_available;
                return (
                  <div key={c}>
                    <Seat
                      seat={seat}
                      isSelected={isSelected}
                      taken={taken}
                      isBusiness={isBusiness}
                      onClick={() => seat && seat.is_available && onSelect(seat)}
                    />
                    {/* Aisle spacer after C */}
                    {c === AISLE_AFTER && <div style={{ width: 24 }} />}
                  </div>
                );
              })}

              <div style={{
                display: 'grid',
                placeItems: 'center',
                fontSize: 12,
                color: '#94a3b8',
                fontWeight: 600,
              }}>
                {row}
              </div>
            </div>
          </div>
        );
      })}

      {/* ---------- Legend (price-aware) ---------- */}
      <div style={{
        display: 'flex',
        gap: 24,
        justifyContent: 'center',
        marginTop: 32,
        flexWrap: 'wrap',
        fontSize: 13,
        color: '#64748b',
      }}>
        <Legend color="#fff" border="#e2e8f0" label="Available" />
        <Legend color="#2563eb" label="Selected" />
        <Legend color="#cbd5e0" label="Taken" dashed />

        {economyPrice != null && (
          <Legend
            color="#fff"
            border="#e2e8f0"
            label={`Economy · $${economyPrice.toFixed(2)}`}
          />
        )}
        {businessPrice != null && (
          <Legend
            color="#fef3c7"
            border="#fcd34d"
            label={`Business · $${businessPrice.toFixed(2)}`}
          />
        )}
      </div>
    </div>
  );
}

// ---------- Seat ----------

function Seat({ seat, isSelected, taken, isBusiness, onClick }) {
  if (!seat) {
    // Empty slot (e.g. missing seat in a row) — render blank
    return <div style={{ width: 40, height: 40 }} />;
  }

  const base = {
    width: 40,
    height: 40,
    borderRadius: 8,
    display: 'grid',
    placeItems: 'center',
    fontSize: 11,
    fontWeight: 600,
    cursor: taken ? 'not-allowed' : 'pointer',
    userSelect: 'none',
  };

  let colors;
  if (isSelected) {
    colors = { background: '#2563eb', color: '#fff', border: '2px solid #1d4ed8' };
  } else if (taken) {
    colors = {
      background: '#f1f5f9',
      color: '#cbd5e0',
      border: '2px dashed #cbd5e0',
    };
  } else if (isBusiness) {
    colors = {
      background: '#fef3c7',
      color: '#b45309',
      border: '2px solid #fcd34d',
    };
  } else {
    colors = {
      background: '#fff',
      color: '#0f172a',
      border: '2px solid #e2e8f0',
    };
  }

  // Build a rich tooltip with the price when available
  const priceHint = seat.price != null
    ? ` · $${Number(seat.price).toFixed(2)}`
    : '';
  const title = `${seat.seat_number} · ${seat.seat_class} · ${seat.position}${priceHint}`;

  return (
    <motion.button
      type="button"
      onClick={onClick}
      disabled={taken}
      whileHover={!taken ? { scale: 1.08 } : {}}
      whileTap={!taken ? { scale: 0.94 } : {}}
      style={{ ...base, ...colors }}
      title={title}
    >
      {seat.seat_number}
    </motion.button>
  );
}

// ---------- Legend ----------

function Legend({ color, label, dashed, border }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{
        width: 20, height: 20, borderRadius: 5,
        background: dashed ? '#f1f5f9' : color,
        border: dashed
          ? `2px dashed ${color}`
          : border
            ? `2px solid ${border}`
            : 'none',
      }} />
      <span>{label}</span>
    </div>
  );
}

// ---------- Grid ----------

const gridStyles = {
  display: 'grid',
  gridTemplateColumns: '24px repeat(6, 40px) 24px',
  gap: 8,
  justifyContent: 'center',
  alignItems: 'center',
};