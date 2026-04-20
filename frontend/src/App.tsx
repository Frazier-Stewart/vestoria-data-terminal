import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, theme } from 'antd';

// Pages
import Dashboard from '@/pages/Dashboard';
import Assets from '@/pages/Assets';
import AssetDetail from '@/pages/AssetDetail';
import Indicators from '@/pages/Indicators';
import IndicatorDetail from '@/pages/IndicatorDetail';
import Watchlist from '@/pages/Watchlist';
import Login from '@/pages/Login';

// Layouts
import MainLayout from '@/layouts/MainLayout';
import { useAuthStore } from '@/stores/auth';

function App() {
  const [isDark, setIsDark] = useState(false);
  const { isAuthenticated, checkAuth } = useAuthStore();
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    setIsDark(mediaQuery.matches);

    const handler = (e: MediaQueryListEvent) => {
      setIsDark(e.matches);
    };
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  useEffect(() => {
    const initAuth = async () => {
      await checkAuth();
      setAuthLoading(false);
    };
    initAuth();
  }, [checkAuth]);

  if (authLoading) {
    return <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>加载中...</div>;
  }

  return (
    <ConfigProvider
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: '#6366f1',
          colorBgBase: isDark ? '#0f172a' : '#ffffff',
          colorTextBase: isDark ? '#f8fafc' : '#0f172a',
        },
      }}
    >
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          {isAuthenticated ? (
            <Route path="/" element={<MainLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="assets" element={<Assets />} />
              <Route path="assets/:id" element={<AssetDetail />} />
              <Route path="indicators" element={<Indicators />} />
              <Route path="indicators/:id" element={<IndicatorDetail />} />
              <Route path="watchlist" element={<Watchlist />} />
            </Route>
          ) : (
            <Route path="*" element={<Navigate to="/login" replace />} />
          )}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </ConfigProvider>
  );
}

export default App;
