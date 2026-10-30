# SmartServe — Smart Canteen, Restaurant & Café Management System

A simple, smart and ML-powered platform for managing canteens, restaurants and small cafés from one place.

## 1. About the Project

SmartServe is a web-based management system designed to make daily food-business operations easier.

A canteen, restaurant or café can log in to its own portal and manage its menu, orders, billing, sales and customer feedback.

The system also uses Machine Learning (ML) to analyse student feedback, identify common food complaints, understand customer preferences and forecast future demand.

The main idea is simple: **record daily business activity automatically and use that data to make better decisions.**

## 2. Problem Statement

Many college canteens serve the same menu repeatedly. Students may become bored with the available dishes, find food too spicy or have other complaints, but the canteen may not have an organised way to collect and analyse their opinions.

Small food businesses may also manage bills, sales and stock manually. This makes it difficult to track popular items, identify trends and plan the next day's requirements.

SmartServe addresses these problems through digital billing, QR-based feedback, centralised data storage and Machine Learning analysis.

## 3. Main Objectives

- Make daily order entry and billing simple.
- Generate a unique order number automatically.
- Allow the cashier to choose between a printed receipt and a physical coupon.
- Collect student feedback using a QR code.
- Keep feedback results private to authorised canteen administrators.
- Identify common complaints and frequently requested dishes.
- Track daily sales and popular menu items.
- Forecast future demand using historical data.
- Provide separate portals for canteens, restaurants and cafés.
- Evaluate ML models using suitable performance metrics.

## 4. Main Modules

### 4.1 Authentication and Business Portals

The platform supports different business types.

**Canteen portal**
- Quick billing for ready-to-serve food.
- Menu and daily sales management.
- QR feedback analytics.
- Food complaint analysis.
- New dish requests.
- Demand forecasting.

**Restaurant portal**
- Dine-in and takeaway orders.
- Table and kitchen-order management.
- Billing and sales reports.
- Menu and ingredient inventory management.

**Café portal**
- Coffee, beverages and snack management.
- Customisable sizes and add-ons.
- Quick billing and takeaway orders.
- Ingredient and stock tracking.

**Super Admin portal**
- Manage registered businesses.
- Manage authorised accounts and roles.
- View platform-level information.

Each business sees its own data and features. A canteen administrator cannot access another business's private records.

### 4.2 Canteen Billing System

The canteen usually serves food that is already prepared. Therefore, the billing workflow should remain fast and simple.

1. The cashier logs in.
2. The cashier selects items from the menu.
3. The cashier enters quantities.
4. The system calculates the total automatically.
5. The system generates a unique order ID.
6. The cashier chooses one of two options.

**Option A: Print Receipt**

The system prepares a small receipt containing:
- Canteen name.
- Order ID.
- Date and time.
- Item names and quantities.
- Prices and total amount.

A compatible receipt printer is needed for physical printing.

**Option B: Physical Coupon**

The order is saved in the database, but the cashier gives the student an existing physical coupon instead of printing a normal receipt.

If required, the system can record that a coupon was issued and store its reference number.

Both options retain the order data for sales reports and ML analysis.

### 4.3 QR-Based Student Feedback

A QR code is printed and displayed around the canteen. Students scan it using their phones and complete a short feedback form.

The form can contain the following questions.

**Question 1: Which food did you eat?**

Examples:
- Dal Roti
- Chana Chawal
- Rajma Chawal
- Other available meals

**Question 2: Did you like the food?**

- Yes, I liked it.
- No, I did not like it.
- I want a new dish on the menu.

**Question 3: If you did not like the food, what was the problem?**

- Too much chilli.
- Too much salt.
- Taste was not good.
- Food quality or freshness.
- The menu is repetitive.
- Other reason.

An optional text box lets students explain the problem in their own words.

**Question 4: Which new dish would you like?**

Students can select from a list or type a different dish.

The form should take only a short time to complete.

### 4.4 Private Feedback Dashboard

Only authorised canteen administrators can view feedback results.

