'use client';

import React, { useState, useEffect, useRef } from 'react';
import { ClientPortal } from '@/components/portals/ClientPortal';
import {
  X,
  Send,
  Search,
  MessageSquare,
  User,
  Check,
  CheckCheck,
  Sparkles,
  Smile,
  Shield,
  Clock,
} from 'lucide-react';

/**
 * MessengerModal (Layer 3 Glassmorphism Open Messenger)
 *
 * Architecture:
 * - Free 1-1 Chat between ANY users in the system (Open Messenger)
 * - User Directory search with instant filter
 * - Conversation management, unread indicators, and sent timestamps
 * - Wrapped in ClientPortal with isolation: isolate & z-index: 60
 * - Multi-plane responsive layout (contact list + message thread)
 */

export interface MessengerModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser?: string;
  lang?: 'vi' | 'en';
}

interface ChatContact {
  id: string;
  username: string;
  fullName: string;
  avatarColor: string;
  status: 'online' | 'offline';
  lastMessage: string;
  lastTime: string;
  unreadCount: number;
}

interface MessageItem {
  id: string;
  sender: string;
  text: string;
  timestamp: string;
  isMe: boolean;
}

const INITIAL_CONTACTS: ChatContact[] = [
  {
    id: 'c1',
    username: 'hoang_nam',
    fullName: 'Hoàng Nam (Manga Artist)',
    avatarColor: 'bg-[#805342]',
    status: 'online',
    lastMessage: 'Nét vẽ khung tranh số 4 rất ấn tượng bạn nhé!',
    lastTime: '10:32',
    unreadCount: 1,
  },
  {
    id: 'c2',
    username: 'mai_anh',
    fullName: 'Mai Anh (Biên tập viên)',
    avatarColor: 'bg-emerald-500',
    status: 'online',
    lastMessage: 'Đoạn mở đầu In Medias Res đọc cuốn lắm!',
    lastTime: 'Hôm qua',
    unreadCount: 0,
  },
  {
    id: 'c3',
    username: 'quoc_tuan',
    fullName: 'Quốc Tuấn (Tác giả Light Novel)',
    avatarColor: 'bg-amber-500',
    status: 'offline',
    lastMessage: 'Bạn có tham gia sự kiện sáng tác tuần này không?',
    lastTime: '2 ngày trước',
    unreadCount: 0,
  },
  {
    id: 'c4',
    username: 'thu_ha',
    fullName: 'Thu Hà (Độc giả)',
    avatarColor: 'bg-rose-500',
    status: 'offline',
    lastMessage: 'Hóng chương mới của bộ truyện lịch sử ạ.',
    lastTime: '3 ngày trước',
    unreadCount: 0,
  },
];

