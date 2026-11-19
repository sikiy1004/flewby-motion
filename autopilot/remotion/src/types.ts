export type Axes = { value: number; rating: number; popular: number; features: number };
export type Marks = { value: string; rating: string; popular: string; features: string };

export type Product = {
  name: string;
  price: number;
  review_avg: number;
  review_count: number;
  features: string[];
  score: number;
  axes: Axes;
  marks: Marks;
  best?: boolean;
  label_main: string;
  label_suffix: string;
  label_chip: string;
  photo?: string;
};

export type Word = { text: string; start: number; end: number; em?: boolean };
export type Caption = { start: number; end: number; words: Word[] };

export type Scene = {
  type: "hook" | "product" | "tip" | "picks" | "cta";
  start: number; // 秒
  duration: number; // 秒
  voice?: string;
  voiceStart?: number; // シーン開始からの秒
  // hook
  hookChunks?: { text: string; em?: boolean }[];
  subtitle?: string;
  bigN?: string;
  bigLabel?: string;
  hookSize?: number;
  photos?: string[];
  // product
  product?: Product;
  index?: number;
  total?: number;
  // tip
  n?: number;
  title?: string;
  body?: string;
  anno?: string;
  // picks
  picks?: { label: string; name: string; reason: string; icon: string }[];
};

export type ReelProps = {
  fps: number;
  width: number;
  height: number;
  durationInFrames: number;
  theme: string;
  postNo: number;
  genre: string;
  formatLabel: string;
  dateLabel: string;
  illust: string; // inline SVG
  icons: Record<string, string>;
  scenes: Scene[];
  captions: Caption[];
  bgm?: string;
  bgmVolume: number;
  sfx: { whoosh: string; impact: string; pop: string; line: string };
  bgVideo?: string;
  credit?: string;
  glyphs: string;
};
