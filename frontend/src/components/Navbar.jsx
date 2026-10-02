// src/components/Navbar.jsx

import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import {
  FiUser,
  FiMenu,
  FiX,
  FiSearch,
  FiLogOut,
  FiChevronDown,
  FiHome,
  FiBriefcase,
} from "react-icons/fi";
import { MdFlightTakeoff } from "react-icons/md";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const isLanding = location.pathname === "/";
  const transparent = isLanding && !scrolled;

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 40);
    };

    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });

    return () => {
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  const closeMobileMenu = () => {
    setMobileOpen(false);
  };

  const handleLogout = () => {
    logout();
    closeMobileMenu();
    navigate("/");
  };

  const initial = user?.email?.charAt(0)?.toUpperCase() || "";

  const isActive = (path) => location.pathname === path;

  const textColor = transparent ? "#ffffff" : "var(--ink)";
  const mutedColor = transparent
    ? "rgba(255,255,255,.9)"
    : "var(--muted)";

  return (
    <motion.header
      initial={false}
      animate={{
        backgroundColor: transparent
          ? "rgba(6,21,43,.72)"
          : "rgba(255,255,255,.94)",
        boxShadow: transparent
          ? "0 4px 24px rgba(0,0,0,.12)"
          : "0 1px 24px rgba(11,31,58,.07)",
        backdropFilter: transparent ? "blur(14px)" : "blur(16px)",
      }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      style={{
        position: "fixed",
        inset: "0 0 auto 0",
        height: "var(--nav-height)",
        zIndex: 1000,
        borderBottom: transparent
          ? "1px solid rgba(255,255,255,.08)"
          : "1px solid rgba(228,233,241,.7)",
      }}
    >
      <div
        className="container"
        style={{
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        {/* Logo */}
        <Link
          to="/"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            color: textColor,
            fontFamily: '"Plus Jakarta Sans", sans-serif',
            fontSize: 20,
            fontWeight: 800,
            letterSpacing: "-.04em",
            flexShrink: 0,
          }}
        >
          <span
            style={{
              width: 38,
              height: 38,
              display: "grid",
              placeItems: "center",
              borderRadius: 12,
              background: transparent
                ? "rgba(255,255,255,.14)"
                : "#eaf3ff",
              color: transparent ? "#ffffff" : "var(--primary)",
            }}
          >
            <MdFlightTakeoff size={23} />
          </span>

          <span>Aeriva</span>
        </Link>

        {/* Desktop Navigation */}
        <nav
          className="desktop-nav"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 4,
          }}
        >
          <NavLink
            to="/"
            active={isActive("/")}
            transparent={transparent}
            icon={<FiHome size={16} />}
          >
            Home
          </NavLink>

          <NavLink
            to="/search"
            active={isActive("/search")}
            transparent={transparent}
            icon={<FiSearch size={16} />}
          >
            Search flights
          </NavLink>

          {isAuthenticated && (
            <>
              <NavLink
                to="/bookings"
                active={
                  isActive("/bookings") ||
                  location.pathname.startsWith("/bookings/")
                }
                transparent={transparent}
                icon={<FiBriefcase size={16} />}
              >
                My Bookings
              </NavLink>

              <NavLink
                to="/profile"
                active={isActive("/profile")}
                transparent={transparent}
                icon={<FiUser size={16} />}
              >
                Profile
              </NavLink>

              <div
                style={{
                  width: 1,
                  height: 24,
                  background: transparent
                    ? "rgba(255,255,255,.2)"
                    : "var(--line)",
                  margin: "0 8px",
                }}
              />

              <Link
                to="/profile"
                title={user?.email || "Profile"}
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: "50%",
                  display: "grid",
                  placeItems: "center",
                  background: transparent
                    ? "rgba(255,255,255,.16)"
                    : "var(--primary)",
                  color: "#fff",
                  fontFamily: '"Manrope", sans-serif',
                  fontSize: 13,
                  fontWeight: 700,
                  transition: "transform .2s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = "scale(1.06)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "scale(1)";
                }}
              >
                {initial || <FiUser size={17} />}
              </Link>

              <button
                onClick={handleLogout}
                title="Sign out"
                style={{
                  width: 38,
                  height: 38,
                  marginLeft: 4,
                  display: "grid",
                  placeItems: "center",
                  background: "transparent",
                  color: mutedColor,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = transparent
                    ? "rgba(255,255,255,.1)"
                    : "#f1f5f9";
                  e.currentTarget.style.color = "var(--danger)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.color = mutedColor;
                }}
              >
                <FiLogOut size={17} />
              </button>
            </>
          )}

          {!isAuthenticated && (
            <>
              <Link
                to="/login"
                style={{
                  padding: "10px 16px",
                  color: textColor,
                  fontFamily: '"Manrope", sans-serif',
                  fontSize: 14,
                  fontWeight: 600,
                }}
              >
                Sign in
              </Link>

              <Link
                to="/register"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "11px 18px",
                  borderRadius: 12,
                  background: transparent
                    ? "#ffffff"
                    : "var(--primary)",
                  color: transparent ? "var(--primary)" : "#ffffff",
                  fontFamily: '"Manrope", sans-serif',
                  fontSize: 14,
                  fontWeight: 700,
                  boxShadow: transparent
                    ? "0 8px 24px rgba(0,0,0,.12)"
                    : "none",
                }}
              >
                Get started

                <FiChevronDown
                  size={14}
                  style={{ transform: "rotate(-90deg)" }}
                />
              </Link>
            </>
          )}
        </nav>

        {/* Mobile Toggle */}
        <button
          className="mobile-menu-button"
          onClick={() => setMobileOpen((value) => !value)}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          style={{
            width: 42,
            height: 42,
            display: "none",
            placeItems: "center",
            background: transparent
              ? "rgba(255,255,255,.12)"
              : "#f1f5f9",
            color: textColor,
          }}
        >
          {mobileOpen ? <FiX size={21} /> : <FiMenu size={21} />}
        </button>
      </div>

      {/* Mobile Navigation */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            style={{
              position: "absolute",
              top: "calc(var(--nav-height) + 8px)",
              left: 16,
              right: 16,
              padding: 12,
              background: "rgba(255,255,255,.98)",
              border: "1px solid var(--line)",
              borderRadius: 18,
              boxShadow: "0 16px 40px rgba(11,31,58,.12)",
            }}
          >
            <MobileLink
              to="/"
              icon={<FiHome size={17} />}
              active={isActive("/")}
              onClick={closeMobileMenu}
            >
              Home
            </MobileLink>

            <MobileLink
              to="/search"
              icon={<FiSearch size={17} />}
              active={isActive("/search")}
              onClick={closeMobileMenu}
            >
              Search flights
            </MobileLink>

            {isAuthenticated ? (
              <>
                <MobileLink
                  to="/bookings"
                  icon={<FiBriefcase size={17} />}
                  active={
                    isActive("/bookings") ||
                    location.pathname.startsWith("/bookings/")
                  }
                  onClick={closeMobileMenu}
                >
                  My Bookings
                </MobileLink>

                <MobileLink
                  to="/profile"
                  icon={<FiUser size={17} />}
                  active={isActive("/profile")}
                  onClick={closeMobileMenu}
                >
                  Profile
                </MobileLink>

                <button
                  onClick={handleLogout}
                  style={{
                    width: "100%",
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    padding: "13px 14px",
                    marginTop: 4,
                    background: "transparent",
                    color: "var(--danger)",
                    textAlign: "left",
                    fontFamily: '"Manrope", sans-serif',
                    fontSize: 14,
                    fontWeight: 600,
                  }}
                >
                  <FiLogOut size={17} />
                  Sign out
                </button>
              </>
            ) : (
              <>
                <MobileLink
                  to="/login"
                  onClick={closeMobileMenu}
                >
                  Sign in
                </MobileLink>

                <Link
                  to="/register"
                  onClick={closeMobileMenu}
                  style={{
                    display: "block",
                    marginTop: 8,
                    padding: "13px 16px",
                    borderRadius: 12,
                    background: "var(--primary)",
                    color: "#fff",
                    textAlign: "center",
                    fontFamily: '"Manrope", sans-serif',
                    fontSize: 14,
                    fontWeight: 700,
                  }}
                >
                  Get started
                </Link>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Responsive Navbar Styles */}
      <style>
        {`
          @media (max-width: 800px) {
            .desktop-nav {
              display: none !important;
            }

            .mobile-menu-button {
              display: grid !important;
            }
          }
        `}
      </style>
    </motion.header>
  );
}

