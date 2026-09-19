export interface User {
  id: number;
  username: string;
}

export interface AuthResponse {
  status: 'success' | 'error';
  token?: string;
  access_token?: string;
  token_type?: string;
  username?: string;
  user?: User;
  message?: string;
  detail?: string;
}

export interface StoryDetail {
  id: number;
  session_id?: string;
  title?: string;
  refined_prompt: string;
  story_content: string;
  word_count: number;
  snippet?: string;
  created_at: string;
}

export interface ComicPanel {
  panel_id?: number;
  panel_index: number;
  image_url: string;
  image_prompt: string;
  dialogue_text: string;
  layout_type: 'square' | 'wide' | 'tall';
}

export interface ComicResponse {
  status: 'success' | 'error';
  comic_id?: number;
  panels?: ComicPanel[];
  adapted_offset?: number;
  has_more?: boolean;
  no_more_text?: boolean;
  message?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface TrendingTopic {
  id: string;
  title: string;
  genre: string;
  tags: string[];
  description: string;
  prompt_snippet: string;
}

export interface GenreItem {
  vi: string;
  en: string;
}

export interface GenreCategory {
  name_vi: string;
  name_en: string;
  items: GenreItem[];
}

export interface InterviewResponse {
  status: 'success' | 'error';
  message: string;
  is_ready?: boolean;
}

export interface RefineResponse {
  status: 'success' | 'error';
  refined_prompt?: string;
  message?: string;
}

export interface EditTextResponse {
  status: 'success' | 'error';
  revised_text?: string;
  message?: string;
}

export interface CopilotEventResponse {
  status: 'success' | 'error';
  data?: {
    action: 'reply_user' | 'command_writer' | 'reject_and_rewrite' | 'heal_image' | string;
    action_params?: {
      message?: string;
      instruction?: string;
      fix_instruction?: string;
      critique?: string;
      panel_id?: number;
      new_prompt?: string;
    };
    thought?: string;
  };
  message?: string;
}

export type StoryLength = 'short' | 'medium' | 'long';
export type CreativityLevel = 1 | 2 | 3;
export type PacingLevel = 1 | 2 | 3;