The dashboard can display:
- Total feedback submissions.
- Percentage of students who liked the food.
- Percentage of students who disliked it.
- Most common complaints.
- Most requested new dishes.
- Feedback trends by day and meal.
- Written comments, subject to the configured privacy rules.
- ML-generated insights.

For example, the dashboard might report that many students complained about excessive chilli in rajma. The canteen administrator can use that information to review the recipe.

These figures must be calculated from actual submissions, not manually fixed example values.

### 4.5 Sales and Menu Analytics

Each completed order is stored automatically.

The system can calculate:
- Daily and weekly sales.
- Number of orders.
- Best-selling dishes.
- Total quantity sold per item.
- Sales trends by time and day.
- Popular and less popular menu items.

Combining sales data with feedback gives the canteen a better understanding of what students actually buy and what they want changed.

## 5. Machine Learning Features

### 5.1 Feedback Classification

The ML model analyses feedback and assigns relevant categories.

Examples:
- Positive feedback.
- Negative feedback.
- Excessive spice complaint.
- Taste complaint.
- Food quality complaint.
- Repetitive menu complaint.

For written comments, a text-classification model can identify common themes.

Example comment:

> The rajma was good, but it was too spicy today.

The system may identify positive feedback about taste and a separate complaint about spice.

A single positive/negative label may not capture this accurately, so multi-label or aspect-based classification can be used.

### 5.2 New Dish Demand Analysis

The system counts requests for different dishes.

For example, if many students request chole bhature, the dashboard ranks it among the most requested items.

This initial ranking can be calculated directly from database records. ML can be added later to identify trends and forecast future demand.

A high number of requests does not automatically mean the dish must be added. The canteen administrator makes the final decision after considering cost, equipment and availability.

### 5.3 Demand Forecasting

The system uses historical sales to estimate future demand.

Possible inputs include:
- Date and day of the week.
- Previous sales.
- Item-wise quantities.
- Meal category.
- Recent demand trends.
- Feedback trends, where useful.

For example, the system might estimate that demand for rajma chawal will increase on a particular weekday.

The prediction is an estimate, not a guarantee. It becomes more useful when enough reliable historical data is available.

## 6. Machine Learning Evaluation Metrics

Different metrics are required for different ML tasks.

| Metric | Purpose |
|---|---|
| Accuracy | Measures the proportion of correct classification predictions. |
| Precision | Measures how many predicted examples of a class were actually correct. |
| Recall | Measures how many actual examples of a class were identified. |
| F1-score | Balances precision and recall. |
| MAE | Measures the average absolute error in numerical predictions. |
| R² score | Measures how well a regression model explains variation in the target values. |

Accuracy, precision, recall and F1-score will evaluate feedback classification.

MAE and R² will evaluate a separate regression task, such as forecasting daily feedback counts or item demand.

The feedback classifier reports repeated, stratified 3-fold cross-validation results. Each fold is held out from training, and repeating the folds gives a better view of how much the score varies on this small dataset. It must not claim a high accuracy score without testing the model. The current 18 labels are demonstration examples only; collect a much larger human-reviewed dataset before treating the score as meaningful.

## 7. Technology Stack

The following stack is proposed for the project.

| Technology | Purpose |
|---|---|
| React | User interface and dashboards |
| Vite | Frontend development server and build tool |
| Python | Backend and ML implementation |
| FastAPI | Backend API |
| MongoDB | Store orders, menus, feedback and business data |
| PyMongo | Connect Python to MongoDB |
| Scikit-learn | Train and evaluate ML models |
| Pandas | Clean and prepare data |
| NumPy | Numerical calculations |
| HTML and CSS | Page structure and styling |
| JavaScript | Frontend interactions |

A receipt printer can be connected for physical receipts. The precise printing method depends on the printer and the environment in which the application runs.

## 8. Proposed Project Structure

```text
SmartServe/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── CanteenDashboard.jsx
│   │   │   ├── RestaurantDashboard.jsx
│   │   │   ├── CafeDashboard.jsx
│   │   │   ├── Billing.jsx
│   │   │   ├── FeedbackForm.jsx
│   │   │   └── Analytics.jsx
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── requirements.txt
│
├── ml/
│   ├── prepare_data.py
│   ├── train_feedback_model.py
│   ├── forecast_demand.py
│   └── evaluate_models.py
│   └── evaluate_demand.py
│
├── data/
│   └── sample_data.csv
│   └── feedback_labels.csv (small demonstration labels only)
│
├── README.md
└── .env.example
```

