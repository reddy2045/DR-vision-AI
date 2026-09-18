import { useState } from 'react';
import { Activity, ArrowRight, LockKeyhole, Mail } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login: signIn } = useAuth();
  const navigate = useNavigate();

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      await signIn({ login, password });
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message || 'Login failed');
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
            See the signal<br />
            <em>behind the image.</em>
          </h1>
          <p>A calm, reliable workspace for diabetic retinopathy screening at the point of care.</p>
        </div>

        <div className="auth-caption">AI output supports qualified clinical review and does not replace diagnosis.</div>
      </div>

      <div className="auth-form-wrap">
        <form className="auth-form" onSubmit={submit}>
          <span className="eyebrow">Secure staff access</span>
          <h2>Welcome back</h2>
          <p className="form-lead">Sign in to continue to your screening workspace.</p>

          {error && <div className="form-error">{error}</div>}

          <label>
            Employee ID or email
            <div className="input-icon">
              <Mail size={17} />
              <input
                value={login}
                onChange={(e) => setLogin(e.target.value)}
                required
                autoComplete="username"
                placeholder="Enter your employee ID or email"
              />
            </div>
          </label>

          <label>
            Password
            <div className="input-icon">
              <LockKeyhole size={17} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                placeholder="Enter your password"
              />
            </div>
          </label>

          <button type="submit" className="button primary wide" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in'}
            {!loading && <ArrowRight size={17} />}
          </button>

          <div className="auth-switcher">
            <span>New here?</span>
            <Link to="/signup">Create an account</Link>
          </div>
        </form>
      </div>
    </div>
  );
}
