"use client";

import { useState, useMemo, useEffect } from "react";
import { ClientPortal } from "@/components/portals/ClientPortal";
import { api } from "@/lib/api";
import { storage } from "@/lib/storage";
import { translations, Language } from "@/lib/i18n";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (username: string, fullName?: string) => void;
  lang: Language;
}

export function AuthModal({ isOpen, onClose, onSuccess, lang }: Props) {
  const [isLogin, setIsLogin] = useState(true);
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [lockoutSeconds, setLockoutSeconds] = useState(0);

  const t = translations[lang];

  useEffect(() => {
    if (lockoutSeconds <= 0) return;
    const interval = setInterval(() => {
      setLockoutSeconds((prev) => (prev > 1 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [lockoutSeconds]);

  const rules = useMemo(() => ({
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    digit: /[0-9]/.test(password),
    special: /[^A-Za-z0-9]/.test(password),
    noSpace: password.length > 0 && !/\s/.test(password),
  }), [password]);

  const allRulesPassed =
    rules.length &&
    rules.uppercase &&
    rules.lowercase &&
    rules.digit &&
    rules.special &&
    rules.noSpace;

  const passwordsMatch = !isLogin && password.length > 0 && password === confirmPassword;

  const strength = useMemo(() => {
    let score = 0;
    if (rules.length) score++;
    if (rules.uppercase) score++;
    if (rules.lowercase) score++;
    if (rules.digit) score++;
    if (rules.special) score++;
    if (rules.noSpace) score++;

    if (score <= 2) {
      return { label: lang === "vi" ? "Yếu" : "Weak", percent: 33, color: "bg-neutral-400" };
    }
    if (score <= 4) {
      return { label: lang === "vi" ? "Trung bình" : "Medium", percent: 66, color: "bg-neutral-600 dark:bg-neutral-400" };
    }
    return { label: lang === "vi" ? "Mạnh" : "Strong", percent: 100, color: "bg-black dark:bg-white" };
  }, [rules, lang]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (lockoutSeconds > 0) return;
    setError("");
    setSuccessMsg("");
    setLoading(true);

    try {
      if (isLogin) {
        const res = await api.login(username, password);
        if (res.access_token) {
          const authUser = res.username || username;
          storage.setToken(res.access_token);
          storage.setUser(authUser, res.full_name);
          onSuccess(authUser, res.full_name);
          onClose();
        } else {
          setError(res.detail || res.message || (lang === "vi" ? "Đăng nhập thất bại" : "Login failed"));
        }
      } else {
        if (!allRulesPassed) {
          setError(lang === "vi" ? "Mật khẩu chưa đáp ứng đầy đủ chính sách bảo mật." : "Password does not meet complexity requirements.");
          setLoading(false);
          return;
        }
        if (password !== confirmPassword) {
          setError(t.pass_match_err);
          setLoading(false);
          return;
        }

        const res = await api.register(username, password, fullName.trim() || undefined);
        if (res.status === "success" || res.access_token || res.message) {
          if (res.access_token) {
            const authUser = res.username || username;
            storage.setToken(res.access_token);
            storage.setUser(authUser, res.full_name);
            onSuccess(authUser, res.full_name);
            onClose();
          } else {
            setSuccessMsg(res.message || (lang === "vi" ? "Đăng ký thành công" : "Registration successful"));
            setTimeout(() => {
              setIsLogin(true);
              setSuccessMsg("");
            }, 1200);
          }
        } else {
          setError(res.detail || res.message || (lang === "vi" ? "Đăng ký thất bại" : "Registration failed"));
        }
      }
    } catch (err: any) {
      const msg = err.message || "";
      if (msg.includes("429") || msg.toLowerCase().includes("thử lại sau") || msg.toLowerCase().includes("lockout")) {
        const match = msg.match(/(\d+)\s*giây/i) || msg.match(/(\d+)\s*seconds/i);
        const secs = match ? parseInt(match[1], 10) : 300;
        setLockoutSeconds(secs);
        setError(msg);
      } else {
        setError(msg || (lang === "vi" ? "Lỗi kết nối máy chủ" : "Network connection error"));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <ClientPortal>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto select-none font-sans">
        <div className="relative w-full max-w-md bg-[#FAF7F2] rounded-xl p-6 shadow-2xl border border-neutral-300/80 my-8 text-neutral-900">
          <button
            type="button"
            onClick={onClose}
            className="absolute top-4 right-4 px-2 py-0.5 text-xs font-mono font-bold uppercase rounded border border-neutral-300 text-neutral-600 hover:text-black hover:bg-neutral-100 transition-colors"
            aria-label="Close"
          >
            [ĐÓNG]
          </button>

          <div className="flex items-center gap-2 mb-2">
            <span className="px-2 py-0.5 text-[10px] font-mono font-bold uppercase rounded border border-neutral-300 bg-white text-neutral-800">
              [TÀI KHOẢN]
            </span>
            <h2 className="text-lg font-bold font-mono uppercase tracking-wider text-neutral-900">
              {isLogin ? t.login : t.register}
            </h2>
          </div>
          <p className="text-xs text-neutral-500 mb-5 font-mono">
            {isLogin ? t.auth_login_desc : t.auth_register_desc}
          </p>

          {/* Lockout Banner */}
          {lockoutSeconds > 0 && (
            <div className="mb-4 p-3 rounded border border-amber-300 bg-amber-50 text-amber-900 text-xs font-mono flex items-center gap-2">
              <span className="font-bold">[KHÓA TẠM THỜI]</span>
              <div className="flex-1">
                {t.lockout_notice}{" "}
                <span className="font-bold">{lockoutSeconds}s</span>
              </div>
            </div>
          )}

          {/* Error Banner */}
          {error && (
            <div className="mb-4 p-3 rounded border border-red-300 bg-red-50 text-red-800 text-xs font-mono">
              <span className="font-bold mr-1.5">[LỖI]:</span>
              <span>{error}</span>
            </div>
          )}

          {/* Success Banner */}
          {successMsg && (
            <div className="mb-4 p-3 rounded border border-emerald-300 bg-emerald-50 text-emerald-800 text-xs font-mono">
              <span className="font-bold mr-1.5">[THÀNH CÔNG]:</span>
              <span>{successMsg}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4 font-mono">
            {/* Full Name (Register Only) */}
            {!isLogin && (
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-neutral-600 mb-1.5">
                  {t.full_name}
                </label>
                <input
                  type="text"
                  autoComplete="name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder={t.full_name_placeholder}
                  className="w-full px-3.5 py-2.5 rounded border border-neutral-300 bg-white text-neutral-900 text-xs focus:outline-none focus:border-neutral-900 transition-colors"
                />
              </div>
            )}

            {/* Username */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-neutral-600 mb-1.5">
                {t.username}
              </label>
              <input
                type="text"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder={t.username}
                className="w-full px-3.5 py-2.5 rounded border border-neutral-300 bg-white text-neutral-900 text-xs focus:outline-none focus:border-neutral-900 transition-colors"
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-neutral-600 mb-1.5">
                {t.password}
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  autoComplete={isLogin ? "current-password" : "new-password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t.password}
                  className="w-full px-3.5 pr-14 py-2.5 rounded border border-neutral-300 bg-white text-neutral-900 text-xs focus:outline-none focus:border-neutral-900 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-xs text-neutral-500 hover:text-black"
                >
                  {showPassword ? "[Ẩn]" : "[Hiện]"}
                </button>
              </div>
            </div>

            {/* Strength Meter & Checklist (Register Only) */}
            {!isLogin && password.length > 0 && (
              <div className="space-y-3 pt-1">
                <div>
                  <div className="flex justify-between items-center text-xs mb-1 font-bold text-neutral-600">
                    <span>{t.strength_meter_title}</span>
                    <span>{strength.label}</span>
                  </div>
                  <div className="w-full h-1.5 rounded bg-neutral-200 overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 rounded ${strength.color}`}
                      style={{ width: `${strength.percent}%` }}
                    />
                  </div>
                </div>
                <div className="p-3 rounded bg-white border border-neutral-300 space-y-1.5 text-xs">
                  <CheckItem passed={rules.length} label={t.rule_length} />
                  <CheckItem passed={rules.uppercase} label={t.rule_uppercase} />
                  <CheckItem passed={rules.lowercase} label={t.rule_lowercase} />
                  <CheckItem passed={rules.digit} label={t.rule_digit} />
                  <CheckItem passed={rules.special} label={t.rule_special} />
                  <CheckItem passed={rules.noSpace} label={t.rule_no_space} />
                </div>
              </div>
            )}

            {/* Confirm Password (Register Only) */}
            {!isLogin && (
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-neutral-600 mb-1.5">
                  {t.confirm_password}
                </label>
                <div className="relative">
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder={t.confirm_password_placeholder}
                    className="w-full px-3.5 pr-14 py-2.5 rounded border border-neutral-300 bg-white text-neutral-900 text-xs focus:outline-none focus:border-neutral-900 transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-2.5 text-xs text-neutral-500 hover:text-black"
                  >
                    {showConfirmPassword ? "[Ẩn]" : "[Hiện]"}
                  </button>
                </div>
                {confirmPassword.length > 0 && (
                  <div className="mt-1.5 text-xs flex items-center gap-1.5 font-bold">
                    <span>{passwordsMatch ? "[✓] " + t.pass_match_ok : "[x] " + t.pass_match_err}</span>
                  </div>
                )}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || lockoutSeconds > 0 || (!isLogin && (!allRulesPassed || !passwordsMatch))}
              className="w-full py-2.5 rounded font-bold text-xs uppercase tracking-wider bg-neutral-900 text-white hover:bg-neutral-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed mt-2 shadow-xs"
            >
              {loading ? t.loading : isLogin ? `[${t.login}]` : `[${t.register}]`}
            </button>
          </form>

          <div className="mt-5 text-center text-xs font-mono text-neutral-500">
            <span>{isLogin ? t.no_account : t.has_account}</span>{" "}
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin);
                setError("");
                setSuccessMsg("");
              }}
              className="font-bold underline text-neutral-900 hover:text-black"
            >
              {isLogin ? t.register_now : t.login_now}
            </button>
          </div>
        </div>
      </div>
    </ClientPortal>
  );
}

function CheckItem({ passed, label }: { passed: boolean; label: string }) {
  return (
    <div className={`flex items-center gap-2 transition-colors ${
      passed ? "text-black dark:text-white font-bold" : "text-neutral-400 dark:text-neutral-600"
    }`}>
      <span className="font-mono text-xs">{passed ? "[✓]" : "[•]"}</span>
      <span>{label}</span>
    </div>
  );
}
