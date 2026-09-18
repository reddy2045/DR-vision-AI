export default function Badge({ children, tone = 'neutral' }) { return <span className={`badge badge-${tone}`}>{children}</span>; }
export function severityTone(level) { const value = Number(level); return value === 0 ? 'success' : value === 1 ? 'info' : value === 2 ? 'warning' : 'danger'; }
