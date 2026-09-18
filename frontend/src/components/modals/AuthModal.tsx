"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { storage } from "@/lib/storage";
import { translations, Language } from "@/lib/i18n";
import { X, Lock, User as UserIcon } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (username: string) => void;
  lang: Language;
}

export function AuthModal({ isOpen, onClose, onSuccess, lang }: Props) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const t = translations[lang];

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError(lang === 'vi' ? "Vui lòng nhập đầy đủ tài khoản và mật khẩu." : "Please enter username and password.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = isLogin
        ? await api.login(username.trim(), password)
        : await api.register(username.trim(), password);

      if (res.status === 'success' && res.token) {
        storage.setToken(res.token);
        onSuccess(username.trim());
        onClose();
      } else {
        setError(res.message || res.detail || (isLogin ? "Đăng nhập thất bại" : "Đăng ký thất bại"));
      }
    } catch (err: any) {
      setError(err.message || "Lỗi kết nối máy chủ");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-2xl border border-slate-200 dark:border-slate-800">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
        >
          <X className="w-5 h-5" />
        </button>

        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
          {isLogin ? t.login : t.register}
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
          {isLogin
            ? (lang === 'vi' ? "Đăng nhập để lưu trữ và tiếp tục bản thảo của bạn." : "Log in to save and resume your manuscripts.")
            : (lang === 'vi' ? "Tạo tài khoản miễn phí và bắt đầu sáng tác ngay." : "Create a free account and start writing today.")}
        </p>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-1.5">
              {t.username}
            </label>
            <div className="relative">
              <UserIcon className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder={t.username}
                className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-1.5">
              {t.password}
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t.password}
                className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg font-semibold text-white bg-brand-700 hover:bg-brand-800 dark:bg-brand-600 dark:hover:bg-brand-700 shadow transition-colors disabled:opacity-50"
          >
            {loading ? t.loading : (isLogin ? t.login : t.register)}
          </button>
        </form>

        <div className="mt-5 text-center text-sm text-slate-500 dark:text-slate-400">
          <span>{isLogin ? t.no_account : t.has_account}</span>{" "}
          <button
            type="button"
            onClick={() => {
              setIsLogin(!isLogin);
              setError("");
            }}
            className="font-bold text-brand-700 dark:text-brand-400 hover:underline"
          >
            {isLogin ? t.register_now : t.login_now}
          </button>
        </div>
      </div>
    </div>
  );
}
