import React, { useEffect, useRef } from 'react';
import { ShieldCheck } from 'lucide-react';
import TopographyBackground from './TopographyBackground';

export default function HeroSection() {
  const backdropRef = useRef(null);
  const waypointsRef = useRef(null);

  // Subtle Mouse Parallax Effect (Desktop only, respects reduced motion)
  useEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isFinePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

    if (prefersReducedMotion || !isFinePointer) return;

    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;
    let animId = null;

    const handleMouseMove = (e) => {
      const centerX = window.innerWidth / 2;
      const centerY = window.innerHeight / 2;
      targetX = (e.clientX - centerX) / centerX; // -1 to 1
      targetY = (e.clientY - centerY) / centerY; // -1 to 1
    };

    const animate = () => {
      // Smooth lerp
      currentX += (targetX - currentX) * 0.05;
      currentY += (targetY - currentY) * 0.05;

      if (backdropRef.current) {
        backdropRef.current.style.transform = `translate3d(${(currentX * 3.5).toFixed(2)}px, ${(currentY * 2.5).toFixed(2)}px, 0)`;
      }

      if (waypointsRef.current) {
        waypointsRef.current.style.transform = `translate3d(${(currentX * 1.5).toFixed(2)}px, ${(currentY * 1.2).toFixed(2)}px, 0)`;
      }

      animId = requestAnimationFrame(animate);
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    animId = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      if (animId) cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <section className="hero-landing">
      {/* React Bits-style Topographic Canvas Contour Background */}
      <TopographyBackground />

      {/* Subtle Background Route & Map Contour Art */}
      <div className="hero-route-backdrop" aria-hidden="true">
        <svg
          viewBox="0 0 1000 200"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="hero-backdrop-svg"
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            <linearGradient id="heroRouteGradient" x1="0" y1="0" x2="1000" y2="0" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0" />
              <stop offset="3%" stopColor="#3b82f6" stopOpacity="0.38" />
              <stop offset="7.5%" stopColor="#15803d" stopOpacity="0.65" />
              <stop offset="42%" stopColor="#3b82f6" stopOpacity="0.45" />
              <stop offset="82%" stopColor="#3b82f6" stopOpacity="0.45" />
              <stop offset="92.5%" stopColor="#dc2626" stopOpacity="0.65" />
              <stop offset="97%" stopColor="#3b82f6" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
            </linearGradient>
            <linearGradient id="contourFade" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#78716c" stopOpacity="0.08" />
              <stop offset="100%" stopColor="#78716c" stopOpacity="0.01" />
            </linearGradient>
            <filter id="glowFilter" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Primary Route Line & Animated Pulses Group (Parallax Layer) */}
          <g ref={backdropRef} className="hero-route-paths-group">
            {/* Faint road contour lines spanning full breadth */}
            <path
              d="M -40 85 C 180 35, 320 130, 560 75 C 800 25, 920 110, 1040 80"
              stroke="url(#contourFade)"
              strokeWidth="1"
              strokeDasharray="4 6"
            />
            <path
              d="M -40 130 C 160 85, 330 165, 580 125 C 830 85, 920 155, 1040 130"
              stroke="url(#contourFade)"
              strokeWidth="1"
            />

            {/* Primary Flowing Journey Route Path — Connecting Origin to Destination */}
            <path
              id="heroJourneyPath"
              d="M -40 50 L 75 50 C 180 50, 260 98, 380 98 C 500 98, 580 142, 680 146 C 780 150, 840 155, 925 155 L 1040 155"
              stroke="url(#heroRouteGradient)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />

            {/* Subtle Traveling Flow Particle along Route Path */}
            <circle r="3.2" fill="#3b82f6" opacity="0.65" filter="url(#glowFilter)">
              <animateMotion
                dur="16s"
                repeatCount="indefinite"
                path="M -40 50 L 75 50 C 180 50, 260 98, 380 98 C 500 98, 580 142, 680 146 C 780 150, 840 155, 925 155 L 1040 155"
              />
            </circle>
            <circle r="1.6" fill="#ffffff" opacity="0.85">
              <animateMotion
                dur="16s"
                repeatCount="indefinite"
                path="M -40 50 L 75 50 C 180 50, 260 98, 380 98 C 500 98, 580 142, 680 146 C 780 150, 840 155, 925 155 L 1040 155"
              />
            </circle>
          </g>

          {/* Secondary Layer: Interactive Landmarks & Waypoints (Parallax Layer) */}
          <g ref={waypointsRef} className="hero-waypoints-group">
            {/* 1. Clearly Visible ORIGIN Marker on the Left Side of the Hero */}
            <g transform="translate(75, 50)" className="hero-origin-marker">
              <circle r="13" fill="#15803d" fillOpacity="0.1" />
              <circle r="8.5" fill="#fcfbf9" stroke="#15803d" strokeWidth="2.5" />
              <circle r="3.8" fill="#15803d" />
              <text
                x="0"
                y="-15"
                textAnchor="middle"
                fill="#15803d"
                fontSize="9.5"
                fontWeight="800"
                letterSpacing="0.09em"
                fontFamily="system-ui, sans-serif"
                className="hero-endpoint-text"
              >
                ORIGIN
              </text>
            </g>

            {/* Subtle mid-journey risk/waypoint points along the route */}
            <g transform="translate(400, 98)">
              <circle r="6" stroke="#ea580c" strokeWidth="1" strokeOpacity="0.35" fill="none" />
              <circle r="2.8" fill="#ea580c" fillOpacity="0.8" />
            </g>
            <g transform="translate(680, 146)">
              <polygon points="0,-3.5 3.5,0 0,3.5 -3.5,0" fill="#dc2626" fillOpacity="0.75" />
            </g>

            {/* 2. Clearly Visible DESTINATION Marker on the Right Side of the Hero (Muted Red/Coral) */}
            <g transform="translate(925, 155)" className="hero-dest-marker">
              <circle r="13" fill="#dc2626" fillOpacity="0.1" />
              <circle r="8.5" fill="#fcfbf9" stroke="#dc2626" strokeWidth="2.5" />
              <circle r="3.8" fill="#dc2626" />
              <text
                x="0"
                y="-15"
                textAnchor="middle"
                fill="#dc2626"
                fontSize="9.5"
                fontWeight="800"
                letterSpacing="0.09em"
                fontFamily="system-ui, sans-serif"
                className="hero-endpoint-text"
              >
                DESTINATION
              </text>
            </g>
          </g>
        </svg>
      </div>

      <div className="hero-content-stack">
        {/* Eyebrow / Brand Lockup Badge */}
        <div className="hero-eyebrow-badge">
          <ShieldCheck size={13} className="eyebrow-icon" />
          <span className="eyebrow-text">SAFE ROUTE AI</span>
          <span className="eyebrow-sep">·</span>
          <span className="eyebrow-sub">ROAD SAFETY RISK INTELLIGENCE</span>
        </div>

        {/* Hero Headline */}
        <h1 className="hero-headline">
          Know the road before you take it.
        </h1>

        {/* Supporting Copy */}
        <p className="hero-subhead">
          Enter your journey. See risky stretches ahead, understand why they're flagged, and know how to stay safer.
        </p>
      </div>
    </section>
  );
}
