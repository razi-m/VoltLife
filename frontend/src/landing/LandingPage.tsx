import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';

const SDG_GOALS = [
  { num: 7, title: 'Affordable & Clean Energy', color: '#FCC30B', icon: '☀', desc: 'Extending battery life multiplies clean energy access across rural India' },
  { num: 9, title: 'Industry, Innovation & Infrastructure', color: '#F36D25', icon: '⚙', desc: 'AI-powered grading and deployment builds resilient energy infrastructure' },
  { num: 12, title: 'Responsible Consumption & Production', color: '#BF8B2E', icon: '♻', desc: 'Second-life deployment diverts millions of batteries from landfills' },
  { num: 13, title: 'Climate Action', color: '#3F7E44', icon: '🌍', desc: 'Every redeployed battery saves 65 kg CO₂ — scaling to megatonnes by 2030' },
];

const STATS = [
  { value: '40M+', label: 'Batteries Retiring by 2030', color: '#4d8eff' },
  { value: '120 GWh', label: 'Second-Life Energy Potential', color: '#4edea3' },
  { value: '8.2M', label: 'Tonnes CO₂ Reduction', color: '#f59e0b' },
];

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [scrollY, setScrollY] = useState(0);
  const [activeGoal, setActiveGoal] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // No useEffect token clearing — handleRoleSelect manages tokens directly

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Rotate SDG highlights
  useEffect(() => {
    const interval = setInterval(() => setActiveGoal(g => (g + 1) % SDG_GOALS.length), 4000);
    return () => clearInterval(interval);
  }, []);

  // Particle canvas animation
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    const particles: { x: number; y: number; vx: number; vy: number; r: number; color: string; alpha: number }[] = [];
    const colors = ['#FCC30B', '#F36D25', '#BF8B2E', '#3F7E44', '#4d8eff', '#4edea3'];

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    for (let i = 0; i < 80; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        r: 1.5 + Math.random() * 2,
        color: colors[Math.floor(Math.random() * colors.length)],
        alpha: 0.15 + Math.random() * 0.35,
      });
    }

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.alpha;
        ctx.fill();
      }

      // Draw connections
      ctx.globalAlpha = 0.04;
      ctx.strokeStyle = '#4edea3';
      ctx.lineWidth = 0.5;
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }
      ctx.globalAlpha = 1;

      animId = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, []);

  const handleLaunch = () => {
    localStorage.setItem('user_role', 'seller');
    localStorage.setItem('supplier_token', 'demo_session');
    localStorage.setItem('supplier_username', 'Guest Seller');
    localStorage.setItem('supplier_company', 'Demo Corp');
    navigate('/dashboard');
  };

  return (
    <div className="landing">
      {/* Particle canvas background */}
      <canvas ref={canvasRef} className="landing__canvas" />

      {/* Gradient overlays */}
      <div className="landing__gradient-top" />
      <div className="landing__gradient-bottom" />

      {/* Nav */}
      <nav className={`landing__nav ${scrollY > 50 ? 'landing__nav--scrolled' : ''}`}>
        <div className="landing__nav-inner">
          <div className="landing__logo">
            <span className="landing__logo-bolt">⚡</span>
            <span className="landing__logo-text">VoltLife</span>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="landing__hero">
        <div className="landing__hero-content">
          <div className="landing__hero-badge">INDIA'S BATTERY OPERATING SYSTEM</div>
          <h1 className="landing__hero-title">
            Every Battery<br />
            <span className="landing__hero-gradient">Deserves a Second Life</span>
          </h1>
          <p className="landing__hero-subtitle">
            AI-powered lifecycle management for India's 40 million retiring batteries.
            Powering sustainable development through circular energy.
          </p>

          {/* SDG Goals - inline */}
          <div className="landing__sdg-grid landing__sdg-grid--hero">
            {SDG_GOALS.map((goal, i) => (
              <div
                key={goal.num}
                className={`landing__sdg-card ${activeGoal === i ? 'landing__sdg-card--active' : ''}`}
                onMouseEnter={() => setActiveGoal(i)}
              >
                <div className="landing__sdg-num" style={{ background: goal.color }}>
                  SDG {goal.num}
                </div>
                <div className="landing__sdg-icon">{goal.icon}</div>
                <h3 className="landing__sdg-card-title">{goal.title}</h3>
                <p className="landing__sdg-desc">{goal.desc}</p>
              </div>
            ))}
          </div>

          {/* Launch button */}
          <button className="landing__cta-primary landing__cta-primary--large" onClick={handleLaunch}>
            Launch Mission Control →
          </button>
        </div>
      </section>

      {/* Stats */}
      <section className="landing__stats">
        {STATS.map((s) => (
          <div key={s.label} className="landing__stat">
            <div className="landing__stat-value" style={{ color: s.color }}>{s.value}</div>
            <div className="landing__stat-label">{s.label}</div>
          </div>
        ))}
      </section>

      {/* Final CTA */}
      <section className="landing__final-cta">
        <h2 className="landing__final-title">Ready to Transform India's Battery Future?</h2>
        <p className="landing__final-sub">
          Join the mission to give every battery a dignified second life.
        </p>
        <button className="landing__cta-primary landing__cta-primary--large" onClick={handleLaunch}>
          Launch Mission Control →
        </button>
      </section>

      {/* Footer */}
      <footer className="landing__footer">
        <div className="landing__footer-inner">
          <span>© 2026 VoltLife — India's Battery OS</span>
          <span className="landing__footer-sdg">SDG 7 · 9 · 12 · 13</span>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
