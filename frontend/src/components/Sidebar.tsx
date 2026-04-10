import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderOpen,
  FlaskConical,
  ScanBarcode,
  Users,
  LogOut,
  BookOpen,
} from 'lucide-react';
import { clearTokens, getAccessToken } from '../auth';
import { jwtDecode } from '../utils/jwt';

interface NavItem {
  to: string;
  icon: React.ReactNode;
  label: string;
  adminOnly?: boolean;
}

const navItems: NavItem[] = [
  { to: '/', icon: <LayoutDashboard size={18} />, label: 'Dashboard' },
  { to: '/projects', icon: <FolderOpen size={18} />, label: 'Projects' },
  { to: '/experiments', icon: <FlaskConical size={18} />, label: 'Experiments' },
  { to: '/barcode', icon: <ScanBarcode size={18} />, label: 'Inventory Lookup' },
  { to: '/users', icon: <Users size={18} />, label: 'Users', adminOnly: true },
];

function isAdmin(): boolean {
  const token = getAccessToken();
  if (!token) return false;
  try {
    const decoded = jwtDecode(token);
    const roles: string[] = (decoded.roles as string[]) || (decoded.scopes as string[]) || [];
    return roles.includes('admin');
  } catch {
    return false;
  }
}

export default function Sidebar() {
  const navigate = useNavigate();
  const admin = isAdmin();

  function handleSignOut() {
    clearTokens();
    navigate('/login');
  }

  return (
    <aside className="w-60 min-h-screen bg-indigo-900 flex flex-col text-white flex-shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-5 border-b border-indigo-700">
        <BookOpen size={22} className="text-indigo-300" />
        <span className="font-semibold text-lg tracking-tight">Lab Notebook</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {navItems.map(item => {
          if (item.adminOnly && !admin) return null;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-700 text-white'
                    : 'text-indigo-200 hover:bg-indigo-800 hover:text-white'
                }`
              }
            >
              {item.icon}
              {item.label}
            </NavLink>
          );
        })}
      </nav>

      {/* Sign out */}
      <div className="px-3 py-4 border-t border-indigo-700">
        <button
          onClick={handleSignOut}
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-indigo-200 hover:bg-indigo-800 hover:text-white w-full transition-colors"
        >
          <LogOut size={18} />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
