import { useEffect, useState } from 'react';
import { BarChart3 } from 'lucide-react';
import { request } from '../services/api';

export default function Analytics({ businessId }) {
  const [data, setData] = useState(null); const [error, setError] = useState('');
  useEffect(() => { request(`/businesses/${businessId}/analytics/sales`).then(setData).catch(err => setError(err.message)); }, [businessId]);
  return <><div className="page-title"><p className="eyebrow">KNOW YOUR BUSINESS</p><h1>Sales analytics</h1><p className="muted">A clear view of completed orders and popular items.</p></div>{error && <p className="notice">{error}</p>}<section className="content-card"><div className="section-heading"><h2><BarChart3 size={20} /> Items sold</h2><span className="pill">{data?.order_count ?? '—'} orders</span></div>{data?.items_sold.map(([name, quantity]) => <div className="bar-row" key={name}><span>{name}</span><div className="bar-track"><i style={{ width: `${Math.max(6, quantity / Math.max(...data.items_sold.map(([, count]) => count)) * 100)}%` }} /></div><b>{quantity}</b></div>)}{!data?.items_sold.length && <p className="empty-state">Complete an order to see sales analytics.</p>}</section></>;
}