/* Desktop navigation link */
function NavLink({ to, children, active, transparent, icon }) {
  return (
    <Link
      to={to}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 7,
        padding: "10px 13px",
        borderRadius: 10,
        color: transparent
          ? "rgba(255,255,255,.98)"
          : active
            ? "var(--primary)"
            : "var(--ink)",
        background: active
          ? transparent
            ? "rgba(255,255,255,.12)"
            : "#eef5ff"
          : "transparent",
        fontFamily: '"Manrope", sans-serif',
        fontSize: 14,
        fontWeight: active ? 700 : 600,
        transition: ".2s ease",
        textShadow: transparent
          ? "0 1px 6px rgba(0,0,0,.2)"
          : "none",
      }}
    >
      {icon}
      {children}
    </Link>
  );
}

/* Mobile navigation link */
function MobileLink({ to, children, active, icon, onClick }) {
  return (
    <Link
      to={to}
      onClick={onClick}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "13px 14px",
        borderRadius: 12,
        color: active ? "var(--primary)" : "var(--ink)",
        background: active ? "#eef5ff" : "transparent",
        fontFamily: '"Manrope", sans-serif',
        fontSize: 14,
        fontWeight: active ? 700 : 600,
      }}
    >
      {icon}
      {children}
    </Link>
  );
}