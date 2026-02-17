export type CheckRunStatus = "running" | "completed" | "failed";

export type AnalysisStatus = "pending" | "complete";

export interface CheckRun {
  id: string;
  scheduled_time: string;
  started_at: string;
  completed_at: string | null;
  status: CheckRunStatus;
  feeds_checked: number;
  new_items_found: number;
  cards_generated: number;
  error_log: string | null;
  briefing_id?: string | null;
  briefing_error?: string | null;
  analysis_status?: AnalysisStatus | null;
}

