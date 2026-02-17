export type UserRole = "admin" | "reviewer" | "viewer";

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  google_id: string;
  created_at: string;
  updated_at: string;
}

