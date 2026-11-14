import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig, OffthreadVideo, staticFile } from 'remotion';
import { TZERO_COLORS } from '../types';

export const NineStarsHookScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Floating text entrance
  const textSpring = spring({ frame, fps, config: { damping: 13 } });

  // 9 stars spotlight reveals around frame 60 (2 seconds in)
  const spotlightSpring = spring({
    frame: frame - 55,
    fps,
    config: { damping: 12, mass: 0.8 },
  });

  const spotlightOpacity = interpolate(frame - 55, [0, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Outro transition cue around frame 210
  const transitionZoom = interpolate(frame, [210, 240], [1, 1.25], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const transitionFade = interpolate(frame, [225, 240], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: "'Outfit', 'Inter', sans-serif",
        color: TZERO_COLORS.textMain,
        padding: '0 80px',
        width: '100%',
        height: '100%',
        gap: 60,
        opacity: transitionFade,
        transform: `scale(${transitionZoom})`,
      }}
    >
      {/* Left Column: Viral POV Text & 9 Stars Highlight */}
      <div
        style={{
          flex: 1.2,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          transform: `scale(${textSpring})`,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            background: 'rgba(244, 63, 94, 0.15)',
            border: `1px solid ${TZERO_COLORS.rose}`,
            padding: '8px 20px',
            borderRadius: 30,
            color: TZERO_COLORS.rose,
            fontSize: 18,
            fontWeight: 700,
            letterSpacing: 2,
            marginBottom: 20,
            width: 'fit-content',
            boxShadow: '0 0 20px rgba(244, 63, 94, 0.3)',
          }}
        >
          <span>🔥</span>
          <span>DEV STRUGGLE IS REAL</span>
        </div>

        <h1
          style={{
            fontSize: 54,
            fontWeight: 900,
            lineHeight: 1.15,
            margin: '0 0 24px 0',
            color: '#f8fafc',
          }}
        >
          POV: You built an AI algorithm that cuts prompt bills by{' '}
          <span
            style={{
              color: TZERO_COLORS.cyan,
              textShadow: '0 0 30px rgba(0, 240, 255, 0.6)',
            }}
          >
            95%
          </span>
          ...
        </h1>

        {/* 100 Stars Milestone Box */}
        {frame >= 50 && (
          <div
            style={{
              transform: `scale(${spotlightSpring})`,
              opacity: spotlightOpacity,
              background: 'rgba(15, 23, 42, 0.95)',
              border: `2px solid ${TZERO_COLORS.amber}`,
              borderRadius: 18,
              padding: '24px 30px',
              boxShadow: '0 10px 40px rgba(245, 158, 11, 0.25)',
              marginBottom: 20,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 8 }}>
              <span style={{ fontSize: 36 }}>⭐</span>
              <span style={{ fontSize: 36, fontWeight: 900, color: TZERO_COLORS.amber, fontFamily: 'monospace' }}>
                Road to 100 Stars Milestone
              </span>
              <span style={{ fontSize: 32 }}>🚀</span>
            </div>
            <p style={{ margin: 0, fontSize: 18, color: TZERO_COLORS.textMuted }}>
              Empirical AST engine, 58 MCP tools, 352 passing tests... Help us reach 100 stars!
            </p>
          </div>
        )}

        <div style={{ fontSize: 24, fontWeight: 700, color: TZERO_COLORS.cyan }}>
          Let me show you why this is actually insane 👇
        </div>
      </div>

      {/* Right Column: Real Footage Container */}
      <div
        style={{
          flex: 0.9,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <div
          style={{
            width: 380,
            height: 680,
            borderRadius: 36,
            overflow: 'hidden',
            border: '4px solid rgba(0, 240, 255, 0.4)',
            boxShadow: '0 25px 60px rgba(0, 0, 0, 0.9), 0 0 40px rgba(0, 240, 255, 0.3)',
            background: '#000',
            position: 'relative',
          }}
        >
          {/* Real Phone Recording Video (CFR 30fps) */}
          <OffthreadVideo
            src={staticFile('TZERO_cfr.mp4')}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
            startFrom={0}
            endAt={240}
          />

          {/* Neon corner overlay badge */}
          <div
            style={{
              position: 'absolute',
              bottom: 18,
              left: 18,
              right: 18,
              background: 'rgba(3, 7, 18, 0.88)',
              backdropFilter: 'blur(10px)',
              borderRadius: 12,
              padding: '10px 14px',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span style={{ fontSize: 13, fontWeight: 700, color: '#f8fafc' }}>
              toprakahmetaydogmus/TZeroAlgorithm
            </span>
            <span style={{ fontSize: 13, fontWeight: 800, color: TZERO_COLORS.amber }}>
              ⭐ 9
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
