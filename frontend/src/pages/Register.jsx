import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FiArrowRight,
  FiCalendar,
  FiHome,
  FiLock,
  FiMail,
  FiPhone,
  FiUser,
} from "react-icons/fi";
import { MdFlightTakeoff } from "react-icons/md";

import { useAuth } from "../context/AuthContext";

export default function Register() {
  const [form, setForm] = useState({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    phone: "",
    date_of_birth: "",
    passport_number: "",
    address: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { register } = useAuth();
  const navigate = useNavigate();

  const set = (key) => (e) =>
    setForm((current) => ({
      ...current,
      [key]: e.target.value,
    }));

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const result = await register({
      ...form,
      email: form.email.trim(),
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      phone: form.phone.trim(),
      passport_number: form.passport_number.trim(),
      address: form.address.trim() || null,
    });

    setLoading(false);

    if (result.success) navigate("/", { replace: true });
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
        onSubmit={submit}
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
        style={{
          width: "100%",
          maxWidth: 580,
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
            Create your account
          </h1>

          <p style={{ color: "var(--muted)", fontSize: 14 }}>
            Join Aeriva and make your next journey easier
          </p>
        </div>

        <div
          className="register-grid"
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 16,
          }}
        >
          <Field
            id="first_name"
            label="First name"
            icon={<FiUser />}
            value={form.first_name}
            onChange={set("first_name")}
            placeholder="First name"
            autoComplete="given-name"
          />

          <Field
            id="last_name"
            label="Last name"
            icon={<FiUser />}
            value={form.last_name}
            onChange={set("last_name")}
            placeholder="Last name"
            autoComplete="family-name"
          />
        </div>

        <Field
          id="email"
          label="Email address"
          icon={<FiMail />}
          type="email"
          value={form.email}
          onChange={set("email")}
          placeholder="you@example.com"
          autoComplete="email"
        />

        <Field
          id="password"
          label="Password"
          icon={<FiLock />}
          type="password"
          value={form.password}
          onChange={set("password")}
          placeholder="At least 6 characters"
          autoComplete="new-password"
          minLength={6}
        />

        <div
          className="register-grid"
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 16,
          }}
        >
          <Field
            id="phone"
            label="Phone number"
            icon={<FiPhone />}
            value={form.phone}
            onChange={set("phone")}
            placeholder="+880..."
            autoComplete="tel"
          />

          <Field
            id="date_of_birth"
            label="Date of birth"
            icon={<FiCalendar />}
            type="date"
            value={form.date_of_birth}
            onChange={set("date_of_birth")}
            autoComplete="bday"
          />
        </div>

        <Field
          id="passport_number"
          label="Passport number"
          icon={<FiUser />}
          value={form.passport_number}
          onChange={set("passport_number")}
          placeholder="Enter passport number"
          autoComplete="off"
        />

        <Field
          id="address"
          label="Address"
          icon={<FiHome />}
          value={form.address}
          onChange={set("address")}
          placeholder="Your address (optional)"
          autoComplete="street-address"
          required={false}
        />

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            role="alert"
            style={{
              marginTop: 4,
              padding: "11px 13px",
              borderRadius: 10,
              background: "#fef2f2",
              border: "1px solid #fecaca",
              color: "#b42318",
              fontSize: 13,
              lineHeight: 1.5,
            }}
          >
            {error}
          </motion.div>
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
            marginTop: 22,
            padding: "14px 20px",
            fontSize: 15,
          }}
        >
          {loading ? "Creating account…" : "Create account"}
          {!loading && <FiArrowRight size={16} />}
        </button>

        <p
          style={{
            marginTop: 20,
            color: "var(--muted)",
            textAlign: "center",
            fontSize: 14,
          }}
        >
          Already have an account?{" "}
          <Link
            to="/login"
            style={{
              color: "var(--primary)",
              fontFamily: '"Manrope", sans-serif',
              fontWeight: 700,
            }}
          >
            Sign in
          </Link>
        </p>
      </motion.form>

      <style>{`
        @media (max-width: 600px) {
          .register-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}

function Field({
  id,
  label,
  icon,
  type = "text",
  value,
  onChange,
  placeholder,
  autoComplete,
  minLength,
  required = true,
}) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label htmlFor={id}>{label}</label>

      <div style={{ position: "relative" }}>
        <span
          style={{
            position: "absolute",
            top: "50%",
            left: 14,
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
          onChange={onChange}
          placeholder={placeholder}
          autoComplete={autoComplete}
          minLength={minLength}
          required={required}
          style={{ paddingLeft: 42 }}
        />
      </div>
    </div>
  );
}