export function MessengerModal({
  isOpen,
  onClose,
  currentUser = 'creator',
  lang = 'vi',
}: MessengerModalProps) {
  const [contacts, setContacts] = useState<ChatContact[]>(INITIAL_CONTACTS);
  const [selectedContact, setSelectedContact] = useState<ChatContact>(INITIAL_CONTACTS[0]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [inputText, setInputText] = useState<string>('');

  const [messages, setMessages] = useState<Record<string, MessageItem[]>>({
    c1: [
      {
        id: 'm1',
        sender: 'hoang_nam',
        text: 'Chào bạn! Mình vừa xem qua bản thảo manga của bạn.',
        timestamp: '10:28',
        isMe: false,
      },
      {
        id: 'm2',
        sender: currentUser,
        text: 'Chào bạn Nam, cảm ơn bạn đã quan tâm! Bạn thấy phần nét vẽ thế nào?',
        timestamp: '10:30',
        isMe: true,
      },
      {
        id: 'm3',
        sender: 'hoang_nam',
        text: 'Nét vẽ khung tranh số 4 rất ấn tượng bạn nhé! Phối cảnh chiều sâu rất tốt.',
        timestamp: '10:32',
        isMe: false,
      },
    ],
    c2: [
      {
        id: 'm4',
        sender: 'mai_anh',
        text: 'Đoạn mở đầu In Medias Res đọc cuốn lắm!',
        timestamp: 'Hôm qua',
        isMe: false,
      },
    ],
  });

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, selectedContact]);

  if (!isOpen) return null;

  const filteredContacts = contacts.filter(
    (c) =>
      c.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.fullName.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const activeMessages = messages[selectedContact.id] || [];

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = inputText.trim();
    if (!trimmed) return;

    const newMsg: MessageItem = {
      id: `msg_${Date.now()}`,
      sender: currentUser,
      text: trimmed,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isMe: true,
    };

    setMessages((prev) => ({
      ...prev,
      [selectedContact.id]: [...(prev[selectedContact.id] || []), newMsg],
    }));

    setInputText('');

    // Update last message in contact list
    setContacts((prev) =>
      prev.map((c) =>
        c.id === selectedContact.id
          ? { ...c, lastMessage: trimmed, lastTime: 'Vừa xong' }
          : c
      )
    );
  };

  return (
    <ClientPortal zIndex={60}>
      <div className="fixed inset-0 flex items-center justify-center p-3 sm:p-6 bg-slate-950/70 backdrop-blur-md overflow-hidden">
        <div
          role="dialog"
          aria-modal="true"
          aria-label={lang === 'vi' ? 'Hộp thoại Open Messenger' : 'Open Messenger Dialog'}
          className="relative w-full max-w-4xl h-[86vh] max-h-[720px] bg-[#fbf8f1] dark:bg-[#302a25] border border-[#e2d8cb] dark:border-[#50453c] rounded-xl shadow-xl overflow-hidden flex flex-col md:flex-row"
        >
          {/* Left Panel: Contact List & Directory Search */}
          <div className="w-full md:w-80 border-r border-[#ded5c9] dark:border-[#50453c] flex flex-col shrink-0 bg-[#f4f0e8] dark:bg-[#28231f]">
            {/* Header */}
            <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-[#805342] dark:text-[#dfb79b]" />
                <h2 className="font-bold text-sm sm:text-base text-slate-900 dark:text-white">
                  Open Messenger
                </h2>
              </div>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-[#eee4d7] text-[#704331] dark:bg-[#45352c] dark:text-[#dfb79b] border border-[#ddc9b5] dark:border-[#665044]">
                {lang === 'vi' ? 'Toàn mạng' : 'Open'}
              </span>
            </div>

            {/* Search Box */}
            <div className="p-3">
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={lang === 'vi' ? 'Tìm tác giả, độc giả...' : 'Search creators, readers...'}
                  className="w-full pl-9 pr-3 py-1.5 rounded-xl text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 text-slate-900 dark:text-white"
                />
              </div>
            </div>

            {/* Contact List */}
            <div className="flex-1 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800/60">
              {filteredContacts.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-400">
                  {lang === 'vi' ? 'Không tìm thấy người dùng phù hợp' : 'No users found'}
                </div>
              ) : (
                filteredContacts.map((contact) => {
                  const isSelected = contact.id === selectedContact.id;
                  return (
                    <button
                      key={contact.id}
                      type="button"
                      onClick={() => setSelectedContact(contact)}
                      className={`w-full p-3 flex items-start gap-3 text-left transition-colors ${
                        isSelected
                          ? 'bg-[#fbf8f1] dark:bg-[#302a25] border-l-4 border-[#805342] shadow-xs'
                          : 'hover:bg-slate-100/60 dark:hover:bg-slate-800/40'
                      }`}
                    >
                      <div className="relative shrink-0">
                        <div
                          className={`w-9 h-9 rounded-full ${contact.avatarColor} text-white font-bold flex items-center justify-center text-xs shadow-sm`}
                        >
                          {contact.fullName.charAt(0)}
                        </div>
                        {contact.status === 'online' && (
                          <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white dark:ring-slate-900" />
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-xs text-slate-900 dark:text-slate-100 truncate">
                            {contact.fullName}
                          </span>
                          <span className="text-[10px] text-slate-400 shrink-0 ml-1">
                            {contact.lastTime}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate mt-0.5">
                          {contact.lastMessage}
                        </p>
                      </div>

                      {contact.unreadCount > 0 && (
                        <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-brand-700 text-white shrink-0">
                          {contact.unreadCount}
                        </span>
                      )}
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Right Panel: Active Chat Thread */}
          <div className="flex-1 flex flex-col h-full bg-[#fbf8f1] dark:bg-[#302a25] min-w-0">
            {/* Thread Header */}
            <div className="h-14 px-5 border-b border-[#ded5c9] dark:border-[#50453c] flex items-center justify-between shrink-0 bg-[#fbf8f1] dark:bg-[#302a25]">
              <div className="flex items-center gap-3 min-w-0">
                <div
                  className={`w-8 h-8 rounded-full ${selectedContact.avatarColor} text-white font-bold flex items-center justify-center text-xs shrink-0`}
                >
                  {selectedContact.fullName.charAt(0)}
                </div>
                <div className="min-w-0">
                  <div className="font-bold text-xs sm:text-sm text-slate-900 dark:text-white truncate">
                    {selectedContact.fullName}
                  </div>
                  <div className="text-[10px] text-slate-400 flex items-center gap-1.5">
                    <span
                      className={`inline-block w-1.5 h-1.5 rounded-full ${
                        selectedContact.status === 'online' ? 'bg-emerald-500' : 'bg-slate-400'
                      }`}
                    />
                    <span>
                      {selectedContact.status === 'online'
                        ? lang === 'vi'
                          ? 'Đang trực tuyến'
                          : 'Online'
                        : lang === 'vi'
                        ? 'Ngoại tuyến'
                        : 'Offline'}
                    </span>
                    <span>• @{selectedContact.username}</span>
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={onClose}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Messages Thread */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50/50 dark:bg-slate-950/20">
              {activeMessages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col ${msg.isMe ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`max-w-[78%] px-4 py-2.5 rounded-2xl text-xs sm:text-sm shadow-xs ${
                      msg.isMe
                        ? 'bg-[#714033] text-[#fffaf0] rounded-tr-xs'
                        : 'bg-[#f1ece3] dark:bg-[#3a312b] text-slate-900 dark:text-slate-100 border border-[#e2d8cb] dark:border-[#50453c] rounded-tl-xs'
                    }`}
                  >
                    <p className="leading-relaxed whitespace-pre-wrap break-words">{msg.text}</p>
                  </div>
                  <div className="flex items-center gap-1 mt-1 text-[10px] text-slate-400 px-1">
                    <span>{msg.timestamp}</span>
                    {msg.isMe && <CheckCheck className="w-3 h-3 text-[#9f684a]" />}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input Box */}
            <form
              onSubmit={handleSendMessage}
              className="p-3 border-t border-[#ded5c9] dark:border-[#50453c] bg-[#fbf8f1] dark:bg-[#302a25] flex items-center gap-2"
            >
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder={
                  lang === 'vi'
                    ? `Nhắn tin cho @${selectedContact.username}...`
                    : `Message @${selectedContact.username}...`
                }
                className="flex-1 px-4 py-2 rounded-xl text-xs sm:text-sm bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 text-slate-900 dark:text-white"
              />
              <button
                type="submit"
                disabled={!inputText.trim()}
                className="px-4 py-2 rounded-lg bg-[#714033] hover:bg-[#573229] text-[#fffaf0] font-semibold text-xs flex items-center gap-1.5 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">{lang === 'vi' ? 'Gửi' : 'Send'}</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </ClientPortal>
  );
}

export default MessengerModal;
