export const ENTERPRISE_COPY = {
  nav: {
    enterprise: "Enterprise",
    intelligence: "Intelligence",
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
    intelligence: "Loading enterprise intelligence...",
    approvals: "Checking pending approvals...",
    activity: "Reading audit trail..."
  },
  errors: {
    workspace: "Workspace data could not be loaded.",
    intelligence: "Enterprise intelligence could not be loaded.",
    offline: "You appear to be offline. Desktop actions will reconnect when the backend is available."
  },
  intelligence: {
    title: "Executive Intelligence",
    subtitle: "Memory, graph, assistant, documents, workflows, and release health",
    memory: "Executive memory",
    graph: "Knowledge graph",
    analytics: "Advanced analytics",
    assistant: "Executive assistant",
    documents: "Document intelligence",
    workflows: "Workflow automation",
    observability: "Observability",
    collaboration: "Collaboration",
    search: "Global search",
    questionPlaceholder: "Ask about risks, approvals, suppliers, rejected decisions...",
    searchPlaceholder: "Search all enterprise records",
    upload: "Import document",
    runWorkflow: "Run workflow",
    ask: "Ask",
    empty: "No records yet.",
    fallback: "Compatibility mode",
    noGraph: "No graph nodes are available yet."
  }
} as const;
