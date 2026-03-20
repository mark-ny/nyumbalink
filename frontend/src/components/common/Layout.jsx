import React, { useState, useEffect } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import {
  Home, Search, Heart, LayoutDashboard, LogIn, LogOut,
  User, Menu, X, Bell, ChevronDown, Shield, Plus
} from 'lucide-react';
import useAuthStore from '../../hooks/useAuthStore';
import { notificationsAPI } from '../../services/api';
import clsx from 'clsx';

export default function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [scrolled, setScrolled] = useState(false);
  const { user, isAuthenticated, logout, isAdmin, isOwner } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const isHome = location.pathname === '/';

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      notificationsAPI.list({ per_page: 1 })
        .then(res => setUnreadCount(res.data.unread_count))
        .catch(() => {});
    }
  }, [isAuthenticated, location.pathname]);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const navLinks = [
    { to: '/listings', label: 'Browse Properties' },
    { to: '/listings?category=rent', label: 'For Rent' },
    { to: '/listings?category=short_stay', label: 'Short Stay' },
    { to: '/listings?category=plot_sale', label: 'Land & Plots' },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {/* NAVBAR */}
      <header className={clsx(
        'fixed top-0 left-0 right-0 z-50 transition-all duration-300',
        scrolled || !isHome
          ? 'bg-white/95 backdrop-blur-md shadow-sm'
          : 'bg-transparent'
      )}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 lg:h-20">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2 flex-shrink-0">
              <div className="w-9 h-9 bg-primary-600 rounded-xl flex items-center justify-center">
                <Home size={18} className="text-white" />
              </div>
              <span className="font-display text-xl font-bold text-dark-900">
                Nyumba<span className="text-primary-600">Link</span>
              </span>
            </Link>

            {/* Desktop nav */}
            <nav className="hidden lg:flex items-center gap-1">
              {navLinks.map(link => (
                <Link
                  key={link.to}
                  to={link.to}
                  className={clsx(
                    'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                    location.pathname + location.search === link.to
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:text-primary-700 hover:bg-gray-100'
                  )}
                >
                  {link.label}
                </Link>
              ))}
            </nav>

            {/* Desktop right */}
            <div className="hidden lg:flex items-center gap-3">
              {isAuthenticated ? (
                <>
                  {isOwner() && (
                    <Link
                      to="/dashboard/create"
                      className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-primary-700 transition-colors"
                    >
                      <Plus size={16} />
                      List Property
                    </Link>
                  )}

                  {/* Notifications */}
                  <Link to="/dashboard" className="relative p-2 text-gray-600 hover:text-primary-600 transition-colors">
                    <Bell size={20} />
                    {unreadCount > 0 && (
                      <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                        {unreadCount > 9 ? '9+' : unreadCount}
                      </span>
                    )}
                  </Link>

                  {/* User menu */}
                  <div className="relative">
                    <button
                      onClick={() => setUserMenuOpen(!userMenuOpen)}
                      className="flex items-center gap-2 p-1 rounded-xl hover:bg-gray-100 transition-colors"
                    >
                      <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                        {user?.avatar_url
                          ? <img src={user.avatar_url} alt={user.name} className="w-8 h-8 rounded-full object-cover" />
                          : <span className="text-primary-700 text-sm font-semibold">{user?.name?.[0]?.toUpperCase()}</span>
                        }
                      </div>
                      <span className="text-sm font-medium text-gray-700">{user?.name?.split(' ')[0]}</span>
                      <ChevronDown size={14} className="text-gray-400" />
                    </button>

                    {userMenuOpen && (
                      <div className="absolute right-0 mt-2 w-52 bg-white rounded-2xl shadow-floating border border-gray-100 py-2 z-50">
                        <Link to="/profile" onClick={() => setUserMenuOpen(false)}
                          className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50">
                          <User size={16} className="text-gray-400" />
                          My Profile
                        </Link>
                        <Link to="/dashboard" onClick={() => setUserMenuOpen(false)}
                          className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50">
                          <LayoutDashboard size={16} className="text-gray-400" />
                          Dashboard
                        </Link>
                        <Link to="/saved" onClick={() => setUserMenuOpen(false)}
                          className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50">
                          <Heart size={16} className="text-gray-400" />
                          Saved Properties
                        </Link>
                        {isAdmin() && (
                          <Link to="/admin" onClick={() => setUserMenuOpen(false)}
                            className="flex items-center gap-3 px-4 py-2.5 text-sm text-primary-600 hover:bg-primary-50">
                            <Shield size={16} />
                            Admin Panel
                          </Link>
                        )}
                        <hr className="my-1 border-gray-100" />
                        <button onClick={handleLogout}
                          className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-red-600 hover:bg-red-50">
                          <LogOut size={16} />
                          Sign Out
                        </button>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <>
                  <Link to="/login" className="text-sm font-medium text-gray-600 hover:text-primary-700 px-4 py-2">
                    Sign In
                  </Link>
                  <Link to="/register"
                    className="bg-primary-600 text-white px-5 py-2.5 rounded-xl text-sm font-medium hover:bg-primary-700 transition-colors">
                    Get Started
                  </Link>
                </>
              )}
            </div>

            {/* Mobile menu toggle */}
            <button
              className="lg:hidden p-2 text-gray-600"
              onClick={() => setMenuOpen(!menuOpen)}
            >
              {menuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="lg:hidden bg-white border-t border-gray-100 shadow-lg">
            <div className="px-4 py-4 space-y-1">
              {navLinks.map(link => (
                <Link key={link.to} to={link.to}
                  onClick={() => setMenuOpen(false)}
                  className="block px-4 py-3 rounded-xl text-gray-700 hover:bg-gray-50 font-medium">
                  {link.label}
                </Link>
              ))}
              <hr className="my-2" />
              {isAuthenticated ? (
                <>
                  <Link to="/dashboard" onClick={() => setMenuOpen(false)}
                    className="block px-4 py-3 rounded-xl text-gray-700 hover:bg-gray-50">Dashboard</Link>
                  <Link to="/profile" onClick={() => setMenuOpen(false)}
                    className="block px-4 py-3 rounded-xl text-gray-700 hover:bg-gray-50">Profile</Link>
                  {isOwner() && (
                    <Link to="/dashboard/create" onClick={() => setMenuOpen(false)}
                      className="block px-4 py-3 rounded-xl bg-primary-600 text-white font-medium text-center">
                      + List Property
                    </Link>
                  )}
                  <button onClick={() => { setMenuOpen(false); handleLogout(); }}
                    className="w-full text-left px-4 py-3 rounded-xl text-red-600 hover:bg-red-50">
                    Sign Out
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" onClick={() => setMenuOpen(false)}
                    className="block px-4 py-3 rounded-xl text-gray-700 hover:bg-gray-50">Sign In</Link>
                  <Link to="/register" onClick={() => setMenuOpen(false)}
                    className="block px-4 py-3 rounded-xl bg-primary-600 text-white font-medium text-center">
                    Create Account
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </header>

      {/* Page content */}
      <main className="flex-1 pt-16 lg:pt-20">
        <Outlet />
      </main>

      {/* FOOTER */}
      <footer className="bg-dark-900 text-gray-400 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
            <div className="col-span-1 md:col-span-2">
              <Link to="/" className="flex items-center gap-2 mb-4">
                <div className="w-9 h-9 bg-primary-600 rounded-xl flex items-center justify-center">
                  <Home size={18} className="text-white" />
                </div>
                <span className="font-display text-xl font-bold text-white">
                  Nyumba<span className="text-primary-400">Link</span>
                </span>
              </Link>
              <p className="text-sm leading-relaxed max-w-xs">
                Kenya's trusted property marketplace. Find houses, apartments, short stays,
                and land across all 47 counties.
              </p>
              <p className="mt-4 text-xs">© {new Date().getFullYear()} NyumbaLink. All rights reserved.</p>
            </div>

            <div>
              <h4 className="text-white font-semibold mb-4">Browse</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/listings?category=rent" className="hover:text-white transition-colors">Houses for Rent</Link></li>
                <li><Link to="/listings?category=short_stay" className="hover:text-white transition-colors">Short Stay</Link></li>
                <li><Link to="/listings?category=plot_sale" className="hover:text-white transition-colors">Land & Plots</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="text-white font-semibold mb-4">Account</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/register" className="hover:text-white transition-colors">Create Account</Link></li>
                <li><Link to="/login" className="hover:text-white transition-colors">Sign In</Link></li>
                <li><Link to="/dashboard" className="hover:text-white transition-colors">Dashboard</Link></li>
                <li><Link to="/dashboard/create" className="hover:text-white transition-colors">List a Property</Link></li>
              </ul>
            </div>
          </div>
        </div>
      </footer>

      {/* Overlay for user menu */}
      {userMenuOpen && (
        <div className="fixed inset-0 z-40" onClick={() => setUserMenuOpen(false)} />
      )}
    </div>
  );
}
