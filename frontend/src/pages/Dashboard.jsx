import { Activity, AlertTriangle, ArrowUpRight, ScanLine, ShieldCheck, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import ScreeningCard from '../components/ScreeningCard';
import { Empty, ErrorState, Loading } from '../components/State';
import { usePatients } from '../hooks/usePatients';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
  const { patients, loading, error, refresh } = usePatients();
  const { user } = useAuth();
  const [screenings, setScreenings] = useState({});

  useEffect(() => {
    let active = true;

    Promise.all(patients.slice(0, 6).map(async (patient) => {
      try {
        return [patient.patient_id, await api.screening(patient.patient_id)];
      } catch {
        return [patient.patient_id, null];
      }
    })).then((entries) => active && setScreenings(Object.fromEntries(entries)));

    return () => {
      active = false;
    };
  }, [patients]);

  const completed = Object.values(screenings).filter(Boolean);
  const referable = completed.filter((item) => item.referable).length;
  const urgentReferrals = completed.filter((item) => item.referral_urgency === 'urgent').length;
  const firstName = user?.full_name?.trim().split(/\s+/)[0] || 'there';

  return <>
    <PageHeader
      eyebrow="Overview"
      title={`Good morning, ${firstName}`}
      description="A focused view of your primary health centre's retinal screening activity."
      action={<Link className="button primary" to="/screening/new"><ScanLine size={17} /> New screening</Link>}
    />

    {error && <ErrorState message={error} retry={refresh} />}

    <section className="metric-grid">
      <div className="metric-card">
        <span className="metric-icon blue"><Users size={19} /></span>
        <small>Patients in registry</small>
        <strong>{loading ? '...' : patients.length}</strong>
        <span className="metric-note">Across this workspace</span>
      </div>
      <div className="metric-card">
        <span className="metric-icon green"><ShieldCheck size={19} /></span>
        <small>Screenings loaded</small>
        <strong>{loading ? '...' : completed.length}</strong>
        <span className="metric-note">Latest available results</span>
      </div>
      <div className="metric-card">
        <span className="metric-icon amber"><Activity size={19} /></span>
        <small>Referable results</small>
        <strong>{loading ? '...' : referable}</strong>
        <span className="metric-note">Requires clinical review</span>
      </div>
      <div className="metric-card">
        <span className="metric-icon teal"><AlertTriangle size={19} /></span>
        <small>Urgent referrals</small>
        <strong>{loading ? '...' : urgentReferrals}</strong>
        <span className="metric-note">Needs review within 7 days</span>
      </div>
    </section>

    <section className="section-heading">
      <div><span className="eyebrow">Recent activity</span><h3>Latest patient screenings</h3></div>
      <Link to="/history" className="text-link">View history <ArrowUpRight size={15} /></Link>
    </section>

    {loading ? <Loading /> : patients.length === 0 ? <Empty title="No patients yet" message="Start a new screening to create the first patient record." /> : <div className="screening-grid">
      {patients.slice(0, 6).map((patient) => <ScreeningCard key={patient.patient_id} patient={patient} screening={screenings[patient.patient_id]} />)}
    </div>}
  </>;
}
