'use client';

import React, { useState, useEffect, useRef } from 'react';
import { ClientPortal } from '@/components/portals/ClientPortal';

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
    avatarColor: 'bg-neutral-800',
    status: 'online',
    lastMessage: 'Tôi vừa xem 4 khung tranh vừa tạo, nét vẽ rất khớp với bản thảo!',
    lastTime: '10:42',
    unreadCount: 1,
  },
  {
    id: 'c2',
    username: 'minh_chau',
    fullName: 'Minh Châu (Biên kịch Dã sử)',
    avatarColor: 'bg-neutral-700',
    status: 'online',
    lastMessage: 'Cốt truyện Thánh Gióng ở hồi 2 nên đẩy cao trào trận địa.',
    lastTime: 'Hôm qua',
    unreadCount: 0,
  },
  {
    id: 'c3',
    username: 'tuan_anh_99',
    fullName: 'Tuấn Anh',
    avatarColor: 'bg-neutral-600',
    status: 'offline',
    lastMessage: 'Bạn có nhận hợp tác chuyển thể Light Novel thành truyện tranh không?',
    lastTime: '3 ngày trước',
    unreadCount: 0,
  },
];

const INITIAL_MESSAGES: Record<string, MessageItem[]> = {
  c1: [
    {
      id: 'm1',
      sender: 'hoang_nam',
      text: 'Chào bạn! Mình theo dõi bộ truyện chữ của bạn từ chương 1.',
      timestamp: '10:30',
      isMe: false,
    },
    {
      id: 'm2',
      sender: 'me',
      text: 'Cảm ơn Nam nhé! Mình đang dùng Comic AI Agent để chuyển sang khung tranh.',
      timestamp: '10:35',
      isMe: true,
    },
    {
      id: 'm3',
      sender: 'hoang_nam',
      text: 'Tôi vừa xem 4 khung tranh vừa tạo, nét vẽ rất khớp với bản thảo!',
      timestamp: '10:42',
      isMe: false,
    },
  ],
  c2: [
    {
      id: 'm2_1',
      sender: 'minh_chau',
      text: 'Chào đồng nghiệp! Tư liệu lịch sử thời Tiền Lê bạn lấy từ đâu thế?',
      timestamp: '14:20',
      isMe: false,
    },
    {
      id: 'm2_2',
      sender: 'me',
      text: 'Mình dùng kho dữ liệu lorebook và Story Bible tích hợp sẵn của NarrAI.',
      timestamp: '14:25',
      isMe: true,
    },
    {
      id: 'm2_3',
      sender: 'minh_chau',
      text: 'Cốt truyện Thánh Gióng ở hồi 2 nên đẩy cao trào trận địa.',
      timestamp: 'Hôm qua',
      isMe: false,
    },
  ],
  c3: [
    {
      id: 'm3_1',
      sender: 'tuan_anh_99',
      text: 'Bạn có nhận hợp tác chuyển thể Light Novel thành truyện tranh không?',
      timestamp: '3 ngày trước',
      isMe: false,
    },
  ],
};