This is a proposed structure. The files must be created as the implementation progresses.

### Implementation status

The FastAPI backend includes business registration, account creation and sign-in, menu items, order recording, feedback submission and summaries, QR image generation, stock records and sales summaries. The feedback dashboard now calls an authenticated insights endpoint that classifies written comments with the locally trained demo classifier and shows its cross-validation metrics. Sales analytics now calls an authenticated demand-forecast endpoint that uses completed business orders and returns a seven-day per-item baseline estimate when at least two sales days are available. These insights render in the portal with dataset-size and estimate limitations visible.

Menu items can now define café sizes with extra prices, add-ons with prices, and ingredient quantities used per item. Checkout validates options and prices against the saved menu. When a recipe is configured, checkout deducts stock and rejects orders that would make stock negative. The backend also records manual stock movements. Admin/manager roles protect menu editing, reporting, feedback dashboards, and stock management; cashier roles can access restaurant tables and order operations.

First business and account setup is restricted to requests from the local computer so a setup key is not needed during development. Do not expose the service publicly without adding a proper invitation or operator-controlled registration flow. Receipt printing uses the browser print dialog, and ML examples use tiny demonstration datasets, so neither the app nor model results are production-ready.

The ML demonstration labels are not real customer feedback and must not be reported as a valid model result. Replace them with a representative, consented, human-reviewed dataset before drawing conclusions. `ml/evaluate_demand.py` uses chronological holdout data and reports MAE and R² where the test set is large enough. The live portal demand estimate is a simple baseline, not a guarantee or a learned item-specific model. The classifier is trained from the supplied demo labels; its predictions are suggestions for administrator review.

## 9. MongoDB Database Design

The database can contain the following collections.

**businesses**

Stores business name, business type and configuration.

**users**

Stores authorised user accounts, roles and business associations. Passwords must be securely hashed.

**menu_items**

Stores item name, price, availability and business ID.

**orders**

Stores order ID, business ID, items, quantities, total amount, date, time and order type.

**feedback**

Stores the selected meal, rating or opinion, complaint categories, written comments, requested dishes and submission timestamp.

**inventory**

Stores stock levels and stock movements for businesses that use inventory tracking.

**model_predictions**

Stores forecast values, prediction dates, model version and evaluation information where appropriate.

Each business-owned record should include a business identifier so that access can be restricted to the correct business.

## 10. How the System Works

The overall workflow is:

1. The business administrator creates a menu.
2. The cashier enters an order.
3. The system calculates the bill and generates an order ID.
4. The cashier selects printed receipt or physical coupon.
5. The completed order is saved to MongoDB.
6. Students submit feedback through the QR form.
7. Feedback is saved to MongoDB.
8. The dashboard updates sales and feedback summaries.
9. The ML model classifies feedback and forecasts selected numerical targets.
10. The administrator reviews the insights and decides what changes to make.

## 11. Installation and Setup

### Requirements

Install:
- Python 3.11 or another compatible supported version.
- Node.js and npm.
- MongoDB running locally or a MongoDB Atlas database.
- Git, if the project is managed using Git.

### Step 1: Clone the Project

```bash
git clone YOUR_REPOSITORY_URL
cd SmartServe
```

Replace `YOUR_REPOSITORY_URL` with the actual repository URL.

### Step 2: Configure the Backend

```bash
cd backend
python -m venv venv
```

Activate the virtual environment on Windows:

