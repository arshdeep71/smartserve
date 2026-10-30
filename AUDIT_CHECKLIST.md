# SmartServe Canteen Portal Audit

**Audit date:** 2026-10-30  
**Scope:** Logged-in canteen business portal, public QR feedback, and the repository's ML demonstration scripts.  
**Method:** Manual browser interactions for portal workflows; direct execution of each `ml/` script.  
**Test records:** Records prefixed `AUDIT -` were created to exercise menu, stock, order, and public feedback flows. They remain in the local development database.

**ML connection update (2026-10-30):** The feedback classifier and live-order demand baseline are now connected to authenticated FastAPI routes and portal panels. Backend imports, route registration, classifier predictions, metric serialization, the demand insufficient-data response, Python compilation, and the Vite production build were checked. The updated panels have not yet been visually rechecked in an authenticated browser session.

## Portal checklist

| Feature | Status | What was checked |
|---|---|---|
| Email-and-password sign-in | **Pass (authenticated API); browser recheck pending** | The supplied demo credentials successfully obtained a token after fixing the missing local JWT configuration. The sign-in form has not yet been submitted in the visible browser. |
| Dashboard data loading | **Pass** | Dashboard screens loaded business data from the API. Sales, order count, active menu items, open kitchen count, popular items, and order progress are wired in the running UI. |
| Menu add and list | **Pass** | Added `AUDIT - Masala Tea` and verified it appeared in the order menu. The add form accepted price/category and optional size, add-on, and recipe details. |
| Menu edit and availability toggle | **Implemented; authenticated browser recheck pending** | Menu supports editing core fields, sizes, add-ons, and recipes, plus hiding/showing items. A protected partial-update API route was added. |
| POS item selection and total | **Pass** | Added one audit item; the bill showed ₹25.00 and enabled checkout. |
| Order creation and unique order ID | **Pass** | Submitted a dine-in order; confirmation showed `SS-BEE894A306 · ₹25.00`. |
| Order type selection | **Pass** | Counter, takeaway, and dine-in options were visible; dine-in was selected for the test order. |
| Kitchen order queue | **Pass** | The submitted order appeared in the queue as pending. Changed it through preparing, ready, and completed. |
| Analytics totals | **Pass** | Sales analytics showed ₹25, 1 order, and `AUDIT - Masala Tea` with 1 sold, matching the submitted order. |
| Inventory add/list | **Pass** | Added `AUDIT - Rice` (5 kg) and `AUDIT - Dal` (4.8 kg); both appeared in stock on hand. |
| Recipe stock deduction / shortage rejection | **Implemented; authenticated browser recheck pending** | Checkout deducts recipe quantities, rejects insufficient stock, and records each deduction in stock movement history. The existing audit order used an item without a recipe, so it did not prove deduction behavior. |
| Customer feedback QR generation / download link | **Pass** | The feedback page rendered a QR code and exposed a download link. The displayed URL was local to this development setup. |
| Public QR feedback form | **Pass** | Opened the public link while signed out, submitted an audit response (disliked, too spicy, dish request), and received the thank-you confirmation. |
| Private feedback summary and comment classifier | **Pass, integration smoke checked** | The portal now loads feedback totals/complaints/requests and comment classifications. The authenticated API logic returned one classified audit comment (`spice`) and the model metrics; the panel was not visually rechecked in an authenticated browser session. Predictions are explicitly labeled as preliminary. |
| Live demand forecast in sales analytics | **Pass, integration smoke checked** | Analytics now calls a protected endpoint based on completed business orders. The current test data covers one sales day, so the API correctly returns an insufficient-data message rather than using unrelated sample sales. |
| Receipt printing | **Implemented; device check pending** | Checkout offers receipt printing and renders the saved order details in a print layout. The browser print dialog and physical printer were not exercised. |
| Physical coupon workflow | **Implemented for recording; issuance is manual** | Checkout can record a coupon reference and marks the order for a physical coupon. Staff still need to issue the physical coupon themselves. |
| Inventory movement history / stock adjustments | **Implemented; authenticated browser recheck pending** | Inventory shows recorded movements and manual stock changes create history entries. Order recipe deductions are recorded as movements too. |
| Search and notifications | **Implemented; authenticated browser recheck pending** | Global search matches menu items and orders; notifications surface open orders and low-stock items. |
| Restaurant tables and staff permissions | **Out of scope as requested** | Restaurant table navigation has been removed from this portal. No staff-permission workflow was added. |
| Staff permissions and staff creation | **Out of scope as requested** | The canteen completion does not add or audit staff-permission workflows. |
| Business isolation | **Not verified** | No second business was used during this manual audit. |
| Dashboard actions | **Implemented; authenticated browser recheck pending** | “Manage menu” routes to menu management; New order opens checkout. Search and notifications have working data-backed behavior. |
| Visual readability | **Fix implemented; visual recheck pending** | Updated the shared content-card styles to use readable light surfaces and stronger text contrast. A fresh authenticated browser visual check is still pending. |

