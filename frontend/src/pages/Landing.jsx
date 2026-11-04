// src/pages/Landing.jsx
import HeroSection from '../sections/landing/HeroSection';
import DestinationsSection from '../sections/landing/DestinationsSection';
import RecommendedRoutes from '../components/RecommendedRoutes';
import FeaturesSection from '../sections/landing/FeaturesSection';
import CTASection from '../sections/landing/CTASection';
import Footer from '../sections/landing/Footer';

export default function Landing() {
  return (
    <>
      <HeroSection />
      <RecommendedRoutes />
      <DestinationsSection />  
      <FeaturesSection />
      <CTASection />
      <Footer />
    </>
  );
}