```bash
venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

From the project root, copy `.env.example` to `backend/.env` and set the connection details and a long random JWT secret:

```env
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=smartserve
JWT_SECRET=replace-with-a-long-random-secret
```

Do not commit real credentials to GitHub.

### Step 3: Start the Backend

From the project root, start the API:

```bash
uvicorn backend.main:app --reload
```

The API will usually be available at:

```text
http://127.0.0.1:8000
```

FastAPI's interactive API documentation is usually available at:

```text
http://127.0.0.1:8000/docs
```

### Step 4: Start the Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite in the terminal.

The frontend API URL defaults to `http://localhost:8000/api`. Set `VITE_API_URL` in `frontend/.env` if the backend runs elsewhere.

### Creating the first business and admin

Start MongoDB and the backend first. The sign-in page has a **Set up a new business** option. Enter the business details, admin email, and password. Setup works only from the computer running the backend. After setup, sign in with the admin email and password; the generated business ID is handled by the app. A signed-in business admin can use the account endpoint to add staff.

For menu recipes, add menu items with a `recipe` mapping from inventory item name to quantity consumed per serving; ensure those exact ingredient names exist in inventory. The order API validates café size/add-on price choices from the saved menu and deducts recipe quantities from inventory when the order is accepted. A stock shortfall rejects the order. Use `POST /api/businesses/{business_id}/stock-movements` to record deliveries or adjustments.

To run the demo ML reports, install the Python requirements and run `python ml/evaluate_models.py` and `python ml/evaluate_demand.py` from the project root. The supplied comment labels are examples for exercising the code only; their metrics do not represent real-world performance.

## 12. Data Collection and Testing

For the initial demonstration, sample data can be used to test the interface and database workflow.

However, sample data should be clearly labelled as demonstration data.

For meaningful ML evaluation:
1. Collect genuine feedback with permission.
2. Review and label a representative set of comments.
3. Split the data into training and test sets.
4. Train the classification model on training data.
5. Evaluate it on unseen test data.
6. Calculate accuracy, precision, recall and F1-score.
7. Evaluate demand forecasts using MAE and R².
8. Record limitations and compare results against a simple baseline.

For forecasting, use chronological train/test splitting where appropriate to avoid training on future information.

If the initial dataset is small, the project can still demonstrate the complete workflow, but the report must clearly state that ML results are preliminary.

## 13. Security and Privacy

- Only authorised users can access business dashboards.
- Passwords must be hashed, never stored as plain text.
- Business data must be isolated by business ID.
- Student feedback must not be publicly exposed.
- Rate limits or duplicate-submission controls should reduce spam.
- Collect only the information required for the project.
- Keep database credentials in environment variables.
- Do not claim that a QR form guarantees one response per student unless identity verification or another reliable control is implemented.

## 14. Limitations

- Predictions depend on the quantity and quality of available data.
- Feedback may be biased because not every student will submit a response.
- Written comments may contain ambiguous or mixed opinions.
- A demand forecast cannot guarantee actual sales.
- Inventory accuracy depends on recording stock movements correctly.
- Receipt printing depends on compatible hardware and configuration.

## 15. Future Enhancements

- Support additional languages.
- Add sales and feedback reports that can be exported.
- Introduce table management and kitchen displays for restaurants.
- Add low-stock alerts and ingredient-level inventory.
- Forecast demand separately for individual menu items.
- Add admin-approved menu changes based on feedback.
- Integrate supported payment services if required.
- Add business subscription plans and usage reports.
- Improve feedback classification as more labelled data becomes available.

## 16. Expected Outcome

SmartServe aims to provide a single platform for managing different food businesses while adapting the workflow to each business type.

For a college canteen, the focus is quick billing, physical coupon handling, QR-based student feedback and menu improvement.

For restaurants and cafés, the system can support more detailed order and inventory workflows.

By combining daily operational data with Machine Learning, the project demonstrates how a practical business application can turn routine records into useful insights.

## 17. Conclusion

SmartServe combines web development, database management and Machine Learning in one practical project.

It addresses real problems such as repetitive canteen menus, unstructured feedback, manual sales tracking and uncertain demand.

The goal is not to replace the administrator's decisions, but to provide reliable data and understandable insights that help the business improve its service.

**Project title:** SmartServe — Multi-Business POS and AI-Powered Feedback & Demand Analytics

**Core technologies:** React, FastAPI, MongoDB, PyMongo and Scikit-learn.
