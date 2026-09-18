import { storage } from './storage';
import { AuthResponse, StoryDetail, ComicResponse } from './types';

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

export const api = {
  // Auth
  async login(username: string, password: string):Promise<AuthResponse> {
    const res = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    return res.json();
  },

  async register(username: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    return res.json();
  },

  async me() {
    const res = await fetch(`${API_BASE_URL}/me`, { headers: authHeaders() });
    return res.json();
  },

  // Setup Flow
  async chatInterview(initialPrompt: string, history: Array<{role: string; content: string}>, userMessage?: string) {
    const res = await fetch(`${API_BASE_URL}/chat-interview`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        initial_prompt: initialPrompt,
        chat_history: history,
        user_message: userMessage,
      }),
    });
    return res.json();
  },

  async refinePrompt(initialPrompt: string, history: Array<{role: string; content: string}>) {
    const res = await fetch(`${API_BASE_URL}/refine-prompt`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        initial_prompt: initialPrompt,
        chat_history: history,
      }),
    });
    return res.json();
  },

  // Streaming Text Generation
  async streamStory(
    endpoint: string,
    payload: Record<string, any>,
    onChunk: (text: string) => void,
    onComplete: (fullText: string) => void,
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
      let accumulated = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        accumulated += chunk;
        onChunk(chunk);
      }

      onComplete(accumulated);
    } catch (e: any) {
      onError(e);
    }
  },

  // Selection Edit
  async editText(storyText: string, selectedText: string, instruction: string) {
    const res = await fetch(`${API_BASE_URL}/edit-text`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        story_text: storyText,
        selected_text: selectedText,
        instruction: instruction,
      }),
    });
    return res.json();
  },

  // Copilot Chat
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
