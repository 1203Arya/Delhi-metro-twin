interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
}

export function EmptyState({ icon = "📭", title, description, action }: EmptyStateProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center p-8 text-center">
      <div className="mb-3 text-3xl">{icon}</div>
      <h3 className="mb-1 text-sm font-semibold text-surface-700 dark:text-surface-300">
        {title}
      </h3>
      {description && (
        <p className="mb-3 max-w-xs text-xs text-surface-500">{description}</p>
      )}
      {action && (
        <button className="btn-primary text-xs" onClick={action.onClick}>
          {action.label}
        </button>
      )}
    </div>
  );
}
