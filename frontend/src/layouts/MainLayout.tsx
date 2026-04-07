import { useState, useEffect } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Database,
  Activity,
  Star,
  Menu,
  X,
  ChevronRight,
  Bell,
  BarChart3,
} from 'lucide-react';

const menuItems = [
  { path: '/', label: '仪表盘', icon: LayoutDashboard },
  { path: '/assets', label: '标的列表', icon: Database },
  { path: '/watchlist', label: '关注列表', icon: Star },
  { path: '/indicators', label: '指标中心', icon: Activity },
];

export default function MainLayout() {
  const location = useLocation();
  const from = (location.state as { from?: string })?.from;
  const isFromWatchlist = from === 'watchlist';
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024);
      if (window.innerWidth < 1024) {
        setSidebarOpen(false);
      } else {
        setSidebarOpen(true);
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    
    // When on asset detail page, only highlight based on source
    if (location.pathname.startsWith('/assets/')) {
      if (path === '/watchlist' && isFromWatchlist) {
        return true;
      }
      if (path === '/assets' && !isFromWatchlist) {
        return true;
      }
      return false;
    }
    
    // Normal matching for other pages
    return location.pathname.startsWith(path);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', background: 'var(--bg-secondary)' }}>
      {/* Top Navigation Bar */}
      <header
        style={{
          height: '64px',
          background: 'var(--bg-primary)',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          padding: '0 24px',
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 100,
        }}
      >
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginRight: '16px' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <BarChart3 size={22} color="white" />
          </div>
          <div>
            <div
              style={{
                fontSize: '18px',
                fontWeight: 700,
                color: 'var(--text-primary)',
                letterSpacing: '-0.5px',
              }}
            >
              Vestoria
            </div>
            <div
              style={{
                fontSize: '11px',
                color: 'var(--text-muted)',
                marginTop: '-2px',
              }}
            >
              数据终端
            </div>
          </div>
        </div>

        {/* Sidebar Toggle Button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
            background: 'var(--bg-secondary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            color: 'var(--text-secondary)',
            transition: 'all 0.2s ease',
            marginRight: '16px',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--primary-color)';
            e.currentTarget.style.color = 'var(--primary-color)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--border-color)';
            e.currentTarget.style.color = 'var(--text-secondary)';
          }}
          title={sidebarOpen ? '收起侧边栏' : '展开侧边栏'}
        >
          {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
        </button>

        {/* Spacer */}
        <div style={{ flex: 1 }} />

        {/* Right Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-secondary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              color: 'var(--text-secondary)',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--primary-color)';
              e.currentTarget.style.color = 'var(--primary-color)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-color)';
              e.currentTarget.style.color = 'var(--text-secondary)';
            }}
          >
            <Bell size={20} />
          </button>
        </div>
      </header>

      {/* Main Layout Container */}
      <div style={{ display: 'flex', flex: 1, marginTop: '64px' }}>
        {/* Sidebar */}
        <aside
          style={{
            position: isMobile ? 'fixed' : 'relative',
            left: 0,
            top: 0,
            height: isMobile ? 'calc(100vh - 64px)' : 'calc(100vh - 64px)',
            width: sidebarOpen ? '240px' : '72px',
            background: 'var(--bg-primary)',
            borderRight: '1px solid var(--border-color)',
            transition: 'width 0.3s ease, transform 0.3s ease',
            zIndex: 99,
            display: 'flex',
            flexDirection: 'column',
            boxShadow: sidebarOpen ? '4px 0 24px rgba(0,0,0,0.06)' : 'none',
            transform: isMobile && !sidebarOpen ? 'translateX(-100%)' : 'translateX(0)',
          }}
        >
          {/* Navigation */}
          <nav style={{ flex: 1, padding: '16px 12px', overflowY: 'auto' }}>
            <div
              style={{
                fontSize: '11px',
                fontWeight: 600,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '12px',
                marginLeft: sidebarOpen ? '12px' : '0',
                textAlign: sidebarOpen ? 'left' : 'center',
              }}
            >
              {sidebarOpen ? '主菜单' : '•••'}
            </div>

            {menuItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: sidebarOpen ? '12px 16px' : '12px',
                    marginBottom: '4px',
                    borderRadius: '10px',
                    textDecoration: 'none',
                    color: active ? 'var(--primary-color)' : 'var(--text-secondary)',
                    background: active
                      ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%)'
                      : 'transparent',
                    transition: 'all 0.2s ease',
                    justifyContent: sidebarOpen ? 'flex-start' : 'center',
                    border: active ? '1px solid rgba(99, 102, 241, 0.2)' : '1px solid transparent',
                  }}
                  onMouseEnter={(e) => {
                    if (!active) {
                      e.currentTarget.style.background = 'var(--bg-tertiary)';
                      e.currentTarget.style.color = 'var(--text-primary)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!active) {
                      e.currentTarget.style.background = 'transparent';
                      e.currentTarget.style.color = 'var(--text-secondary)';
                    }
                  }}
                >
                  <Icon size={20} />
                  {sidebarOpen && (
                    <span style={{ fontSize: '14px', fontWeight: 500 }}>{item.label}</span>
                  )}
                  {sidebarOpen && active && (
                    <ChevronRight
                      size={16}
                      style={{ marginLeft: 'auto', opacity: 0.5 }}
                    />
                  )}
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Overlay for mobile */}
        {isMobile && sidebarOpen && (
          <div
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.5)',
              zIndex: 98,
              top: '64px',
            }}
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main Content */}
        <main 
          style={{ 
            flex: 1, 
            display: 'flex', 
            flexDirection: 'column',
            minWidth: 0,
            marginLeft: isMobile ? 0 : undefined,
          }}
        >
          <div
            style={{
              flex: 1,
              padding: '24px 32px',
              overflowY: 'auto',
              height: 'calc(100vh - 64px)',
            }}
          >
            <div
              style={{
                maxWidth: '1600px',
                margin: '0 auto',
              }}
            >
              <Outlet />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
