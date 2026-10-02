import { useEffect, useRef, useState } from "react";

export default function CountdownTimer({
  secondsRemaining,
  onExpire,
  onTick,
}) {
  const [remaining, setRemaining] = useState(
    Math.max(0, Number(secondsRemaining) || 0)
  );

  // Remember the last onExpire we fired so we only call it once.
  const firedRef = useRef(false);

  // If the parent passes a fresh value (e.g. after a re-fetch),
  // reset the counter.
  useEffect(() => {
    firedRef.current = false;
    setRemaining(Math.max(0, Number(secondsRemaining) || 0));
  }, [secondsRemaining]);

  useEffect(() => {
    if (remaining <= 0) {
      if (!firedRef.current) {
        firedRef.current = true;
        if (typeof onExpire === "function") onExpire();
      }
      return;
    }

    const id = setInterval(() => {
      setRemaining((current) => {
        const next = Math.max(0, current - 1);
        if (typeof onTick === "function") onTick(next);
        return next;
      });
    }, 1000);

    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [remaining]);

  const mm = String(Math.floor(remaining / 60)).padStart(2, "0");
  const ss = String(remaining % 60).padStart(2, "0");

  // Colour shifts red when under a minute left.
  const urgent = remaining <= 60;

  return (
    <span
      style={{
        fontVariantNumeric: "tabular-nums",
        fontWeight: 700,
        color: urgent ? "var(--danger, #b42318)" : "inherit",
      }}
    >
      {mm}:{ss}
    </span>
  );
}
