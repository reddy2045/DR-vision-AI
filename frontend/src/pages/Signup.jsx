import { useState } from 'react';
import { Activity, ArrowRight, LockKeyhole, Mail, UserRound } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Signup() {
  const [fullName, setFullName] = useState('');
  const [employeeId, setEmployeeId] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register: signUp } = useAuth();
  const navigate = useNavigate();

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      await signUp({ full_name: fullName, employee_id: employeeId, email, password });
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-art">
        <div className="auth-orbit orbit-one" />
        <div className="auth-orbit orbit-two" />
        <div className="auth-brand">
          <span className="brand-mark"><Activity size={22} /></span>
          <span>
            <b>DR Vision AI</b>
            <small>PHC screening platform</small>
          </span>
        </div>

        <div className="auth-copy">
          <span className="eyebrow">Clinical intelligence, thoughtfully delivered</span>
          <h1>
            Build a safer<br />
            <em>screening workflow.</em>
          </h1>
          <p>Set up your PHC worker account to manage screenings and clinical reviews with confidence.</p>
        </div>

        <div className="auth-caption">AI output supports qualified clinical review and does not replace diagnosis.</div>
      </div>

      <div className="auth-form-wrap">
        <form className="auth-form" onSubmit={submit}>
          <span className="eyebrow">Create account</span>
          <h2>Join the screening team</h2>
          <p className="form-lead">Start your secure clinical workspace.</p>

          {error && <div className="form-error">{error}</div>}

          <label>
            Full name
            <div className="input-icon">
              <UserRound size={17} />
              <input value={fullName} onChange={(e) => setFullName(e.target.value)} required placeholder="Enter your full name" />
            </div>
          </label>

          <label>
            Employee ID
            <div className="input-icon">
              <UserRound size={17} />
              <input value={employeeId} onChange={(e) => setEmployeeId(e.target.value)} required placeholder="Enter your employee ID" />
            </div>
          </label>

          <label>
            Email address
            <div className="input-icon">
              <Mail size={17} />
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="Enter your email" />
            </div>
          </label>

          <label>
            Password
            <div className="input-icon">
              <LockKeyhole size={17} />
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required placeholder="Minimum 8 characters" />
            </div>
          </label>

          <button type="submit" className="button primary wide" disabled={loading}>
            {loading ? 'Creating account...' : 'Create account'}
            {!loading && <ArrowRight size={17} />}
          </button>

          <div className="auth-switcher">
            <span>Already registered?</span>
            <Link to="/login">Sign in</Link>
          </div>
        </form>
      </div>
    </div>
  );
}
