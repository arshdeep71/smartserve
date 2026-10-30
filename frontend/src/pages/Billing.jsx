import { useEffect, useMemo, useState } from 'react';
import { Minus, Plus, ReceiptText, ShoppingBasket } from 'lucide-react';
import { request } from '../services/api';

export default function Billing({ businessId }) {
  const [menu, setMenu] = useState([]); const [cart, setCart] = useState({}); const [receiptType, setReceiptType] = useState('print'); const [message, setMessage] = useState('');
  useEffect(() => { request(`/businesses/${businessId}/menu`).then(setMenu).catch(err => setMessage(err.message)); }, [businessId]);
  const total = useMemo(() => menu.reduce((sum, item) => sum + (cart[item.id] || 0) * item.price, 0), [menu, cart]);
  function change(item, amount) { setCart(previous => ({ ...previous, [item.id]: Math.max(0, (previous[item.id] || 0) + amount) })); }
  async function checkout() {
    const items = menu.filter(item => cart[item.id]).map(item => ({ item_id: item.id, name: item.name, quantity: cart[item.id], unit_price: item.price }));
    if (!items.length) return setMessage('Add a menu item to start an order.');
    try { const order = await request(`/businesses/${businessId}/orders`, { method: 'POST', body: JSON.stringify({ items, receipt_type: receiptType }) }); setMessage(`Order ${order.order_id} saved · ₹${order.total.toFixed(2)}`); setCart({}); }
    catch (error) { setMessage(error.message); }
  }
  return <><div className="page-title"><p className="eyebrow">POINT OF SALE</p><h1>New order</h1><p className="muted">Tap an item to add it to the bill.</p></div><div className="billing-layout"><section className="content-card"><div className="section-heading"><h2>Available menu</h2><span className="pill">{menu.length} items</span></div><div className="menu-grid">{menu.map(item => <article className="menu-tile" key={item.id}><span className="menu-emoji">🍽️</span><b>{item.name}</b><span className="muted">{item.category}</span><strong>₹{item.price.toFixed(2)}</strong><button className="small-button" onClick={() => change(item, 1)}><Plus size={15} /> Add</button></article>)}</div>{!menu.length && <p className="empty-state">Your menu is empty. Add items from the Menu page first.</p>}</section><aside className="content-card order-card"><div className="section-heading"><h2><ShoppingBasket size={19} /> Current bill</h2></div>{menu.filter(item => cart[item.id]).map(item => <div className="cart-row" key={item.id}><span>{item.name}<small>₹{item.price.toFixed(2)} each</small></span><div className="quantity"><button onClick={() => change(item, -1)}><Minus size={13} /></button>{cart[item.id]}<button onClick={() => change(item, 1)}><Plus size={13} /></button></div></div>)}{!Object.values(cart).some(Boolean) && <p className="empty-state">Choose items to begin.</p>}<div className="total-row"><span>Total</span><strong>₹{total.toFixed(2)}</strong></div><label className="select-label">Receipt option<select value={receiptType} onChange={event => setReceiptType(event.target.value)}><option value="print">Print receipt</option><option value="coupon">Physical coupon</option></select></label><button className="primary-button full" disabled={!total} onClick={checkout}><ReceiptText size={17} /> Complete order</button>{message && <p className="form-message">{message}</p>}</aside></div></>;
}
