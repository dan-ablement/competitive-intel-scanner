export interface ContentTemplateSection {
  title: string;
  description: string;
  prompt_hint: string;
}

export interface ContentTemplate {
  id: string;
  content_type: string;
  name: string;
  description: string;
  sections: ContentTemplateSection[];
  doc_name_pattern: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

