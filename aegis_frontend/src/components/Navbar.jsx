import { NavLink } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { useState, useEffect } from 'react';
import { fetchPendingApprovals } from '../api';

export default function Navbar() {
  const [pendingCount, setPendingCount] = useState(0);

  useEffect(() => {
    const poll = async () => {
      try {
        const approvals = await fetchPendingApprovals();
        setPendingCount(approvals.length);
      } catch { /* ignore */ }
    };
    poll();
    const interval = setInterval(poll, 3000);
    return () => clearInterval(interval);
  }, []);

  const links = [
    { to: '/', label: 'Dashboard', end: true },
    { to: '/agents', label: 'Agents' },
    { to: '/activity', label: 'Activity' },
    { to: '/approvals', label: 'Approvals', badge: pendingCount },
  ];

  return (
    <nav className="h-16 border-b border-divider flex items-center px-4 sm:px-8 sticky top-0 bg-surface z-50">
      {/* Logo */}
      <NavLink to="/" className="flex items-center gap-2 mr-6 sm:mr-10 shrink-0">
        <Shield className="w-7 h-7 text-ink" strokeWidth={2.5} />
        <span className="text-xl sm:text-[22px] font-extrabold text-ink tracking-tight">Aegis</span>
      </NavLink>

      {/* Nav links */}
      <div className="flex h-full items-center gap-1 overflow-x-auto">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) =>
              `h-full flex items-center px-3 sm:px-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                isActive
                  ? 'text-ink border-positive'
                  : 'text-ink-secondary border-transparent hover:text-ink'
              }`
            }
          >
            {link.label}
            {link.badge > 0 && (
              <span className="ml-1.5 px-1.5 min-w-[18px] text-center text-[10px] font-bold bg-negative text-white rounded-full">
                {link.badge}
              </span>
            )}
          </NavLink>
        ))}
      </div>

      {/* Status */}
      <div className="ml-auto flex items-center gap-2 shrink-0">
        <span className="w-2 h-2 rounded-full bg-positive" />
        <span className="text-sm text-ink-secondary hidden sm:inline">Online</span>
      </div>
    </nav>
  );
}
