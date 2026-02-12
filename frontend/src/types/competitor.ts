export interface Competitor {
  id: string;
  name: string;
  description: string;
  key_products: string;
  target_customers: string;
  known_strengths: string;
  known_weaknesses: string;
  augment_overlap: string;
  pricing: string;
  content_types: string[];
  is_active: boolean;
  is_suggested: boolean;
  suggested_reason: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

