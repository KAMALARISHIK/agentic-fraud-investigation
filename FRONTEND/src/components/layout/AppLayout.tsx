import React, { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  ShieldAlert,
  CheckCircle2,
  Database,
  Bot,
  LogOut,
  ChevronDown,
  RefreshCw,
  ExternalLink,
  Circle,
} from 'lucide-react';
import { Logo } from '../ui/Logo';
import { StatusBanner } from '../ui/StatusBanner';
import { api, HealthResponse } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';

export const AppLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const fetchHealth = async () => {
    setIsCheckingHealth(true);
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch {
      setHealth({
        status: 'disconnected',
        tigergraph_connected: false,
        duckdb_connected: false,
        cases_loaded: 0,
        version: '1.0.0',
      });
    } finally {
      setIsCheckingHealth(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const isTigerGraphAsleep = health !== null && !health.tigergraph_connected;

  const navItems = [
    {
      to: '/app',
      label: 'Overview',
      hint: 'Executive dashboard & operational KPIs',
      icon: <LayoutDashboard className="w-4 h-4 shrink-0" />,
      end: true,
    },
    {
      to: '/app/cases',
      label: 'Investigations',
      hint: 'Case queue, graph investigations & triage',
      icon: <ShieldAlert className="w-4 h-4 shrink-0" />,
      end: false,
    },
    {
      to: '/app/approvals',
      label: 'Approvals',
      hint: 'Human-in-the-loop analyst action routing',
      icon: <CheckCircle2 className="w-4 h-4 shrink-0" />,
      end: false,
    },
    {
      to: '/app/memory',
      label: 'Case Memory',
      hint: 'Graph pattern rings & historical vector memory',
      icon: <Database className="w-4 h-4 shrink-0" />,
      end: false,
    },
    {
      to: '/app/agent',
      label: 'AI Agent',
      hint: 'Agent reasoning, tool analytics & policy inspection',
      icon: <Bot className="w-4 h-4 shrink-0" />,
      end: false,
    },
  ];

  // Get active title and hint based on current pathname
  const currentNav = navItems.find((item) =>
    item.end ? location.pathname === item.to : location.pathname.startsWith(item.to)
  );

  return (
    <div className="min-h-screen bg-[#FAF9F5] flex flex-col text-[#141413]">
      <StatusBanner
        isTigerGraphAsleep={isTigerGraphAsleep}
        onRefresh={fetchHealth}
        isChecking={isCheckingHealth}
      />

      <div className="flex-1 flex min-h-0">
        {/* Left Sidebar */}
        <aside className="w-64 shrink-0 border-r border-[#E8E6DC] bg-[#FAF9F5] flex flex-col justify-between hidden md:flex">
          <div>
            {/* Logo Header */}
            <div className="p-5 border-b border-[#E8E6DC]">
              <NavLink to="/app" className="block">
                <Logo showText={true} />
              </NavLink>
            </div>

            {/* Navigation Links */}
            <div className="p-3">
              <div className="px-3 py-2 text-[10px] uppercase tracking-wider font-semibold text-[#6B6A65]/80">
                Workspace
              </div>
              <nav className="space-y-1">
                {navItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.end}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-[#F5E6DF] text-[#D97757] font-semibold shadow-2xs'
                          : 'text-[#6B6A65] hover:text-[#141413] hover:bg-white/80'
                      }`
                    }
                  >
                    {item.icon}
                    <span>{item.label}</span>
                  </NavLink>
                ))}
              </nav>
            </div>
          </div>

          {/* Sidebar Footer */}
          <div className="p-4 border-t border-[#E8E6DC] space-y-3 bg-[#FAF9F5]">
            <div className="bg-white rounded-xl p-3 border border-[#E8E6DC] text-xs">
              <div className="flex items-center justify-between text-[11px] text-[#6B6A65] mb-1">
                <span className="font-medium">System Status</span>
                <span className="flex items-center gap-1.5 font-medium text-[#141413]">
                  <Circle
                    className={`w-2 h-2 fill-current ${
                      health?.tigergraph_connected
                        ? 'text-[#2F855A]'
                        : 'text-[#B7791F]'
                    }`}
                  />
                  {health?.tigergraph_connected ? 'Connected' : 'Asleep'}
                </span>
              </div>
              <div className="text-[10px] text-[#6B6A65]">
                TigerGraph Cloud & DuckDB
              </div>
            </div>

            <div className="flex items-center justify-between text-[11px] text-[#6B6A65] px-1">
              <span>Powered by TigerGraph</span>
              <a
                href="https://www.tigergraph.com"
                target="_blank"
                rel="noreferrer"
                className="text-[#6B6A65] hover:text-[#D97757] transition-colors"
                title="TigerGraph Cloud"
              >
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 bg-[#FAF9F5]">
          {/* Top Bar */}
          <header className="h-16 px-6 border-b border-[#E8E6DC] bg-white flex items-center justify-between sticky top-0 z-30">
            <div className="flex items-center gap-3">
              <div className="md:hidden">
                <Logo size={24} />
              </div>
              <div>
                <h2 className="font-serif text-lg font-semibold text-[#141413] leading-none">
                  {currentNav?.label || 'FraudSight Platform'}
                </h2>
                {currentNav?.hint && (
                  <p className="text-[11px] text-[#6B6A65] mt-0.5">{currentNav.hint}</p>
                )}
              </div>
            </div>

            {/* Right User & Status Area */}
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#FAF9F5] border border-[#E8E6DC] text-xs text-[#6B6A65]">
                <span
                  className={`w-2 h-2 rounded-full ${
                    health?.tigergraph_connected ? 'bg-[#2F855A]' : 'bg-[#B7791F]'
                  }`}
                />
                <span className="font-medium text-[11px] text-[#141413]">
                  {health?.tigergraph_connected ? 'Graph Ready' : 'Graph Standby'}
                </span>
                <button
                  onClick={fetchHealth}
                  disabled={isCheckingHealth}
                  className="hover:text-[#141413] transition-colors ml-1 cursor-pointer"
                  title="Refresh status"
                >
                  <RefreshCw className={`w-3 h-3 ${isCheckingHealth ? 'animate-spin' : ''}`} />
                </button>
              </div>

              {/* User Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-2.5 p-1.5 pr-2 rounded-xl hover:bg-[#FAF9F5] border border-transparent hover:border-[#E8E6DC] transition-colors cursor-pointer"
                >
                  <div className="w-7 h-7 rounded-lg bg-[#F5E6DF] text-[#D97757] font-semibold text-xs flex items-center justify-center border border-[#E8C5B8]">
                    {user?.name?.[0] || 'A'}
                  </div>
                  <div className="hidden sm:block text-left text-xs">
                    <div className="font-medium text-[#141413] leading-tight">{user?.name || 'Analyst'}</div>
                    <div className="text-[10px] text-[#6B6A65] leading-tight">{user?.role?.split(' ')[0] || 'Analyst'}</div>
                  </div>
                  <ChevronDown className="w-3.5 h-3.5 text-[#6B6A65]" />
                </button>

                {showUserMenu && (
                  <div className="absolute right-0 mt-2 w-52 bg-white rounded-xl border border-[#E8E6DC] shadow-lg py-1.5 z-50 text-xs">
                    <div className="px-3 py-2 border-b border-[#E8E6DC]">
                      <div className="font-medium text-[#141413]">{user?.name}</div>
                      <div className="text-[11px] text-[#6B6A65] truncate">{user?.email}</div>
                      <div className="text-[10px] text-[#D97757] font-medium mt-1">{user?.role}</div>
                    </div>
                    <button
                      onClick={() => {
                        setShowUserMenu(false);
                        logout();
                        navigate('/login');
                      }}
                      className="w-full px-3 py-2 text-left text-[#C0392B] hover:bg-[#FBEAE7]/50 flex items-center gap-2 transition-colors cursor-pointer"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            </div>
          </header>

          {/* Page Outlet */}
          <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto overflow-y-auto">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
};
