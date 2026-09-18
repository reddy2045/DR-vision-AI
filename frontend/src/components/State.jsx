import { AlertCircle, LoaderCircle } from 'lucide-react';
export function Loading({ label = 'Loading clinical data...' }) { return <div className="state-panel"><LoaderCircle className="spin" size={26}/><span>{label}</span></div>; }
export function ErrorState({ message, retry }) { return <div className="state-panel error-state"><AlertCircle size={24}/><span>{message}</span>{retry && <button className="button ghost" onClick={retry}>Try again</button>}</div>; }
export function Empty({ title = 'Nothing here yet', message }) { return <div className="state-panel"><span className="empty-icon">○</span><b>{title}</b>{message && <span>{message}</span>}</div>; }
