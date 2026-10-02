import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { FiArrowRight, FiLock, FiMail } from "react-icons/fi";
import { MdFlightTakeoff } from "react-icons/md";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const { login, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const redirectTo =
    new URLSearchParams(location.search).get("next") || "/";

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const result = await login(email.trim(), password);

    if (result.success) navigate(redirectTo, { replace: true });
    else setError(result.error);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "100px 24px 60px",
        background:
          "radial-gradient(circle at top right, rgba(56,189,248,.16), transparent 35%), linear-gradient(135deg, #071a33, #0b3b78 65%, #1677ff)",
      }}
    >
      <motion.form
        onSubmit={handleSubmit}
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
        style={{
          width: "100%",
          maxWidth: 420,
          padding: 36,
          background: "rgba(255,255,255,.98)",
          border: "1px solid rgba(255,255,255,.4)",
          borderRadius: "var(--radius-lg)",
          boxShadow: "0 30px 70px rgba(7,26,51,.3)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 30 }}>
          <div
            style={{
              width: 48,
              height: 48,
              margin: "0 auto 16px",
              display: "grid",
              placeItems: "center",
              borderRadius: 14,
              background: "#eaf3ff",
              color: "var(--primary)",
            }}
          >
            <MdFlightTakeoff size={27} />
          </div>

          <h1 style={{ fontSize: 28, marginBottom: 7 }}>
            Welcome back
          </h1>

          <p style={{ color: "var(--muted)", fontSize: 14 }}>
            Sign in to continue your journey
          </p>
        </div>

        <Field
          id="email"
          label="Email address"
          icon={<FiMail />}
          type="email"
          value={email}
          onChange={setEmail}
          placeholder="Enter your email"
          autoComplete="email"
        />

        <Field
          id="password"
          label="Password"
          icon={<FiLock />}
          type="password"
          value={password}
          onChange={setPassword}
          placeholder="Enter your password"
          autoComplete="current-password"
        />

        {error && (
          <div
            role="alert"
            style={{
              marginBottom: 16,
              padding: "11px 13px",
              borderRadius: 10,
              background: "#fef2f2",
              border: "1px solid #fecaca",
              color: "#b42318",
              fontSize: 13,
            }}
          >
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="btn-primary"
          style={{
            width: "100%",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            gap: 8,
            padding: "13px 18px",
            marginTop: 4,
            fontSize: 15,
          }}
        >
          {loading ? "Signing in…" : "Sign in"}
          {!loading && <FiArrowRight size={16} />}
        </button>

        <p
          style={{
            marginTop: 22,
            color: "var(--muted)",
            textAlign: "center",
            fontSize: 14,
          }}
        >
          Don't have an account?{" "}
          <Link
            to="/register"
            style={{
              color: "var(--primary)",
              fontFamily: '"Manrope", sans-serif',
              fontWeight: 700,
            }}
          >
            Create one
          </Link>
        </p>
      </motion.form>
    </div>
  );
}

function Field({
  id,
  label,
  icon,
  type,
  value,
  onChange,
  placeholder,
  autoComplete,
}) {
  return (
    <div style={{ marginBottom: 18 }}>
      <label htmlFor={id}>{label}</label>

      <div style={{ position: "relative" }}>
        <span
          style={{
            position: "absolute",
            left: 14,
            top: "50%",
            display: "grid",
            placeItems: "center",
            color: "#98a2b3",
            transform: "translateY(-50%)",
            pointerEvents: "none",
          }}
        >
          {icon}
        </span>

        <input
          id={id}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoComplete={autoComplete}
          style={{ paddingLeft: 42 }}
          required
        />
      </div>
    </div>
  );
}