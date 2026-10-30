import './styles.css';

const root = document.querySelector('#root');
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);

const feedbackBusiness = new URLSearchParams(location.search).get('feedback');
if (feedbackBusiness && !localStorage.getItem('token')) {
  root.innerHTML = `<main class="login-screen"><form class="login-card" id="public-feedback"><span class="brand-icon large">☕</span><p class="eyebrow">SMARTSERVE FEEDBACK</p><h1>How was your meal?</h1><label>Food you ate<input name="meal" required placeholder="Meal or item" /></label><label>Your experience<select name="opinion"><option value="liked">I liked it</option><option value="disliked">I did not like it</option><option value="request">I have a dish request</option></select></label><label>Anything to improve?<select name="complaint"><option value="">No complaint</option><option>Too spicy</option><option>Too salty</option><option>Taste</option><option>Freshness or quality</option><option>Repetitive menu</option><option>Other</option></select></label><label>Comment<input name="comment" maxlength="1000" /></label><label>Dish request<input name="requested_dish" maxlength="100" /></label><button class="primary-button full">Send feedback</button><p class="error" id="feedback-message"></p></form></main>`;
  root.querySelector('#public-feedback').addEventListener('submit', async event => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    try { const response = await fetch(`${API}/businesses/${encodeURIComponent(feedbackBusiness)}/feedback`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values) }); const result = await response.json(); if (!response.ok) throw new Error(result.detail || 'Could not send feedback'); root.innerHTML = '<main class="login-screen"><section class="login-card"><h1>Thank you!</h1><p class="muted">Your feedback has been recorded.</p></section></main>'; }
    catch (error) { root.querySelector('#feedback-message').textContent = error.message; }
  });
}

