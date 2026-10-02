import SectionHeader from "../../components/ui/SectionHeader";
import DestinationCard from "../../components/ui/DestinationCard";
import { DESTINATIONS } from "../../constants/landing";

export default function DestinationsSection() {
  return (
    <section style={{ padding: "96px 0", background: "var(--bg)" }}>
      <div className="container">
        <SectionHeader
          eyebrow="Explore"
          title="Popular destinations"
        />

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: 24,
            marginTop: 44,
          }}
        >
          {DESTINATIONS.map((destination, index) => (
            <DestinationCard
              key={destination.code}
              {...destination}
              delay={index * 0.08}
            />
          ))}
        </div>
      </div>
    </section>
  );
}