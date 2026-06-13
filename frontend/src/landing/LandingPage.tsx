import React, { useRef, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Scene from './Scene';
import ScrollStory from './ScrollStory';
import './LandingPage.css';

const STATS = [
  { label: 'Batteries Retiring by 2030', value: '40M+', color: '#4d8eff' },
  { label: 'Second-Life Energy Potential', value: '120 GWh', color: '#4edea3' },
  { label: 'CO₂ Reduction Potential', value: '8.2M', unit: 'tonnes', color: '#f59e0b' },
];

const SECTIONS = [
  {
    num: '01', title: "India's Battery Crisis",
    desc: "By 2030, over 40 million EV and industrial batteries will reach end-of-first-life. Without intelligent systems, they become hazardous waste — leaching lithium, cobalt, and nickel into groundwater.",
    accent: '#ff5451',
  },
  {
    num: '02', title: 'Battery Aadhaar Identity',
    desc: "Every battery receives a unique 21-character identity — its Aadhaar. This QR-scannable passport tracks chemistry, manufacturer, health, and lifecycle events from birth to responsible end-of-life.",
    accent: '#4d8eff',
  },
  {
    num: '03', title: 'AI-Powered Assessment',
    desc: "Our ML engine analyzes 18 telemetry dimensions — cycle degradation, thermal exposure, internal resistance growth — to predict remaining useful life and assign a grade from S (pristine) to D (end-of-life).",
    accent: '#06b6d4',
  },
  {
    num: '04', title: 'Deployment Intelligence',
    desc: "Grade-matched routing algorithm considers proximity, demand capacity, chemistry compatibility, and grid requirements to find the optimal second-life deployment — from solar storage to rural microgrids.",
    accent: '#4edea3',
  },
  {
    num: '05', title: 'Environmental Impact',
    desc: "Every battery diverted to second-life saves 65 kg of CO₂. VoltLife transforms waste into infrastructure — powering schools, health centers, telecom towers, and solar installations across India.",
    accent: '#f59e0b',
  },
];

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [scrollY, setScrollY] = useState(0);
  const heroRef = useRef<HTMLDivElement>(null);
  const [hasWebGL, setHasWebGL] = useState(false);
  const [activeSection, setActiveSection] = useState<string>('01');
  const sectionRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  useEffect(() => {
    // Detect WebGL support
    try {
      const canvas = document.createElement('canvas');
      const supported = !!(
        window.WebGLRenderingContext &&
        (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
      );
      setHasWebGL(supported);
    } catch (e) {
      setHasWebGL(false);
    }
  }, []);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const num = entry.target.getAttribute('data-section-num');
            if (num) {
              setActiveSection(num);
            }
          }
        });
      },
      {
        root: null,
        rootMargin: '-30% 0px -30% 0px',
        threshold: 0.1,
      }
    );

    Object.values(sectionRefs.current).forEach((ref) => {
      if (ref) observer.observe(ref);
    });

    return () => {
      observer.disconnect();
    };
  }, [hasWebGL]);

  return (
    <div className="landing">
      {/* 3D Cinematic Backdrop (Conditional on WebGL support) */}
      {hasWebGL && (
        <Scene>
          <ScrollStory />
        </Scene>
      )}

      {/* Navigation */}
      <nav className={`landing__nav ${scrollY > 50 ? 'landing__nav--scrolled' : ''}`}>
        <div className="landing__nav-inner">
          <div className="landing__logo">
            <span className="landing__logo-bolt">⚡</span>
            <span className="landing__logo-text">VoltLife</span>
          </div>
          <button className="landing__cta-nav" onClick={() => navigate('/dashboard')}>
            Launch Platform →
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section className="landing__hero" ref={heroRef}>
        <div className="landing__hero-bg">
          {/* Particle grid effect (only if not rendering 3D R3F scene) */}
          {!hasWebGL && (
            <div className="landing__particles">
              {Array.from({ length: 60 }).map((_, i) => (
                <div
                  key={i}
                  className="landing__particle"
                  style={{
                    left: `${Math.random() * 100}%`,
                    top: `${Math.random() * 100}%`,
                    animationDelay: `${Math.random() * 5}s`,
                    animationDuration: `${3 + Math.random() * 4}s`,
                    opacity: 0.1 + Math.random() * 0.4,
                  }}
                />
              ))}
            </div>
          )}

          {/* Glow orbs */}
          <div className="landing__orb landing__orb--blue" style={{ transform: `translateY(${scrollY * 0.3}px)` }} />
          <div className="landing__orb landing__orb--green" style={{ transform: `translateY(${scrollY * 0.2}px)` }} />
        </div>

        <div className="landing__hero-content">
          <div className="landing__hero-badge text-label-caps">INDIA'S BATTERY OPERATING SYSTEM</div>
          <h1 className="landing__hero-title">
            Every Battery<br />
            <span className="landing__hero-gradient">Deserves a Second Life</span>
          </h1>
          <p className="landing__hero-subtitle">
            AI-powered lifecycle management for India's 40 million retiring batteries. 
            Assess. Deploy. Impact.
          </p>
          <div className="landing__hero-actions">
            <button className="landing__cta-primary" onClick={() => navigate('/dashboard')}>
              Enter Mission Control
            </button>
            <button className="landing__cta-secondary" onClick={() => navigate('/assess')}>
              Try Assessment →
            </button>
          </div>
        </div>

        {/* 2D Fallback Battery Wireframe (Only shown if WebGL is not available) */}
        {!hasWebGL && (
          <div className="landing__battery-visual">
            <div className="landing__battery-frame">
              <div className="landing__battery-terminal" />
              <div className="landing__battery-body">
                <div className="landing__battery-cells">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <div
                      key={i}
                      className="landing__battery-cell"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
                <div className="landing__battery-scan">
                  <div className="landing__scan-line" />
                </div>
              </div>
            </div>
            <div className="landing__battery-label text-data-md">
              BPAN: INFOAN480415032400231
            </div>
          </div>
        )}
      </section>

      {/* Stats bar */}
      <section className="landing__stats">
        {STATS.map((stat) => (
          <div key={stat.label} className="landing__stat">
            <div className="landing__stat-value text-data-lg" style={{ color: stat.color }}>
              {stat.value}{stat.unit && <span className="landing__stat-unit"> {stat.unit}</span>}
            </div>
            <div className="text-label-caps">{stat.label}</div>
          </div>
        ))}
      </section>

      {/* Story sections */}
      <section className="landing__story">
        {SECTIONS.map((section) => (
          <div
            key={section.num}
            data-section-num={section.num}
            ref={(el) => {
              sectionRefs.current[section.num] = el;
            }}
            className={`landing__section ${activeSection === section.num ? 'landing__section--active' : ''}`}
          >
            <div className="landing__section-num text-data-lg" style={{ color: section.accent }}>
              {section.num}
            </div>
            <div className="landing__section-content">
              <h2 className="landing__section-title">{section.title}</h2>
              <div className="landing__section-accent" style={{ background: section.accent }} />
              <p className="landing__section-desc">{section.desc}</p>
            </div>
          </div>
        ))}
      </section>

      {/* Final CTA */}
      <section className="landing__final-cta">
        <h2 className="landing__final-title">Ready to Transform India's Battery Future?</h2>
        <p className="text-body-lg text-on-surface-variant" style={{ maxWidth: 600, textAlign: 'center' }}>
          Join the mission to give every battery a dignified second life. 
          Explore the platform and see the impact in real time.
        </p>
        <button className="landing__cta-primary" onClick={() => navigate('/dashboard')}>
          Launch VoltLife →
        </button>
      </section>

      {/* Footer */}
      <footer className="landing__footer">
        <div className="landing__footer-inner">
          <span>© 2026 VoltLife — India's Battery OS</span>
          <span className="text-label-caps">Built for India 2030</span>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
