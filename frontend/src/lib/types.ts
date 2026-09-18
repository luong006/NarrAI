export interface User {
  id: number;
  username: string;
}

export interface AuthResponse {
  status: 'success' | 'error';
  token?: string;
  user?: User;
  message?: string;
  detail?: string;
}

export interface StoryDetail {
  id: number;
  session_id: string;
  refined_prompt: string;
  story_content: string;
  word_count: number;
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

export type StoryLength = 'short' | 'medium' | 'long';
export type CreativityLevel = 1 | 2 | 3;
export type PacingLevel = 1 | 2 | 3;
