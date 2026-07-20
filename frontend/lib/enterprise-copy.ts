export const ENTERPRISE_COPY = {
  nav: {
    enterprise: "Enterprise",
    command: "Command palette",
    notifications: "Notifications"
  },
  dashboard: {
    title: "Enterprise Workspace",
    subtitle: "Organization activity, approvals, tasks, and executive signals",
    organization: "Organization",
    departments: "Departments",
    teams: "Teams",
    users: "Users",
    pendingApprovals: "Pending approvals",
    tasks: "Tasks",
    activity: "Board activity",
    calendar: "Upcoming reviews",
    analytics: "Analytics",
    executiveSignals: "Executive signals"
  },
  empty: {
    approvals: "No approvals are waiting.",
    tasks: "No open tasks yet.",
    activity: "Activity will appear after meetings and workflow changes.",
    calendar: "No scheduled reviews yet."
  },
  loading: {
    dashboard: "Loading organization workspace...",
    approvals: "Checking pending approvals...",
    activity: "Reading audit trail..."
  },
  errors: {
    workspace: "Workspace data could not be loaded.",
    offline: "You appear to be offline. Desktop actions will reconnect when the backend is available."
  }
} as const;
