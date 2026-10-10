'use client';

import React, { useState } from 'react';
import { ClientPortal } from '@/components/portals/ClientPortal';
import { api } from '@/lib/api';
import {
  X,
  Coins,
  ShieldCheck,
  Sparkles,
  CheckCircle2,
  Copy,
  Lock,
  RefreshCw,
} from 'lucide-react';

/**
 * CoinTopupModal credits demo coins through the authenticated backend endpoint.
 */

export interface CoinTopupModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentBalance?: number;
  username?: string;
  onTopupSuccess?: (addedCoins: number, newBalance: number) => void;
  lang?: 'vi' | 'en';
}

interface TopupPackage {
  id: string;
  vnd: number;
  coins: number;
  bonus: number;
  popular?: boolean;
}

const PACKAGES: TopupPackage[] = [
  { id: 'pkg_50', vnd: 50000, coins: 50, bonus: 0 },
  { id: 'pkg_100', vnd: 100000, coins: 100, bonus: 0, popular: true },
  { id: 'pkg_200', vnd: 200000, coins: 220, bonus: 20 },
  { id: 'pkg_500', vnd: 500000, coins: 580, bonus: 80 },
];

export function CoinTopupModal({
  isOpen,
  onClose,
  currentBalance = 100,
  username = 'creator',
  onTopupSuccess,
  lang = 'vi',
}: CoinTopupModalProps) {
  const [selectedPkg, setSelectedPkg] = useState<TopupPackage>(PACKAGES[1]);
  const [copied, setCopied] = useState<boolean>(false);
  const [processing, setProcessing] = useState<boolean>(false);
  const [successNotice, setSuccessNotice] = useState<boolean>(false);
  const [topupError, setTopupError] = useState<string | null>(null);

  if (!isOpen) return null;

  const transferCode = `NARRAI_${username.toUpperCase().replace(/[^A-Z0-9]/g, '')}_${selectedPkg.coins}XU`;

  const handleCopyCode = () => {
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(transferCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleTopup = async () => {
    if (processing) return;
    setProcessing(true);
    setTopupError(null);
    try {
      const result = await api.topupCoins(selectedPkg.coins + selectedPkg.bonus);
      setSuccessNotice(true);
      onTopupSuccess?.(result.amount, result.new_balance);
      setTimeout(() => {
        setSuccessNotice(false);
        onClose();
      }, 1600);
    } catch (error) {
      setTopupError(error instanceof Error
        ? error.message
        : (lang === 'vi' ? 'Không thể nạp xu.' : 'Unable to top up coins.'));
    } finally {
      setProcessing(false);
    }
  };

  return (
    <ClientPortal zIndex={60}>
      <div className="fixed inset-0 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md overflow-y-auto">
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="coin-modal-title"
          className="relative w-full max-w-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden my-8"
        >
          {/* Header Banner */}
          <div className="relative bg-gradient-to-r from-amber-500 via-amber-600 to-amber-700 px-6 py-5 text-white flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center border border-white/30 shadow-inner">
                <Coins className="w-6 h-6 text-amber-100" />
              </div>
              <div>
                <h2 id="coin-modal-title" className="text-lg font-bold">
                  {lang === 'vi' ? 'Nạp Xu Sáng Tác NarrAI' : 'Top Up NarrAI Coins'}
                </h2>
                <p className="text-xs text-amber-100 opacity-90">
                  {lang === 'vi'
                    ? 'Chế độ demo MVP: xu được cộng trực tiếp, chưa xử lý thanh toán ngân hàng.'
                    : 'MVP demo mode: coins are credited directly; no bank payment is processed.'}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-colors"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="p-6 space-y-6">
            {/* Current Balance Bar */}
            <div className="flex items-center justify-between p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200/80 dark:border-amber-800/60">
              <div className="flex items-center gap-2 text-sm text-amber-900 dark:text-amber-200">
                <Sparkles className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                <span>{lang === 'vi' ? 'Số dư hiện tại:' : 'Current balance:'}</span>
              </div>
              <div className="font-mono font-bold text-lg text-amber-700 dark:text-amber-300">
                {currentBalance.toLocaleString()} {lang === 'vi' ? 'Xu' : 'Coins'}
              </div>
            </div>

            {/* Package Grid */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2.5">
                {lang === 'vi' ? 'Chọn gói nạp' : 'Select Package'}
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {PACKAGES.map((pkg) => {
                  const isSelected = selectedPkg.id === pkg.id;
                  return (
                    <button
                      key={pkg.id}
                      type="button"
                      onClick={() => {
                        setSelectedPkg(pkg);
                        setTopupError(null);
                      }}
                      disabled={processing || successNotice}
                      className={`relative p-3 rounded-xl border text-left transition-all ${
                        isSelected
                          ? 'border-amber-500 bg-amber-500/10 dark:bg-amber-500/20 shadow-sm ring-2 ring-amber-500/40'
                          : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 bg-slate-50 dark:bg-slate-800/50'
                      }`}
                    >
                      {pkg.popular && (
                        <span className="absolute -top-2 -right-1 px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-amber-600 text-white shadow-xs">
                          {lang === 'vi' ? 'Hot' : 'Popular'}
                        </span>
                      )}
                      <div className="font-bold text-base text-slate-900 dark:text-white">
                        {pkg.coins + pkg.bonus}{' '}
                        <span className="text-xs font-normal text-amber-600 dark:text-amber-400">
                          {lang === 'vi' ? 'Xu' : 'Coins'}
                        </span>
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        {pkg.vnd.toLocaleString()} đ
                      </div>
                      {pkg.bonus > 0 && (
                        <div className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 mt-1">
                          +{pkg.bonus} {lang === 'vi' ? 'thưởng' : 'bonus'}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Usage Cost Reference */}
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs space-y-1.5">
              <div className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-slate-400" />
                <span>{lang === 'vi' ? 'Biểu phí định giá minh bạch:' : 'Transparent Pricing Guide:'}</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 text-slate-600 dark:text-slate-400 text-[11px]">
                <div>• {lang === 'vi' ? 'Truyện ngắn: 8 xu' : 'Short story: 8 coins'}</div>
                <div>• {lang === 'vi' ? 'Truyện dài: 16 xu' : 'Long story: 16 coins'}</div>
                <div>• {lang === 'vi' ? 'Sửa văn bản: 2 xu' : 'Edit prose: 2 coins'}</div>
                <div>• {lang === 'vi' ? 'Manga: 16 xu' : 'Manga adaptation: 16 coins'}</div>
                <div className="col-span-2 text-emerald-600 dark:text-emerald-400 font-medium">
                  • 100 xu: ~3 truyện + 10 lần sửa + 2 lần manga
                </div>
              </div>
            </div>

            {/* Demo top-up reference */}
            <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-4 space-y-3 bg-white dark:bg-slate-900">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
                  {lang === 'vi' ? 'Mã tham chiếu demo:' : 'Demo reference:'}
                </span>
                <button
                  type="button"
                  onClick={handleCopyCode}
                  className="inline-flex items-center gap-1 text-xs font-semibold text-amber-600 dark:text-amber-400 hover:underline"
                >
                  {copied ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span>{lang === 'vi' ? 'Đã sao chép' : 'Copied'}</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>{lang === 'vi' ? 'Sao chép' : 'Copy'}</span>
                    </>
                  )}
                </button>
              </div>

              <div className="font-mono text-xs sm:text-sm font-bold p-2.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 select-all break-all border border-slate-200 dark:border-slate-700">
                {transferCode}
              </div>

              {/* Demo-mode disclosure */}
              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center gap-2 text-[11px] text-slate-500 dark:text-slate-400">
                <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                <span>
                  {lang === 'vi'
                    ? 'Không cần chuyển khoản trong bản demo. Chọn gói sẽ cộng xu vào số dư tài khoản.'
                    : 'No bank transfer is required in this demo. Selecting a package credits your account.'}
                </span>
              </div>
            </div>

            {topupError && (
              <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
                {topupError}
              </div>
            )}

            {/* Success Notification */}
            {successNotice && (
              <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 text-sm flex items-center gap-2 animate-fadeIn font-semibold">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                <span>
                  {lang === 'vi'
                    ? `Nạp thành công +${selectedPkg.coins + selectedPkg.bonus} Xu vào tài khoản!`
                    : `Successfully topped up +${selectedPkg.coins + selectedPkg.bonus} Coins!`}
                </span>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-sm font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                {lang === 'vi' ? 'Đóng' : 'Close'}
              </button>
              <button
                type="button"
                onClick={handleTopup}
                disabled={processing || successNotice}
                className="px-5 py-2 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 shadow-md shadow-amber-500/20 flex items-center gap-2 transition-all disabled:opacity-60"
              >
                {processing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>{lang === 'vi' ? 'Đang cập nhật số dư...' : 'Updating balance...'}</span>
                  </>
                ) : (
                  <>
                    <Coins className="w-4 h-4" />
                    <span>
                      {lang === 'vi' ? 'Nạp xu demo' : 'Add demo coins'}
                    </span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </ClientPortal>
  );
}

export default CoinTopupModal;
