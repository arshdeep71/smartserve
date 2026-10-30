import { useState } from 'react';
import { Bell, LogOut, Search } from 'lucide-react';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import CanteenDashboard from './pages/CanteenDashboard';
import RestaurantDashboard from './pages/RestaurantDashboard';
import CafeDashboard from './pages/CafeDashboard';
import Billing from './pages/Billing';
import Menu from './pages/Menu';
import FeedbackForm from './pages/FeedbackForm';
import Analytics from './pages/Analytics';

export default function App() {
  const [signedIn, setSignedIn] = useState(Boolean(localStorage.getItem('token')));
  const [page, setPage] = useState('dashboard');
  const businessId = localStorage.getItem('businessId') || '';
  if (!signedIn) return <Login onLogin={() => setSignedIn(true)} />;
  const Page = ({ dashboardType }) => {
    if (page === 'billing') return <Billing businessId={businessId} />;
    if (page === 'menu') return <Menu businessId={businessId} />;
    if (page === 'feedback') return <FeedbackForm businessId={businessId} />;
    if (page === 'analytics') return <Analytics businessId={businessId} />;
    const props = { businessId, setPage };
    if (dashboardType === 'restaurant') return <RestaurantDashboard {...props} />;
    if (dashboardType === 'cafe') return <CafeDashboard {...props} />;
    return <CanteenDashboard {...props} />;
  };
  return <div className="app-shell"><Sidebar page={page} setPage={setPage} /><main className="main-area"><header className="topbar"><div className="search-box"><Search size={17} /><input placeholder="Search your workspace" /></div><div className="top-actions"><button className="icon-button" aria-label="Notifications"><Bell size={18} /></button><span className="user-avatar">S</span><span className="user-name">Business admin</span><button className="icon-button" aria-label="Sign out" onClick={() => { localStorage.removeItem('token'); setSignedIn(false); }}><LogOut size={17} /></button></div></header><div className="page-wrap"><Page dashboardType={localStorage.getItem('businessType')} /></div></main></div>;
}
