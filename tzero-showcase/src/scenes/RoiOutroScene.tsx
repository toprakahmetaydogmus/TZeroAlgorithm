import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { TZERO_COLORS } from '../types';

export const RoiOutroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const containerSpring = spring({ frame, fps, config: { damping: 14 } });

  // Annual savings counter animation up to $419,001
  const savingsNumber = interpolate(frame, [10, 70], [0, 419001], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Terminal typing animation for pip install tzero-mcp
  const commandText = 'pip install tzero-mcp';
  const charsShown = Math.min(
    commandText.length,
    Math.floor(interpolate(frame, [50, 95], [0, commandText.length], { extrapolateLeft: 'clamp' }))
  );
  const typedCommand = commandText.substring(0, charsShown);
  const cursorBlink = Math.floor(frame / 12) % 2 === 0;

  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: "'Outfit', 'Inter', sans-serif",
        color: TZERO_COLORS.textMain,
        transform: `scale(${containerSpring})`,
        padding: '0 60px',
        width: '100%',
        height: '100%',
      }}
    >
      <div
        style={{
          color: TZERO_COLORS.emerald,
          fontSize: 18,
          fontWeight: 700,
          letterSpacing: 4,
          textTransform: 'uppercase',
          marginBottom: 8,
        }}
      >
        PROVEN FINANCIAL ROI
      </div>

      <h2 style={{ fontSize: 44, fontWeight: 800, margin: '0 0 16px 0', color: '#f8fafc' }}>
        Net Annual Dollar Savings for Engineering Teams
      </h2>

      {/* Big ROI Counter */}
      <div
        style={{
          fontSize: 90,
          fontWeight: 900,
          fontFamily: 'monospace',
          color: TZERO_COLORS.emerald,
          textShadow: '0 0 50px rgba(16, 185, 129, 0.6)',
          marginBottom: 8,
          letterSpacing: '-1px',
        }}
      >
        ${Math.round(savingsNumber).toLocaleString()} / YR
      </div>
      <div style={{ color: TZERO_COLORS.textMuted, fontSize: 18, marginBottom: 36 }}>
        Benchmark: 8-Developer Squad on Claude 3.5 Sonnet (15,000 Prompts/Mo)
      </div>

      {/* Terminal Box */}
      <div
        style={{
          width: '100%',
          maxWidth: 720,
          background: '#090d16',
          border: '1px solid rgba(0, 240, 255, 0.35)',
          borderRadius: 14,
          overflow: 'hidden',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.8), 0 0 30px rgba(0, 240, 255, 0.2)',
          marginBottom: 36,
        }}
      >
        {/* Terminal Header */}
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.95)',
            padding: '12px 18px',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#f43f5e' }} />
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#f59e0b' }} />
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#10b981' }} />
          <span style={{ color: '#94a3b8', fontSize: 13, marginLeft: 8, fontFamily: 'monospace' }}>
            bash — 1-click install
          </span>
        </div>

        {/* Terminal Body */}
        <div style={{ padding: '24px 28px', fontFamily: 'monospace', fontSize: 24, color: '#e2e8f0' }}>
          <span style={{ color: TZERO_COLORS.cyan }}>$ </span>
          <span>{typedCommand}</span>
          <span style={{ color: TZERO_COLORS.cyan, opacity: cursorBlink ? 1 : 0 }}>_</span>
        </div>
      </div>

      {/* Compatibility Badge Bar */}
      <div style={{ display: 'flex', gap: 14, marginBottom: 28 }}>
        {['Cursor', 'Claude Desktop', 'Windsurf', 'Cline', 'Antigravity IDE', 'Standalone Windows .exe'].map((agent) => (
          <div
            key={agent}
            style={{
              background: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: 20,
              padding: '6px 16px',
              fontSize: 14,
              fontWeight: 600,
              color: '#cbd5e1',
            }}
          >
            {agent}
          </div>
        ))}
      </div>

      {/* Star Callout & Outro URL */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
        <div style={{ fontSize: 22, fontWeight: 800, color: '#f59e0b', letterSpacing: 1 }}>
          ⭐ Help us reach our 100 Stars Milestone — Star the repo &amp; try it free!
        </div>
        <div style={{ fontSize: 18, fontWeight: 600, color: TZERO_COLORS.cyan }}>
          github.com/toprakahmetaydogmus/TZeroAlgorithm • tzero-indol.vercel.app
        </div>
      </div>
    </div>
  );
};
