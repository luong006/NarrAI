export interface User {
  id: number;
  username: string;
  full_name?: string;
}

export interface AuthResponse {
  status: 'success' | 'error';
  token?: string;
  access_token?: string;
  token_type?: string;
  username?: string;
  full_name?: string;
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
  is_ready?: boolean;
  timestamp?: number;
  is_offline_fallback?: boolean;
  error_message?: string;
  failed_prompt?: string;
}

export interface IntakeChatOptions {
  modelTier: 'flash' | 'versatile' | 'master';
  length: StoryLength;
  refinedPrompt?: string;
  chatHistory?: ChatMessage[];
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
    action: 'reply_user' | 'command_writer' | 'reject_and_rewrite' | 'heal_image' | 'edit_story_direct' | string;
    action_params?: {
      message?: string;
      instruction?: string;
      fix_instruction?: string;
      critique?: string;
      panel_id?: number;
      new_prompt?: string;
      updated_story_content?: string;
      summary_of_changes?: string;
      edit_type?: string;
    };
    thought?: string;
  };
  message?: string;
}

export type StoryLength = 'short' | 'medium' | 'long';
export type CreativityLevel = 1 | 2 | 3;
export type PacingLevel = 1 | 2 | 3;

export interface SocialPostAuthor {
  id: number;
  username: string;
  full_name?: string;
}

export interface SocialComment {
  id: number;
  user_id: number;
  username: string;
  full_name?: string;
  comment_text: string;
  sentiment_score?: number;
  created_at?: string;
  parent_comment_id?: number | null;
  replies?: SocialComment[];
}

export interface SocialPost {
  id: number;
  user_id?: number;
  author_name?: string;
  author_avatar?: string;
  story_id?: number;
  title: string;
  content_snippet: string;
  story_content?: string;
  story_full_text?: string;
  comic_panels?: ComicPanel[];
  cover_image_url?: string;
  genre?: string;
  tags?: string[];
  is_fanfiction?: boolean;
  disclaimer?: string;
  dsgo_entities?: string[];
  dsgo_spaces?: string[];
  likes_count: number;
  comments_count: number;
  views_count: number;
  completion_count?: number;
  dwell_time_avg?: number;
  created_at?: string;
  author?: SocialPostAuthor;
  comments?: SocialComment[];
  is_cold_start_exploration?: boolean;
  score?: number;
  liked_by_me?: boolean;
}

export interface PublishSocialPostPayload {
  title: string;
  content_snippet: string;
  story_id?: number | null;
  story_text?: string;
  genre?: string;
  tags?: string[];
  is_fanfiction?: boolean;
  disclaimer?: string;
  cover_image_url?: string | null;
  dsgo_entities?: string[];
  dsgo_spaces?: string[];
  concept_vector?: number[];
}

export interface InteractSocialPostPayload {
  post_id: number;
  interaction_type: 'LIKE' | 'COMMENT' | 'BOOKMARK' | 'SHARE' | 'CLICK' | 'SCROLL_50' | 'SCROLL_100' | 'DWELL_TIME' | string;
  dwell_seconds?: number;
  scroll_depth?: number;
  comment_text?: string;
  parent_comment_id?: number | null;
}

export interface SocialFeedParams {
  genre?: string;
  limit?: number;
  offset?: number;
}

export interface SocialFeedResponse {
  success: boolean;
  data: {
    items: SocialPost[];
    total: number;
    page_limit: number;
    offset: number;
    has_more: boolean;
  };
}

export interface SocialPostDetailResponse {
  success: boolean;
  data?: SocialPost;
  message?: string;
  detail?: string;
}


