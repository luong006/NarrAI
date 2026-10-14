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
  SocialPost,
  SocialFeedResponse,
  PublishSocialPostPayload,
  InteractSocialPostPayload,
  SocialFeedParams,
  SocialPostDetailResponse,
} from './types';

function getBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    return 'http://localhost:8000/api';
  }
  return 'https://final-1-jl49.onrender.com/api';
}

export const API_BASE_URL = getBaseUrl();

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
  if (!data) return "Lỗi máy chủ / Server error";
  if (typeof data === "string") return data;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((e: any) => e.msg || JSON.stringify(e)).join(", ");
  }
  if (data.message && typeof data.message === "string") return data.message;
  return "Đã xảy ra lỗi không xác định / An unexpected error occurred";
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
        full_name: data.full_name || data.username || username.trim(),
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

  async register(username: string, password: string, fullName?: string): Promise<AuthResponse> {
    try {
      const res = await fetch(`${API_BASE_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: username.trim(),
          password,
          full_name: fullName ? fullName.trim() : "",
        }),
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
        full_name: data.full_name || data.username || username.trim(),
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
        return { status: 'error', message: parseErrorDetail(data), statusCode: res.status };
      }
      return {
        status: 'success',
        username: data.username,
        full_name: data.full_name || data.username,
      };
    } catch (err: any) {
      return { status: 'error', message: err?.message || "Network Error" };
    }
  },

  async getMe() {
    return this.me();
  },

  // Setup Flow
  async chatInterview(history: Array<{role: string; content: string}>, maxRetries = 2): Promise<InterviewResponse> {
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const res = await fetch(`${API_BASE_URL}/chat-interview`, {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({ chat_history: history, fallback_to_heuristic: true }),
        });
        if (!res.ok) {
          const errorText = await res.text();
          let message = `Lỗi máy chủ (${res.status})`;
          try {
            const parsed = JSON.parse(errorText);
            message = parsed.message || parsed.detail || message;
          } catch {}
          if (res.status === 503 && attempt < maxRetries) {
            await new Promise((r) => setTimeout(r, 2000 * (attempt + 1)));
            continue;
          }
          if (res.status === 503) {
            message = "Máy chủ AI đang khởi động (Render cold-boot). Hãy bấm Thử lại sau giây lát.";
          }
          return { status: 'error', message };
        }
        return await res.json();
      } catch (err: any) {
        if (attempt < maxRetries) {
          await new Promise((r) => setTimeout(r, 2000 * (attempt + 1)));
          continue;
        }
        return {
          status: 'error',
          message: err?.message || 'Không thể kết nối với máy chủ AI (Lỗi mạng hoặc máy chủ ngoại tuyến)',
        };
      }
    }
    return { status: 'error', message: 'Không thể kết nối với máy chủ AI sau nhiều lần thử.' };
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
        // Đọc body để lấy message lỗi rõ ràng thay vì generic error
        let errMsg = `API Error (${res.status})`;
        try {
          const errData = await res.json();
          errMsg = errData.detail || errData.message || errMsg;
        } catch { /* ignore */ }
        throw new Error(errMsg);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let fullAccumulated = '';

      const cleanText = (txt: string) => {
        return txt
          .replace(/\[(?:GENERATION_ERROR|HISTORICAL_VIOLATION|Lỗi sinh truyện|Loi sinh truyen|Lỗi|Loi):[\s\S]*$/i, '')
          .replace(/\[(?:SESSION_ID|STORY_ID):[^\]]*\]/g, '')
          .trim();
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          const decoderTail = decoder.decode();
          if (decoderTail) {
            fullAccumulated += decoderTail;
            onChunk(decoderTail, cleanText(fullAccumulated));
          }
          break;
        }
        const chunk = decoder.decode(value, { stream: true });
        fullAccumulated += chunk;
        const currentClean = cleanText(fullAccumulated);
        onChunk(chunk, currentClean);
      }

      // Extract Session ID & Story ID & Error
      const sessionMatch = fullAccumulated.match(/\[SESSION_ID:([^\]]+)\]/);
      const storyMatch = fullAccumulated.match(/\[STORY_ID:(\d+)\]/);
      const errorMatch = fullAccumulated.match(/\[(?:GENERATION_ERROR|HISTORICAL_VIOLATION|Lỗi sinh truyện|Loi sinh truyen|Lỗi|Loi):\s*([\s\S]*?)\]/i);

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
  async generateComic(storyId: number | null, storyText: string): Promise<ComicResponse> {
    try {
      const res = await fetch(`${API_BASE_URL}/comic/generate`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ story_id: storyId || null, story_text: storyText }),
      });
      const data = await res.json();
      if (!res.ok) {
        return {
          status: 'error',
          message: data.detail || data.message || `Lỗi HTTP ${res.status}`,
          code: res.status,
        } as any;
      }
      return data;
    } catch (err: any) {
      return {
        status: 'error',
        message: err.message || 'Không thể kết nối tới máy chủ khi chuyển thể truyện tranh',
      } as any;
    }
  },

  async continueComic(comicId: number, storyText: string): Promise<ComicResponse & { code?: number; error_code?: string; required_coins?: number; current_coins?: number }> {
    try {
      const res = await fetch(`${API_BASE_URL}/comic/continue`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ comic_id: comicId, story_text: storyText }),
      });
      const data = await res.json();
      if (!res.ok) {
        return {
          status: 'error',
          message: data.detail || data.message || `Lỗi HTTP ${res.status}`,
          code: res.status,
          error_code: data.error_code,
          required_coins: data.required_coins,
          current_coins: data.current_coins,
        } as any;
      }
      return data;
    } catch (err: any) {
      return {
        status: 'error',
        message: err.message || 'Không thể kết nối tới máy chủ khi tạo tiếp tranh',
      } as any;
    }
  },

  getComicImageUrl(imageUrl: string): string {
    if (!imageUrl) return '';
    if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://') || imageUrl.startsWith('data:')) return imageUrl;
    const apiOrigin = API_BASE_URL.replace(/\/api\/?$/, '');
    try {
      const cleanPath = imageUrl.startsWith('/') ? imageUrl : `/${imageUrl}`;
      return `${apiOrigin}${cleanPath}`;
    } catch {
      return imageUrl;
    }
  },

  // Coins & Banking
  async getCoinsBalance(): Promise<{ status: string; coins?: number; balance?: number }> {
    try {
      const res = await fetch(`${API_BASE_URL}/coins/balance`, { headers: authHeaders() });
      if (res.ok) return res.json();
      const fallbackRes = await fetch(`${API_BASE_URL}/balance`, { headers: authHeaders() });
      if (fallbackRes.ok) return fallbackRes.json();
      return { status: 'error', coins: 0 };
    } catch {
      return { status: 'error', coins: 0 };
    }
  },

  async topupCoins(amount: number): Promise<{ amount: number; new_balance: number }> {
    const res = await fetch(`${API_BASE_URL}/coins/topup`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        amount,
        description: 'MVP demo coin top-up',
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(parseErrorDetail(data));
    }
    if (typeof data.amount !== 'number' || typeof data.new_balance !== 'number') {
      throw new Error('Máy chủ trả về kết quả nạp xu không hợp lệ.');
    }
    return { amount: data.amount, new_balance: data.new_balance };
  },

  // Social & Literary Feed (Requirement #4)
  async getSocialFeed(
    paramsOrGenre?: SocialFeedParams | string,
    limit = 20,
    offset = 0
  ): Promise<SocialFeedResponse> {
    try {
      let finalGenre: string | undefined;
      let finalLimit = limit;
      let finalOffset = offset;
      let feedType: SocialFeedParams["feed_type"] = "recommended";
      let selectedGenres: string[] = [];
      let searchQuery: string | undefined;

      if (paramsOrGenre && typeof paramsOrGenre === "object") {
        finalGenre = paramsOrGenre.genre;
        if (paramsOrGenre.limit !== undefined) finalLimit = paramsOrGenre.limit;
        if (paramsOrGenre.offset !== undefined) finalOffset = paramsOrGenre.offset;
        if (paramsOrGenre.feed_type) feedType = paramsOrGenre.feed_type;
        selectedGenres = paramsOrGenre.genres || [];
        searchQuery = paramsOrGenre.q?.trim();
      } else if (typeof paramsOrGenre === "string") {
        finalGenre = paramsOrGenre;
      }

      const params = new URLSearchParams({
        limit: String(finalLimit),
        offset: String(finalOffset),
        feed_type: feedType,
      });

      if (finalGenre && finalGenre !== "All" && finalGenre !== "Tất cả") {
        params.append("genre", finalGenre);
      }
      selectedGenres.forEach((genre) => params.append("genres", genre));
      if (searchQuery) params.set("q", searchQuery);

      const res = await fetch(`${API_BASE_URL}/social/feed?${params.toString()}`, {
        headers: authHeaders(),
      });

      if (!res.ok) {
        return {
          success: false,
          data: { items: [], total: 0, page_limit: finalLimit, offset: finalOffset, has_more: false },
          message: parseErrorDetail(await res.json().catch(() => null)),
        };
      }
      return res.json();
    } catch (err) {
      return {
        success: false,
        data: { items: [], total: 0, page_limit: limit, offset, has_more: false },
        message: err instanceof Error ? err.message : "Không thể tải bảng tin.",
      };
    }
  },

  async publishSocialPost(
    payload: PublishSocialPostPayload
  ): Promise<{ success: boolean; message?: string; post_id?: number; data?: any; statusCode?: number }> {
    try {
      const res = await fetch(`${API_BASE_URL}/social/publish`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        return { success: false, message: parseErrorDetail(data), statusCode: res.status };
      }
      return data;
    } catch (err: any) {
      return { success: false, message: err.message || "Không thể kết nối đến máy chủ khi đăng bài." };
    }
  },

  // Backwards-compatible alias for publishPost
  async publishPost(
    payload: PublishSocialPostPayload
  ): Promise<{ success: boolean; message?: string; post_id?: number; data?: any; statusCode?: number }> {
    return this.publishSocialPost(payload);
  },

  async interactSocialPost(
    payload: InteractSocialPostPayload
  ): Promise<{ success: boolean; message?: string; interaction_id?: number; metadata?: any }> {
    try {
      const res = await fetch(`${API_BASE_URL}/social/interact`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) return { success: false, message: parseErrorDetail(data) };
      return data;
    } catch (err: any) {
      return { success: false, message: err.message };
    }
  },

  // Backwards-compatible alias for interactPost
  async interactPost(
    payload: InteractSocialPostPayload
  ): Promise<{ success: boolean; message?: string; interaction_id?: number; metadata?: any }> {
    return this.interactSocialPost(payload);
  },

  async getSocialPostDetails(postId: number): Promise<SocialPostDetailResponse> {
    try {
      const res = await fetch(`${API_BASE_URL}/social/post/${postId}`, {
        headers: authHeaders(),
      });
      return res.json();
    } catch (err: any) {
      return { success: false, detail: err.message };
    }
  },

  // Backwards-compatible alias for getPostDetails
  async getPostDetails(postId: number): Promise<SocialPostDetailResponse> {
    return this.getSocialPostDetails(postId);
  },

  async followAuthor(userId: number): Promise<{ success: boolean; message?: string }> {
    try {
      const res = await fetch(`${API_BASE_URL}/social/follow/${userId}`, {
        method: "POST",
        headers: authHeaders(),
      });
      return await res.json();
    } catch (err: any) {
      return { success: false, message: err?.message };
    }
  },

  async unfollowAuthor(userId: number): Promise<{ success: boolean; message?: string }> {
    try {
      const res = await fetch(`${API_BASE_URL}/social/unfollow/${userId}`, {
        method: "POST",
        headers: authHeaders(),
      });
      return await res.json();
    } catch (err: any) {
      return { success: false, message: err?.message };
    }
  },

  // ComfyUI Integration Helpers
  async getComfyUIStatus(): Promise<{
    enabled: boolean;
    available: boolean;
    base_url: string;
    selected_checkpoint?: string;
    available_checkpoints?: string[];
    available_loras?: string[];
  }> {
    try {
      const res = await fetch(`${API_BASE_URL}/comic/comfyui/status`, { headers: authHeaders() });
      if (res.ok) return res.json();
      return { enabled: false, available: false, base_url: '' };
    } catch {
      return { enabled: false, available: false, base_url: '' };
    }
  },

  async setComfyUIUrl(url: string): Promise<{ status: string; url: string; online: boolean; message: string }> {
    try {
      const res = await fetch(`${API_BASE_URL}/comic/comfyui/set-url`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ url }),
      });
      return res.json();
    } catch (err: any) {
      return { status: 'error', url, online: false, message: err.message || 'Không thể kết nối' };
    }
  },

  // ==================== AI STORY PIPELINE ENDPOINTS ====================

  async getPipelineQueue(): Promise<{ status: string; data: import('./types').PipelineOverview }> {
    const res = await fetch(`${API_BASE_URL}/admin/story-pipeline/queue`, {
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error("Không thể tải danh sách hàng đợi pipeline");
    return res.json();
  },

  async addPipelinePrompt(payload: {
    title: string;
    id?: string;
    topic?: string;
    category?: string;
    genre?: string[];
    language?: string;
    sourceLanguages?: string[];
  }): Promise<{ status: string; message: string; data: import('./types').PipelineStoryItem }> {
    const res = await fetch(`${API_BASE_URL}/admin/story-pipeline/queue`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Lỗi khi thêm đề bài vào hàng đợi");
    return data;
  },

  async batchAddPipelinePrompts(items: any[]): Promise<{ status: string; data: any }> {
    const res = await fetch(`${API_BASE_URL}/admin/story-pipeline/queue/batch`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ items }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Lỗi khi nhập hàng loạt đề bài");
    return data;
  },

  async updatePipelinePrompt(
    storyId: string,
    updates: Partial<import('./types').PipelineStoryItem>
  ): Promise<{ status: string; message: string; data: import('./types').PipelineStoryItem }> {
    const res = await fetch(`${API_BASE_URL}/admin/story-pipeline/queue/${storyId}`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: JSON.stringify(updates),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Lỗi khi cập nhật đề bài");
    return data;
  },

  async deletePipelinePrompt(storyId: string): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE_URL}/admin/story-pipeline/queue/${storyId}`, {
      method: 'DELETE',
      headers: authHeaders(),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Lỗi khi xóa đề bài");
    return data;
  },

  async runPipeline(payload?: { story_id?: string; limit?: number }): Promise<{ status: string; data: any }> {
    const res = await fetch(`${API_BASE_URL}/admin/story-pipeline/run`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload || {}),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Lỗi khi thực thi pipeline");
    return data;
  },

  async getPipelineJobs(): Promise<{ status: string; overview: import('./types').PipelineOverview; recentLogs: import('./types').PipelineLogEntry[] }> {
    const res = await fetch(`${API_BASE_URL}/admin/story-pipeline/jobs`, {
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error("Không thể tải trạng thái công việc pipeline");
    return res.json();
  },

  async getPipelineJobDetail(storyId: string): Promise<{ status: string; story: import('./types').PipelineStoryItem; logs: import('./types').PipelineLogEntry[]; preview?: import('./types').PipelineStoryDetail }> {
    const res = await fetch(`${API_BASE_URL}/admin/story-pipeline/jobs/${storyId}`, {
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error("Không thể tải chi tiết tiến trình");
    return res.json();
  },

  async getPipelinePullRequests(): Promise<{ status: string; count: number; data: import('./types').PipelinePullRequest[] }> {
    const res = await fetch(`${API_BASE_URL}/admin/story-pipeline/pull-requests`, {
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error("Không thể tải danh sách Pull Requests");
    return res.json();
  },

  async mergePipelinePullRequest(prNumber: number, storyId: string): Promise<{ status: string; message: string }> {
    window.open(`https://github.com/anhdinh0701/final/pull/${prNumber}`, '_blank');
    return { status: 'success', message: `Đang mở GitHub PR #${prNumber} để duyệt và merge` };
  },

  async revalidatePipelineStory(storyId: string): Promise<{ status: string; storyId: string; validation: import('./types').PipelineValidationResult }> {
    const res = await fetch(`${API_BASE_URL}/admin/story-pipeline/validate/${storyId}`, {
      method: 'POST',
      headers: authHeaders(),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Lỗi khi kiểm định lại truyện");
    return data;
  },

  async getPipelineStoryPreview(storyId: string): Promise<{ status: string; data: import('./types').PipelineStoryDetail }> {
    const res = await fetch(`${API_BASE_URL}/admin/story-pipeline/preview/${storyId}`, {
      headers: authHeaders(),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Chưa có bản thảo truyện để xem trước");
    return data;
  },

  async getPublishedStories(category?: string): Promise<{ status: string; count: number; data: import('./types').PipelineStoryDetail[] }> {
    const url = category ? `${API_BASE_URL}/stories/published?category=${encodeURIComponent(category)}` : `${API_BASE_URL}/stories/published`;
    const res = await fetch(url);
    if (!res.ok) return { status: 'error', count: 0, data: [] };
    return res.json();
  },
};