export function MessengerModal({
  isOpen,
  onClose,
  currentUser = 'creator',
  lang = 'vi',
}: MessengerModalProps) {
  const [contacts, setContacts] = useState<ChatContact[]>(INITIAL_CONTACTS);
  const [selectedContact, setSelectedContact] = useState<ChatContact>(INITIAL_CONTACTS[0]);
  const [messagesMap, setMessagesMap] = useState<Record<string, MessageItem[]>>(INITIAL_MESSAGES);
  const [searchQuery, setSearchQuery] = useState('');
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeMessages = messagesMap[selectedContact.id] || [];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
      setContacts((prev) =>
        prev.map((c) => (c.id === selectedContact.id ? { ...c, unreadCount: 0 } : c))
      );
    }
  }, [isOpen, selectedContact.id, activeMessages.length]);

  if (!isOpen) return null;

  const filteredContacts = contacts.filter(
    (c) =>
      c.fullName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const newMsg: MessageItem = {
      id: `msg_${Date.now()}`,
      sender: currentUser,
      text: inputText.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isMe: true,
    };

    setMessagesMap((prev) => ({
      ...prev,
      [selectedContact.id]: [...(prev[selectedContact.id] || []), newMsg],
    }));

    setContacts((prev) =>
      prev.map((c) =>
        c.id === selectedContact.id
          ? {
              ...c,
              lastMessage: inputText.trim(),
              lastTime: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            }
          : c
      )
    );

    setInputText('');
  };

  return (
    <ClientPortal zIndex={60}>
      <div className="fixed inset-0 flex items-center justify-center p-3 sm:p-6 bg-black/70 backdrop-blur-md overflow-hidden select-none font-sans">
        <div
          role="dialog"
          aria-modal="true"
          aria-label={lang === 'vi' ? 'Hộp thoại Open Messenger' : 'Open Messenger Dialog'}
          className="relative w-full max-w-4xl h-[86vh] max-h-[720px] bg-[#FAF7F2] border border-neutral-300/80 rounded-xl shadow-2xl overflow-hidden flex flex-col md:flex-row text-neutral-900"
        >
          {/* Left Panel: Contact List & Directory Search */}
          <div className="w-full md:w-80 border-r border-neutral-300/80 flex flex-col shrink-0 bg-[#FAF7F2] font-mono">
            {/* Header */}
            <div className="p-4 border-b border-neutral-300/80 flex items-center justify-between bg-[#FAF7F2]">
              <div className="flex items-center gap-2">
                <span className="px-1.5 py-0.5 rounded border border-neutral-300 bg-white text-xs font-bold uppercase text-neutral-800">
                  [TIN NHẮN]
                </span>
                <h2 className="font-bold text-xs sm:text-sm uppercase tracking-wider text-neutral-900">
                  Open Messenger
                </h2>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded border border-neutral-300 bg-[#F5EFE6] text-neutral-800">
                {lang === 'vi' ? 'Toàn mạng' : 'Open'}
              </span>
            </div>

            {/* Search Box */}
            <div className="p-3 bg-[#FAF7F2]">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={lang === 'vi' ? 'Tìm tác giả, độc giả...' : 'Search creators, readers...'}
                className="w-full px-3 py-1.5 rounded text-xs bg-white border border-neutral-300 text-neutral-900 placeholder:text-neutral-400 focus:outline-none focus:border-neutral-500"
              />
            </div>

            {/* Contact List */}
            <div className="flex-1 overflow-y-auto divide-y divide-neutral-200/80">
              {filteredContacts.length === 0 ? (
                <div className="p-6 text-center text-xs text-neutral-500">
                  {lang === 'vi' ? 'Không tìm thấy người dùng' : 'No users found'}
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
                          ? 'bg-white font-bold border-l-4 border-l-neutral-900 shadow-xs'
                          : 'hover:bg-[#F5EFE6]'
                      }`}
                    >
                      <div className="relative shrink-0">
                        <div
                          className={`w-8 h-8 rounded-full ${contact.avatarColor} text-white font-bold flex items-center justify-center text-xs shadow-xs`}
                        >
                          {contact.fullName.charAt(0)}
                        </div>
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="text-xs truncate text-neutral-900 font-medium">
                            {contact.fullName}
                          </span>
                          <span className="text-[10px] text-neutral-500 shrink-0 ml-1">
                            {contact.lastTime}
                          </span>
                        </div>
                        <p className="text-[11px] text-neutral-500 truncate mt-0.5 font-sans">
                          {contact.lastMessage}
                        </p>
                      </div>

                      {contact.unreadCount > 0 && (
                        <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-neutral-900 text-white shrink-0">
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
          <div className="flex-1 flex flex-col h-full bg-[#FAF7F2] min-w-0">
            {/* Thread Header */}
            <div className="h-14 px-5 border-b border-neutral-300/80 flex items-center justify-between shrink-0 bg-[#FAF7F2] font-mono">
              <div className="flex items-center gap-3 min-w-0">
                <div
                  className={`w-8 h-8 rounded-full ${selectedContact.avatarColor} text-white font-bold flex items-center justify-center text-xs shrink-0`}
                >
                  {selectedContact.fullName.charAt(0)}
                </div>
                <div className="min-w-0">
                  <div className="font-bold text-xs sm:text-sm text-neutral-900 truncate">
                    {selectedContact.fullName}
                  </div>
                  <div className="text-[10px] text-neutral-500 flex items-center gap-1.5">
                    <span>
                      {selectedContact.status === 'online'
                        ? lang === 'vi'
                          ? '[Online]'
                          : '[Online]'
                        : lang === 'vi'
                        ? '[Offline]'
                        : '[Offline]'}
                    </span>
                    <span>• @{selectedContact.username}</span>
                  </div>
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

            {/* Messages Thread */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[#FAF7F2]/60">
              {activeMessages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col ${msg.isMe ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`max-w-[78%] px-4 py-2.5 rounded text-xs sm:text-sm shadow-xs ${
                      msg.isMe
                        ? 'bg-neutral-900 text-white font-sans'
                        : 'bg-white border border-neutral-300 text-neutral-900 font-sans'
                    }`}
                  >
                    <p className="leading-relaxed whitespace-pre-wrap break-words">{msg.text}</p>
                  </div>
                  <div className="flex items-center gap-1 mt-1 text-[10px] font-mono text-neutral-500 px-1">
                    <span>{msg.timestamp}</span>
                    {msg.isMe && <span>[✓✓]</span>}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input Box */}
            <form
              onSubmit={handleSendMessage}
              className="p-3 border-t border-neutral-300/80 bg-[#FAF7F2] flex items-center gap-2 font-mono"
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
                className="flex-1 px-4 py-2 rounded text-xs bg-white border border-neutral-300 text-neutral-900 placeholder:text-neutral-400 focus:outline-none focus:border-neutral-500"
              />
              <button
                type="submit"
                disabled={!inputText.trim()}
                className="px-4 py-2 rounded bg-neutral-900 hover:bg-neutral-800 text-white font-bold text-xs uppercase tracking-wider transition-colors disabled:opacity-40 shadow-xs"
              >
                [Gửi]
              </button>
            </form>
          </div>
        </div>
      </div>
    </ClientPortal>
  );
}

export default MessengerModal;
