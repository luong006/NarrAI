"use client";

import React, { useState, useEffect, useRef } from "react";
import Image from "next/image";
import {
  Clapperboard,
  Play,
  Pause,
  RotateCcw,
  Repeat,
  Maximize2,
  Film,
  Camera,
  Sliders,
  Sparkles,
  Download,
  Plus,
  Layers,
  ChevronRight,
  Eye,
  Info,
  Clock,
  ArrowRight,
  Check,
} from "lucide-react";
import { Language, translations } from "@/lib/i18n";

export interface MotionScene {
  id: string;
  title: string;
  duration: number; // in seconds
  image: string;
  cameraMovement: "pan-left" | "pan-right" | "zoom-in" | "zoom-out" | "tilt-up" | "orbit" | "static";
  motionStrength: number;
  motionBlur: boolean;
  focalLength: string;
  prompt: string;
}

interface Props {
  lang: Language;
  onBackToManga?: () => void;
  onBackToEditor?: () => void;
}

export function MotionStudio({ lang, onBackToManga, onBackToEditor }: Props) {
  const t = translations[lang];

  // Default motion scenes using actual project visual assets
  const [scenes, setScenes] = useState<MotionScene[]>([
    {
      id: "scene-1",
      title: lang === "vi" ? "Cảnh 01: Kiếm Khách Bến Sông Mưa" : "Scene 01: Swordsman in Rain",
      duration: 4,
      image: "/assets/landing/world_warrior_rain.png",
      cameraMovement: "zoom-in",
      motionStrength: 6,
      motionBlur: true,
      focalLength: "50mm",
      prompt:
        lang === "vi"
          ? "Mưa rơi chậm, áo tơi bay nhẹ trong gió đêm bến sông, camera từ từ zoom cận vào ánh mắt quyết đoán, ánh chớp lóe phản chiếu lưỡi thép."
          : "Slow rain falling, straw cloak drifting in wind, camera zooms slowly into determined eyes, lightning reflections on cold blade.",
    },
    {
      id: "scene-2",
      title: lang === "vi" ? "Cảnh 02: Nàng Thiềm Khởi Ấn Trầm Hương" : "Scene 02: Sealing Ritual Maiden",
      duration: 4,
      image: "/assets/landing/hero_character_aodai.png",
      cameraMovement: "pan-left",
      motionStrength: 4,
      motionBlur: false,
      focalLength: "85mm",
      prompt:
        lang === "vi"
          ? "Ánh sáng vàng kim từ ngọc bội lan tỏa, tà áo lụa gợn sóng mờ ảo, camera lia ngang nhẹ nhàng làm nổi bật thần thái trầm mặc."
          : "Golden light emanating from jade seal, silk fabrics waving gently, soft camera pan highlighting calm noble expression.",
    },
    {
      id: "scene-3",
      title: lang === "vi" ? "Cảnh 03: Chân Dung Kiếm Khí Thiếu Nữ" : "Scene 03: Manga Heroine Gaze",
      duration: 3,
      image: "/assets/landing/manga_heroine_portrait.png",
      cameraMovement: "orbit",
      motionStrength: 5,
      motionBlur: true,
      focalLength: "35mm",
      prompt:
        lang === "vi"
          ? "Tóc bay ngược chiều gió, ánh nhìn sắc bén hướng về phía trước, luồng kiếm khí bao quanh chuyển động xoay nhẹ."
          : "Hair flowing against wind, sharp direct gaze, subtle aura rotation around heroine.",
    },
    {
      id: "scene-4",
      title: lang === "vi" ? "Cảnh 04: Thần Mộc & Cội Nguồn Dân Gian" : "Scene 04: Ancient Roots & Child",
      duration: 5,
      image: "/assets/landing/folktale_child_roots.png",
      cameraMovement: "zoom-out",
      motionStrength: 3,
      motionBlur: false,
      focalLength: "24mm",
      prompt:
        lang === "vi"
          ? "Đom đóm bay lơ lửng quanh rễ cây cổ thụ khổng lồ, góc máy từ từ lùi xa mở rộng không gian huyền ảo."
          : "Fireflies floating around giant ancient roots, wide slow pull back revealing mythical woodland.",
    },
  ]);

  const [selectedSceneIndex, setSelectedSceneIndex] = useState(0);
  const currentScene = scenes[selectedSceneIndex] || scenes[0];

  // Playback state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [isLooping, setIsLooping] = useState(true);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const [aspectRatio, setAspectRatio] = useState<"16:9" | "9:16" | "1:1">("16:9");
  const [fps, setFps] = useState<"24" | "30" | "60">("24");

  // Camera preview animation ref
  const animFrameRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number>(Date.now());

  // Export modal state
  const [showExportModal, setShowExportModal] = useState(false);
  const [isCopiedPrompt, setIsCopiedPrompt] = useState(false);

  // Playback loop
  useEffect(() => {
    if (!isPlaying) {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      return;
    }

    lastTimeRef.current = Date.now();

    const tick = () => {
      const now = Date.now();
      const delta = (now - lastTimeRef.current) / 1000;
      lastTimeRef.current = now;

      setCurrentTime((prev) => {
        const next = prev + delta * playbackSpeed;
        if (next >= currentScene.duration) {
          if (isLooping) {
            return 0;
          } else {
            setIsPlaying(false);
            return currentScene.duration;
          }
        }
        return next;
      });

      animFrameRef.current = requestAnimationFrame(tick);
    };

    animFrameRef.current = requestAnimationFrame(tick);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isPlaying, currentScene.duration, isLooping, playbackSpeed]);

  const handleTogglePlay = () => {
    if (currentTime >= currentScene.duration) {
      setCurrentTime(0);
    }
    setIsPlaying(!isPlaying);
  };

  const handleRestart = () => {
    setCurrentTime(0);
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setCurrentTime(val);
  };

  // Update current scene field
  const handleUpdateCurrentScene = (updates: Partial<MotionScene>) => {
    setScenes((prev) =>
      prev.map((s, idx) => (idx === selectedSceneIndex ? { ...s, ...updates } : s))
    );
  };

  // Compute CSS transform based on camera movement and current time progress
  const progress = currentScene.duration > 0 ? currentTime / currentScene.duration : 0;
  const strengthFactor = (currentScene.motionStrength / 10) * 12; // 0% to 12% shift

  const getCameraTransform = () => {
    switch (currentScene.cameraMovement) {
      case "zoom-in":
        return `scale(${1 + progress * (strengthFactor / 50)})`;
      case "zoom-out":
        return `scale(${1 + (1 - progress) * (strengthFactor / 50)})`;
      case "pan-left":
        return `translateX(-${progress * strengthFactor}%) scale(1.08)`;
      case "pan-right":
        return `translateX(${progress * strengthFactor}%) scale(1.08)`;
      case "tilt-up":
        return `translateY(-${progress * strengthFactor}%) scale(1.08)`;
      case "orbit":
        return `rotate(${progress * 2}deg) scale(${1 + Math.sin(progress * Math.PI) * 0.05})`;
      case "static":
      default:
        return "scale(1)";
    }
  };

  const cameraPresets = [
    { id: "zoom-in", label: lang === "vi" ? "Zoom Vào" : "Zoom In", icon: "🔍+" },
    { id: "zoom-out", label: lang === "vi" ? "Zoom Ra" : "Zoom Out", icon: "🔍-" },
    { id: "pan-left", label: lang === "vi" ? "Lướt Trái" : "Pan Left", icon: "⬅️" },
    { id: "pan-right", label: lang === "vi" ? "Lướt Phải" : "Pan Right", icon: "➡️" },
    { id: "tilt-up", label: lang === "vi" ? "Nâng Góc" : "Tilt Up", icon: "⬆️" },
    { id: "orbit", label: lang === "vi" ? "Quỹ Đạo" : "Orbit", icon: "🔄" },
    { id: "static", label: lang === "vi" ? "Tĩnh" : "Static", icon: "⏸️" },
  ];

  return (
    <div className="flex-1 flex flex-col h-full bg-[#FAF7F2] text-neutral-900 select-none overflow-hidden font-sans">
      {/* 1. Header Toolbar */}
      <header className="h-14 border-b border-neutral-300/80 px-4 flex items-center justify-between shrink-0 bg-[#FAF7F2]/90 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs font-mono text-neutral-500">
            <span>NarrAI</span>
            <ChevronRight className="w-3.5 h-3.5 text-neutral-400" />
            <span className="text-neutral-950 font-semibold flex items-center gap-1.5">
              <Clapperboard className="w-4 h-4 text-neutral-950" />
              Motion Studio
            </span>
          </div>

          <div className="h-4 w-px bg-neutral-300/80 hidden sm:block" />

          {/* Current scene selector */}
          <div className="hidden md:flex items-center gap-2">
            <span className="text-xs font-mono text-neutral-500">
              {lang === "vi" ? "Phân cảnh:" : "Scene:"}
            </span>
            <span className="text-xs font-medium text-neutral-900 px-2 py-0.5 rounded bg-white border border-neutral-300/80 font-mono shadow-xs">
              {currentScene.title}
            </span>
          </div>
        </div>

        {/* Right Header Controls */}
        <div className="flex items-center gap-2">
          {/* Aspect Ratio Selector */}
          <div className="flex items-center rounded-lg border border-neutral-300/80 bg-neutral-200/50 p-0.5 text-[11px] font-mono">
            {(["16:9", "9:16", "1:1"] as const).map((ratio) => (
              <button
                key={ratio}
                type="button"
                onClick={() => setAspectRatio(ratio)}
                className={`px-2 py-1 rounded transition-colors ${
                  aspectRatio === ratio
                    ? "bg-white text-neutral-950 font-bold shadow-xs"
                    : "text-neutral-600 hover:text-neutral-950"
                }`}
              >
                {ratio}
              </button>
            ))}
          </div>

          {/* FPS Selector */}
          <div className="hidden sm:flex items-center rounded-lg border border-neutral-300/80 bg-neutral-200/50 p-0.5 text-[11px] font-mono">
            {(["24", "30", "60"] as const).map((val) => (
              <button
                key={val}
                type="button"
                onClick={() => setFps(val)}
                className={`px-2 py-1 rounded transition-colors ${
                  fps === val
                    ? "bg-white text-neutral-950 font-bold shadow-xs"
                    : "text-neutral-600 hover:text-neutral-950"
                }`}
              >
                {val}fps
              </button>
            ))}
          </div>

          {/* Export Button */}
          <button
            type="button"
            onClick={() => setShowExportModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-neutral-900 text-white font-mono text-xs font-bold hover:bg-neutral-800 transition-colors shadow-xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{lang === "vi" ? "Xuất Video" : "Export MP4"}</span>
          </button>
        </div>
      </header>

      {/* 2. Main 3-Column Motion Workspace */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* LEFT COLUMN: Scene & Keyframe Timeline (Hidden on small mobile) */}
        <aside className="w-64 border-r border-neutral-300/80 bg-[#FAF7F2] flex-col shrink-0 hidden md:flex">
          <div className="p-3 border-b border-neutral-300/70 flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-mono text-neutral-600 uppercase tracking-wider">
              <Film className="w-3.5 h-3.5" />
              <span>{lang === "vi" ? "Phân Cảnh" : "Scenes"}</span>
            </div>
            <span className="text-[11px] font-mono text-neutral-500">
              {scenes.length} {lang === "vi" ? "cảnh" : "cuts"}
            </span>
          </div>

          {/* Scene List */}
          <div className="flex-1 overflow-y-auto p-2 space-y-2">
            {scenes.map((scene, idx) => {
              const isSelected = idx === selectedSceneIndex;
              return (
                <div
                  key={scene.id}
                  onClick={() => {
                    setSelectedSceneIndex(idx);
                    setCurrentTime(0);
                    setIsPlaying(false);
                  }}
                  className={`group relative rounded-lg border p-2 cursor-pointer transition-all ${
                    isSelected
                      ? "border-neutral-900 bg-white shadow-xs"
                      : "border-neutral-300/60 bg-white/70 hover:bg-white"
                  }`}
                >
                  <div className="flex gap-2.5 items-center">
                    <div className="relative w-16 h-12 rounded overflow-hidden shrink-0 bg-black border border-neutral-700">
                      <Image
                        src={scene.image}
                        alt={scene.title}
                        fill
                        className="object-cover"
                        sizes="64px"
                      />
                      <div className="absolute bottom-0 right-0 px-1 py-0.2 bg-black/80 text-[9px] font-mono text-neutral-300">
                        {scene.duration}s
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-medium text-neutral-900 truncate font-sans">
                        {scene.title}
                      </div>
                      <div className="flex items-center gap-1 mt-1 text-[10px] font-mono text-neutral-500">
                        <Camera className="w-2.5 h-2.5" />
                        <span className="capitalize">{scene.cameraMovement}</span>
                      </div>
                    </div>
                  </div>
                  {isSelected && (
                    <div className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-neutral-900 animate-pulse" />
                  )}
                </div>
              );
            })}

            {/* Quick add scene button */}
            <button
              type="button"
              onClick={() => {
                const newId = `scene-${scenes.length + 1}`;
                const newScene: MotionScene = {
                  id: newId,
                  title: `${lang === "vi" ? "Cảnh" : "Scene"} 0${scenes.length + 1}`,
                  duration: 4,
                  image: "/assets/landing/world_warrior_rain.png",
                  cameraMovement: "pan-right",
                  motionStrength: 5,
                  motionBlur: true,
                  focalLength: "50mm",
                  prompt:
                    lang === "vi"
                      ? "Góc máy quay xoay chuyển điện ảnh, hạt sáng bay lượn trong không gian."
                      : "Cinematic camera turn, atmospheric glowing particles.",
                };
                setScenes([...scenes, newScene]);
                setSelectedSceneIndex(scenes.length);
                setCurrentTime(0);
              }}
              className="w-full flex items-center justify-center gap-1.5 py-2.5 rounded-lg border border-dashed border-neutral-400 bg-white/50 text-neutral-600 hover:text-neutral-950 hover:border-neutral-600 text-xs font-mono transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>{lang === "vi" ? "Thêm Phân Cảnh" : "Add Scene"}</span>
            </button>
          </div>

          {/* Quick link to Manga / Story Lab */}
          <div className="p-3 border-t border-neutral-300/70 text-xs font-mono space-y-1.5">
            {onBackToManga && (
              <button
                type="button"
                onClick={onBackToManga}
                className="w-full flex items-center justify-between text-neutral-600 hover:text-neutral-950 py-1 transition-colors"
              >
                <span>{lang === "vi" ? "➔ Nhập từ Manga Studio" : "➔ From Manga Studio"}</span>
              </button>
            )}
            {onBackToEditor && (
              <button
                type="button"
                onClick={onBackToEditor}
                className="w-full flex items-center justify-between text-neutral-600 hover:text-neutral-950 py-1 transition-colors"
              >
                <span>{lang === "vi" ? "➔ Xem Bản thảo Story" : "➔ View Story Draft"}</span>
              </button>
            )}
          </div>
        </aside>

        {/* CENTER COLUMN: Cinematic Canvas & Timeline Scrubber */}
        <div className="flex-1 flex flex-col min-h-0 bg-[#FAF7F2] overflow-hidden">
          {/* Main Visual Preview Canvas */}
          <div className="flex-1 flex items-center justify-center p-4 relative overflow-hidden bg-neutral-200/40">
            {/* Aspect Ratio Bounding Container */}
            <div
              className={`relative rounded-xl overflow-hidden border border-neutral-800 bg-black shadow-2xl transition-all duration-300 flex items-center justify-center ${
                aspectRatio === "16:9"
                  ? "w-full max-w-4xl aspect-video"
                  : aspectRatio === "9:16"
                  ? "h-full max-h-[560px] aspect-[9/16]"
                  : "w-full max-w-[500px] aspect-square"
              }`}
            >
              {/* Animated Keyframe Image Layer */}
              <div
                className="absolute inset-0 w-full h-full transition-transform duration-75 ease-out overflow-hidden"
                style={{
                  transform: getCameraTransform(),
                }}
              >
                <Image
                  src={currentScene.image}
                  alt={currentScene.title}
                  fill
                  className={`object-cover ${
                    currentScene.motionBlur && isPlaying ? "blur-[0.6px]" : ""
                  }`}
                  priority
                />
              </div>

              {/* Cinematic Vignette Overlay */}
              <div className="absolute inset-0 pointer-events-none bg-gradient-to-t from-black/60 via-transparent to-black/30" />

              {/* Watermark / Studio Badge */}
              <div className="absolute top-3 left-3 px-2 py-0.5 rounded bg-black/70 backdrop-blur border border-white/10 text-[10px] font-mono text-neutral-300 pointer-events-none flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span>NARR MOTION PREVIEW</span>
              </div>

              {/* Current Camera Preset Overlay indicator */}
              <div className="absolute top-3 right-3 px-2 py-0.5 rounded bg-black/70 backdrop-blur border border-white/10 text-[10px] font-mono text-neutral-400 pointer-events-none capitalize">
                {currentScene.cameraMovement} · {currentScene.focalLength}
              </div>

              {/* Center Play Button Overlay (when paused) */}
              {!isPlaying && (
                <button
                  type="button"
                  onClick={handleTogglePlay}
                  className="absolute inset-0 m-auto w-14 h-14 rounded-full bg-white/20 hover:bg-white/30 backdrop-blur-md border border-white/30 flex items-center justify-center text-white transition-transform hover:scale-110 shadow-2xl z-10"
                >
                  <Play className="w-6 h-6 ml-0.5 fill-white" />
                </button>
              )}
            </div>
          </div>

          {/* Timeline & Player Bar */}
          <div className="h-24 border-t border-neutral-300/80 bg-[#FAF7F2] px-6 py-3 flex flex-col justify-between shrink-0">
            {/* Scrubber slider and time marks */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-[11px] font-mono text-neutral-600">
                <div className="flex items-center gap-2">
                  <span className="text-neutral-950 font-bold">
                    00:0{Math.floor(currentTime)}:
                    {Math.floor((currentTime % 1) * 30)
                      .toString()
                      .padStart(2, "0")}
                  </span>
                  <span className="text-neutral-400">/</span>
                  <span>
                    00:0{currentScene.duration}:00
                  </span>
                </div>
                <div className="text-[10px] text-neutral-500 uppercase tracking-wider">
                  {lang === "vi" ? "Tiến độ khung hình:" : "Frame Progress:"} {Math.round(progress * 100)}%
                </div>
              </div>

              {/* Scrubber track */}
              <div className="relative flex items-center">
                <input
                  type="range"
                  min={0}
                  max={currentScene.duration}
                  step={0.01}
                  value={currentTime}
                  onChange={handleSeek}
                  className="w-full h-1.5 bg-neutral-300 rounded-lg appearance-none cursor-pointer accent-neutral-900"
                />
              </div>
            </div>

            {/* Playback action controls */}
            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-2">
                {/* Restart */}
                <button
                  type="button"
                  onClick={handleRestart}
                  className="p-1.5 rounded hover:bg-white text-neutral-600 hover:text-neutral-950 transition-colors shadow-xs"
                  title={lang === "vi" ? "Xem lại từ đầu" : "Restart"}
                >
                  <RotateCcw className="w-4 h-4" />
                </button>

                {/* Play / Pause */}
                <button
                  type="button"
                  onClick={handleTogglePlay}
                  className="px-3 py-1 rounded bg-neutral-900 text-white hover:bg-neutral-800 transition-colors flex items-center gap-1.5 text-xs font-mono font-bold shadow-xs"
                >
                  {isPlaying ? (
                    <>
                      <Pause className="w-3.5 h-3.5 fill-white" />
                      <span>Tạm dừng</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5 fill-white" />
                      <span>Phát</span>
                    </>
                  )}
                </button>

                {/* Loop */}
                <button
                  type="button"
                  onClick={() => setIsLooping(!isLooping)}
                  className={`p-1.5 rounded transition-colors ${
                    isLooping
                      ? "text-neutral-950 bg-white border border-neutral-300/80 shadow-xs"
                      : "text-neutral-500 hover:text-neutral-900"
                  }`}
                  title={lang === "vi" ? "Lặp lại liên tục" : "Loop"}
                >
                  <Repeat className="w-4 h-4" />
                </button>

                {/* Speed toggle */}
                <button
                  type="button"
                  onClick={() => {
                    const speeds = [0.5, 1, 1.5];
                    const nextIndex = (speeds.indexOf(playbackSpeed) + 1) % speeds.length;
                    setPlaybackSpeed(speeds[nextIndex]);
                  }}
                  className="px-2 py-0.5 rounded bg-white border border-neutral-300/80 text-[11px] font-mono text-neutral-700 hover:text-neutral-950 transition-colors shadow-xs"
                >
                  {playbackSpeed}x
                </button>
              </div>

              {/* Scene Info Snippet */}
              <div className="text-[11px] font-mono text-neutral-500 hidden sm:block truncate max-w-xs">
                {currentScene.title} · {currentScene.cameraMovement}
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Camera Parameters & Motion Prompt Inspector */}
        <aside className="w-80 border-l border-neutral-300/80 bg-[#FAF7F2] flex-col shrink-0 overflow-y-auto hidden lg:flex">
          <div className="p-3 border-b border-neutral-300/70 flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-mono text-neutral-600 uppercase tracking-wider">
              <Sliders className="w-3.5 h-3.5" />
              <span>{lang === "vi" ? "Đạo Diễn Chuyển Động" : "Motion Director"}</span>
            </div>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white border border-neutral-300/80 text-neutral-600 shadow-xs">
              {currentScene.focalLength}
            </span>
          </div>

          <div className="p-4 space-y-5">
            {/* 1. Camera Movement Presets */}
            <div>
              <label className="text-xs font-mono text-neutral-800 block mb-2 font-semibold">
                {lang === "vi" ? "Quỹ Đạo Máy Quay (Camera Trajectory)" : "Camera Trajectory"}
              </label>
              <div className="grid grid-cols-2 gap-1.5">
                {cameraPresets.map((preset) => {
                  const isActive = currentScene.cameraMovement === preset.id;
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() =>
                        handleUpdateCurrentScene({
                          cameraMovement: preset.id as MotionScene["cameraMovement"],
                        })
                      }
                      className={`flex items-center gap-2 p-2 rounded-lg border text-xs font-mono transition-all text-left ${
                        isActive
                          ? "border-neutral-900 bg-white text-neutral-950 font-bold shadow-xs"
                          : "border-neutral-300/60 bg-white/60 text-neutral-600 hover:border-neutral-400 hover:text-neutral-950"
                      }`}
                    >
                      <span>{preset.icon}</span>
                      <span className="truncate">{preset.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 2. Motion Strength Slider */}
            <div>
              <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                <span className="text-neutral-700">
                  {lang === "vi" ? "Cường Độ Chuyển Động" : "Motion Strength"}
                </span>
                <span className="text-neutral-950 font-bold">{currentScene.motionStrength} / 10</span>
              </div>
              <input
                type="range"
                min={1}
                max={10}
                value={currentScene.motionStrength}
                onChange={(e) =>
                  handleUpdateCurrentScene({ motionStrength: parseInt(e.target.value) })
                }
                className="w-full h-1.5 bg-neutral-300 rounded-lg appearance-none cursor-pointer accent-neutral-900"
              />
            </div>

            {/* 3. Focal Length & Motion Blur */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-mono text-neutral-600 block mb-1.5">
                  {lang === "vi" ? "Tiêu Cự Ống Kính" : "Focal Length"}
                </label>
                <select
                  value={currentScene.focalLength}
                  onChange={(e) => handleUpdateCurrentScene({ focalLength: e.target.value })}
                  className="w-full rounded-lg border border-neutral-300/80 bg-white px-2.5 py-1.5 text-xs font-mono text-neutral-900 focus:outline-none focus:border-neutral-900 shadow-xs"
                >
                  <option value="24mm">24mm (Ultra Wide)</option>
                  <option value="35mm">35mm (Cinematic)</option>
                  <option value="50mm">50mm (Standard)</option>
                  <option value="85mm">85mm (Portrait)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-mono text-neutral-600 block mb-1.5">
                  {lang === "vi" ? "Motion Blur" : "Motion Blur"}
                </label>
                <button
                  type="button"
                  onClick={() =>
                    handleUpdateCurrentScene({ motionBlur: !currentScene.motionBlur })
                  }
                  className={`w-full py-1.5 rounded-lg border text-xs font-mono transition-colors shadow-xs ${
                    currentScene.motionBlur
                      ? "border-neutral-900 bg-neutral-900 text-white font-bold"
                      : "border-neutral-300/80 bg-white text-neutral-600 hover:text-neutral-950"
                  }`}
                >
                  {currentScene.motionBlur ? "BẬT (ON)" : "TẮT (OFF)"}
                </button>
              </div>
            </div>

            {/* 4. Motion Prompt Area */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-mono text-neutral-800 font-semibold flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-neutral-600" />
                  <span>{lang === "vi" ? "Kịch Bản Chuyển Động" : "Motion Prompt"}</span>
                </label>
                <button
                  type="button"
                  onClick={() => {
                    navigator.clipboard.writeText(currentScene.prompt);
                    setIsCopiedPrompt(true);
                    setTimeout(() => setIsCopiedPrompt(false), 2000);
                  }}
                  className="text-[10px] font-mono text-neutral-500 hover:text-neutral-950 transition-colors"
                >
                  {isCopiedPrompt ? "✓ Đã chép" : "Sao chép"}
                </button>
              </div>
              <textarea
                value={currentScene.prompt}
                onChange={(e) => handleUpdateCurrentScene({ prompt: e.target.value })}
                rows={4}
                className="w-full rounded-lg border border-neutral-300/80 bg-white p-2.5 text-xs font-sans text-neutral-900 focus:outline-none focus:border-neutral-900 leading-relaxed resize-none shadow-xs"
                placeholder={
                  lang === "vi"
                    ? "Mô tả chi tiết chuyển động nhân vật, ánh sáng, máy quay..."
                    : "Describe motion, camera movement, atmospheric lighting..."
                }
              />

              {/* Quick Prompt Tags */}
              <div className="flex flex-wrap gap-1 mt-2">
                {[
                  lang === "vi" ? "Mưa rơi chậm" : "Slow rain",
                  lang === "vi" ? "Gió thổi tà áo" : "Wind on cloak",
                  lang === "vi" ? "Sương mù mờ ảo" : "Mist floating",
                  lang === "vi" ? "Ánh chớp lóe" : "Lightning flash",
                ].map((tag, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      if (!currentScene.prompt.includes(tag)) {
                        handleUpdateCurrentScene({
                          prompt: currentScene.prompt + `, ${tag}`,
                        });
                      }
                    }}
                    className="px-2 py-0.5 rounded bg-white hover:bg-neutral-100 border border-neutral-300/70 text-[10px] font-mono text-neutral-700 hover:text-neutral-950 transition-colors shadow-xs"
                  >
                    +{tag}
                  </button>
                ))}
              </div>
            </div>

            {/* 5. Pipeline Reality Notice (No fake generation states!) */}
            <div className="rounded-lg border border-neutral-300/80 bg-white p-3 text-xs space-y-2 shadow-xs">
              <div className="flex items-center gap-2 text-neutral-800 font-mono font-semibold">
                <Info className="w-3.5 h-3.5 text-neutral-500 shrink-0" />
                <span>ComfyUI AnimateDiff Pipeline</span>
              </div>
              <p className="text-[11px] text-neutral-600 leading-relaxed font-sans">
                {lang === "vi"
                  ? "Hạ tầng render video đang trong lộ trình tích hợp pipeline ComfyUI AnimateDiff v3 & SVD. Không gian Motion Studio hiện đang hoạt động ở chế độ Preview trực quan thời gian thực, cho phép bạn thiết lập hoàn chỉnh kịch bản camera và dòng thời gian."
                  : "The video rendering engine is actively integrating ComfyUI AnimateDiff v3 & SVD. Motion Studio is operating in real-time interactive preview mode, letting you direct camera timelines and motion parameters."}
              </p>
              <div className="pt-1 flex items-center justify-between text-[10px] font-mono text-neutral-500 border-t border-neutral-200">
                <span>GPU Cluster: ComfyUI SVD Node</span>
                <span className="text-emerald-700 font-bold">● Sẵn sàng đồng bộ</span>
              </div>
            </div>
          </div>
        </aside>
      </div>

      {/* 3. Export Modal / Drawer */}
      {showExportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl border border-neutral-300/80 bg-[#FAF7F2] p-6 shadow-2xl space-y-4 text-neutral-900">
            <div className="flex items-center justify-between border-b border-neutral-300/70 pb-3">
              <div className="flex items-center gap-2">
                <Film className="w-4 h-4 text-neutral-900" />
                <h3 className="font-bold text-sm text-neutral-950 font-mono uppercase tracking-wider">
                  {lang === "vi" ? "Xuất Video Phân Cảnh" : "Export Scene Video"}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowExportModal(false)}
                className="text-neutral-500 hover:text-neutral-950 text-xs font-mono"
              >
                [✕]
              </button>
            </div>

            <div className="space-y-3 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-neutral-200 text-neutral-600">
                <span>{lang === "vi" ? "Độ phân giải:" : "Resolution:"}</span>
                <span className="text-neutral-950 font-bold">1920 × 1080 (Full HD)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-neutral-200 text-neutral-600">
                <span>{lang === "vi" ? "Tỷ lệ & Tốc độ:" : "Aspect & FPS:"}</span>
                <span className="text-neutral-950 font-bold">{aspectRatio} · {fps} FPS</span>
              </div>
              <div className="flex justify-between py-1 border-b border-neutral-200 text-neutral-600">
                <span>{lang === "vi" ? "Thời lượng phân cảnh:" : "Duration:"}</span>
                <span className="text-neutral-950 font-bold">{currentScene.duration} giây</span>
              </div>
              <div className="flex justify-between py-1 border-b border-neutral-200 text-neutral-600">
                <span>{lang === "vi" ? "Quỹ đạo máy quay:" : "Camera:"}</span>
                <span className="text-neutral-950 font-bold capitalize">{currentScene.cameraMovement}</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-white border border-neutral-300/70 text-[11px] text-neutral-600 leading-relaxed font-sans shadow-xs">
              {lang === "vi"
                ? "Bản dựng kịch bản camera và các thông số keyframe đã được đóng gói chuẩn bị cho cụm render GPU. Bạn có thể xuất kịch bản JSON hoặc lưu phiên bản làm việc này vào dự án."
                : "Camera keyframe configurations and trajectory parameters have been bundled. You can export the scene manifest or save it to your project library."}
            </div>

            <div className="flex items-center gap-2 pt-2">
              <button
                type="button"
                onClick={() => {
                  const manifest = JSON.stringify(currentScene, null, 2);
                  const blob = new Blob([manifest], { type: "application/json" });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `motion-scene-${currentScene.id}.json`;
                  a.click();
                  URL.revokeObjectURL(url);
                  setShowExportModal(false);
                }}
                className="flex-1 py-2.5 rounded-lg border border-neutral-300/80 bg-white text-neutral-900 hover:bg-neutral-100 text-xs font-mono transition-colors text-center shadow-xs"
              >
                {lang === "vi" ? "Tải File Kịch Bản JSON" : "Download JSON Manifest"}
              </button>
              <button
                type="button"
                onClick={() => setShowExportModal(false)}
                className="flex-1 py-2.5 rounded-lg bg-neutral-900 text-white font-bold text-xs font-mono hover:bg-neutral-800 transition-colors text-center shadow-xs"
              >
                {lang === "vi" ? "Đóng" : "Done"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
