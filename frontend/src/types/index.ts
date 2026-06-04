export type Platform = 'instagram' | 'tiktok'
export type ScrapeStatus = 'pending' | 'scraping' | 'success' | 'error'
export type JobStatus = 'queued' | 'running' | 'success' | 'failed'

export interface Post {
  id: number
  post_id: string
  thumbnail_url: string | null
  local_thumbnail: string | null
  post_url: string | null
  likes: number
  comments: number
  posted_at: string | null
  is_video: boolean
  caption: string | null
  media_type: string | null
  view_count: number
}

export interface Hashtag {
  tag: string
  count: number
}

export interface Mention {
  mention: string
  count: number
}

export interface Influencer {
  id: number
  platform: Platform
  username: string
  display_name: string | null
  profile_pic_url: string | null
  bio: string | null
  followers: number
  following: number
  total_posts: number
  is_verified: boolean
  avg_likes: number
  avg_comments: number
  engagement_rate: number
  posts_per_week: number
  has_comments_data: boolean
  top_hashtags: Hashtag[]
  top_mentions: Mention[]
  inferred_niches: string[]
  estimated_reach: number
  estimated_impressions: number
  photo_count: number
  video_count: number
  last_scraped_at: string | null
  scrape_status: ScrapeStatus
  scrape_error: string | null
  created_at: string | null
}

export interface LinkedInfluencer {
  id: number
  platform: Platform
  username: string
  display_name: string | null
  profile_pic_url: string | null
  followers: number
  engagement_rate: number
  scrape_status: ScrapeStatus
}

export interface SponsoredPost {
  post_id: string
  post_url: string | null
  thumbnail_url: string | null
  matched_tags: string[]
  matched_brands: string[]
  caption_snippet: string | null
}

export interface InfluencerDetail extends Influencer {
  posts: Post[]
  linked_influencer: LinkedInfluencer | null
  detected_sponsorships: SponsoredPost[]
}

export interface InfluencerListResponse {
  data: Influencer[]
  total: number
  page: number
  page_size: number
}

export interface ScrapeJob {
  id: number
  influencer_id: number | null
  status: JobStatus
  triggered_at: string | null
  completed_at: string | null
  error_message: string | null
}

export interface ScrapeResponse {
  job_id: number
  influencer_id: number
  status: string
}

export type BudgetTier = 'nano' | 'micro' | 'macro' | 'mega'
export type CollabStatus = 'potential' | 'contacted' | 'in_progress' | 'done'

export interface Collaboration {
  id: number
  brand_id: number
  influencer_id: number
  status: CollabStatus
  notes: string | null
  created_at: string | null
  updated_at: string | null
}

export interface Brand {
  id: number
  name: string
  description: string | null
  ig_link: string | null
  tt_link: string | null
  profile_pic_url: string | null
  categories: string[]
  platform: Platform | 'both'
  budget_tier: BudgetTier
  min_er: number
  collaboration_count: number
  created_at: string | null
}

export interface BrandDetail extends Brand {
  collaborations: Collaboration[]
}

export interface MatchResult extends Influencer {
  match_score: number
  match_reasons: string[]
  collaboration: Collaboration | null
}

export interface FilterState {
  platform: Platform | ''
  minFollowers: number | ''
  maxFollowers: number | ''
  minEr: number | ''
  maxEr: number | ''
  sortBy: string
  order: 'asc' | 'desc'
  search: string
  niche: string
  page: number
}
