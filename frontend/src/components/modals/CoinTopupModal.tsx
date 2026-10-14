'use client';

import React, { useState } from 'react';
import { ClientPortal } from '@/components/portals/ClientPortal';
import { api } from '@/lib/api';

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

  const transferCode = `NARR_${username.toUpperCase().replace(/[^A-Z0-9]/g, '')}_${selectedPkg.coins}`;

  const handleCopyCode = () => {
    navigator.clipboard.writeText(transferCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleTopup = async () => {
    setProcessing(true);
    setTopupError(null);
    try {
      const addedCoins = selectedPkg.coins + selectedPkg.bonus;
      const res = await api.topupCoins(addedCoins);

      if (res && typeof res.new_balance === 'number') {
        setSuccessNotice(true);
        if (onTopupSuccess) {
          onTopupSuccess(addedCoins, res.new_balance);
        }
        setTimeout(() => {
          setSuccessNotice(false);
          onClose();
        }, 1500);
      } else {
        setTopupError('Nạp xu thất bại.');
      }
    } catch (err: any) {
      setTopupError(err.message || 'Lỗi kết nối khi nạp xu.');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <ClientPortal>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto select-none font-sans">
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="coin-modal-title"
          className="relative w-full max-w-lg bg-[#FAF7F2] rounded-xl shadow-2xl border border-neutral-300/80 overflow-hidden my-8 text-neutral-900"
        >
          {/* Header Banner */}
          <div className="border-b border-neutral-300/80 bg-[#FAF7F2] px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <span className="px-2 py-0.5 rounded border border-neutral-300 bg-white font-mono text-xs font-bold text-neutral-800">
                [XU]
              </span>
              <div>
                <h2 id="coin-modal-title" className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-900">
                  {lang === 'vi' ? 'Nạp Xu Sáng Tác NarrAI' : 'Top Up NarrAI Coins'}
                </h2>
                <p className="text-[11px] font-mono text-neutral-500">
                  {lang === 'vi'
                    ? 'Chế độ demo MVP: xu được cộng trực tiếp vào số dư.'
                    : 'MVP demo mode: coins are credited directly.'}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={onClose}
              className="px-2 py-0.5 text-xs font-mono font-bold uppercase rounded border border-neutral-300 text-neutral-600 hover:text-black hover:bg-neutral-100 transition-colors"
              aria-label="Close"
            >
              [ĐÓNG]
            </button>
          </div>

          <div className="p-6 space-y-5 font-mono">
            {/* Current Balance Bar */}
            <div className="flex items-center justify-between p-3 rounded border border-neutral-300/80 bg-white shadow-xs">
              <span className="text-xs text-neutral-500 uppercase tracking-wider">
                {lang === 'vi' ? 'Số dư hiện tại:' : 'Current balance:'}
              </span>
              <span className="font-bold text-base text-neutral-900">
                {currentBalance.toLocaleString()} XU
              </span>
            </div>

            {/* Package Grid */}
            <div>
              <label className="block text-xs font-bold text-neutral-600 uppercase tracking-wider mb-2">
                {lang === 'vi' ? 'Chọn gói nạp' : 'Select Package'}
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
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
                      className={`relative p-3 rounded border text-left transition-colors ${
                        isSelected
                          ? 'border-neutral-900 bg-neutral-100 font-bold text-neutral-950 shadow-xs ring-1 ring-neutral-900'
                          : 'border-neutral-300 bg-white hover:bg-neutral-50 text-neutral-800'
                      }`}
                    >
                      {pkg.popular && (
                        <span className="absolute -top-2 -right-1 px-1.5 py-0.2 rounded text-[9px] font-bold uppercase bg-neutral-900 text-white">
                          {lang === 'vi' ? 'Hot' : 'Popular'}
                        </span>
                      )}
                      <div className="font-bold text-sm text-neutral-900">
                        {pkg.coins + pkg.bonus} XU
                      </div>
                      <div className="text-[11px] text-neutral-500 mt-0.5">
                        {pkg.vnd.toLocaleString()} đ
                      </div>
                      {pkg.bonus > 0 && (
                        <div className="text-[10px] text-amber-700 mt-1 font-bold">
                          +{pkg.bonus} {lang === 'vi' ? 'thưởng' : 'bonus'}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Usage Cost Reference */}
            <div className="p-3 rounded bg-[#F5EFE6] border border-neutral-300/80 text-xs space-y-1.5">
              <div className="font-bold text-neutral-800 uppercase tracking-wider">
                {lang === 'vi' ? '[BIỂU PHÍ ĐỊNH GIÁ MINH BẠCH]' : '[PRICING GUIDE]'}
              </div>
              <div className="grid grid-cols-2 gap-1.5 text-neutral-600 text-[11px]">
                <div>• {lang === 'vi' ? 'Truyện ngắn: 8 xu' : 'Short story: 8 coins'}</div>
                <div>• {lang === 'vi' ? 'Truyện dài: 16 xu' : 'Long story: 16 coins'}</div>
                <div>• {lang === 'vi' ? 'Sửa văn bản: 2 xu' : 'Edit prose: 2 coins'}</div>
                <div>• {lang === 'vi' ? 'Manga: 100 xu/4 khung (sau 12 khung)' : 'Manga: 100 coins/4 panels'}</div>
              </div>
            </div>

            {/* Demo top-up reference */}
            <div className="border border-neutral-300/80 rounded p-3.5 space-y-2 bg-white shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-neutral-600">
                  {lang === 'vi' ? 'Mã tham chiếu:' : 'Reference code:'}
                </span>
                <button
                  type="button"
                  onClick={handleCopyCode}
                  className="text-xs font-bold underline text-neutral-900 hover:text-black"
                >
                  {copied ? (lang === 'vi' ? '[Đã sao chép]' : '[Copied]') : (lang === 'vi' ? '[Sao chép]' : '[Copy]')}
                </button>
              </div>

              <div className="font-mono text-xs font-bold p-2 rounded bg-[#FAF7F2] text-neutral-900 select-all break-all border border-neutral-300">
                {transferCode}
              </div>
            </div>

            {topupError && (
              <div role="alert" className="p-3 rounded border border-red-300 bg-red-50 text-red-800 text-xs font-mono">
                [LỖI]: {topupError}
              </div>
            )}

            {/* Success Notification */}
            {successNotice && (
              <div className="p-3 rounded border border-emerald-300 bg-emerald-50 text-emerald-800 text-xs font-mono font-bold">
                [THÀNH CÔNG]: +{selectedPkg.coins + selectedPkg.bonus} XU ĐÃ ĐƯỢC CỘNG VÀO SỐ DƯ!
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 pt-2 border-t border-neutral-300/80">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded text-xs font-mono font-bold uppercase border border-neutral-300 text-neutral-700 hover:text-black hover:bg-neutral-100 transition-colors"
              >
                {lang === 'vi' ? '[Đóng]' : '[Close]'}
              </button>
              <button
                type="button"
                onClick={handleTopup}
                disabled={processing || successNotice}
                className="px-5 py-2 rounded text-xs font-mono font-bold uppercase tracking-wider bg-neutral-900 text-white hover:bg-neutral-800 transition-colors disabled:opacity-40 shadow-xs"
              >
                {processing
                  ? (lang === 'vi' ? '[Đang nạp xu...]' : '[Processing...]')
                  : (lang === 'vi' ? `[Nạp +${selectedPkg.coins + selectedPkg.bonus} Xu Demo]` : `[Add +${selectedPkg.coins + selectedPkg.bonus} Coins]`)}
              </button>
            </div>
          </div>
        </div>
      </div>
    </ClientPortal>
  );
}
