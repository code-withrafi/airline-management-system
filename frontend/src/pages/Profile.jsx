// src/pages/Profile.jsx

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  FiUser,
  FiPhone,
  FiCalendar,
  FiCreditCard,
  FiMapPin,
  FiLock,
  FiCheck,
  FiAlertCircle,
  FiEdit3,
} from "react-icons/fi";

import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

const inputGrid = {
  display: "grid",
  gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
  gap: 16,
};

function initials(first = "", last = "") {
  return `${first[0] || ""}${last[0] || ""}`.toUpperCase() || "U";
}

function fmtLongDate(iso) {
  if (!iso) return "—";

  return new Date(iso).toLocaleDateString([], {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

export default function Profile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [state, setState] = useState({
    loading: true,
    error: null,
  });

  useEffect(() => {
    api
      .get("/api/passengers/me")
      .then(({ data }) => {
        setProfile(data);
        setState({ loading: false, error: null });
      })
      .catch((err) => {
        setState({
          loading: false,
          error:
            err.response?.data?.detail ||
            "Could not load profile.",
        });
      });
  }, []);

  if (state.loading) return <Loading />;
  if (state.error) return <ErrorBlock message={state.error} />;
  if (!profile) return null;

  const fullName = `${profile.first_name} ${profile.last_name}`;

  return (
    <div className="page">
      <div className="container profile-container">
        <motion.header
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          style={{ marginBottom: 32 }}
        >
          <div className="eyebrow">Account</div>

          <h1 className="profile-title">My profile</h1>

          <p className="profile-subtitle">
            Manage your personal information and account security.
          </p>
        </motion.header>

        <div className="profile-layout">
          <ProfileCard
            profile={profile}
            fullName={fullName}
          />

          <div className="profile-forms">
            <PersonalInfoCard
              profile={profile}
              onUpdated={setProfile}
            />

            <PasswordCard email={user?.email} />
          </div>
        </div>
      </div>

      <style>{`
        .profile-container {
          max-width: 1100px;
        }

        .eyebrow {
          margin-bottom: 8px;
          color: var(--primary);
          font-family: "Manrope", sans-serif;
          font-size: 12px;
          font-weight: 700;
          letter-spacing: .08em;
          text-transform: uppercase;
        }

        .profile-title {
          font-size: clamp(28px, 4vw, 38px);
          letter-spacing: -.03em;
          margin-bottom: 7px;
        }

        .profile-subtitle {
          color: var(--muted);
          font-size: 15px;
        }

        .profile-layout {
          display: grid;
          grid-template-columns: minmax(240px, 300px) minmax(0, 1fr);
          gap: 24px;
          align-items: start;
        }

        .profile-forms {
          display: grid;
          gap: 24px;
        }

        .profile-avatar-card {
          position: sticky;
          top: 96px;
        }

        @media (max-width: 850px) {
          .profile-layout {
            grid-template-columns: 1fr;
          }

          .profile-avatar-card {
            position: static;
          }
        }

        @media (max-width: 600px) {
          .profile-container {
            width: min(100% - 24px, 1100px);
          }

          .profile-layout {
            gap: 16px;
          }

          .profile-forms {
            gap: 16px;
          }

          .profile-card {
            padding: 22px !important;
          }

          .profile-form-card {
            padding: 22px !important;
          }

          .profile-input-grid {
            grid-template-columns: 1fr !important;
          }

          .profile-actions {
            justify-content: stretch !important;
          }

          .profile-actions button {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
}

function ProfileCard({ profile, fullName }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.45 }}
      className="card profile-card profile-avatar-card"
      style={{
        padding: 28,
        textAlign: "center",
      }}
    >
      <div
        style={{
          width: 88,
          height: 88,
          margin: "0 auto 16px",
          display: "grid",
          placeItems: "center",
          borderRadius: "50%",
          background:
            "linear-gradient(135deg, var(--primary), #0757c9)",
          color: "#fff",
          fontFamily: '"Plus Jakarta Sans", sans-serif',
          fontSize: 28,
          fontWeight: 800,
          boxShadow: "0 10px 28px rgba(22,119,255,.2)",
        }}
      >
        {initials(profile.first_name, profile.last_name)}
      </div>

      <h2
        style={{
          fontSize: 18,
          marginBottom: 4,
        }}
      >
        {fullName}
      </h2>

      <p
        style={{
          color: "var(--muted)",
          fontSize: 13,
          marginBottom: 22,
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        {profile.email}
      </p>

      <div
        style={{
          borderTop: "1px solid var(--line)",
          paddingTop: 20,
          display: "grid",
          gap: 14,
          textAlign: "left",
        }}
      >
        <InfoChip
          icon={FiCreditCard}
          label="Passport"
          value={profile.passport_number}
        />

        <InfoChip
          icon={FiCalendar}
          label="Born"
          value={fmtLongDate(profile.date_of_birth)}
        />

        <InfoChip
          icon={FiUser}
          label="Member since"
          value={fmtLongDate(profile.created_at)}
        />
      </div>
    </motion.div>
  );
}

function InfoChip({ icon: Icon, label, value }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
      }}
    >
      <div
        style={{
          width: 34,
          height: 34,
          flexShrink: 0,
          display: "grid",
          placeItems: "center",
          borderRadius: 10,
          background: "#eef5ff",
          color: "var(--primary)",
        }}
      >
        <Icon size={15} />
      </div>

      <div style={{ minWidth: 0 }}>
        <div
          style={{
            color: "#98a2b3",
            fontFamily: '"Manrope", sans-serif',
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: ".05em",
            textTransform: "uppercase",
          }}
        >
          {label}
        </div>

        <div
          style={{
            marginTop: 2,
            fontSize: 13,
            fontWeight: 600,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {value || "—"}
        </div>
      </div>
    </div>
  );
}

function PersonalInfoCard({ profile, onUpdated }) {
  const [form, setForm] = useState({
    first_name: profile.first_name,
    last_name: profile.last_name,
    phone: profile.phone,
    date_of_birth: profile.date_of_birth || "",
    passport_number: profile.passport_number,
    address: profile.address || "",
  });

  const [state, setState] = useState({
    saving: false,
    error: "",
    saved: false,
  });

  const set = (key) => (e) =>
    setForm((current) => ({
      ...current,
      [key]: e.target.value,
    }));

  const handleSubmit = async (e) => {
    e.preventDefault();

    setState({
      saving: true,
      error: "",
      saved: false,
    });

    try {
      const { data } = await api.put("/api/passengers/me", {
        ...form,
        date_of_birth: form.date_of_birth || null,
        address: form.address.trim() || null,
      });

      onUpdated(data);

      setState({
        saving: false,
        error: "",
        saved: true,
      });

      setTimeout(
        () =>
          setState((current) => ({
            ...current,
            saved: false,
          })),
        2200
      );
    } catch (err) {
      setState({
        saving: false,
        saved: false,
        error: getError(err, "Could not save changes."),
      });
    }
  };

  return (
    <motion.form
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.05 }}
      className="card profile-form-card"
      style={{ padding: 28 }}
    >
      <CardHeader
        icon={FiEdit3}
        title="Personal information"
        subtitle="Update the details used for ticketing and check-in."
      />

      <div
        className="profile-input-grid"
        style={inputGrid}
      >
        <Field
          label="First name"
          value={form.first_name}
          onChange={set("first_name")}
          required
        />

        <Field
          label="Last name"
          value={form.last_name}
          onChange={set("last_name")}
          required
        />

        <Field
          label="Phone"
          value={form.phone}
          onChange={set("phone")}
          icon={FiPhone}
          required
        />

        <Field
          label="Date of birth"
          type="date"
          value={form.date_of_birth}
          onChange={set("date_of_birth")}
          icon={FiCalendar}
        />

        <Field
          label="Passport number"
          value={form.passport_number}
          onChange={set("passport_number")}
          icon={FiCreditCard}
          required
        />

        <Field
          label="Address"
          value={form.address}
          onChange={set("address")}
          icon={FiMapPin}
          placeholder="Optional"
        />
      </div>

      <StatusBanner state={state} />

      <ActionButton
        loading={state.saving}
        saved={state.saved}
        savedText="Saved"
        defaultText="Save changes"
      />
    </motion.form>
  );
}

function PasswordCard({ email }) {
  const [form, setForm] = useState({
    old_password: "",
    new_password: "",
    confirm_password: "",
  });

  const [state, setState] = useState({
    saving: false,
    error: "",
    saved: false,
  });

  const set = (key) => (e) =>
    setForm((current) => ({
      ...current,
      [key]: e.target.value,
    }));

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (form.new_password !== form.confirm_password) {
      setState({
        saving: false,
        saved: false,
        error: "New passwords do not match.",
      });
      return;
    }

    if (form.new_password.length < 6) {
      setState({
        saving: false,
        saved: false,
        error: "New password must be at least 6 characters.",
      });
      return;
    }

    setState({
      saving: true,
      error: "",
      saved: false,
    });

    try {
      await api.post("/api/passengers/me/password", {
        old_password: form.old_password,
        new_password: form.new_password,
      });

      setForm({
        old_password: "",
        new_password: "",
        confirm_password: "",
      });

      setState({
        saving: false,
        error: "",
        saved: true,
      });

      setTimeout(
        () =>
          setState((current) => ({
            ...current,
            saved: false,
          })),
        2500
      );
    } catch (err) {
      setState({
        saving: false,
        saved: false,
        error: getError(err, "Could not change password."),
      });
    }
  };

  return (
    <motion.form
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.1 }}
      className="card profile-form-card"
      style={{ padding: 28 }}
    >
      <CardHeader
        icon={FiLock}
        title="Account & security"
        subtitle="Keep your account protected with a strong password."
      />

      <div style={{ marginBottom: 16 }}>
        <label>Email address</label>

        <input
          type="email"
          value={email || ""}
          disabled
          style={{
            background: "#f8fafc",
            color: "var(--muted)",
            cursor: "not-allowed",
          }}
        />
      </div>

      <div
        className="profile-input-grid"
        style={inputGrid}
      >
        <Field
          label="Current password"
          type="password"
          value={form.old_password}
          onChange={set("old_password")}
          required
        />

        <Field
          label="New password"
          type="password"
          value={form.new_password}
          onChange={set("new_password")}
          minLength={6}
          required
        />

        <Field
          label="Confirm new password"
          type="password"
          value={form.confirm_password}
          onChange={set("confirm_password")}
          minLength={6}
          required
        />
      </div>

      <StatusBanner state={state} />

      <ActionButton
        loading={state.saving}
        saved={state.saved}
        savedText="Updated"
        defaultText="Update password"
      />
    </motion.form>
  );
}

function CardHeader({ icon: Icon, title, subtitle }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: 13,
        marginBottom: 24,
      }}
    >
      <div
        style={{
          width: 42,
          height: 42,
          flexShrink: 0,
          display: "grid",
          placeItems: "center",
          borderRadius: 12,
          background: "#eaf3ff",
          color: "var(--primary)",
        }}
      >
        <Icon size={19} />
      </div>

      <div>
        <h2
          style={{
            fontSize: 18,
            marginBottom: 4,
          }}
        >
          {title}
        </h2>

        <p
          style={{
            color: "var(--muted)",
            fontSize: 13,
            lineHeight: 1.5,
          }}
        >
          {subtitle}
        </p>
      </div>
    </div>
  );
}

function Field({
  label,
  type = "text",
  value,
  onChange,
  required,
  icon: Icon,
  placeholder,
  minLength,
}) {
  return (
    <div>
      <label>{label}</label>

      <div style={{ position: "relative" }}>
        {Icon && (
          <Icon
            size={15}
            style={{
              position: "absolute",
              top: 15,
              left: 13,
              color: "#98a2b3",
              pointerEvents: "none",
            }}
          />
        )}

        <input
          type={type}
          value={value || ""}
          onChange={onChange}
          required={required}
          placeholder={placeholder}
          minLength={minLength}
          style={{
            paddingLeft: Icon ? 38 : undefined,
          }}
        />
      </div>
    </div>
  );
}

function ActionButton({
  loading,
  saved,
  savedText,
  defaultText,
}) {
  return (
    <div
      className="profile-actions"
      style={{
        display: "flex",
        justifyContent: "flex-end",
        marginTop: 20,
      }}
    >
      <button
        type="submit"
        disabled={loading}
        className="btn-primary"
        style={{
          minWidth: 150,
          padding: "12px 22px",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
          fontSize: 14,
        }}
      >
        {saved ? (
          <>
            <FiCheck size={15} />
            {savedText}
          </>
        ) : loading ? (
          "Updating…"
        ) : (
          defaultText
        )}
      </button>
    </div>
  );
}

function StatusBanner({ state }) {
  if (state.error) {
    return (
      <div
        style={{
          marginTop: 20,
          padding: "11px 13px",
          display: "flex",
          alignItems: "center",
          gap: 8,
          borderRadius: 10,
          background: "#fff5f4",
          border: "1px solid #f5c2c0",
          color: "#b42318",
          fontSize: 13,
        }}
      >
        <FiAlertCircle size={15} />
        {state.error}
      </div>
    );
  }

  if (state.saved) {
    return (
      <motion.div
        initial={{ opacity: 0, y: -5 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          marginTop: 20,
          padding: "11px 13px",
          display: "flex",
          alignItems: "center",
          gap: 8,
          borderRadius: 10,
          background: "#ecfdf3",
          border: "1px solid #abefc6",
          color: "#087443",
          fontSize: 13,
        }}
      >
        <FiCheck size={15} />
        Changes saved successfully.
      </motion.div>
    );
  }

  return null;
}

function Loading() {
  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 1100 }}>
        <div
          className="card"
          style={{
            height: 420,
            background:
              "linear-gradient(90deg, #f1f5f9 0%, #e2e8f0 50%, #f1f5f9 100%)",
            backgroundSize: "200% 100%",
            animation: "profileShimmer 1.4s infinite",
          }}
        />
      </div>

      <style>{`
        @keyframes profileShimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
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
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="card"
          style={{
            padding: 44,
            textAlign: "center",
          }}
        >
          <div
            style={{
              width: 58,
              height: 58,
              margin: "0 auto 16px",
              display: "grid",
              placeItems: "center",
              borderRadius: 16,
              background: "#fff0ef",
              color: "var(--danger)",
            }}
          >
            <FiAlertCircle size={28} />
          </div>

          <h2
            style={{
              fontSize: 20,
              marginBottom: 8,
            }}
          >
            Could not load profile
          </h2>

          <p
            style={{
              color: "var(--muted)",
              fontSize: 14,
            }}
          >
            {message}
          </p>
        </motion.div>
      </div>
    </div>
  );
}

function getError(err, fallback) {
  const detail = err.response?.data?.detail;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(", ");
  }

  return fallback;
}