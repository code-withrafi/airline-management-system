// src/App.jsx

import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";

import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";

import Landing from "./pages/Landing";
import SearchResults from "./pages/SearchResults";
import FlightDetails from "./pages/FlightDetails";
import Login from "./pages/Login";
import Register from "./pages/Register";

import Booking from "./pages/Booking";
import Payment from "./pages/Payment";
import Confirmation from "./pages/Confirmation";
import MyBookings from "./pages/MyBookings";
import BookingDetail from "./pages/BookingDetail";
import Profile from "./pages/Profile";

function AnimatedPage({ children }) {
  return (
    <motion.main
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{
        duration: 0.35,
        ease: [0.22, 1, 0.36, 1],
      }}
      style={{
        minHeight: "100vh",
        paddingTop: "var(--nav-height)",
      }}
    >
      {children}
    </motion.main>
  );
}

export default function App() {
  const location = useLocation();

  return (
    <>
      <Navbar />

      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>

          {/* Public Routes */}
          <Route
            path="/"
            element={
              <AnimatedPage>
                <Landing />
              </AnimatedPage>
            }
          />

          <Route
            path="/search"
            element={
              <AnimatedPage>
                <SearchResults />
              </AnimatedPage>
            }
          />

          <Route
            path="/flights/:id"
            element={
              <AnimatedPage>
                <FlightDetails />
              </AnimatedPage>
            }
          />

          <Route
            path="/login"
            element={
              <AnimatedPage>
                <Login />
              </AnimatedPage>
            }
          />

          <Route
            path="/register"
            element={
              <AnimatedPage>
                <Register />
              </AnimatedPage>
            }
          />

          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route
              path="/booking/:flightId"
              element={
                <AnimatedPage>
                  <Booking />
                </AnimatedPage>
              }
            />

            <Route
              path="/payment/:bookingId"
              element={
                <AnimatedPage>
                  <Payment />
                </AnimatedPage>
              }
            />

            <Route
              path="/confirmation/:bookingId"
              element={
                <AnimatedPage>
                  <Confirmation />
                </AnimatedPage>
              }
            />

            <Route
              path="/bookings"
              element={
                <AnimatedPage>
                  <MyBookings />
                </AnimatedPage>
              }
            />

            <Route
              path="/bookings/:id"
              element={
                <AnimatedPage>
                  <BookingDetail />
                </AnimatedPage>
              }
            />

            <Route
              path="/profile"
              element={
                <AnimatedPage>
                  <Profile />
                </AnimatedPage>
              }
            />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AnimatePresence>
    </>
  );
}