import SectionHeader from "../../components/ui/SectionHeader";
import FeatureCard from "../../components/ui/FeatureCard";
import { FEATURES } from "../../constants/landing";

export default function FeaturesSection() {
  return (
    <section style={{ padding: "96px 0", background: "var(--surface)" }}>
      <div className="container">
        <SectionHeader
          eyebrow="Why Aeriva"
          title="Booking that just works"
        />

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: 24,
            marginTop: 44,
          }}
        >
          {FEATURES.map((feature, index) => (
            <FeatureCard
              key={feature.title}
              {...feature}
              delay={index * 0.1}
            />
          ))}
        </div>
      </div>
    </section>
  );
}