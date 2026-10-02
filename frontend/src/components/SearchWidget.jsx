import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FiCalendar,
  FiChevronDown,
  FiMapPin,
  FiSearch,
} from "react-icons/fi";
import { api } from "../api/client";

const today = () => new Date().toISOString().slice(0, 10);

export default function SearchWidget({ compact = false, initial = {} }) {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [originCode, setOriginCode] = useState(initial.origin || "");
  const [destinationCode, setDestinationCode] = useState(
    initial.destination || ""
  );
  const [date, setDate] = useState(initial.date || today());
  const [suggestions, setSuggestions] = useState([]);
  const [activeField, setActiveField] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    if (!initial.origin) return;

    api
      .get("/api/flights/airports/search", {
        params: { q: initial.origin },
      })
      .then((response) => {
        const airport = response.data.find(
          (item) =>
            item.iata_code === initial.origin.trim().toUpperCase()
        );

        if (airport) {
          setOrigin(`${airport.city} — ${airport.name}`);
        }
      })
      .catch(() => {});
  }, [initial.origin]);

  useEffect(() => {
    if (!initial.destination) return;

    api
      .get("/api/flights/airports/search", {
        params: { q: initial.destination },
      })
      .then((response) => {
        const airport = response.data.find(
          (item) =>
            item.iata_code === initial.destination.trim().toUpperCase()
        );

        if (airport) {
          setDestination(`${airport.city} — ${airport.name}`);
        }
      })
      .catch(() => {});
  }, [initial.destination]);

  useEffect(() => {
    if (!activeField) return;

    const value = activeField === "origin" ? origin : destination;

    if (value.trim().length < 2) return;

    let cancelled = false;

    const timer = setTimeout(() => {
      api
        .get("/api/flights/airports/search", {
          params: { q: value.trim() },
        })
        .then((response) => {
          if (!cancelled) {
            setSuggestions(response.data);
          }
        })
        .catch(() => {
          if (!cancelled) {
            setSuggestions([]);
          }
        });
    }, 250);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [origin, destination, activeField]);

  const handleInput = (field, value) => {
    if (field === "origin") {
      setOrigin(value);
      setOriginCode("");
    } else {
      setDestination(value);
      setDestinationCode("");
    }

    setActiveField(field);

    if (value.trim().length < 2) {
      setSuggestions([]);
    }
  };

  const selectAirport = (airport) => {
    const displayValue = `${airport.city} — ${airport.name}`;

    if (activeField === "origin") {
      setOrigin(displayValue);
      setOriginCode(airport.iata_code);
    } else {
      setDestination(displayValue);
      setDestinationCode(airport.iata_code);
    }

    setSuggestions([]);
    setActiveField(null);
  };

  const submit = (e) => {
    e.preventDefault();

    if (!originCode || !destinationCode) return;

    const params = new URLSearchParams({
      origin: originCode,
      destination: destinationCode,
      date,
    });

    navigate(`/search?${params.toString()}`);
  };

  const inputStyle = {
    paddingLeft: 42,
    paddingRight: 36,
    fontWeight: 600,
  };

  const iconStyle = {
    position: "absolute",
    top: 15,
    left: 14,
    color: "#98a2b3",
    pointerEvents: "none",
    zIndex: 2,
  };

  return (
    <motion.form
      onSubmit={submit}
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.45 }}
      style={{
        display: "grid",
        gridTemplateColumns: compact
          ? "1fr 1fr 1fr auto"
          : "1.2fr 1.2fr 1fr auto",
        gap: 10,
        width: "100%",
        maxWidth: 900,
        margin: "0 auto",
        padding: 10,
        border: "1px solid rgba(255,255,255,.35)",
        borderRadius: 18,
        background: "rgba(255,255,255,.97)",
        boxShadow: "0 20px 60px rgba(7,26,51,.22)",
      }}
    >
      <AirportField
        value={origin}
        onChange={(value) => handleInput("origin", value)}
        onFocus={() => {
          setActiveField("origin");
          setSuggestions([]);
        }}
        onSelect={selectAirport}
        suggestions={suggestions}
        active={activeField === "origin"}
        placeholder="From city or airport"
        iconStyle={iconStyle}
        inputStyle={inputStyle}
      />

      <AirportField
        value={destination}
        onChange={(value) => handleInput("destination", value)}
        onFocus={() => {
          setActiveField("destination");
          setSuggestions([]);
        }}
        onSelect={selectAirport}
        suggestions={suggestions}
        active={activeField === "destination"}
        placeholder="To city or airport"
        iconStyle={iconStyle}
        inputStyle={inputStyle}
      />

      <div style={{ position: "relative" }}>
        <FiCalendar style={iconStyle} />

        <input
          type="date"
          value={date}
          min={today()}
          onChange={(e) => setDate(e.target.value)}
          style={inputStyle}
          required
        />
      </div>

      <button
        type="submit"
        className="btn-primary"
        disabled={!originCode || !destinationCode}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
          padding: "0 24px",
          whiteSpace: "nowrap",
        }}
      >
        <FiSearch size={17} />
        Search
      </button>
    </motion.form>
  );
}

