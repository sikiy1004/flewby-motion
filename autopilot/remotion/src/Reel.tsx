import React, { useEffect, useState } from "react";
import {
  AbsoluteFill, Audio, Easing, OffthreadVideo, Sequence, continueRender, delayRender, interpolate, spring,
  staticFile, useCurrentFrame, useVideoConfig,
} from "remotion";
import type { Caption, Product, ReelProps, Scene } from "./types";

// ---------------------------------------------------------------- helpers
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const useSpring = (delay = 0, config: Record<string, number> = { damping: 13, mass: 0.6, stiffness: 140 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - delay, fps, config });
};
const Svg: React.FC<{ html: string; style?: React.CSSProperties }> = ({ html, style }) => (
  <div style={{ display: "inline-flex", ...style }} dangerouslySetInnerHTML={{ __html: html }} />
);
const yen = (n: number) => n.toLocaleString("ja-JP");

// ---------------------------------------------------------------- fonts / css
const useAssets = (glyphs: string) => {
  const [handle] = useState(() => delayRender("fonts and css", { timeoutInMilliseconds: 90000 }));
  useEffect(() => {
    const load = (href: string) =>
      new Promise<void>((resolve) => {
        const l = document.createElement("link");
        l.rel = "stylesheet";
        l.href = href;
        l.onload = () => resolve();
        l.onerror = () => resolve();
        document.head.appendChild(l);
      });
    (async () => {
      await Promise.all([load(staticFile("webfonts/webfonts.css")), load(staticFile("design.css"))]);
      const fams = ['900 40px "Zen Kaku Gothic New"', '700 40px "Zen Kaku Gothic New"', '400 40px "DM Serif Display"',
        'italic 400 40px "DM Serif Display"', '600 40px "Klee One"'];
      await Promise.all(fams.map((f) => document.fonts.load(f, glyphs || "あア亜Aa1").catch(() => null)));
      await document.fonts.ready;
      continueRender(handle);
    })();
  }, [handle, glyphs]);
};

