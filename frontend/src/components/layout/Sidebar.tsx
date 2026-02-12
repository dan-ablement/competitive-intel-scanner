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
import { useCards } from "@/hooks/use-cards";
import { useSuggestions } from "@/hooks/use-suggestions";
import { useCompetitors } from "@/hooks/use-competitors";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, badgeKey: null },
  { to: "/cards", label: "Analysis Cards", icon: CreditCard, badgeKey: "cards" as const },
  { to: "/briefings", label: "Briefings", icon: FileText, badgeKey: null },
  { to: "/competitors", label: "Competitors", icon: Users, badgeKey: "competitors" as const },
  { to: "/augment-profile", label: "Augment Profile", icon: Building2, badgeKey: null },
  { to: "/feeds", label: "Feeds", icon: Rss, badgeKey: null },
  { to: "/settings", label: "Settings", icon: Settings, badgeKey: "suggestions" as const },
];

type BadgeKey = "cards" | "competitors" | "suggestions";

function useSidebarBadges(): Record<BadgeKey, number> {
  const { data: cards } = useCards();
  const { data: suggestions } = useSuggestions();
  const { data: suggestedCompetitors } = useCompetitors({ is_suggested: true });

  const draftOrReview = (cards ?? []).filter(
    (c) => c.status === "draft" || c.status === "in_review"
  ).length;
  const pendingSuggestions = (suggestions ?? []).filter((s) => s.status === "pending").length;
  const suggestedCount = (suggestedCompetitors ?? []).length;

  return {
    cards: draftOrReview,
    competitors: suggestedCount,
    suggestions: pendingSuggestions,
  };
}

export function Sidebar() {
  const badges = useSidebarBadges();

  return (
    <aside className="flex h-full w-60 flex-col border-r border-sidebar-border bg-sidebar">
      <div className="flex h-14 items-center gap-2 border-b border-sidebar-border px-4">
        <Bell className="h-5 w-5 text-sidebar-foreground" />
        <span className="text-lg font-semibold text-sidebar-foreground">
          CompIntel
        </span>
      </div>
      <nav className="flex-1 space-y-1 p-2">
        {navItems.map((item) => {
          const badgeCount = item.badgeKey ? badges[item.badgeKey] : 0;
          return (
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
              <span className="flex-1">{item.label}</span>
              {badgeCount > 0 && (
                <span className="rounded-full bg-primary/20 px-1.5 py-0.5 text-xs font-semibold text-primary">
                  {badgeCount}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}

