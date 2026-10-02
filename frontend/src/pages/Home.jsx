// src/pages/Home.jsx
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function Home() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div style={{ padding: 32, maxWidth: 900, margin: '0 auto' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <h1>SkyNex</h1>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <span style={{ color: '#718096', fontSize: 14 }}>{user?.email}</span>
          <button onClick={handleLogout} style={{ background: '#e2e8f0', padding: '8px 14px' }}>
            Sign out
          </button>
        </div>
      </header>

      <div style={{ background: '#fff', padding: 32, borderRadius: 12, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
        <h2 style={{ marginBottom: 12 }}>Welcome back! 🎉</h2>
        <p style={{ color: '#4a5568' }}>
          Phase 4 complete — you're authenticated via JWT and this page is protected.
          <br />Next: flight search UI.
        </p>
      </div>
    </div>
  );
}