// ---------------------------------------------------------------- background
const Background: React.FC<{ bgVideo?: string; hookEnd: number }> = ({ bgVideo, hookEnd }) => {
  const frame = useCurrentFrame();
  const t = frame / 30;
  return (
    <AbsoluteFill className="paper">
      <div style={{ position: "absolute", width: 980, height: 980, borderRadius: "50%", background: "var(--paper2)",
        right: -420 + Math.sin(t * 0.6) * 40, top: -300 + Math.cos(t * 0.5) * 30, opacity: 0.9 }} />
      <div style={{ position: "absolute", width: 640, height: 640, borderRadius: "50%", background: "var(--pop)", opacity: 0.22,
        left: -260 + Math.cos(t * 0.7) * 30, bottom: 380 + Math.sin(t * 0.4) * 40 }} />
      {bgVideo ? (
        <Sequence durationInFrames={hookEnd}>
          <AbsoluteFill style={{ opacity: interpolate(frame, [hookEnd - 8, hookEnd], [1, 0], clamp) }}>
            <OffthreadVideo src={staticFile(bgVideo)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(15,10,8,.62) 0%, rgba(15,10,8,.38) 48%, rgba(15,10,8,.15) 70%, var(--paper) 96%)" }} />
          </AbsoluteFill>
        </Sequence>
      ) : null}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- header & progress
const Header: React.FC<{ postNo: number; scenes: Scene[]; light: boolean }> = ({ postNo, scenes, light }) => {
  const frame = useCurrentFrame();
  const t = frame / 30;
  return (
    <div style={{ position: "absolute", left: 70, right: 170, top: 214, color: light ? "#fff" : "var(--ink)" }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 22 }}>
        {scenes.map((s, i) => {
          const p = interpolate(t, [s.start, s.start + s.duration], [0, 1], clamp);
          return (
            <div key={i} style={{ flex: 1, height: 9, borderRadius: 5, background: "var(--line)", overflow: "hidden" }}>
              <div style={{ width: `${p * 100}%`, height: "100%", background: "var(--ink)" }} />
            </div>
          );
        })}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ font: '400 40px "DM Serif Display"' }}>BIKADEN <i style={{ color: "var(--accent)" }}>Note</i>
          <span style={{ fontSize: 28, color: "var(--sub)", marginLeft: 14 }}>vol.{String(postNo).padStart(3, "0")}</span></span>
        <span className="pr">PR</span>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------- transition wipe
const Wipe: React.FC<{ at: number }> = ({ at }) => {
  const frame = useCurrentFrame();
  const f = frame - at;
  if (f < -7 || f > 7) return null;
  const x = interpolate(f, [-7, 7], [-1300, 1300], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{ position: "absolute", top: -300, bottom: -300, width: 900, left: 90 + x, background: "var(--accent)",
        transform: "skewX(-14deg)" }} />
      <div style={{ position: "absolute", top: -300, bottom: -300, width: 160, left: 90 + x - 200, background: "var(--pop)",
        transform: "skewX(-14deg)" }} />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- scenes
const AREA: React.CSSProperties = { position: "absolute", left: 70, right: 150, top: 350, height: 860 };

const Photo: React.FC<{ src: string; size: number; rot: number; style?: React.CSSProperties; cap?: string }> = ({ src, size, rot, style, cap }) => (
  <div className="polaroid" style={{ width: size, height: size + 32, transform: `rotate(${rot}deg)`, ...style }}>
    <img src={staticFile(src)} />
    {cap ? <div className="cap">{cap}</div> : null}
  </div>
);

const HookScene: React.FC<{ s: Scene; p: ReelProps }> = ({ s, p }) => {
  const frame = useCurrentFrame();
  const onVideo = !!p.bgVideo;
  const photos = s.photos || [];
  const stamp = useSpring(5, { damping: 9, mass: 0.6, stiffness: 160 });
  const big = useSpring(16);
  const art = useSpring(10);
  const chunks = s.hookChunks || [];
  return (
    <div style={{ ...AREA, transform: `scale(${interpolate(frame, [0, s.duration * 30], [1, 1.04])})`, transformOrigin: "40% 40%" }}>
      <div style={{ display: "flex", gap: 14, alignItems: "center", transform: `translateX(${interpolate(frame, [0, 10], [-600, 0], { ...clamp, easing: Easing.out(Easing.cubic) })}px)` }}>
        <span className="chip">{p.genre}</span><span className="chip line">{p.formatLabel}</span>
      </div>
      <div className="head" style={{ fontSize: s.hookSize || 118, lineHeight: 1.16, marginTop: 34, display: "flex", flexWrap: "wrap",
        color: onVideo ? "#fff" : "var(--ink)", textShadow: onVideo ? "0 4px 24px rgba(0,0,0,.45)" : undefined }}>
        {chunks.map((c, i) => {
          const sp = spring({ frame: frame - 2 - i * 3, fps: 30, config: { damping: 11, mass: 0.5, stiffness: 170 } });
          const sweep = interpolate(frame, [10 + i * 3, 18 + i * 3], [0, 100], clamp);
          return (
            <span key={i} style={{ display: "inline-block", transform: `translateY(${(1 - sp) * 60}px) scale(${0.7 + 0.3 * sp})`, opacity: sp,
              background: c.em ? `linear-gradient(transparent 56%, var(--pop) 56%, var(--pop) 90%, transparent 90%) no-repeat 0 0 / ${sweep}% 100%` : undefined }}>
              {c.text}
            </span>
          );
        })}
      </div>
      <div style={{ position: "absolute", left: -10, bottom: 70, display: "flex", alignItems: "flex-end", gap: 14,
        transform: `translateY(${(1 - big) * 300}px)`, opacity: big }}>
        <span style={{ font: 'italic 400 280px/0.8 "DM Serif Display"', color: "var(--accent)" }}>{s.bigN}</span>
        <span className="head" style={{ fontSize: 52, lineHeight: 1.25, paddingBottom: 12, color: onVideo ? "#fff" : "var(--ink)" }} dangerouslySetInnerHTML={{ __html: s.bigLabel || "" }} />
      </div>
      <div style={{ position: "absolute", right: -30, bottom: -10, width: 400, height: 400, transform: `scale(${art}) rotate(${(1 - art) * -30}deg)` }}>
        {photos.length ? (
          <>
            {photos[1] ? <Photo src={photos[1]} size={210} rot={-12} style={{ left: -60, top: 40, opacity: interpolate(frame, [10, 16], [0, 1], clamp) }} /> : null}
            {photos[2] ? <Photo src={photos[2]} size={200} rot={11} style={{ left: 200, top: -10, opacity: interpolate(frame, [13, 19], [0, 1], clamp) }} /> : null}
            <Photo src={photos[0]} size={300} rot={-4} style={{ left: 50, top: 70 }} />
            <div className="tape" style={{ left: 120, top: 60, transform: "rotate(-8deg)" }} />
          </>
        ) : (
          <>
            <div className="illust-wrap" style={{ width: 380, height: 380 }}><Svg html={p.illust} /></div>
            <div className="tape" style={{ left: 40, top: 20, transform: "rotate(-24deg)" }} />
          </>
        )}
      </div>
      <div className="stamp" style={{ right: -20, top: 400, transform: `rotate(-14deg) scale(${interpolate(stamp, [0, 1], [2.4, 1])})`, opacity: Math.min(1, stamp * 1.5) }}>
        <small>SAVE</small><b>保存版</b><small>{p.dateLabel.replace("月", ".").replace("日", "")}</small>
      </div>
    </div>
  );
};

const Mark: React.FC<{ m: string; delay: number; label: string; icon: string }> = ({ m, delay, label, icon }) => {
  const sp = useSpring(delay, { damping: 10, mass: 0.5, stiffness: 180 });
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6, transform: `scale(${sp})`, opacity: sp }}>
      <Svg html={icon} />
      <span style={{ font: '900 24px "Zen Kaku Gothic New"', color: "var(--sub)" }}>{label}</span>
      <span className={`mk ${m === "◎" ? "mk-best" : m === "○" ? "mk-mid" : "mk-low"}`} style={{ fontSize: 76 }}>{m}</span>
    </div>
  );
};

