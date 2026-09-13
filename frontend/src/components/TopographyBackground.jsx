import React, { useEffect, useRef } from 'react';

/**
 * TopographyBackground — A high-performance, subtle canvas-based
 * topographic contour line background inspired by React Bits Topography/Threads.
 *
 * Features:
 * - Ultra-subtle geographic contour lines in warm stone tones
 * - Responsive cursor deflection (smooth lerp)
 * - Zero layout shift or text readability impact (pointer-events: none)
 * - Automatically freezes into a static elegant frame on touch / prefers-reduced-motion
 * - Adapts to light/dark theme dynamically
 */
export default function TopographyBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isFinePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

    let width = 0;
    let height = 0;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);
    let animId = null;
    let time = 0;

    // Mouse coordinates (normalized & smoothed)
    let mouse = { x: -1000, y: -1000, targetX: -1000, targetY: -1000 };

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.parentElement ? canvas.parentElement.clientWidth : window.innerWidth;
      height = canvas.parentElement ? canvas.parentElement.clientHeight : window.innerHeight;
      dpr = Math.min(window.devicePixelRatio || 1, 2);

      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      ctx.scale(dpr, dpr);

      // Re-draw immediately on resize
      drawContours(time);
    };

    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      mouse.targetX = e.clientX - rect.left;
      mouse.targetY = e.clientY - rect.top;
    };

    const handleMouseLeave = () => {
      mouse.targetX = -1000;
      mouse.targetY = -1000;
    };

    // Determine contour colors based on current document theme (subtle, low-opacity)
    const getStrokeColor = (index, total) => {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      const alphaBase = isDark ? 0.035 : 0.055;
      const alphaVar = Math.sin((index / total) * Math.PI) * (isDark ? 0.02 : 0.03);
      const alpha = Math.max(0.015, alphaBase + alphaVar);

      return isDark
        ? `rgba(214, 208, 196, ${alpha.toFixed(3)})`
        : `rgba(95, 87, 76, ${alpha.toFixed(3)})`;
    };

    // Render topographic contour lines
    const drawContours = (t) => {
      ctx.clearRect(0, 0, width, height);

      const numLines = Math.min(22, Math.max(12, Math.floor(height / 36)));
      const stepY = height / (numLines + 1);

      // Smooth mouse interpolation
      mouse.x += (mouse.targetX - mouse.x) * 0.05;
      mouse.y += (mouse.targetY - mouse.y) * 0.05;

      for (let i = 0; i < numLines; i++) {
        const baseY = stepY * (i + 1);
        ctx.beginPath();
        ctx.lineWidth = i % 4 === 0 ? 1.4 : 0.9;
        ctx.strokeStyle = getStrokeColor(i, numLines);

        if (i % 3 === 0) {
          ctx.setLineDash([4, 6]);
        } else {
          ctx.setLineDash([]);
        }

        const segments = Math.max(30, Math.floor(width / 24));
        const stepX = width / segments;

        for (let j = 0; j <= segments; j++) {
          const x = j * stepX;

          // Topographic multi-frequency elevation equation
          const freq1 = 0.0028;
          const freq2 = 0.0055;
          const freq3 = 0.0012;

          let yOffset =
            Math.sin(x * freq1 + i * 0.45 + t * 0.4) * 16 +
            Math.cos(x * freq2 - i * 0.35 + t * 0.25) * 10 +
            Math.sin(x * freq3 + t * 0.15) * 8;

          // Mouse deflection field: gentle displacement within radius
          if (mouse.x > -500 && mouse.y > -500) {
            const dx = x - mouse.x;
            const dy = baseY - mouse.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const radius = 220;

            if (dist < radius) {
              const force = Math.cos((dist / radius) * (Math.PI / 2));
              yOffset += (dy / (dist || 1)) * force * 14;
            }
          }

          const y = baseY + yOffset;

          if (j === 0) {
            ctx.moveTo(x, y);
          } else {
            // Smooth curve
            ctx.lineTo(x, y);
          }
        }

        ctx.stroke();
      }
    };

    // Initialize dimensions
    handleResize();
    window.addEventListener('resize', handleResize);

    // If reduced motion or touch pointer, draw one static frame and stop
    if (prefersReducedMotion || !isFinePointer) {
      drawContours(0);
      return () => {
        window.removeEventListener('resize', handleResize);
      };
    }

    // Interactive desktop animation loop
    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    document.addEventListener('mouseleave', handleMouseLeave);

    const loop = () => {
      time += 0.002;
      drawContours(time);
      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
      if (animId) cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <div className="topography-canvas-wrapper" aria-hidden="true">
      <canvas ref={canvasRef} className="topography-canvas" />
    </div>
  );
}