function AirportField({
  value,
  onChange,
  onFocus,
  onSelect,
  suggestions,
  active,
  placeholder,
  iconStyle,
  inputStyle,
}) {
  return (
    <div style={{ position: "relative" }}>
      <FiMapPin style={iconStyle} />

      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={onFocus}
        placeholder={placeholder}
        style={inputStyle}
        required
      />

      <FiChevronDown
        size={14}
        style={{
          position: "absolute",
          top: 17,
          right: 13,
          color: "#98a2b3",
          pointerEvents: "none",
        }}
      />

      {active && value.trim().length >= 2 && suggestions.length > 0 && (
        <div
          style={{
            position: "absolute",
            top: "calc(100% + 8px)",
            left: 0,
            right: 0,
            zIndex: 50,
            padding: 6,
            background: "#fff",
            border: "1px solid var(--line)",
            borderRadius: 14,
            boxShadow: "0 16px 40px rgba(11,31,58,.14)",
          }}
        >
          {suggestions.map((airport) => (
            <button
              key={airport.id}
              type="button"
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => onSelect(airport)}
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "11px 10px",
                background: "transparent",
                textAlign: "left",
                borderRadius: 10,
              }}
            >
              <span
                style={{
                  width: 34,
                  height: 34,
                  display: "grid",
                  placeItems: "center",
                  flexShrink: 0,
                  borderRadius: 9,
                  background: "#eaf3ff",
                  color: "var(--primary)",
                }}
              >
                <FiMapPin size={16} />
              </span>

              <span style={{ minWidth: 0, flex: 1 }}>
                <span
                  style={{
                    display: "block",
                    color: "var(--ink)",
                    fontSize: 13,
                    fontWeight: 700,
                  }}
                >
                  {airport.city}
                </span>

                <span
                  style={{
                    display: "block",
                    marginTop: 2,
                    color: "var(--muted)",
                    fontSize: 11,
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {airport.name}
                </span>
              </span>

              <strong
                style={{
                  color: "var(--primary)",
                  fontFamily: '"Manrope", sans-serif',
                  fontSize: 12,
                }}
              >
                {airport.iata_code}
              </strong>
            </button>
          ))}
        </div>
      )}

      {active && value.trim().length >= 2 && suggestions.length === 0 && (
        <div
          style={{
            position: "absolute",
            top: "calc(100% + 8px)",
            left: 0,
            right: 0,
            zIndex: 50,
            padding: 16,
            background: "#fff",
            border: "1px solid var(--line)",
            borderRadius: 14,
            boxShadow: "0 16px 40px rgba(11,31,58,.14)",
            color: "var(--muted)",
            fontSize: 12,
          }}
        >
          No airports found
        </div>
      )}
    </div>
  );
}