const ProductScene: React.FC<{ s: Scene; p: ReelProps }> = ({ s, p }) => {
  const frame = useCurrentFrame();
  const pr = s.product as Product;
  const enter = useSpring(0, { damping: 15, mass: 0.7, stiffness: 120 });
  const art = useSpring(6);
  const nameChars = Math.floor(interpolate(frame, [6, 20], [0, pr.name.length], clamp));
  const price = Math.round(interpolate(frame, [6, 26], [pr.price * 0.4, pr.price], { ...clamp, easing: Easing.out(Easing.cubic) }) / 10) * 10;
  const stars = interpolate(frame, [18, 34], [0, pr.review_avg / 5], clamp);
  const ring = interpolate(frame, [26, 50], [0, pr.score / 100], { ...clamp, easing: Easing.out(Easing.cubic) });
  const punch = frame > s.duration * 30 * 0.55 ? interpolate(frame - s.duration * 30 * 0.55, [0, 4], [1.06, 1.0], clamp) : 1;
  const C = 2 * Math.PI * 70;
  const isJp = !/^\d+$/.test(pr.label_main);
  return (
    <div style={{ ...AREA, transform: `translateX(${(1 - enter) * 900}px) skewX(${(1 - enter) * -8}deg) scale(${punch})` }}>
      {isJp ? null : <div style={{ position: "absolute", right: -40, top: 260, font: isJp ? '900 250px/1 "Zen Kaku Gothic New"' : 'italic 400 470px/0.8 "DM Serif Display"',
        color: "var(--accent)", opacity: 0.09, transform: `scale(${interpolate(frame, [0, 20], [1.3, 1], clamp)})`, transformOrigin: "right top", whiteSpace: "nowrap" }}>
        {pr.label_main}
      </div>}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ font: '900 30px "Zen Kaku Gothic New"', color: "var(--sub)", marginBottom: 6 }}>{pr.label_chip}</div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 6 }}>
            <span style={{ font: isJp ? '900 128px/1 "Zen Kaku Gothic New"' : 'italic 400 220px/0.8 "DM Serif Display"', color: "var(--accent)" }}>{pr.label_main}</span>
            <span className="head" style={{ fontSize: 64 }}>{pr.label_suffix}</span>
          </div>
        </div>
        <div style={{ position: "relative", transform: `scale(${art}) rotate(${(1 - art) * 25}deg)` }}>
          {pr.photo ? (
            <div style={{ position: "relative", width: 290, height: 320 }}><Photo src={pr.photo} size={280} rot={4} style={{ left: 0, top: 0 }} /></div>
          ) : (
            <div className="illust-wrap" style={{ width: 270, height: 270 }}><Svg html={p.illust.replace(/width="\d+" height="\d+"/, 'width="210" height="210"')} /></div>
          )}
          <div className="tape" style={{ right: -40, top: 0, transform: "rotate(28deg)", width: 160 }} />
        </div>
      </div>
      <div className="head" style={{ fontSize: 66, lineHeight: 1.2, marginTop: 18, minHeight: 80 }}>
        {pr.name.slice(0, nameChars)}<span style={{ opacity: frame % 16 < 8 && nameChars < pr.name.length ? 1 : 0 }}>|</span>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginTop: 8 }}>
        <span style={{ font: '400 150px/1 "DM Serif Display"', letterSpacing: "-.02em" }}>{yen(price)}</span>
        <span className="head" style={{ fontSize: 56 }}>円</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 18, marginTop: 14, font: '700 34px "Zen Kaku Gothic New"', color: "var(--sub)" }}>
        <span className="stars" style={{ fontSize: 46 }}>★★★★★<span className="fill" style={{ width: `${stars * 100}%` }}>★★★★★</span></span>
        <b style={{ font: '400 58px "DM Serif Display"', color: "var(--ink)" }}>{pr.review_avg.toFixed(2)}</b>口コミ {yen(pr.review_count)}件
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 26, marginTop: 30 }}>
        <div className="card" style={{ display: "flex", gap: 30, padding: "22px 30px", borderRadius: 28, opacity: interpolate(frame, [16, 22], [0, 1], clamp) }}>
          <Mark m={pr.marks.value} delay={22} label="価格" icon={p.icons.yen} />
          <Mark m={pr.marks.rating} delay={25} label="評価" icon={p.icons.star} />
          <Mark m={pr.marks.popular} delay={28} label="口コミ" icon={p.icons.people} />
          <Mark m={pr.marks.features} delay={31} label="機能" icon={p.icons.spark} />
        </div>
        <div style={{ position: "relative", width: 180, height: 180 }}>
          <svg width="180" height="180" viewBox="0 0 180 180">
            <circle cx="90" cy="90" r="70" fill="var(--soft)" stroke="var(--line)" strokeWidth="14" />
            <circle cx="90" cy="90" r="70" fill="none" stroke="var(--accent)" strokeWidth="14" strokeLinecap="round"
              strokeDasharray={`${C * ring} ${C}`} transform="rotate(-90 90 90)" />
          </svg>
          <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
            <span style={{ font: '400 20px "DM Serif Display"', letterSpacing: ".12em", color: "var(--sub)" }}>SCORE</span>
            <span style={{ font: '400 64px/1 "DM Serif Display"', color: "var(--accent)" }}>{Math.round(pr.score * ring / Math.max(0.0001, pr.score / 100) )}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