function renderLogin(message = '') {
  root.innerHTML = `<main class="login-screen"><form class="login-card" id="login"><span class="brand-icon large">☕</span><p class="eyebrow">SMARTSERVE PORTAL</p><h1>Welcome back</h1><p class="muted">Sign in to manage your food business.</p><label>Email address<input name="email" required type="email" autocomplete="username" placeholder="you@example.com"></label><label>Password<input name="password" required type="password" autocomplete="current-password" placeholder="Enter your password"></label><p class="error">${message}</p><button class="primary-button full">Sign in</button><button class="small-button" type="button" id="setup-account">Set up a new business</button><p class="login-hint">Ask your business administrator for your account email and password.</p></form></main>`;
  root.querySelector('#login').addEventListener('submit', async event => {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    try {
      const response = await fetch(`${API}/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: fields.get('email'), password: fields.get('password') }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Sign in failed');
      localStorage.setItem('token', data.access_token); localStorage.setItem('businessId', data.business_id); renderApp();
    } catch (error) { renderLogin(error.message); }
  });
  root.querySelector('#setup-account').addEventListener('click', () => renderSetup());
}

function renderPlatformLogin(message = '') {
  root.innerHTML = `<main class="login-screen"><form class="login-card" id="platform-login-form"><p class="eyebrow">SMARTSERVE PLATFORM</p><h1>Administrator sign in</h1><label>Email<input name="email" type="email" required></label><label>Password<input name="password" type="password" required></label><p class="error">${message}</p><button class="primary-button full">Sign in</button><button class="small-button" type="button" id="platform-setup">Set up first platform admin</button><button class="small-button" type="button" id="platform-back">Back</button></form></main>`;
  root.querySelector('#platform-back').onclick = () => renderLogin();
  root.querySelector('#platform-setup').onclick = () => renderPlatformSetup();
  root.querySelector('#platform-login-form').onsubmit = async event => { event.preventDefault(); const form = Object.fromEntries(new FormData(event.currentTarget)); try { const response=await fetch(`${API}/platform/login`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(form)});const data=await response.json();if(!response.ok)throw new Error(data.detail||'Sign in failed');localStorage.setItem('token',data.access_token);localStorage.setItem('role','super_admin');localStorage.removeItem('businessId');renderPlatform();} catch(error){renderPlatformLogin(error.message)} };
}

function renderPlatformSetup(message = '') {
  root.innerHTML = `<main class="login-screen"><form class="login-card" id="platform-setup-form"><p class="eyebrow">FIRST PLATFORM ADMIN</p><label>Email<input name="email" type="email" required></label><label>Password<input name="password" type="password" minlength="8" required></label><label>Setup key<input name="setup_key" type="password" required></label><p class="error">${message}</p><button class="primary-button full">Create platform admin</button><button class="small-button" type="button" id="platform-back">Back</button></form></main>`;
  root.querySelector('#platform-back').onclick=()=>renderPlatformLogin();
  root.querySelector('#platform-setup-form').onsubmit=async event=>{event.preventDefault();const form=Object.fromEntries(new FormData(event.currentTarget));try{const response=await fetch(`${API}/platform/setup-admin`,{method:'POST',headers:{'Content-Type':'application/json','X-Setup-Key':form.setup_key},body:JSON.stringify({email:form.email,password:form.password,role:'super_admin'})});const data=await response.json();if(!response.ok)throw new Error(data.detail||'Setup failed');renderPlatformLogin('Admin created. Sign in.')}catch(error){renderPlatformSetup(error.message)}};
}

async function renderPlatform() {
  root.innerHTML='<main class="page-wrap"><p class="eyebrow">PLATFORM MANAGEMENT</p><h1>Registered businesses</h1><div class="content-card" id="platform-list">Loading…</div><button class="small-button" id="platform-logout">Sign out</button></main>';
  root.querySelector('#platform-logout').onclick=()=>{localStorage.removeItem('token');localStorage.removeItem('role');renderLogin()};
  try{const response=await fetch(`${API}/platform/businesses`,{headers:{Authorization:`Bearer ${localStorage.getItem('token')}`}});const rows=await response.json();if(!response.ok)throw new Error(rows.detail||'Could not load businesses');root.querySelector('#platform-list').innerHTML=rows.map(row=>`<div class="list-row"><b>${row.name}</b><span>${row.business_type}</span><span class="grow"></span>${row.users} users · ${row.orders} orders</div>`).join('')||'<p class="empty-state">No businesses registered.</p>'}catch(error){root.querySelector('#platform-list').textContent=error.message}
}

function renderSetup(message = '', existingBusinessId = '') {
  const saved = window.setupValues || {};
  root.innerHTML = `<main class="login-screen"><form class="login-card" id="setup"><span class="brand-icon large">☕</span><p class="eyebrow">FIRST-TIME SETUP</p><h1>${existingBusinessId ? 'Finish account setup' : 'Create your business'}</h1><p class="muted">${existingBusinessId ? `Finish setting up ${window.pendingBusinessName || 'your business'}.` : 'Set up your store and admin account.'}</p>${existingBusinessId ? '' : `<label>Business name<input name="name" required value="${escapeHTML(saved.name || '')}"></label><label>Business type<select name="business_type"><option value="canteen" ${saved.business_type==='canteen'?'selected':''}>Canteen</option><option value="restaurant" ${saved.business_type==='restaurant'?'selected':''}>Restaurant</option><option value="cafe" ${saved.business_type==='cafe'?'selected':''}>Café</option></select></label>`}<label>Admin email<input name="email" type="email" required autocomplete="email" value="${escapeHTML(saved.email || '')}"></label><label>Admin password<input name="password" type="password" minlength="8" required autocomplete="new-password"></label><p class="error">${escapeHTML(message)}</p><button class="primary-button full">${existingBusinessId ? 'Finish setup' : 'Create business and admin'}</button><button class="small-button" type="button" id="back-login">Back to sign in</button></form></main>`;
  if (!existingBusinessId && !window.pendingSetupChecked) { window.pendingSetupChecked = true; fetch(`${API}/businesses/pending-setup`).then(response=>response.ok?response.json():[]).then(rows=>{if(rows.length===1){window.pendingBusinessName=rows[0].name;renderSetup('',rows[0].id)}}).catch(()=>{}); }
  root.querySelector('#back-login').addEventListener('click', () => renderLogin());
  root.querySelector('#setup').addEventListener('submit', async event => {
    event.preventDefault(); const values = Object.fromEntries(new FormData(event.currentTarget)); window.setupValues=values; const headers = { 'Content-Type': 'application/json' };
    try {
      let businessId = existingBusinessId || values.existing_business_id || '';
      if (!businessId) { const created = await fetch(`${API}/businesses`, { method: 'POST', headers, body: JSON.stringify({ name: values.name, business_type: values.business_type }) }); const business = await created.json(); if (!created.ok) throw new Error(formatApiError(business)); businessId = business.id; localStorage.setItem('businessId', businessId); }
      localStorage.setItem('businessId', businessId);
      const account = await fetch(`${API}/businesses/${businessId}/users`, { method: 'POST', headers, body: JSON.stringify({ email: values.email, password: values.password, role: 'admin' }) });
      const result = await account.json(); if (!account.ok) throw new Error(formatApiError(result));
      renderLogin('Setup complete. Sign in with the admin email and password you created.');
    } catch (error) { renderSetup(error.message, localStorage.getItem('businessId') || existingBusinessId); }
  });
}

function escapeHTML(value) { return String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char])); }

function formatApiError(data) {
  const detail = data?.detail;
  if (Array.isArray(detail)) return detail.map(item => item.msg || item.message || JSON.stringify(item)).join('; ');
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail === 'object') return detail.message || JSON.stringify(detail);
  return data?.message || 'Request failed. Check that the API is running.';
}

async function renderApp() {
  const businessId = localStorage.getItem('businessId');
  const token = localStorage.getItem('token');
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
  const api = async (path, options = {}) => { const response = await fetch(`${API}${path}`, { ...options, headers: { ...headers, ...options.headers } }); const result = await response.json(); if (!response.ok) throw new Error(result.detail || 'Request failed'); return result; };
  root.innerHTML = `<div class="app-shell reference-layout"><aside class="sidebar"><button class="menu-toggle" id="menu-toggle" aria-label="Toggle menu">☰</button><div class="brand"><span class="brand-icon">S</span><span>SmartServe<small>BUSINESS</small></span></div><div class="side-label">WORKSPACE</div><nav>${[['Overview','dashboard'],['Orders','orders'],['New order','billing'],['Kitchen','kitchen'],['Menu','menu'],['Feedback','feedback'],['Analytics','analytics'],['Inventory','inventory']].map(([name,key])=>`<button class="nav-link ${key==='dashboard'?'active':''}" data-page="${key}"><span class="nav-symbol">${{dashboard:'⌂',orders:'▧',billing:'▤',kitchen:'◷',menu:'▦',feedback:'✳',analytics:'▥',inventory:'▣'}[key]}</span><span>${name}</span></button>`).join('')}</nav><div class="side-bottom"><span class="online-dot"></span> All systems operational</div></aside><main class="main-area"><header class="topbar"><div class="search-wrapper"><label class="search-box"><span>⌕</span><input id="global-search" placeholder="Search orders and menu…" autocomplete="off"></label><div id="search-results" class="search-results" role="listbox" hidden></div></div><div class="top-actions"><button class="icon-button" id="notifications" aria-label="Notifications" aria-expanded="false">♧</button><span class="user-avatar">S</span><span class="user-name">Store admin</span><button class="nav-link" id="logout">Sign out</button><div id="notification-panel" class="notification-panel" hidden></div></div></header><div class="page-wrap" id="content"><div class="dashboard-heading"><div><h1>Dashboard</h1><p class="muted">Your store performance, at a glance.</p></div><div class="heading-actions"><button class="secondary-button" data-page="menu">Manage menu</button><button class="primary-button" data-page="billing">＋ New order</button></div></div><section class="stats-grid reference-stats"><article class="stat-card lead-stat"><div class="stat-top">TOTAL SALES <span class="stat-round">↗</span></div><strong id="sales">—</strong><small>Revenue from completed orders</small></article><article class="stat-card"><div class="stat-top">TOTAL ORDERS <span class="stat-round">↗</span></div><strong id="orders">—</strong><small>All orders recorded</small></article><article class="stat-card"><div class="stat-top">ACTIVE ITEMS <span class="stat-round">↗</span></div><strong id="products">—</strong><small>Available on your menu</small></article><article class="stat-card"><div class="stat-top">TO PREPARE <span class="stat-round">↗</span></div><strong id="pending">—</strong><small>Open kitchen orders</small></article></section><div class="dashboard-grid"><section class="content-card chart-card"><div class="section-heading"><div><h2>Sales analytics</h2><p class="muted">Weekly activity</p></div><span class="chart-legend"><i></i> Revenue</span></div><div class="sales-chart" id="sales-chart"></div><div class="chart-foot"><span id="chart-average">Average: —</span><span id="chart-peak">Peak: —</span></div></section><section class="content-card fulfillment-card"><div class="section-heading"><h2>Recent orders</h2><button class="text-button" data-page="orders">View all</button></div><div id="recent-orders"></div></section><section class="content-card reminders-card"><div class="section-heading"><h2>Today’s focus</h2></div><div class="reminder-inner"><h3 id="focus-title">Checking your store…</h3><p class="muted" id="focus-note">Orders and stock updates will appear here.</p><button class="primary-button full" data-page="kitchen">Open kitchen queue</button></div></section><section class="content-card progress-card"><div class="section-heading"><h2>Order progress</h2></div><div class="progress-ring" id="progress-ring"><div><strong id="progress-value">—</strong><small>orders completed</small></div></div><div class="progress-legend"><span><i class="done-dot"></i>Completed</span><span><i class="open-dot"></i>In progress</span></div></section><section class="content-card product-card"><div class="section-heading"><h2>Popular menu items</h2><button class="text-button" data-page="menu">＋ Manage</button></div><div id="top-products"></div></section><section class="quick-card"><div><small>SMARTSERVE</small><h2>Keep your service moving</h2><p>Quick access to the tools you use every day.</p></div><div class="quick-actions"><button data-page="billing">＋ New order</button><button data-page="feedback">Show feedback QR</button></div></section></div></div></main></div>`;
  try {
    const [data, menu, orders] = await Promise.all([api(`/businesses/${businessId}/analytics/sales`), api(`/businesses/${businessId}/menu`), api(`/businesses/${businessId}/orders`)]);
    const completed=orders.filter(order=>order.status==='completed').length;const open=orders.filter(order=>!['completed','cancelled'].includes(order.status));
    document.querySelector('#sales').textContent=`₹${data.sales_total.toLocaleString('en-IN')}`;document.querySelector('#orders').textContent=orders.length;document.querySelector('#products').textContent=menu.filter(item=>item.available).length;document.querySelector('#pending').textContent=open.length;
    document.querySelector('#recent-orders').innerHTML=orders.slice(0,5).map(order=>`<div class="activity-row"><span class="activity-icon">▤</span><div class="activity-copy"><b>${order.order_id}</b><small>${order.items.map(item=>`${item.quantity}× ${item.name}`).join(', ')}</small></div><span class="status-pill ${order.status}">${order.status}</span></div>`).join('')||'<p class="empty-state">No orders yet. Start your first order.</p>';
    const best=data.items_sold.slice(0,5);document.querySelector('#top-products').innerHTML=best.map(([name,quantity],index)=>`<div class="activity-row"><span class="product-rank">0${index+1}</span><div class="activity-copy"><b>${name}</b><small>${quantity} sold</small></div><span class="muted">Popular</span></div>`).join('')||'<p class="empty-state">Menu sales will show after your first order.</p>';
    const days=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];const daily=days.map((day,index)=>({day,value:orders.filter(order=>{const date=new Date(order.created_at);return !Number.isNaN(date.valueOf())&&date.getDay()===index}).reduce((sum,order)=>sum+(order.status==='completed'?order.total:0),0)}));const peak=Math.max(...daily.map(x=>x.value),1);document.querySelector('#sales-chart').innerHTML=daily.map(point=>`<div class="chart-column"><span class="bar-value">${point.value?`₹${Math.round(point.value)}`:''}</span><i style="height:${Math.max(point.value?8:3,point.value/peak*100)}%"></i><small>${point.day}</small></div>`).join('');
    const average=Math.round(daily.reduce((sum,x)=>sum+x.value,0)/7);document.querySelector('#chart-average').textContent=`Average: ₹${average.toLocaleString('en-IN')}`;document.querySelector('#chart-peak').textContent=`Peak: ₹${Math.max(...daily.map(x=>x.value)).toLocaleString('en-IN')}`;
    const percent=orders.length?Math.round(completed/orders.length*100):0;document.querySelector('#progress-ring').style.setProperty('--progress',`${percent}%`);document.querySelector('#progress-value').textContent=`${percent}%`;
    document.querySelector('#focus-title').textContent=open.length?`${open.length} order${open.length===1?'':'s'} need attention`:'You’re all caught up';document.querySelector('#focus-note').textContent=open.length?'Review new orders and keep customers updated.':'There are no open orders right now.';
  } catch (error) { document.querySelector('#sales').textContent='—';document.querySelector('#focus-title').textContent='Could not load store data';document.querySelector('#focus-note').textContent=error.message; }
  root.querySelector('#logout').addEventListener('click', () => { localStorage.removeItem('token'); renderLogin(); });
  root.querySelector('#menu-toggle').addEventListener('click',()=>root.querySelector('.sidebar').classList.toggle('collapsed'));
  const navigate = page => {
    root.querySelectorAll('.sidebar [data-page]').forEach(item => item.classList.toggle('active', item.dataset.page === page));
    const content = document.querySelector('#content');
    showPage(page, content, businessId, api);
  };
  root.querySelectorAll('[data-page]').forEach(button => button.addEventListener('click', () => navigate(button.dataset.page)));

  const searchInput = root.querySelector('#global-search');
  const searchResults = root.querySelector('#search-results');
  let searchTimer;
  searchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    const term = searchInput.value.trim().toLocaleLowerCase();
    if (!term) { searchResults.hidden = true; searchResults.replaceChildren(); return; }
    searchTimer = setTimeout(async () => {
      try {
        const [menuItems, orders] = await Promise.all([api(`/businesses/${businessId}/menu`), api(`/businesses/${businessId}/orders`)]);
        const matches = [
          ...menuItems.filter(item => item.name.toLocaleLowerCase().includes(term)).slice(0, 5).map(item => ({ kind: 'Menu item', label: item.name, detail: `₹${item.price.toFixed(2)} · ${item.available ? 'Available' : 'Hidden'}`, page: 'menu' })),
          ...orders.filter(order => order.order_id.toLocaleLowerCase().includes(term) || order.items.some(item => item.name.toLocaleLowerCase().includes(term))).slice(0, 5).map(order => ({ kind: 'Order', label: order.order_id, detail: `${order.status} · ₹${order.total.toFixed(2)}`, page: 'orders' })),
        ].slice(0, 8);
        searchResults.innerHTML = matches.map((match, index) => `<button class="search-result" type="button" role="option" data-result="${index}"><span>${escapeHtml(match.kind)}</span><b>${escapeHtml(match.label)}</b><small>${escapeHtml(match.detail)}</small></button>`).join('') || '<p class="empty-state">No matching orders or menu items.</p>';
        searchResults.hidden = false;
        searchResults.querySelectorAll('[data-result]').forEach(button => button.addEventListener('click', () => {
          const match = matches[Number(button.dataset.result)];
          searchResults.hidden = true;
          searchInput.value = '';
          navigate(match.page);
        }));
      } catch (error) {
        searchResults.innerHTML = `<p class="empty-state">${escapeHtml(error.message)}</p>`;
        searchResults.hidden = false;
      }
    }, 220);
  });
  document.addEventListener('click', event => {
    if (!event.target.closest('.search-wrapper')) searchResults.hidden = true;
  });

  const notificationButton = root.querySelector('#notifications');
  const notificationPanel = root.querySelector('#notification-panel');
  notificationButton.addEventListener('click', async () => {
    if (!notificationPanel.hidden) { notificationPanel.hidden = true; notificationButton.setAttribute('aria-expanded', 'false'); return; }
    notificationPanel.hidden = false;
    notificationButton.setAttribute('aria-expanded', 'true');
    notificationPanel.innerHTML = '<p class="muted">Checking orders and stock…</p>';
    try {
      const [orders, stock] = await Promise.all([api(`/businesses/${businessId}/orders`), api(`/businesses/${businessId}/inventory`)]);
      const openOrders = orders.filter(order => !['completed', 'cancelled'].includes(order.status));
      const lowStock = stock.filter(item => item.quantity <= item.low_stock_at);
      const notices = [
        ...openOrders.map(order => ({ label: `Order ${order.order_id}`, detail: `${order.status} · ${order.items.map(item => item.name).join(', ')}`, page: 'kitchen' })),
        ...lowStock.map(item => ({ label: `${item.name} is low`, detail: `${item.quantity} ${item.unit} remaining`, page: 'inventory' })),
      ];
      notificationPanel.innerHTML = `<h2>Store alerts</h2>${notices.map((notice, index) => `<button class="notification-row" type="button" data-notice="${index}"><b>${escapeHtml(notice.label)}</b><small>${escapeHtml(notice.detail)}</small></button>`).join('') || '<p class="empty-state">No open orders or low-stock ingredients.</p>'}`;
      notificationPanel.querySelectorAll('[data-notice]').forEach(button => button.addEventListener('click', () => { const notice = notices[Number(button.dataset.notice)]; notificationPanel.hidden = true; notificationButton.setAttribute('aria-expanded', 'false'); navigate(notice.page); }));
    } catch (error) { notificationPanel.innerHTML = `<p class="notice">${escapeHtml(error.message)}</p>`; }
  });
}

async function showPage(page, content, businessId, api) {
  const title = { dashboard: 'Overview', orders: 'Order history', billing: 'New order', menu: 'Menu management', feedback: 'Customer feedback', analytics: 'Sales analytics', inventory: 'Inventory', kitchen: 'Kitchen queue' }[page];
  content.innerHTML = `<p class="eyebrow">SMARTSERVE WORKSPACE</p><h1>${title}</h1><p class="muted">Loading your business data…</p>`;
  try {
    if (page === 'orders') {
      const rows = await api(`/businesses/${businessId}/orders`);
      content.innerHTML = `<p class="eyebrow">POINT OF SALE</p><h1>Order history</h1><div class="section-heading"><p class="muted">${rows.length} orders recorded</p><button class="primary-button" data-new-order>＋ New order</button></div><section class="content-card order-history">${rows.map(order => `<article class="order-history-row"><div class="order-history-main"><b>${escapeHtml(order.order_id)}</b><small>${order.created_at ? new Date(order.created_at).toLocaleString() : ''}</small><p>${order.items.map(item => `${escapeHtml(item.quantity)} × ${escapeHtml(item.name)}`).join(', ')}</p></div><div class="order-history-meta"><span class="status-pill ${escapeHtml(order.status)}">${escapeHtml(order.status)}</span><small>${escapeHtml((order.order_type || '').replace('_', ' '))} · ${escapeHtml(order.receipt_type || 'print')}</small></div><strong>₹${order.total.toFixed(2)}</strong></article>`).join('') || '<p class="empty-state">Orders will appear here after checkout.</p>'}</section>`;
      content.querySelector('[data-new-order]').addEventListener('click', () => showPage('billing', content, businessId, api));
    } else if (page === 'menu') {
      const rows = await api(`/businesses/${businessId}/menu`);
      content.innerHTML = `<p class="eyebrow">YOUR OFFERING</p><h1>Menu management</h1><div class="two-column"><section class="content-card"><div class="section-heading"><h2>Menu items</h2><span class="pill">${rows.length} items</span></div><div id="menu-items"></div></section><form class="content-card add-form" id="add-menu"><p class="eyebrow" id="menu-form-eyebrow">NEW ITEM</p><h2 id="menu-form-title">Add to menu</h2><label>Item name<input name="name" required maxlength="100"></label><label>Base price (₹)<input name="price" type="number" min="0.01" step="0.01" required></label><label>Category<select name="category"><option value="meal">Meal</option><option value="snack">Snack</option><option value="beverage">Beverage</option><option value="dessert">Dessert</option></select></label><label>Sizes and extra prices<input name="sizes" placeholder="Small:0, Large:20"></label><label>Add-ons and prices<input name="addons" placeholder="Oat milk:15, Extra shot:20"></label><label>Recipe use per item<input name="recipe" placeholder="AUDIT - Rice:0.2, AUDIT - Dal:0.1"></label><p class="muted">Use comma-separated Name:amount pairs. Recipe amounts are ingredient units used per serving.</p><div class="menu-form-actions"><button class="primary-button" id="menu-submit">Add item</button><button class="secondary-button" id="cancel-menu-edit" type="button" hidden>Cancel edit</button></div><p class="error" id="form-error" role="status"></p></form></div>`;
      const form = content.querySelector('#add-menu');
      const itemsPanel = content.querySelector('#menu-items');
      let editingId = null;
      const pairsToInput = pairs => Object.entries(pairs || {}).map(([name, value]) => `${name}:${value}`).join(', ');
      const parsePairs = value => Object.fromEntries(value.split(',').map(entry => entry.trim()).filter(Boolean).map(entry => {
        const separator = entry.lastIndexOf(':');
        const name = entry.slice(0, separator).trim();
        const amount = Number(entry.slice(separator + 1).trim());
        if (separator < 1 || !name || !Number.isFinite(amount) || amount < 0) throw new Error(`Invalid item: "${entry}". Use Name:amount.`);
        return [name, amount];
      }));
      const renderItems = () => {
        itemsPanel.innerHTML = rows.map(item => `<article class="menu-admin-row"><div class="menu-admin-copy"><b>${escapeHtml(item.name)}</b><small>${escapeHtml(item.category)} · ${item.available ? 'Available' : 'Hidden from checkout'} · ₹${item.price.toFixed(2)}</small></div><button class="small-button" type="button" data-edit-menu="${escapeHtml(item.id)}">Edit</button><button class="small-button" type="button" data-toggle-menu="${escapeHtml(item.id)}">${item.available ? 'Hide' : 'Show'}</button></article>`).join('') || '<p class="empty-state">No items yet. Add your first one.</p>';
        itemsPanel.querySelectorAll('[data-edit-menu]').forEach(button => button.addEventListener('click', () => {
          const item = rows.find(row => row.id === button.dataset.editMenu);
          if (!item) return;
          editingId = item.id;
          form.elements.name.value = item.name;
          form.elements.price.value = item.price;
          form.elements.category.value = item.category;
          form.elements.sizes.value = pairsToInput(item.sizes);
          form.elements.addons.value = pairsToInput(item.add_ons);
          form.elements.recipe.value = pairsToInput(item.recipe);
          form.querySelector('#menu-form-eyebrow').textContent = 'EDIT ITEM';
          form.querySelector('#menu-form-title').textContent = `Edit ${item.name}`;
          form.querySelector('#menu-submit').textContent = 'Save changes';
          form.querySelector('#cancel-menu-edit').hidden = false;
          form.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }));
        itemsPanel.querySelectorAll('[data-toggle-menu]').forEach(button => button.addEventListener('click', async () => {
          const item = rows.find(row => row.id === button.dataset.toggleMenu);
          if (!item) return;
          try {
            await api(`/businesses/${businessId}/menu/${item.id}`, { method: 'PATCH', body: JSON.stringify({ available: !item.available }) });
            await refreshMenu();
          } catch (error) { content.querySelector('#form-error').textContent = error.message; }
        }));
      };
      const refreshMenu = async () => { rows.splice(0, rows.length, ...await api(`/businesses/${businessId}/menu`)); renderItems(); };
      const resetMenuForm = () => {
        editingId = null;
        form.reset();
        form.querySelector('#menu-form-eyebrow').textContent = 'NEW ITEM';
        form.querySelector('#menu-form-title').textContent = 'Add to menu';
        form.querySelector('#menu-submit').textContent = 'Add item';
        form.querySelector('#cancel-menu-edit').hidden = true;
      };
      form.querySelector('#cancel-menu-edit').addEventListener('click', resetMenuForm);
      renderItems();
      form.addEventListener('submit', async event => {
        event.preventDefault();
        const formData = new FormData(form);
        const button = form.querySelector('#menu-submit');
        button.disabled = true;
        form.querySelector('#form-error').textContent = '';
        try {
          const body = {
            name: formData.get('name').trim(),
            price: Number(formData.get('price')),
            category: formData.get('category'),
            available: editingId ? rows.find(item => item.id === editingId)?.available ?? true : true,
            sizes: parsePairs(formData.get('sizes')),
            add_ons: parsePairs(formData.get('addons')),
            recipe: parsePairs(formData.get('recipe')),
          };
          await api(editingId ? `/businesses/${businessId}/menu/${editingId}` : `/businesses/${businessId}/menu`, { method: editingId ? 'PATCH' : 'POST', body: JSON.stringify(body) });
          resetMenuForm();
          await refreshMenu();
        } catch (error) { form.querySelector('#form-error').textContent = error.message; }
        finally { button.disabled = false; }
      });
    } else if (page === 'billing') {
      const [allItems, business] = await Promise.all([api(`/businesses/${businessId}/menu`), api(`/businesses/${businessId}`)]);
      const items = allItems.filter(item => item.available);
      const cart = {};
      content.innerHTML = `<p class="eyebrow">POINT OF SALE</p><h1>New order</h1><div class="billing-layout"><section class="content-card"><div class="section-heading"><h2>Available menu</h2><span class="pill">${items.length} items</span></div><div class="menu-grid">${items.map(item => `<article class="menu-tile"><b>${escapeHtml(item.name)}</b><strong>₹${item.price.toFixed(2)}</strong>${Object.keys(item.sizes || {}).length ? `<label class="option-label">Size<select data-size="${escapeHtml(item.id)}">${Object.entries(item.sizes).map(([name, cost]) => `<option value="${escapeHtml(name)}">${escapeHtml(name)} + ₹${cost.toFixed(2)}</option>`).join('')}</select></label>` : ''}${Object.entries(item.add_ons || {}).map(([name, cost]) => `<label class="addon-option"><input type="checkbox" data-addon="${escapeHtml(item.id)}" value="${escapeHtml(name)}">${escapeHtml(name)} + ₹${cost.toFixed(2)}</label>`).join('')}<button class="small-button" type="button" data-item="${escapeHtml(item.id)}">Add</button></article>`).join('') || '<p class="empty-state">No available items. Add or show items in Menu management.</p>'}</div></section><aside class="content-card order-card"><h2>Current bill</h2><div id="cart-rows"></div><label class="select-label">Order type<select id="order-type"><option value="counter">Counter</option><option value="takeaway">Takeaway</option><option value="dine_in">Dine in</option></select></label><label class="select-label">Receipt option<select id="receipt"><option value="print">Print receipt</option><option value="coupon">Physical coupon</option></select></label><label class="select-label" id="coupon-reference-wrap" hidden>Coupon reference (optional)<input id="coupon-reference" maxlength="60" placeholder="Enter the number on the issued coupon"></label><button class="primary-button full" id="checkout" disabled>Complete order</button><p id="checkout-message" class="form-message" role="status"></p></aside></div><section class="receipt-print" id="receipt-print" hidden></section>`;
      const updateCart = () => {
        const selected = items.filter(item => cart[item.id]);
        const total = selected.reduce((sum, item) => sum + (item.price + (item.sizes?.[cart[item.id].size] || 0) + cart[item.id].addons.reduce((addonSum, addon) => addonSum + (item.add_ons?.[addon] || 0), 0)) * cart[item.id].quantity, 0);
        content.querySelector('#cart-rows').innerHTML = selected.map(item => `<div class="cart-row"><span>${escapeHtml(item.name)} ${escapeHtml(cart[item.id].size || '')}<small>${cart[item.id].addons.map(escapeHtml).join(', ')}</small></span><button class="small-button" type="button" data-remove="${escapeHtml(item.id)}" aria-label="Remove one ${escapeHtml(item.name)}">−</button><b>${cart[item.id].quantity}</b><button class="small-button" type="button" data-add="${escapeHtml(item.id)}" aria-label="Add one ${escapeHtml(item.name)}">+</button></div>`).join('') + `<div class="total-row"><span>Total</span><strong>₹${total.toFixed(2)}</strong></div>`;
        content.querySelector('#checkout').disabled = total <= 0;
      };
      content.querySelectorAll('[data-item]').forEach(button => button.addEventListener('click', () => {
        const id = button.dataset.item;
        const item = items.find(row => row.id === id);
        const size = content.querySelector(`[data-size="${id}"]`)?.value || null;
        const addons = [...content.querySelectorAll(`[data-addon="${id}"]:checked`)].map(input => input.value);
        if (cart[id]) cart[id].quantity++;
        else cart[id] = { quantity: 1, size, addons };
        updateCart();
      }));
      content.querySelector('#cart-rows').addEventListener('click', event => {
        const id = event.target.dataset.add || event.target.dataset.remove;
        if (!id || !cart[id]) return;
        cart[id].quantity = Math.max(0, cart[id].quantity + (event.target.dataset.add ? 1 : -1));
        if (!cart[id].quantity) delete cart[id];
        updateCart();
      });
      content.querySelector('#receipt').addEventListener('change', event => {
        content.querySelector('#coupon-reference-wrap').hidden = event.target.value !== 'coupon';
      });
      content.querySelector('#checkout').addEventListener('click', async event => {
        const button = event.currentTarget;
        button.disabled = true;
        const message = content.querySelector('#checkout-message');
        message.textContent = '';
        try {
          const picked = items.filter(item => cart[item.id]).map(item => ({
            item_id: item.id,
            name: item.name,
            quantity: cart[item.id].quantity,
            unit_price: item.price,
            size: cart[item.id].size,
            add_ons: cart[item.id].addons,
          }));
          const receipt_type = content.querySelector('#receipt').value;
          const order_type = content.querySelector('#order-type').value;
          const coupon_reference = content.querySelector('#coupon-reference').value.trim() || null;
          const order = await api(`/businesses/${businessId}/orders`, { method: 'POST', body: JSON.stringify({ items: picked, receipt_type, order_type, coupon_reference }) });
          Object.keys(cart).forEach(id => delete cart[id]);
          content.querySelector('#coupon-reference').value = '';
          content.querySelector('#receipt').value = 'print';
          content.querySelector('#coupon-reference-wrap').hidden = true;
          updateCart();
          if (receipt_type === 'print') {
            const receiptDate = order.created_at ? new Date(order.created_at).toLocaleString() : new Date().toLocaleString();
            const lines = order.items.map(item => `<div class="receipt-line"><span>${escapeHtml(item.quantity)} × ${escapeHtml(item.name)}${item.size ? ` · ${escapeHtml(item.size)}` : ''}${item.add_ons?.length ? ` · ${item.add_ons.map(escapeHtml).join(', ')}` : ''}</span><strong>₹${(item.quantity * item.unit_price).toFixed(2)}</strong></div>`).join('');
            const receipt = content.querySelector('#receipt-print');
            receipt.innerHTML = `<p class="receipt-brand">SMARTSERVE</p><h2>${escapeHtml(business.name)}</h2><p>Order ${escapeHtml(order.order_id)}</p><p>${escapeHtml(receiptDate)} · ${escapeHtml(order.order_type.replace('_', ' '))}</p><hr>${lines}<hr><div class="receipt-total"><span>Total</span><strong>₹${order.total.toFixed(2)}</strong></div><p class="receipt-thanks">Thank you. Please retain this receipt.</p>`;
            receipt.hidden = false;
            message.innerHTML = `Order ${escapeHtml(order.order_id)} saved · ₹${order.total.toFixed(2)} <button class="small-button" type="button" id="print-receipt">Print receipt</button>`;
            content.querySelector('#print-receipt').addEventListener('click', () => window.print());
          } else {
            const reference = order.coupon_reference ? ` Coupon reference: ${escapeHtml(order.coupon_reference)}.` : '';
            message.textContent = `Order ${order.order_id} saved · ₹${order.total.toFixed(2)}. Give the customer a physical coupon.${reference}`;
            content.querySelector('#receipt-print').hidden = true;
          }
        } catch (error) {
          message.textContent = error.message;
        } finally {
          button.disabled = !items.length;
          updateCart();
        }
      });
      updateCart();
    } else if (page === 'feedback') {
      content.innerHTML=`<p class="eyebrow">LISTEN AND IMPROVE</p><h1>Customer feedback</h1><p class="muted">Share the QR form and review feedback trends and model suggestions.</p><div class="two-column ml-feedback-grid"><section class="content-card qr-card"><h2>Customer feedback QR</h2><p class="muted">Customers can leave feedback without signing in.</p><img alt="Feedback QR code" src="${API}/businesses/${businessId}/feedback/qr"><a class="primary-button" href="${API}/businesses/${businessId}/feedback/qr" download="smartserve-feedback-qr.png">Download QR code</a><p class="share-link">${escapeHtml(location.origin)}/?feedback=${escapeHtml(businessId)}</p></section><section class="content-card" id="feedback-summary"><h2>Feedback summary</h2><p class="muted">Loading recorded responses…</p></section></div><section class="content-card ml-insights-card" id="feedback-ml"><h2>Comment classifier</h2><p class="muted">Loading model insights…</p></section>`;
      const [summaryResult, insightsResult] = await Promise.allSettled([
        api(`/businesses/${businessId}/feedback/summary`),
        api(`/businesses/${businessId}/analytics/feedback-insights`),
      ]);
      const summaryPanel = content.querySelector('#feedback-summary');
      if (summaryResult.status === 'fulfilled') {
        const summary = summaryResult.value;
        const complaints = summary.top_complaints.map(([label, count]) => `<div class="list-row"><span>${escapeHtml(label)}</span><span class="grow"></span><b>${count}</b></div>`).join('') || '<p class="empty-state">No complaints recorded.</p>';
        const requests = summary.requested_dishes.map(([label, count]) => `<div class="list-row"><span>${escapeHtml(label)}</span><span class="grow"></span><b>${count}</b></div>`).join('') || '<p class="empty-state">No dish requests recorded.</p>';
        summaryPanel.innerHTML = `<h2>Feedback summary</h2><div class="feedback-stats"><div><strong>${summary.total}</strong><span>responses</span></div><div><strong>${summary.liked_percent}%</strong><span>liked</span></div><div><strong>${summary.disliked_percent}%</strong><span>disliked</span></div></div><h3>Common complaints</h3>${complaints}<h3>Requested dishes</h3>${requests}`;
      } else {
        summaryPanel.innerHTML = `<h2>Feedback summary</h2><p class="notice">${escapeHtml(summaryResult.reason.message)}</p>`;
      }
      const modelPanel = content.querySelector('#feedback-ml');
      if (insightsResult.status === 'fulfilled') {
        const result = insightsResult.value;
        const metrics = Object.entries(result.cross_validation.metrics).map(([name, score]) => `<div class="metric-tile"><span>${escapeHtml(name)}</span><strong>${(score.mean * 100).toFixed(1)}%</strong><small>± ${(score.std * 100).toFixed(1)} points</small></div>`).join('');
        const predictedCounts = result.predicted_counts.map(([label, count]) => `<span class="prediction-chip">${escapeHtml(label)} <b>${count}</b></span>`).join('') || '<p class="empty-state">Add written comments to feedback to see predictions.</p>';
        const predictions = result.predictions.map(prediction => `<article class="prediction-row"><div><b>${escapeHtml(prediction.meal)}</b><p>${escapeHtml(prediction.comment)}</p></div><span class="prediction-label">${escapeHtml(prediction.predicted_label)}<small>${Math.round(prediction.confidence * 100)}% confidence</small></span></article>`).join('') || '<p class="empty-state">No written comments to classify yet.</p>';
        modelPanel.innerHTML = `<div class="section-heading"><div><h2>Comment classifier</h2><p class="muted">${escapeHtml(result.model)} · ${result.training_examples} demo training examples</p></div><span class="pill">${result.classified_count} comments classified</span></div><p class="notice">${escapeHtml(result.warning)} Cross-validation scores are for the demo training data, not accuracy guarantees for your customers.</p><div class="ml-metrics">${metrics}</div><h3>Predicted themes</h3><div class="prediction-chips">${predictedCounts}</div><h3>Comment predictions</h3>${predictions}`;
      } else {
        modelPanel.innerHTML = `<h2>Comment classifier</h2><p class="notice">Could not load model insights: ${escapeHtml(insightsResult.reason.message)}</p>`;
      }
    } else if (page === 'analytics') {
      const [data, forecast] = await Promise.all([
        api(`/businesses/${businessId}/analytics/sales`),
        api(`/businesses/${businessId}/analytics/demand-forecast`),
      ]);
      const popularItems = data.items_sold.map(([name,count])=>`<div class="list-row"><b>${escapeHtml(name)}</b><span class="grow"></span>${count} sold</div>`).join('')||'<p class="empty-state">Complete orders to see item analytics.</p>';
      const forecastBody = forecast.status === 'ready'
        ? `<p class="forecast-total">${forecast.estimated_total_quantity} <span>estimated items</span></p><p class="muted">Estimate for ${escapeHtml(forecast.forecast_for)} · using completed sales from ${escapeHtml(forecast.window_start)} to ${escapeHtml(forecast.window_end)}.</p><div class="forecast-items">${forecast.items.map(item=>`<div class="list-row"><b>${escapeHtml(item.item)}</b><span class="grow"></span>${item.estimated_quantity} / day</div>`).join('')||'<p class="empty-state">No item-level history in this period.</p>'}</div><p class="notice">${escapeHtml(forecast.warning)}</p>`
        : `<p class="notice">${escapeHtml(forecast.message)}</p><p class="muted">Completed order data will power this estimate once sales span multiple days.</p>`;
      content.innerHTML=`<p class="eyebrow">KNOW YOUR BUSINESS</p><h1>Sales analytics</h1><div class="stats-grid"><article class="stat-card"><div class="stat-top">TOTAL SALES</div><strong>₹${data.sales_total.toLocaleString('en-IN')}</strong></article><article class="stat-card"><div class="stat-top">ORDERS</div><strong>${data.order_count}</strong></article></div><div class="two-column"><section class="content-card"><h2>Popular items</h2>${popularItems}</section><section class="content-card demand-card"><div class="section-heading"><div><h2>Demand forecast</h2><p class="muted">7-day moving average baseline</p></div><span class="pill">${forecast.status === 'ready' ? 'Estimate' : 'Needs data'}</span></div>${forecastBody}</section></div>`;
    } else if (page === 'inventory') {
      const [rows, movements] = await Promise.all([api(`/businesses/${businessId}/inventory`), api(`/businesses/${businessId}/stock-movements`)]);
      content.innerHTML = `<p class="eyebrow">STOCK CONTROL</p><h1>Inventory</h1><div class="two-column"><section class="content-card"><div class="section-heading"><h2>Stock on hand</h2><span class="pill">${rows.length} tracked</span></div>${rows.map(item => `<div class="list-row"><div class="stock-copy"><b>${escapeHtml(item.name)}</b><small class="${item.quantity <= item.low_stock_at ? 'low-stock-label' : ''}">${item.quantity <= item.low_stock_at ? 'Low stock' : 'In stock'}</small></div><span class="grow"></span><strong>${item.quantity} ${escapeHtml(item.unit)}</strong></div>`).join('') || '<p class="empty-state">No stock tracked yet.</p>'}</section><form class="content-card add-form" id="stock-form"><h2>Add or update stock</h2><label>Ingredient<input name="name" required maxlength="100"></label><label>Current quantity<input name="quantity" type="number" min="0" step="0.1" required></label><label>Unit<input name="unit" value="kg" required maxlength="20"></label><button class="primary-button">Save stock</button><p class="muted">Changes are recorded below. Recipe use is deducted automatically when an order is accepted.</p></form></div><section class="content-card movement-card"><div class="section-heading"><h2>Recent stock movements</h2><span class="pill">Last ${movements.length}</span></div>${movements.map(movement => `<div class="list-row"><div class="movement-copy"><b>${escapeHtml(movement.item_name)}</b><small>${escapeHtml(movement.note || 'Stock movement')} · ${movement.recorded_at ? new Date(movement.recorded_at).toLocaleString() : ''}</small></div><span class="grow"></span><strong class="${movement.quantity_change < 0 ? 'movement-out' : 'movement-in'}">${movement.quantity_change > 0 ? '+' : ''}${movement.quantity_change}</strong></div>`).join('') || '<p class="empty-state">Stock additions and order usage will appear here.</p>'}</section>`;
      content.querySelector('#stock-form').addEventListener('submit', async event => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        const button = event.currentTarget.querySelector('button[type="submit"]') || event.currentTarget.querySelector('button');
        button.disabled = true;
        try {
          await api(`/businesses/${businessId}/inventory`, { method: 'PUT', body: JSON.stringify({ name: form.get('name').trim(), quantity: Number(form.get('quantity')), unit: form.get('unit').trim(), low_stock_at: 5 }) });
          showPage(page, content, businessId, api);
        } catch (error) {
          event.currentTarget.insertAdjacentHTML('beforeend', `<p class="error">${escapeHtml(error.message)}</p>`);
          button.disabled = false;
        }
      });
    } else if (page === 'tables') {
      const rows=await api(`/businesses/${businessId}/tables`);content.innerHTML=`<p class="eyebrow">RESTAURANT SERVICE</p><h1>Table management</h1><div class="two-column"><section class="content-card"><h2>Tables</h2>${rows.map(row=>`<div class="list-row"><b>${row.name}</b><span>${row.seats} seats</span><span class="grow"></span><select data-status="${row.id}"><option ${row.status==='available'?'selected':''}>available</option><option ${row.status==='occupied'?'selected':''}>occupied</option><option ${row.status==='reserved'?'selected':''}>reserved</option></select></div>`).join('')||'<p class="empty-state">Add your restaurant tables.</p>'}</section><form class="content-card add-form" id="table-form"><h2>Add a table</h2><label>Table name<input name="name" placeholder="Table 1" required></label><label>Seats<input name="seats" type="number" min="1" value="2" required></label><button class="primary-button">Add table</button></form></div>`;content.querySelector('#table-form').addEventListener('submit',async event=>{event.preventDefault();const form=new FormData(event.currentTarget);await api(`/businesses/${businessId}/tables`,{method:'POST',body:JSON.stringify({name:form.get('name'),seats:Number(form.get('seats'))})});showPage(page,content,businessId,api)});content.querySelectorAll('[data-status]').forEach(select=>select.addEventListener('change',()=>api(`/businesses/${businessId}/tables/${select.dataset.status}/status?status=${select.value}`,{method:'PATCH'})));
    } else if (page === 'kitchen') {
      const rows=await api(`/businesses/${businessId}/orders`);content.innerHTML=`<p class="eyebrow">ORDER PREPARATION</p><h1>Kitchen queue</h1><section class="content-card">${rows.filter(row=>!['completed','cancelled'].includes(row.status)).map(row=>`<article class="list-row" style="align-items:flex-start"><div><b>${row.order_id}</b><small>${row.items.map(item=>`${item.quantity} × ${item.name}`).join(', ')}</small></div><span class="grow"></span><select data-order="${row.order_id}"><option ${row.status==='pending'?'selected':''}>pending</option><option ${row.status==='preparing'?'selected':''}>preparing</option><option ${row.status==='ready'?'selected':''}>ready</option><option>completed</option></select></article>`).join('')||'<p class="empty-state">No open orders.</p>'}</section>`;content.querySelectorAll('[data-order]').forEach(select=>select.addEventListener('change',()=>api(`/businesses/${businessId}/orders/${select.dataset.order}/status?status=${select.value}`,{method:'PATCH'})));
    } else {
      const data=await api(`/businesses/${businessId}/analytics/sales`);content.querySelector('p.muted').textContent=`${data.order_count} orders recorded · ₹${data.sales_total.toLocaleString('en-IN')} total sales`;
    }
  } catch(error) { content.insertAdjacentHTML('beforeend',`<p class="notice">${error.message}</p>`); }
}

if (!feedbackBusiness || localStorage.getItem('token')) { if (localStorage.getItem('token') && localStorage.getItem('businessId')) renderApp(); else if (!feedbackBusiness) renderLogin(); }
