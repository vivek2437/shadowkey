import React, { useEffect, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { 
  AlertTriangle, 
  KeyRound, 
  Fingerprint, 
  Mic, 
  Brain, 
  ShieldCheck, 
  TrendingUp,
  Building2,
  Scale,
  Zap,
  ArrowRight
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { AnimatedCharacters } from '@/components/ui/magnetic-text';

interface SectionProps {
  children: React.ReactNode;
  className?: string;
  id?: string;
}

const Section: React.FC<SectionProps> = ({ children, className = '', id }) => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section
      ref={ref}
      id={id}
      className={`scroll-section ${className}`}
    >
      <motion.div
        initial={{ opacity: 0, y: 60 }}
        animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 60 }}
        transition={{ duration: 0.8, ease: [0.25, 0.4, 0.25, 1] }}
        className="container mx-auto px-6"
      >
        {children}
      </motion.div>
    </section>
  );
};

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  delay?: number;
}

const FeatureCard: React.FC<FeatureCardProps> = ({ icon, title, description, delay = 0 }) => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 40 }}
      transition={{ duration: 0.6, delay, ease: [0.25, 0.4, 0.25, 1] }}
      className="card-enterprise-hover p-8"
    >
      <div className="w-12 h-12 rounded-xl bg-accent flex items-center justify-center mb-6">
        {icon}
      </div>
      <h3 className="text-xl font-semibold text-foreground mb-3">{title}</h3>
      <p className="text-muted-foreground">{description}</p>
    </motion.div>
  );
};

// Section 1: The Problem
export const ProblemSection: React.FC = () => (
  <Section id="problem" className="bg-secondary/30">
    <div className="max-w-4xl mx-auto text-center">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        whileInView={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5 }}
        viewport={{ once: true }}
        className="w-20 h-20 rounded-2xl bg-destructive/10 flex items-center justify-center mx-auto mb-8"
      >
        <AlertTriangle className="w-10 h-10 text-destructive" />
      </motion.div>
      
      <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-6">
        <AnimatedCharacters text="Passwords Are Broken" />
      </h2>
      
      <p className="text-xl text-muted-foreground mb-12 max-w-2xl mx-auto">
        Static authentication fails in a dynamic threat landscape. One-time verification 
        leaves systems vulnerable to session hijacking, credential theft, and insider threats.
      </p>

      <div className="grid md:grid-cols-3 gap-6">
        <FeatureCard
          icon={<KeyRound className="w-6 h-6 text-primary" />}
          title="81% of Breaches"
          description="Involve compromised credentials. Passwords alone can't protect your enterprise."
          delay={0.1}
        />
        <FeatureCard
          icon={<AlertTriangle className="w-6 h-6 text-primary" />}
          title="Static Verification"
          description="Log in once, access everything. No continuous validation of user identity."
          delay={0.2}
        />
        <FeatureCard
          icon={<TrendingUp className="w-6 h-6 text-primary" />}
          title="$4.45M Average"
          description="Cost of a data breach in 2023. The stakes have never been higher."
          delay={0.3}
        />
      </div>
    </div>
  </Section>
);

// Section 2: The Technology
export const TechnologySection: React.FC = () => (
  <Section id="technology">
    <div className="max-w-5xl mx-auto">
      <div className="text-center mb-16">
        <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-6">
          <AnimatedCharacters text="Multi-Modal Biometrics" />
        </h2>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Behavioral biometrics create a unique identity profile that's impossible to replicate.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        <motion.div
          initial={{ opacity: 0, x: -40 }}
          whileInView={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
          className="card-enterprise p-8"
        >
          <div className="flex items-center gap-4 mb-6">
            <div className="w-14 h-14 rounded-xl bg-accent flex items-center justify-center">
              <Fingerprint className="w-7 h-7 text-primary" />
            </div>
            <h3 className="text-2xl font-semibold text-foreground">Keystroke Dynamics</h3>
          </div>
          <p className="text-muted-foreground mb-6">
            Every person types with a unique rhythm. Our ML models analyze timing patterns, 
            dwell time, and flight time to create a behavioral fingerprint.
          </p>
          <ul className="space-y-3">
            {['Typing rhythm analysis', 'Pattern deviation detection', 'Real-time scoring'].map((item, i) => (
              <li key={i} className="flex items-center gap-3 text-foreground">
                <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                {item}
              </li>
            ))}
          </ul>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 40 }}
          whileInView={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          viewport={{ once: true }}
          className="card-enterprise p-8"
        >
          <div className="flex items-center gap-4 mb-6">
            <div className="w-14 h-14 rounded-xl bg-accent flex items-center justify-center">
              <Mic className="w-7 h-7 text-primary" />
            </div>
            <h3 className="text-2xl font-semibold text-foreground">Voice Biometrics</h3>
          </div>
          <p className="text-muted-foreground mb-6">
            Voice patterns are as unique as fingerprints. Our system analyzes vocal characteristics 
            to verify identity without interrupting workflows.
          </p>
          <ul className="space-y-3">
            {['Voiceprint enrollment', 'Continuous verification', 'Liveness detection'].map((item, i) => (
              <li key={i} className="flex items-center gap-3 text-foreground">
                <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                {item}
              </li>
            ))}
          </ul>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
        viewport={{ once: true }}
        className="mt-8 card-enterprise p-8 text-center"
      >
        <div className="w-14 h-14 rounded-xl bg-accent flex items-center justify-center mx-auto mb-6">
          <Brain className="w-7 h-7 text-primary" />
        </div>
        <h3 className="text-2xl font-semibold text-foreground mb-4">Deep Learning Engine</h3>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          Our Phase-5 neural networks continuously learn and adapt to subtle changes in behavior, 
          reducing false positives while maintaining ironclad security.
        </p>
      </motion.div>
    </div>
  </Section>
);