const TipScene: React.FC<{ s: Scene }> = ({ s }) => {
  const frame = useCurrentFrame();
  const n = useSpring(0, { damping: 10, mass: 0.6, stiffness: 160 });
  const title = useSpring(6);
  const sweep = interpolate(frame, [14, 24], [0, 100], clamp);
  const body = s.body || "";
  const chars = Math.floor(interpolate(frame, [16, 16 + body.length * 0.9], [0, body.length], clamp));
  const draw = interpolate(frame, [30, 44], [300, 0], clamp);
  return (
    <div style={AREA}>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 16 }}>
        <span style={{ font: '400 56px "DM Serif Display"', letterSpacing: ".14em", color: "var(--sub)", paddingBottom: 30 }}>POINT</span>
        <span style={{ font: 'italic 400 330px/0.8 "DM Serif Display"', color: "var(--accent)", display: "inline-block", transform: `rotateX(${(1 - n) * 90}deg)` }}>
          {String(s.n).padStart(2, "0")}
        </span>
      </div>
      <div className="head" style={{ fontSize: 100, lineHeight: 1.2, marginTop: 40, transform: `translateY(${(1 - title) * 80}px)`, opacity: title }}>
        <span style={{ background: `linear-gradient(transparent 56%, var(--pop) 56%, var(--pop) 90%, transparent 90%) no-repeat 0 0 / ${sweep}% 100%` }}>{s.title}</span>
      </div>
      <div className="card ruled" style={{ marginTop: 40, padding: "0 34px", font: '500 46px/68px "NotoJP", "Zen Kaku Gothic New"', minHeight: 210 }}>
        {body.slice(0, chars)}
      </div>
      <div style={{ position: "absolute", right: 0, bottom: 10, display: "flex", alignItems: "flex-end", gap: 6 }}>
        <span className="hand" style={{ fontSize: 50, color: "var(--accent)", transform: "rotate(-6deg)", opacity: interpolate(frame, [36, 44], [0, 1], clamp) }}>{s.anno}</span>
        <svg width="130" height="113" viewBox="0 0 150 130"><path d="M130 30 C 90 10, 40 20, 20 70 M14 46 L18 74 L44 68" fill="none" stroke="var(--ink)"
          strokeWidth="5" strokeLinecap="round" strokeDasharray="300" strokeDashoffset={draw} /></svg>
      </div>
    </div>
  );
};

