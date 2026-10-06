"use client";

import { useState, useMemo, useEffect } from "react";
import { ClientPortal } from "@/components/portals/ClientPortal";
import { api } from "@/lib/api";
import { storage } from "@/lib/storage";
import { translations, Language } from "@/lib/i18n";
import {
  X,
  Lock,
  User as UserIcon,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Eye,
  EyeOff,
  ShieldCheck,
  Clock,
} from "lucide-react";

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

  const passwordsMatch = confirmPassword.length > 0 && password === confirmPassword;

  const strength = useMemo(() => {
    if (!password) return { score: 0, percent: 0, label: "", color: "bg-slate-200 dark:bg-slate-700" };
    let passed = 0;
    if (rules.length) passed++;
    if (rules.uppercase) passed++;
    if (rules.lowercase) passed++;
    if (rules.digit) passed++;
    if (rules.special) passed++;
    if (rules.noSpace && password.length >= 12) passed++;
    const score = Math.min(passed, 5);
    switch (score) {
      case 1: return { score: 1, percent: 20, label: t.strength_very_weak, color: "bg-rose-500" };
      case 2: return { score: 2, percent: 40, label: t.strength_weak, color: "bg-orange-500" };
      case 3: return { score: 3, percent: 60, label: t.strength_fair, color: "bg-amber-500" };
      case 4: return { score: 4, percent: 80, label: t.strength_strong, color: "bg-emerald-500" };
      case 5: return { score: 5, percent: 100, label: t.strength_very_strong, color: "bg-indigo-600 dark:bg-indigo-500" };
      default: return { score: 0, percent: 0, label: "", color: "bg-slate-200 dark:bg-slate-700" };
    }
  }, [password, rules, t]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanUser = username.trim();
    const cleanPass = password;
    const cleanFullName = fullName.trim();

    if (lockoutSeconds > 0) {
      setError(`${t.lockout_notice} ${lockoutSeconds}s`);
      return;
    }
    if (!cleanUser || !cleanPass) {
      setError(lang === "vi"
        ? "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu."
        : "Please enter username and password.");
      return;
    }
    if (!isLogin) {
      if (!allRulesPassed) {
        setError(lang === "vi"
          ? "Mật khẩu cần ít nhất 8 ký tự, 1 chữ hoa, 1 chữ thường, 1 số và 1 ký tự đặc biệt."
          : "Password must have at least 8 chars, 1 uppercase, 1 lowercase, 1 number and 1 special character.");
        return;
      }
      if (cleanPass !== confirmPassword) {
        setError(t.pass_match_err);
        return;
      }
    }

    setLoading(true);
    setError("");
    setSuccessMsg("");

    try {
      const res = isLogin
        ? await api.login(cleanUser, cleanPass)
        : await api.register(cleanUser, cleanPass, cleanFullName);

      if (res.status === "success") {
        const token = res.token || res.access_token;
        if (token) {
          storage.setToken(token);
          onSuccess(res.username || cleanUser, res.full_name || cleanFullName);
          onClose();
        } else {
          setSuccessMsg(lang === "vi"
            ? "Đăng ký thành công! Hãy đăng nhập."
            : "Registered successfully! Please log in.");
          setIsLogin(true);
          setPassword("");
          setConfirmPassword("");
        }
      } else {
        const rawDetail = res.detail || res.message || "";
        const matchSec = rawDetail.match(/(\d+)\s*(?:giây|seconds)/i);
        if (matchSec && Number(matchSec[1])) {
          setLockoutSeconds(Number(matchSec[1]));
        } else if (rawDetail.includes("429") || rawDetail.includes("quá nhiều lần")) {
          setLockoutSeconds(60);
        }
        setError(rawDetail || (isLogin
          ? (lang === "vi" ? "Đăng nhập thất bại" : "Login failed")
          : (lang === "vi" ? "Đăng ký thất bại" : "Registration failed")));
      }
    } catch (err: any) {
      setError(typeof err?.message === "string" ? err.message : t.network_error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <ClientPortal zIndex={60}>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
        <div className="relative w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-2xl border border-slate-200 dark:border-slate-800 my-8">

          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2 mb-2">
            <ShieldCheck className="w-6 h-6 text-brand-600 dark:text-brand-400" />
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              {isLogin ? t.login : t.register}
            </h2>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-5">
            {isLogin ? t.auth_login_desc : t.auth_register_desc}
          </p>

          {/* Lockout Banner */}
          {lockoutSeconds > 0 && (
            <div className="mb-4 p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/60 border border-amber-300 dark:border-amber-800 text-amber-800 dark:text-amber-200 text-sm flex items-center gap-2.5">
              <Clock className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 animate-pulse" />
              <div className="flex-1 font-semibold">
                {t.lockout_notice}{" "}
                <span className="font-mono text-base font-bold text-amber-900 dark:text-amber-100">
                  {lockoutSeconds}s
                </span>
              </div>
            </div>
          )}

          {/* Error Banner */}
          {error && (
            <div className="mb-4 p-3.5 rounded-xl bg-red-50 dark:bg-red-950/60 border border-red-200 dark:border-red-800/80 text-red-700 dark:text-red-300 text-sm flex items-start gap-2.5">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
              <div className="flex-1 font-medium">{error}</div>
            </div>
          )}

          {/* Success Banner */}
          {successMsg && (
            <div className="mb-4 p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800/80 text-emerald-700 dark:text-emerald-300 text-sm flex items-start gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
              <div className="flex-1 font-medium">{successMsg}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full Name (Register Only) */}
            {!isLogin && (
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-1.5">
                  {t.full_name}
                </label>
                <div className="relative">
                  <UserIcon className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    autoComplete="name"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder={t.full_name_placeholder}
                    className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>
            )}

            {/* Username */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-1.5">
                {t.username}
              </label>
              <div className="relative">
                <UserIcon className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder={t.username}
                  className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-1.5">
                {t.password}
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type={showPassword ? "text" : "password"}
                  autoComplete={isLogin ? "current-password" : "new-password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t.password}
                  className="w-full pl-9 pr-10 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 font-sans"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Strength Meter & Checklist (Register Only) */}
            {!isLogin && password.length > 0 && (
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between items-center text-xs mb-1.5 font-medium text-slate-600 dark:text-slate-300">
                    <span>{t.strength_meter_title}</span>
                    <span className="font-semibold">{strength.label}</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 rounded-full ${strength.color}`}
                      style={{ width: `${strength.percent}%` }}
                    />
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 space-y-1.5 text-xs">
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
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-1.5">
                  {t.confirm_password}
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder={t.confirm_password_placeholder}
                    className="w-full pl-9 pr-10 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 font-sans"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                    aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                  >
                    {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {confirmPassword.length > 0 && (
                  <div className={`mt-1.5 text-xs flex items-center gap-1.5 font-medium ${
                    passwordsMatch
                      ? "text-emerald-600 dark:text-emerald-400"
                      : "text-rose-600 dark:text-rose-400"
                  }`}>
                    {passwordsMatch ? (
                      <><CheckCircle2 className="w-3.5 h-3.5" /><span>{t.pass_match_ok}</span></>
                    ) : (
                      <><XCircle className="w-3.5 h-3.5" /><span>{t.pass_match_err}</span></>
                    )}
                  </div>
                )}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || lockoutSeconds > 0 || (!isLogin && (!allRulesPassed || !passwordsMatch))}
              className="w-full py-2.5 rounded-lg font-semibold text-white bg-brand-700 hover:bg-brand-800 dark:bg-brand-600 dark:hover:bg-brand-700 shadow transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {loading ? t.loading : isLogin ? t.login : t.register}
            </button>
          </form>

          <div className="mt-5 text-center text-sm text-slate-500 dark:text-slate-400">
            <span>{isLogin ? t.no_account : t.has_account}</span>{" "}
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin);
                setError("");
                setSuccessMsg("");
              }}
              className="font-bold text-brand-700 dark:text-brand-400 hover:underline"
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
      passed
        ? "text-emerald-700 dark:text-emerald-400 font-medium"
        : "text-slate-400 dark:text-slate-500"
    }`}>
      {passed ? (
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
      ) : (
        <XCircle className="w-3.5 h-3.5 text-slate-400 dark:text-slate-600 shrink-0" />
      )}
      <span>{label}</span>
    </div>
  );
}
