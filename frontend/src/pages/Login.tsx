import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, User, ArrowRight } from 'lucide-react';

import { useAuthStore } from '@/stores/auth';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch (err: any) {
      setError(err?.message || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-secondary)' }}>
      <div style={{ width: '100%', maxWidth: '420px', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: '16px', padding: '28px' }}>
        <h1 style={{ fontSize: '24px', margin: '0 0 8px 0', color: 'var(--text-primary)' }}>Data Terminal</h1>
        <p style={{ margin: '0 0 20px 0', color: 'var(--text-muted)', fontSize: '14px' }}>请先登录后使用系统</p>
        {error && (
          <div style={{ marginBottom: '14px', padding: '10px 12px', borderRadius: '10px', background: 'rgba(239,68,68,0.1)', color: '#ef4444', fontSize: '13px' }}>
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '10px 12px' }}>
            <User size={16} color="var(--text-muted)" />
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="用户名"
              style={{ border: 'none', outline: 'none', background: 'transparent', color: 'var(--text-primary)', width: '100%' }}
              required
            />
          </div>
          <div style={{ marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '8px', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '10px 12px' }}>
            <Lock size={16} color="var(--text-muted)" />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="密码"
              style={{ border: 'none', outline: 'none', background: 'transparent', color: 'var(--text-primary)', width: '100%' }}
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            style={{ width: '100%', padding: '10px 14px', border: 'none', borderRadius: '10px', background: 'var(--primary-color)', color: 'white', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '6px', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}
          >
            {loading ? '登录中...' : '登录'}
            {!loading && <ArrowRight size={16} />}
          </button>
        </form>
      </div>
    </div>
  );
}