const PicksScene: React.FC<{ s: Scene }> = ({ s }) => {
  const frame = useCurrentFrame();
  const t = useSpring(0);
  return (
    <div style={AREA}>
      <div className="head" style={{ fontSize: 86, lineHeight: 1.2, transform: `scale(${0.8 + 0.2 * t})`, opacity: t, transformOrigin: "left center" }}>
        <span className="marker">結論</span>：タイプ別なら
      </div>
      <div style={{ marginTop: 30 }}>
        {(s.picks || []).map((k, i) => {
          const sp = spring({ frame: frame - 8 - i * 7, fps: 30, config: { damping: 14, mass: 0.6, stiffness: 140 } });
          return (
            <div key={i} className="card" style={{ display: "flex", alignItems: "center", gap: 26, padding: "22px 30px", marginBottom: 18,
              transform: `translateX(${(1 - sp) * 800}px) rotate(${(1 - sp) * 6}deg)` }}>
              <div style={{ width: 104, height: 104, borderRadius: "50%", background: "var(--paper2)", display: "flex", alignItems: "center", justifyContent: "center", flex: "none" }}>
                <Svg html={k.icon} />
              </div>
              <div>
                <div style={{ font: '900 32px "Zen Kaku Gothic New"', color: "var(--accent)" }}>{k.label}</div>
                <div className="head" style={{ fontSize: 46, lineHeight: 1.22 }}>{k.name}</div>
                <div style={{ font: '700 26px "Zen Kaku Gothic New"', color: "var(--sub)" }}>{k.reason}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const CtaScene: React.FC<{ s: Scene; p: ReelProps }> = ({ p }) => {
  const frame = useCurrentFrame();
  const drop = useSpring(2, { damping: 8, mass: 0.7, stiffness: 150 });
  const sweep = interpolate(frame, [10, 20], [0, 100], clamp);
  const box = useSpring(14);
  const draw = interpolate(frame, [20, 34], [300, 0], clamp);
  return (
    <div style={AREA}>
      <div style={{ position: "absolute", right: 10, top: -30, transform: `translateY(${(1 - drop) * -500}px) rotate(${8 + (1 - drop) * 30}deg)` }}>
        <Svg html={p.icons.bookmark_big} />
      </div>
      <div className="head" style={{ fontSize: 108, lineHeight: 1.2, marginTop: 60 }}>
        比べるときの<br />ために<br />
        <span style={{ background: `linear-gradient(transparent 56%, var(--pop) 56%, var(--pop) 90%, transparent 90%) no-repeat 0 0 / ${sweep}% 100%` }}>保存</span>してね
      </div>
      <div className="card" style={{ marginTop: 56, padding: "40px 44px", font: '900 46px/1.55 "Zen Kaku Gothic New"', transform: `scale(${box})`, transformOrigin: "left center" }}>
        商品リンクはプロフィールの<br />リンク → <span style={{ font: '400 74px "DM Serif Display"', color: "var(--accent)" }}>No.{String(p.postNo).padStart(3, "0")}</span>
        {p.credit ? <div style={{ font: '700 22px "Zen Kaku Gothic New"', color: "var(--sub)", marginTop: 6 }}>音声: {p.credit}</div> : null}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 26 }}>
        <svg width="110" height="95" viewBox="0 0 150 130"><path d="M10 20 C 60 0, 120 30, 120 100 M100 80 L120 104 L138 78" fill="none" stroke="var(--ink)"
          strokeWidth="5" strokeLinecap="round" strokeDasharray="300" strokeDashoffset={draw} /></svg>
        <span className="hand" style={{ fontSize: 46, color: "var(--accent)", opacity: interpolate(frame, [26, 34], [0, 1], clamp) }}>あとで見返せるよ！</span>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------- captions
const Captions: React.FC<{ captions: Caption[] }> = ({ captions }) => {
  const frame = useCurrentFrame();
  const t = frame / 30;
  const cap = captions.find((c) => t >= c.start && t < c.end);
  if (!cap) return null;
  const pop = interpolate(t - cap.start, [0, 0.12], [0.85, 1], clamp);
  return (
    <div style={{ position: "absolute", left: 60, right: 150, top: 1250, height: 230, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ textAlign: "center", transform: `scale(${pop})`, font: '900 72px/1.3 "Zen Kaku Gothic New"', letterSpacing: ".01em",
        WebkitTextStroke: "14px var(--ink)", paintOrder: "stroke fill", color: "#fff" } as React.CSSProperties}>
        {cap.words.map((w, i) => {
          const active = t >= w.start && t < w.end;
          const said = t >= w.start;
          return (
            <span key={i} style={{ color: w.em ? "var(--pop)" : "#fff", opacity: said ? 1 : 0.94,
              display: "inline-block", transform: active ? "translateY(-5px) scale(1.07)" : undefined }}>{w.text}</span>
          );
        })}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------- audio
const bgmVolume = (frame: number, scenes: Scene[], base: number) => {
  const t = frame / 30;
  let duck = 0;
  for (const s of scenes) {
    const a = s.start + (s.voiceStart || 0);
    const b = s.start + s.duration - 0.25;
    duck = Math.max(duck, interpolate(t, [a - 0.15, a, b, b + 0.25], [0, 1, 1, 0], clamp));
  }
  const total = scenes.length ? scenes[scenes.length - 1].start + scenes[scenes.length - 1].duration : 1;
  const fadeOut = interpolate(t, [total - 1.2, total], [1, 0], clamp);
  return base * (1 - 0.6 * duck) * fadeOut;
};

// ---------------------------------------------------------------- main
export const Reel: React.FC<ReelProps> = (p) => {
  useAssets(p.glyphs);
  const frame = useCurrentFrame();
  const hookEnd = Math.round(((p.scenes[0]?.start || 0) + (p.scenes[0]?.duration || 3)) * 30);
  return (
    <AbsoluteFill className={`theme-${p.theme}`} style={{ fontFamily: '"Zen Kaku Gothic New", sans-serif', color: "var(--ink)" }}>
      <Background bgVideo={p.bgVideo} hookEnd={hookEnd} />
      {p.scenes.map((s, i) => {
        const from = Math.round(s.start * 30);
        const dur = Math.round(s.duration * 30);
        return (
          <Sequence key={i} from={from} durationInFrames={dur} layout="none">
            <AbsoluteFill>
              {s.type === "hook" && <HookScene s={s} p={p} />}
              {s.type === "product" && <ProductScene s={s} p={p} />}
              {s.type === "tip" && <TipScene s={s} />}
              {s.type === "picks" && <PicksScene s={s} />}
              {s.type === "cta" && <CtaScene s={s} p={p} />}
            </AbsoluteFill>
            {s.voice ? (
              <Sequence from={Math.round((s.voiceStart || 0) * 30)} layout="none"><Audio src={staticFile(s.voice)} /></Sequence>
            ) : null}
          </Sequence>
        );
      })}
      <Header postNo={p.postNo} scenes={p.scenes} light={!!p.bgVideo && frame < hookEnd} />
      <Captions captions={p.captions} />
      {p.scenes.slice(1).map((s, i) => <Wipe key={i} at={Math.round(s.start * 30)} />)}
      {/* 効果音 */}
      <Sequence from={4} layout="none"><Audio src={staticFile(p.sfx.impact)} volume={0.5} /></Sequence>
      {p.scenes.slice(1).map((s, i) => (
        <Sequence key={`w${i}`} from={Math.max(0, Math.round(s.start * 30) - 6)} layout="none"><Audio src={staticFile(p.sfx.whoosh)} volume={0.45} /></Sequence>
      ))}
      {p.scenes.map((s, i) => s.type === "product" ? (
        <Sequence key={`p${i}`} from={Math.round(s.start * 30) + 22} layout="none"><Audio src={staticFile(p.sfx.pop)} volume={0.35} /></Sequence>
      ) : null)}
      {p.bgm ? <Audio src={staticFile(p.bgm)} loop volume={(f) => bgmVolume(f, p.scenes, p.bgmVolume)} /> : null}
      <div style={{ display: "none" }}>{frame}</div>
    </AbsoluteFill>
  );
};
