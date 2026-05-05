/**
 * Navbar component with user profile and app branding.
 * Sleek glassmorphic design with DaisyUI components.
 */

import { useAuth } from '../context/AuthContext';
import { LogOut, Sparkles, User, Settings, LayoutGrid, FileText, History } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

export function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/chat') {
      return location.pathname.startsWith('/chat');
    }
    return location.pathname === path;
  };

  return (
    <div className="sticky top-0 z-50 w-full border-b border-white/5 bg-black/50 backdrop-blur-2xl">
      <div className="max-w-7xl mx-auto px-4 md:px-6 h-16">
        <div className="flex items-center justify-between h-full">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group shrink-0">
            <div className="w-9 h-9 rounded-lg bg-wonder-lime flex items-center justify-center text-black shadow-[0_0_16px_rgba(217,255,0,0.25)] group-hover:scale-105 transition-transform">
              <Sparkles size={20} />
            </div>
            <span className="text-lg font-black tracking-tight text-white hidden sm:block">
              DOCQA<span className="text-wonder-lime">AI</span>
            </span>
          </Link>

          {/* Center Navigation */}
          {isAuthenticated && (
            <nav className="hidden md:flex items-center gap-1 bg-white/[0.03] rounded-full p-1 border border-white/[0.06]">
              <Link
                to="/"
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold transition-all ${
                  isActive('/')
                    ? 'bg-wonder-lime text-black shadow-[0_0_12px_rgba(217,255,0,0.3)]'
                    : 'text-white/60 hover:text-white hover:bg-white/5'
                }`}
              >
                <FileText size={16} />
                Documents
              </Link>
              <Link
                to="/chat"
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold transition-all ${
                  isActive('/chat')
                    ? 'bg-wonder-lime text-black shadow-[0_0_12px_rgba(217,255,0,0.3)]'
                    : 'text-white/60 hover:text-white hover:bg-white/5'
                }`}
              >
                <History size={16} />
                History
              </Link>
            </nav>
          )}

          {/* Right Side - Avatar */}
          <div className="flex items-center gap-3 shrink-0">
            {isAuthenticated && (
              <div className="dropdown dropdown-end">
                <label
                  tabIndex={0}
                  className="flex items-center gap-3 pl-2 pr-1 py-1 rounded-full bg-white/[0.03] border border-white/[0.08] hover:border-wonder-lime/30 hover:bg-white/[0.06] transition-all cursor-pointer group"
                >
                  <span className="text-sm font-medium text-white/80 hidden sm:block max-w-[100px] truncate">
                    {user?.name?.split(' ')[0] || user?.email?.split('@')[0]}
                  </span>
                  <div className="w-8 h-8 rounded-full overflow-hidden bg-gradient-to-br from-wonder-lime/20 to-white/10 border border-white/10 group-hover:border-wonder-lime/30 transition-colors">
                    {user?.avatar_url ? (
                      <img src={user.avatar_url} alt={user.name || ''} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <User size={16} className="text-white/60" />
                      </div>
                    )}
                  </div>
                </label>
                <ul
                  tabIndex={0}
                  className="mt-2 z-[1] p-1.5 shadow-2xl menu menu-sm dropdown-content bg-[#0a0a0a] border border-white/10 rounded-xl w-56 backdrop-blur-3xl"
                >
                  <div className="px-3 py-2.5 border-b border-white/5 mb-1">
                    <p className="text-[10px] font-bold text-white/40 uppercase tracking-wider mb-0.5">Signed in as</p>
                    <p className="font-semibold text-white text-sm truncate">{user?.name || user?.email}</p>
                  </div>
                  <li>
                    <Link
                      to="/"
                      className="py-2 px-3 rounded-lg flex items-center gap-2.5 hover:bg-white/5 text-white/80 text-sm font-medium transition-colors"
                    >
                      <LayoutGrid size={16} className="text-wonder-lime" />
                      Dashboard
                    </Link>
                  </li>
                  <li>
                    <a className="py-2 px-3 rounded-lg flex items-center gap-2.5 hover:bg-white/5 text-white/80 text-sm font-medium transition-colors cursor-pointer">
                      <Settings size={16} className="text-wonder-lime" />
                      Settings
                    </a>
                  </li>
                  <div className="h-px bg-white/5 my-1"></div>
                  <li>
                    <button
                      onClick={logout}
                      className="py-2 px-3 rounded-lg flex items-center gap-2.5 text-red-400 hover:bg-red-400/10 hover:text-red-300 text-sm font-medium transition-colors w-full"
                    >
                      <LogOut size={16} />
                      Sign out
                    </button>
                  </li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isAuthenticated && (
        <div className="md:hidden border-t border-white/5 bg-black/80 backdrop-blur-xl">
          <div className="flex items-center justify-around px-2 py-2">
            <Link
              to="/"
              className={`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
                isActive('/') ? 'text-wonder-lime' : 'text-white/50'
              }`}
            >
              <FileText size={20} />
              <span className="text-[10px] font-medium">Documents</span>
            </Link>
            <Link
              to="/chat"
              className={`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
                isActive('/chat') ? 'text-wonder-lime' : 'text-white/50'
              }`}
            >
              <History size={20} />
              <span className="text-[10px] font-medium">History</span>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
