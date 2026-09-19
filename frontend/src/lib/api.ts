import { storage } from './storage';
import {
  AuthResponse,
  StoryDetail,
  ComicResponse,
  InterviewResponse,
  RefineResponse,
  EditTextResponse,
  CopilotEventResponse,
  TrendingTopic,
} from './types';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://narrai-c1oc.onrender.com/api';

function authHeaders(): Record<string, string> {
  const token = storage.getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

function parseErrorDetail(data: any): string {
  if (!data) return "Lỗi không xác định từ máy chủ";
  if (typeof data === "string") return data;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((e: any) => e.msg || JSON.stringify(e)).join(", ");
  }
  if (data.message && typeof data.message === "string") return data.message;
  return "Đã xảy ra lỗi không xác định";
}

export const api = {
  // Auth
  async login(username: string, password: string): Promise<AuthResponse> {
    try {
      const formData = new URLSearchParams();
      formData.append('username', username.trim());
      formData.append('password', password);

      const res = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const errorText = parseErrorDetail(data);
        return {
          status: 'error',
          detail: errorText,
          message: errorText,
        };
      }

      const token = data.access_token || data.token;
      return {
        status: 'success',
        token,
        access_token: token,
        username: data.username || username.trim(),
      };
    } catch (err: any) {
      const msg = err?.message || "Không thể kết nối tới máy chủ (Network Error)";
      return {
        status: 'error',
        detail: msg,
        message: msg,
      };
    }
  },

  async register(username: string, password: string): Promise<AuthResponse> {
    try {
      const res = await fetch(`${API_BASE_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username.trim(), password }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const errorText = parseErrorDetail(data);
        return {
          status: 'error',
          detail: errorText,
          message: errorText,
        };
      }

      const token = data.access_token || data.token;
      return {
        status: 'success',
        message: data.message || 'Đăng ký thành công',
        token,
        access_token: token,
        username: data.username || username.trim(),
      };
    } catch (err: any) {
      const msg = err?.message || "Không thể kết nối tới máy chủ (Network Error)";
      return {
        status: 'error',
        detail: msg,
        message: msg,
      };
    }
  },

  async me() {
    try {
      const res = await fetch(`${API_BASE_URL}/me`, { headers: authHeaders() });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        return { status: 'error', message: parseErrorDetail(data) };
      }
      return { status: 'success', username: data.username };
    } catch (err: any) {
      return { status: 'error', message: err?.message || "Network Error" };
    }
  },

  async getMe() {
    return this.me();
  },

  // Setup Flow
  async chatInterview(history: Array<{role: string; content: string}>): Promise<InterviewResponse> {
    const res = await fetch(`${API_BASE_URL}/chat-interview`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ chat_history: history }),
    });
    return res.json();
  },

  async refinePrompt(history: Array<{role: string; content: string}>): Promise<RefineResponse> {
    const res = await fetch(`${API_BASE_URL}/refine-prompt`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ chat_history: history }),
    });
    return res.json();
  },

  // Trending Topics
  async getTrendingTopics(): Promise<{ status: string; topics?: TrendingTopic[] }> {
    try {
      const res = await fetch(`${API_BASE_URL}/trending-topics`);
      return res.json();
    } catch {
      return { status: 'error' };
    }
  },

  // Streaming Text Generation (supports generate-story, init-story, generate-chapter, end-story)
  async streamStory(
    endpoint: string,
    payload: Record<string, any>,
    onChunk: (cleanChunk: string, cleanAccumulated: string) => void,
    onComplete: (result: { fullText: string; cleanText: string; sessionId?: string; storyId?: number; error?: string }) => void,
    onError: (err: Error) => void
  ) {
    try {
      const res = await fetch(`${API_BASE_URL}/${endpoint}`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      });

      if (!res.ok || !res.body) {
        throw new Error(`API Error (${res.status})`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let fullAccumulated = '';

      const cleanText = (txt: string) => {
        return txt
          .replace(/\[(?:GENERATION_ERROR|Lỗi sinh truyện|Loi sinh truyen|Lỗi|Loi):[\s\S]*$/i, '')
          .replace(/\[(?:SESSION_ID|STORY_ID):[^\]]*\]/g, '')
          .trim();
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        fullAccumulated += chunk;
        const currentClean = cleanText(fullAccumulated);
        onChunk(chunk, currentClean);
      }

      // Extract Session ID & Story ID & Error
      const sessionMatch = fullAccumulated.match(/\[SESSION_ID:([^\]]+)\]/);
      const storyMatch = fullAccumulated.match(/\[STORY_ID:(\d+)\]/);
      const errorMatch = fullAccumulated.match(/\[(?:GENERATION_ERROR|Lỗi sinh truyện|Loi sinh truyen|Lỗi|Loi):\s*([\s\S]*?)\]/i);

      onComplete({
        fullText: fullAccumulated,
        cleanText: cleanText(fullAccumulated),
        sessionId: sessionMatch ? sessionMatch[1] : undefined,
        storyId: storyMatch ? Number(storyMatch[1]) : undefined,
        error: errorMatch ? errorMatch[1].trim() : undefined,
      });
    } catch (e: any) {
      onError(e);
    }
  },

  // Selection Edit
  async editText(selectedText: string, instruction: string): Promise<EditTextResponse> {
    const res = await fetch(`${API_BASE_URL}/edit-text`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        original_text: selectedText,
        instruction: instruction,
      }),
    });
    return res.json();
  },

  // Copilot Event System
  async sendCopilotEvent(
    sessionId: string | null,
    storyId: number | null,
    eventType: string,
    eventData: string
  ): Promise<CopilotEventResponse> {
    const res = await fetch(`${API_BASE_URL}/copilot-event`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        session_id: sessionId || 'temp',
        story_id: storyId || null,
        event_type: eventType,
        event_data: eventData,
      }),
    });
    return res.json();
  },

  // Legacy Fallback Chat
  async chatCopilot(storyText: string, userMessage: string, storyId?: number) {
    const res = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        story_text: storyText,
        user_message: userMessage,
        story_id: storyId,
      }),
    });
    return res.json();
  },

  // Stories History
  async getStories(): Promise<{ status: string; stories?: StoryDetail[] }> {
    const res = await fetch(`${API_BASE_URL}/stories`, { headers: authHeaders() });
    return res.json();
  },

  async getStoryDetail(id: number): Promise<{ status: string; story?: StoryDetail }> {
    const res = await fetch(`${API_BASE_URL}/stories/${id}`, { headers: authHeaders() });
    return res.json();
  },

  // Comic
  async generateComic(storyId: number, storyText: string): Promise<ComicResponse> {
    const res = await fetch(`${API_BASE_URL}/comic/generate`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ story_id: storyId, story_text: storyText }),
    });
    return res.json();
  },

  async continueComic(comicId: number, storyText: string): Promise<ComicResponse> {
    const res = await fetch(`${API_BASE_URL}/comic/continue`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ comic_id: comicId, story_text: storyText }),
    });
    return res.json();
  },

  getComicImageUrl(imageUrl: string): string {
    if (!imageUrl) return '';
    if (imageUrl.startsWith('http')) return imageUrl;
    return API_BASE_URL.replace('/api', '') + imageUrl;
  },
};