// Section 3: Zero-Trust Architecture
export const ZeroTrustSection: React.FC = () => (
  <Section id="zero-trust" className="bg-secondary/30">
    <div className="max-w-5xl mx-auto">
      <div className="text-center mb-16">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          whileInView={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
          viewport={{ once: true }}
          className="w-20 h-20 rounded-2xl bg-accent flex items-center justify-center mx-auto mb-8"
        >
          <ShieldCheck className="w-10 h-10 text-primary" />
        </motion.div>
        <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-6">
          <AnimatedCharacters text="Zero-Trust Architecture" />
        </h2>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Never trust, always verify. Continuous authentication for every action.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-12 items-center">
        <motion.div
          initial={{ opacity: 0, x: -40 }}
          whileInView={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
        >
          <div className="space-y-8">
            <div className="flex gap-4">
              <div className="w-12 h-12 rounded-xl bg-accent flex items-center justify-center shrink-0">
                <span className="text-primary font-bold">1</span>
              </div>
              <div>
                <h4 className="text-lg font-semibold text-foreground mb-2">Continuous Verification</h4>
                <p className="text-muted-foreground">Every interaction is validated against the user's behavioral profile in real-time.</p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="w-12 h-12 rounded-xl bg-accent flex items-center justify-center shrink-0">
                <span className="text-primary font-bold">2</span>
              </div>
              <div>
                <h4 className="text-lg font-semibold text-foreground mb-2">Risk-Based Decisions</h4>
                <p className="text-muted-foreground">Dynamic access control based on trust scores, location, and behavior patterns.</p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="w-12 h-12 rounded-xl bg-accent flex items-center justify-center shrink-0">
                <span className="text-primary font-bold">3</span>
              </div>
              <div>
                <h4 className="text-lg font-semibold text-foreground mb-2">Adaptive Response</h4>
                <p className="text-muted-foreground">Automatic escalation to step-up authentication when anomalies are detected.</p>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          viewport={{ once: true }}
          className="relative"
        >
          <div className="card-enterprise p-8 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="relative">
              <div className="flex items-center justify-between mb-6">
                <span className="text-sm font-medium text-muted-foreground">Trust Score</span>
                <span className="text-2xl font-bold text-success">94%</span>
              </div>
              <div className="h-3 bg-secondary rounded-full overflow-hidden mb-6">
                <motion.div
                  initial={{ width: 0 }}
                  whileInView={{ width: '94%' }}
                  transition={{ duration: 1, delay: 0.5 }}
                  viewport={{ once: true }}
                  className="h-full bg-gradient-to-r from-success to-primary rounded-full"
                />
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="p-3 bg-secondary rounded-lg">
                  <span className="text-muted-foreground">Keystroke</span>
                  <p className="font-semibold text-foreground">97%</p>
                </div>
                <div className="p-3 bg-secondary rounded-lg">
                  <span className="text-muted-foreground">Voice</span>
                  <p className="font-semibold text-foreground">91%</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  </Section>
);

// Section 4: Enterprise Value
export const EnterpriseSection: React.FC = () => (
  <Section id="enterprise">
    <div className="max-w-5xl mx-auto">
      <div className="text-center mb-16">
        <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-6">
          <AnimatedCharacters text="Enterprise-Ready" />
        </h2>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Built for scale, designed for compliance, ready for deployment.
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <FeatureCard
          icon={<Building2 className="w-6 h-6 text-primary" />}
          title="Scalability"
          description="Handle millions of authentications per day with our distributed architecture."
          delay={0.1}
        />
        <FeatureCard
          icon={<Scale className="w-6 h-6 text-primary" />}
          title="Compliance"
          description="SOC 2 Type II, GDPR, HIPAA, and CCPA compliant out of the box."
          delay={0.2}
        />
        <FeatureCard
          icon={<Zap className="w-6 h-6 text-primary" />}
          title="Integration"
          description="REST APIs, SDKs, and pre-built integrations for major identity providers."
          delay={0.3}
        />
      </div>
    </div>
  </Section>
);

// Section 5: CTA
export const CTASection: React.FC = () => (
  <Section id="cta" className="bg-primary/5">
    <div className="max-w-3xl mx-auto text-center">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        whileInView={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5 }}
        viewport={{ once: true }}
        className="w-20 h-20 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-8"
      >
        <ShieldCheck className="w-10 h-10 text-primary" />
      </motion.div>
      
      <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-6">
        <AnimatedCharacters text="Ready to Secure Your Future?" />
      </h2>
      
      <p className="text-xl text-muted-foreground mb-10">
        Join industry leaders who trust ShadowKey for continuous, intelligent authentication.
      </p>

      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <Button
          asChild
          size="lg"
          className="bg-primary hover:bg-primary/90 text-primary-foreground px-8 py-6 text-lg rounded-xl glow-primary"
        >
          <Link to="/auth/sign-up">
            Request Access
            <ArrowRight className="ml-2 w-5 h-5" />
          </Link>
        </Button>
        <Button
          asChild
          variant="outline"
          size="lg"
          className="border-border hover:bg-secondary px-8 py-6 text-lg rounded-xl"
        >
          <Link to="/auth/sign-in">
            Sign In
          </Link>
        </Button>
      </div>
    </div>
  </Section>
);

export default {
  ProblemSection,
  TechnologySection,
  ZeroTrustSection,
  EnterpriseSection,
  CTASection,
};
