import { ArrowUpRight, Clock3, Eye } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import Dashboard from './Dashboard';
import Badge, { severityTone } from '../components/Badge';
import { api } from '../services/api';

export default function DashboardWithHistory() {
  const [patients, setPatients] = useState([]);
  const [screenings, setScreenings] = useState({});
  const [loading, setLoading] = useState(true);
  useEffect(() => { let active = true; api.patients().then(async (list) => { const entries = await Promise.all(list.slice(0, 5).map(async (patient) => { try { return [patient.patient_id, await api.screening(patient.patient_id)]; } catch { return [patient.patient_id, null]; } })); if (active) { setPatients(list); setScreenings(Object.fromEntries(entries)); } }).finally(() => active && setLoading(false)); return () => { active = false; }; }, []);
  const rows = patients.map((patient) => ({ patient, screening: screenings[patient.patient_id] })).filter(({ screening }) => screening);
  return <><Dashboard/><section className="history-preview"><div className="section-heading history-preview-heading"><div><span className="eyebrow">Screening history</span><h3>Recent clinical activity</h3></div><Link to="/history" className="text-link">Open full history <ArrowUpRight size={15}/></Link></div>{loading ? <div className="history-loading"><Clock3 size={17}/> Loading screening history...</div> : rows.length === 0 ? <div className="history-empty"><Eye size={18}/><span>Completed screenings will appear here.</span></div> : <div className="history-preview-table"><div className="history-row history-row-head"><span>Patient</span><span>AI result</span><span>Confidence</span><span>Referral</span><span/></div>{rows.map(({ patient, screening }) => <div className="history-row" key={patient.patient_id}><span className="history-patient"><span className="avatar soft">{patient.first_name?.[0]}{patient.last_name?.[0] || ''}</span><span><b>{patient.first_name} {patient.last_name}</b><small>{patient.patient_id}</small></span></span><span><Badge tone={severityTone(screening.dr_level)}>{screening.predicted_class}</Badge><small>Level {screening.dr_level}</small></span><span>{screening.confidence}%</span><span>{screening.referral_urgency || '—'}</span><Link className="icon-link" to={`/patients/${patient.patient_id}`} aria-label={`View ${patient.first_name} screening`}><ArrowUpRight size={16}/></Link></div>)}</div>}</section></>;
}