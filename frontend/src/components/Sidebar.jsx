import { BarChart3, Boxes, Coffee, LayoutDashboard, MessageSquareText, ReceiptText, Utensils } from 'lucide-react';

const links = [
  ['Overview', 'dashboard', LayoutDashboard],
  ['Billing', 'billing', ReceiptText],
  ['Menu', 'menu', Utensils],
  ['Feedback', 'feedback', MessageSquareText],
  ['Analytics', 'analytics', BarChart3],
  ['Inventory', 'inventory', Boxes],
];

export default function Sidebar({ page, setPage }) {
  return <aside className="sidebar">
    <div className="brand"><span className="brand-icon"><Coffee size={20} /></span><span>smartserve<small>BUSINESS PORTAL</small></span></div>
    <div className="side-label">WORKSPACE</div>
    <nav>{links.map(([label, key, Icon]) => <button key={key} className={`nav-link ${page === key ? 'active' : ''}`} onClick={() => setPage(key)}><Icon size={18} />{label}</button>)}</nav>
    <div className="side-bottom"><span className="online-dot" /> All systems operational</div>
  </aside>;
}