## Machine-learning and evaluation checklist

| Script / metric | Status | Result and interpretation |
|---|---|---|
| `ml/prepare_data.py` | **Pass** | Loaded and printed six sample sales rows. |
| `ml/train_feedback_model.py` | **Pass, demo-only** | Trained a TF-IDF + logistic-regression classifier in memory. It does not persist the model or connect it to the web app. |
| `ml/forecast_demand.py` | **Pass, demo-only** | Produced next-day estimate **40.8 units**, using a recent-mean baseline on six sample dates. |
| `ml/evaluate_models.py` — Accuracy | **Pass, weak demo result** | Updated run: **0.556 ± 0.179** across repeated stratified 3-fold cross-validation (18 labeled examples; 5 repeats). The earlier 7-example holdout score was 0.429. |
| `ml/evaluate_models.py` — Macro precision | **Pass, weak demo result** | Updated run: **0.554 ± 0.202** across the repeated folds. |
| `ml/evaluate_models.py` — Macro recall | **Pass, weak demo result** | Updated run: **0.556 ± 0.179** across the repeated folds. |
| `ml/evaluate_models.py` — Macro F1 | **Pass, weak demo result** | Updated run: **0.539 ± 0.184** across the repeated folds. Scores vary widely because the labeled dataset is tiny; they are not suitable for real-world performance claims. |
| `ml/evaluate_demand.py` — MAE | **Pass, weak demo result** | **3.50 units** on chronological holdout. |
| `ml/evaluate_demand.py` — R² | **Pass, weak demo result** | **-0.0204**, meaning this baseline did not outperform a mean-value reference on the held-out sample. |
| ML inference from portal feedback / demand forecasts | **Pass, with important limits** | Admin-only API routes now classify stored written comments and show evaluation metrics; sales analytics now uses completed business orders for a seven-day per-item moving-average estimate. Smoke checks confirmed inference and the insufficient-history response. This is not a learned demand model, and feedback predictions use only 18 demo labels. |

## Audit conclusion

The portal code now covers the canteen workflow: menu editing and availability, checkout, kitchen status changes, receipt layout, coupon-reference capture, recipe-based stock deduction and shortage checks, movement history, search, notifications, analytics, feedback, and the connected ML panels. The order lifecycle and public feedback were manually exercised in the earlier browser audit. This turn's build and backend compile checks are recorded below; menu edits, recipe stock changes, print dialog, coupon capture, search, notifications, and the redesigned UI still need authenticated browser rechecking. The user's browser session was logged out during this pass, so those interactions could not be honestly marked as manually verified. ML evaluation remains a weak demo result: 18 labels for feedback and a basic moving-average demand baseline. Restaurant tables and staff permissions are out of scope.

## Current code checks (2026-10-30)

- `python -m compileall backend ml`: **Pass**.
- Frontend production build via the project-local Vite binary: **Pass** (`vite v6.4.5`).
- Backend health endpoint: **Pass** (`{"status":"ok","app":"SmartServe"}`).
- Canteen sidebar scan: **Pass** (restaurant Tables navigation is absent).
- Demo email/password authentication: **Pass**. Authenticated GET requests returned data for sales, menu, orders, inventory, feedback summary, feedback insights, demand forecast, and stock movement history.
- Feedback QR endpoint: **Pass** (`HTTP 200`, PNG response).
- Login configuration: **Fixed**. Backend now loads `backend/.env` explicitly; a local ignored development JWT secret was created because none was configured.
