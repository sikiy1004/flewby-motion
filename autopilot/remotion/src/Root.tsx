import React from "react";
import { Composition } from "remotion";
import { Reel } from "./Reel";
import type { ReelProps } from "./types";

const defaults: ReelProps = {
  fps: 30, width: 1080, height: 1920, durationInFrames: 90, theme: "kraft", postNo: 1, genre: "ドライヤー",
  formatLabel: "売れ筋比較", dateLabel: "11月19日", illust: "", icons: {}, scenes: [], captions: [],
  bgmVolume: 0.2, sfx: { whoosh: "", impact: "", pop: "", line: "" }, glyphs: "",
};

export const Root: React.FC = () => (
  <Composition
    id="Reel"
    component={Reel as unknown as React.FC<Record<string, unknown>>}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={90}
    defaultProps={defaults as unknown as Record<string, unknown>}
    calculateMetadata={({ props }) => {
      const p = props as unknown as ReelProps;
      return { durationInFrames: p.durationInFrames, fps: p.fps, width: p.width, height: p.height };
    }}
  />
);
