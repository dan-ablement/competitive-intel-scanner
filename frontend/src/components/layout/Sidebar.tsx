import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  CreditCard,
  FileText,
  Users,
  Building2,
  Rss,
  Settings,
  Bell,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/cards", label: "Analysis Cards", icon: CreditCard },
  { to: "/briefings", label: "Briefings", icon: FileText },
  { to: "/competitors", label: "Competitors", icon: Users },
  { to: "/augment-profile", label: "Augment Profile", icon: Building2 },
  { to: "/feeds", label: "Feeds", icon: Rss },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="flex h-full w-60 flex-col border-r border-sidebar-border bg-sidebar">
      <div className="flex h-14 items-center gap-2 border-b border-sidebar-border px-4">
        <Bell className="h-5 w-5 text-sidebar-foreground" />
        <span className="text-lg font-semibold text-sidebar-foreground">
          CompIntel
        </span>
      </div>
      <nav className="flex-1 space-y-1 p-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground hover:bg-sidebar-accent/50"
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

