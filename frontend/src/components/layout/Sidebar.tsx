// components/layout/Sidebar.tsx — Navigation sidebar with real routing

import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { UserButton } from '@clerk/clerk-react';
import {
  LayoutDashboard,
  MessageSquare,
  Radio,
  FileText,
  Settings,
  Zap,
  AlertTriangle,
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

interface NavItemProps {
  icon: React.ReactNode;
  label: string;
  isActive: boolean;
  onClick: () => void;
  badge?: number;
}

function NavItem({ icon, label, isActive, onClick, badge }: NavItemProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className={`
        w-full aspect-square rounded-xl flex items-center justify-center transition-all duration-200 relative group
        ${isActive
          ? 'bg-brand-primary/20 text-brand-glow'
          : 'bg-surface-elevated text-gray-400 hover:text-white hover:bg-surface-border'
        }
      `}
      title={label}
    >
      {icon}
      {badge != null && badge > 0 && (
        <span className="absolute -top-0.5 -right-0.5 min-w-[14px] h-3.5 px-0.5 rounded-full bg-status-human text-[8px] font-bold text-white flex items-center justify-center">
          {badge > 9 ? '9+' : badge}
        </span>
      )}
      {isActive && (
        <span className="absolute -right-0.5 top-1/2 -translate-y-1/2 w-1 h-6 rounded-l-full bg-brand-primary" />
      )}
      <div className="absolute left-full ml-2 px-2 py-1 bg-surface-elevated border border-surface-border rounded-md text-xs text-white whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50">
        {label}
      </div>
    </motion.button>
  );
}

export function Sidebar() {
  const { tenants, activeTenant, setActiveTenant, sessions } = useApp();
  const navigate = useNavigate();
  const location = useLocation();

  const escalationCount = sessions.filter(
    (s) => s.status === 'NEEDS_HUMAN' || s.status === 'AGENT_HANDOFF',
  ).length;

  const navItems = [
    { icon: <LayoutDashboard size={16} />, label: 'Analytics', path: '/dashboard' },
    { icon: <MessageSquare size={16} />, label: 'Inbox', path: '/inbox' },
    {
      icon: <AlertTriangle size={16} />,
      label: 'Escalation Queue',
      path: '/escalation',
      badge: escalationCount,
    },
  ];

  const bottomNav = [
    { icon: <Radio size={16} />, label: 'Broadcast', path: '/broadcast' },
    { icon: <FileText size={16} />, label: 'Templates', path: '/templates' },
    { icon: <Settings size={16} />, label: 'Settings', path: '/settings' },
  ];

  return (
    <div className="w-14 sm:w-16 flex-shrink-0 bg-surface-card border-r border-surface-border flex flex-col items-center py-4 gap-2">
      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-primary to-brand-secondary flex items-center justify-center mb-4 glow-indigo">
        <Zap size={18} className="text-white" />
      </div>

      <div className="flex flex-col gap-2 flex-1 w-full px-2">
        <p className="text-[9px] text-gray-600 uppercase tracking-widest text-center mb-1 hidden sm:block">
          Tenants
        </p>
        {tenants.map((tenant) => {
          const isActiveTenant = activeTenant?.id === tenant.id;
          const parts = tenant.name.split(' ');
          const label = parts[0].charAt(0) + (parts[1]?.charAt(0) || '');
          return (
            <motion.button
              key={tenant.id}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setActiveTenant(tenant)}
              className={`
                w-full aspect-square rounded-xl flex items-center justify-center text-sm font-bold
                transition-all duration-200 relative group
                ${isActiveTenant
                  ? 'text-white shadow-lg'
                  : 'bg-surface-elevated text-gray-400 hover:text-white hover:bg-surface-border'
                }
              `}
              style={
                isActiveTenant
                  ? { backgroundColor: tenant.brand_color, boxShadow: `0 0 16px ${tenant.brand_color}60` }
                  : undefined
              }
              title={tenant.name}
            >
              {label.toUpperCase()}
              <div className="absolute left-full ml-2 px-2 py-1 bg-surface-elevated border border-surface-border rounded-md text-xs text-white whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50">
                {tenant.name}
              </div>
            </motion.button>
          );
        })}

        <div className="w-8 mx-auto border-t border-surface-border my-1" />

        {navItems.map((item) => (
          <NavItem
            key={item.path}
            icon={item.icon}
            label={item.label}
            isActive={location.pathname === item.path}
            onClick={() => navigate(item.path)}
            badge={item.badge}
          />
        ))}
      </div>

      <div className="flex flex-col gap-1 w-full px-2">
        {bottomNav.map((item) => (
          <NavItem
            key={item.path}
            icon={item.icon}
            label={item.label}
            isActive={location.pathname === item.path}
            onClick={() => navigate(item.path)}
          />
        ))}
        <div className="mt-2 flex items-center justify-center">
          <UserButton
            afterSignOutUrl="/"
            appearance={{
              elements: {
                avatarBox: 'w-9 h-9 ring-2 ring-indigo-500/40 ring-offset-2 ring-offset-[#0A0F1E]',
              },
            }}
          />
        </div>
      </div>
    </div>
  );
}
