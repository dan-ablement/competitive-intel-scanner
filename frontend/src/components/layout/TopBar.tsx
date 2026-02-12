import { Bell, LogOut, User } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export function TopBar() {
  const { user, logout, isLoggingOut } = useAuth();

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-background px-6">
      <div />
      <div className="flex items-center gap-4">
        {/* Notification indicator placeholder */}
        <button className="relative rounded-md p-2 text-muted-foreground hover:bg-muted">
          <Bell className="h-5 w-5" />
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-destructive" />
        </button>
        {/* User info and logout */}
        {user && (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-md p-2 text-sm">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-xs font-medium text-primary-foreground">
                {user.name
                  .split(" ")
                  .map((n) => n[0])
                  .join("")
                  .toUpperCase()
                  .slice(0, 2)}
              </div>
              <span className="hidden font-medium sm:inline">{user.name}</span>
            </div>
            <button
              onClick={logout}
              disabled={isLoggingOut}
              className="rounded-md p-2 text-muted-foreground hover:bg-muted disabled:opacity-50"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}
        {!user && (
          <button className="flex items-center gap-2 rounded-md p-2 text-muted-foreground hover:bg-muted">
            <User className="h-5 w-5" />
          </button>
        )}
      </div>
    </header>
  );
}

