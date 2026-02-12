import { Bell, User } from "lucide-react";

export function TopBar() {
  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-background px-6">
      <div />
      <div className="flex items-center gap-4">
        {/* Notification indicator placeholder */}
        <button className="relative rounded-md p-2 text-muted-foreground hover:bg-muted">
          <Bell className="h-5 w-5" />
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-destructive" />
        </button>
        {/* User avatar area placeholder */}
        <button className="flex items-center gap-2 rounded-md p-2 text-muted-foreground hover:bg-muted">
          <User className="h-5 w-5" />
        </button>
      </div>
    </header>
  );
}

