import React from 'react';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import HeroSection from '@/components/sections/HeroSection';
import {
  ProblemSection,
  TechnologySection,
  ZeroTrustSection,
  EnterpriseSection,
  CTASection,
} from '@/components/sections/ScrollSections';

const Index: React.FC = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main>
        <HeroSection />
        <ProblemSection />
        <TechnologySection />
        <ZeroTrustSection />
        <EnterpriseSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
