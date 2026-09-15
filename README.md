# 📊 Sales Analytics Dashboard

A cloud-based **Sales Analytics Dashboard** that allows users to upload sales datasets, store CSV files securely on **Amazon S3**, process and store sales records in **AWS RDS MySQL**, and analyze the data through an interactive web dashboard.

The project combines **Flask, Python, Pandas, MySQL, AWS S3, AWS RDS, HTML, CSS, JavaScript, and Chart.js** to create a complete cloud-based data analytics application.

---

## 🚀 Project Overview

The Sales Analytics Dashboard is designed to transform raw sales CSV files into meaningful business insights.

Users can:

- Register and log in to the application
- Upload sales CSV files
- Store uploaded CSV files in AWS S3
- Process and clean the uploaded data using Pandas
- Store sales records in a centralized MySQL database
- Generate unique dataset IDs
- View key performance indicators
- Visualize sales through interactive charts
- View the top-selling products
- View previously uploaded datasets
- Switch between datasets
- Delete datasets

The application uses a **shared database table architecture**, where all uploaded datasets are stored in one `sales_data` table and separated using `dataset_id`.

---

# ✨ Features

## 🔐 User Authentication

The application provides basic user authentication functionality.

Features include:

- User registration
- User login
- Session-based authentication
- Logout
- Protected dashboard routes
- User-specific dataset history

---

## 📂 CSV Dataset Upload

Users can upload sales datasets in CSV format.

The application:

1. Receives the uploaded CSV
2. Reads the file using Pandas
3. Supports multiple CSV encodings
4. Cleans column names
5. Removes duplicate records
6. Removes empty records
7. Validates required columns
8. Generates a unique `dataset_id`
9. Uploads the original CSV to AWS S3
10. Stores processed records in MySQL
11. Saves dataset metadata in `upload_history`

---

## ☁️ AWS S3 Storage

Uploaded CSV files are stored in an Amazon S3 bucket.

Example:

```text
AWS S3 Bucket
│
└── uploads/
    ├── 20260915_sales.csv
    ├── 20260915_superstore.csv
    └── 20260915_retail.csv
```

This keeps the original uploaded files separate from the processed database records.

---

## 🗄️ AWS RDS MySQL

The application uses **AWS RDS MySQL** as its cloud database.

The database stores:

- User information
- Dataset metadata
- Processed sales records

This allows the dashboard to retrieve and analyze datasets without creating a separate MySQL table for every uploaded CSV.

---

# 🏗️ Application Architecture

The application follows a cloud-based architecture:

```text
                         USER
                           |
                           v
                  +----------------+
                  | Flask Web App  |
                  +-------+--------+
                          |
              +-----------+-----------+
              |                       |
              v                       v
        +-----------+           +-----------+
        |  AWS S3   |           | AWS RDS   |
        |           |           |  MySQL    |
        | CSV Files |           |           |
        +-----------+           +-----+-----+
                                      |
                         +------------+------------+
                         |            |            |
                         v            v            v
                      users    upload_history   sales_data
                                      |
                                      v
                             Analytics Dashboard
                                      |
                         +------------+------------+
                         |            |            |
                         v            v            v
                       KPIs       Charts      Top Products
```

---

# 🔄 Data Flow

The complete upload and analytics workflow is:

```text
CSV File
   |
   v
Flask Upload Route
   |
   v
Read CSV with Pandas
   |
   v
Clean & Validate Data
   |
   v
Generate Dataset ID
   |
   +-------------------------+
   |                         |
   v                         v
AWS S3                    MySQL
   |                         |
   |                    +----+-----+
   |                    |          |
   |                    v          v
   |               sales_data  upload_history
   |                    |
   +--------------------+
                        |
                        v
                Dashboard Queries
                        |
                        v
                  KPIs + Charts
```

---

# 🧩 Shared Dataset Architecture

A major part of the project is the use of a **shared `sales_data` table**.

Instead of creating a new database table for every uploaded CSV, all datasets are stored in the same table.

### Old approach

```text
CSV 1 → dataset_001
CSV 2 → dataset_002
CSV 3 → dataset_003
CSV 4 → dataset_004
```

This creates many database tables and becomes difficult to manage.

### Current approach

```text
CSV 1 ─┐
CSV 2 ─┤
CSV 3 ─┼──→ sales_data
CSV 4 ─┘
```

Each record contains a `dataset_id`.

Example:

```text
dataset_id = 1 → Dataset A
dataset_id = 2 → Dataset B
dataset_id = 3 → Dataset C
```

Queries use the dataset ID to retrieve the correct records:

```sql
SELECT *
FROM sales_data
WHERE dataset_id = %s;
```

This makes the application easier to maintain and scale.

---

# 🗄️ Database Design

The application uses three primary MySQL tables.

---

## 1. `users`

Stores registered user information.

| Column | Description |
|---|---|
| `id` | Unique user ID |
| `name` | User name |
| `email` | User email |
| `password` | User password |
| `created_at` | Account creation timestamp |

---

## 2. `upload_history`

Stores metadata about uploaded datasets.

| Column | Description |
|---|---|
| `id` | Upload history ID |
| `file_name` | Original CSV filename |
| `dataset_id` | Unique dataset identifier |
| `s3_key` | AWS S3 object key |
| `total_rows` | Number of rows |
| `total_columns` | Number of columns |
| `uploaded_by` | User who uploaded the dataset |
| `upload_time` | Upload timestamp |

---

## 3. `sales_data`

Stores the processed sales records.

| Column | Description |
|---|---|
| `id` | Unique record ID |
| `dataset_id` | Dataset identifier |
| `uploaded_by` | User who uploaded the dataset |
| `order_id` | Order identifier |
| `order_date` | Order date |
| `product` | Product name |
| `category` | Product category |
| `quantity` | Quantity sold |
| `sales` | Sales amount |
| `profit` | Profit amount |

---

# 📈 Dashboard Analytics

After a dataset is selected, the application calculates several KPIs.

## Key Performance Indicators

### Total Orders

Number of records/orders in the selected dataset.

### Total Sales

Total sales calculated using:

```text
SUM(sales)
```

### Total Profit

Total profit calculated using:

```text
SUM(profit)
```

### Total Quantity

Total quantity sold:

```text
SUM(quantity)
```

### Average Sales

Average sales value:

```text
AVG(sales)
```

---

# 📊 Data Visualizations

## Top 10 Products by Sales

A bar chart displaying the ten products with the highest total sales.

The data is grouped by product:

```sql
SELECT product, SUM(sales)
FROM sales_data
WHERE dataset_id = %s
GROUP BY product
ORDER BY SUM(sales) DESC
LIMIT 10;
```

---

## Sales by Category

A pie chart showing the distribution of sales across categories.

Example categories could include:

```text
Technology
Furniture
Office Supplies
```

The dashboard dynamically retrieves categories from the selected dataset.

---

# 🏆 Top Products

The dashboard displays the five highest-selling products.

Example:

| Rank | Product | Total Sales |
|---:|---|---:|
| 1 | Product A | ₹61,599 |
| 2 | Product B | ₹27,453 |
| 3 | Product C | ₹22,638 |
| 4 | Product D | ₹21,870 |
| 5 | Product E | ₹19,823 |

The values are calculated dynamically from the selected dataset.

---

# 📁 Dataset History

The application provides a dedicated dataset history page.

Users can see:

- Dataset ID
- File name
- Total rows
- Total columns
- Upload time
- Uploading user

Users can also:

### Open Dataset

Selecting **Open** sets the selected `dataset_id` as the current dataset.

The dashboard then recalculates all KPIs and charts for that dataset.

### Delete Dataset

Deleting a dataset removes:

- Its records from `sales_data`
- Its metadata from `upload_history`
- Its corresponding CSV from AWS S3

---

# 🔄 Dataset Switching

Users can upload multiple datasets.

For example:

```text
Dataset 1
sales_dataset_a.csv

Dataset 2
sales_dataset_b.csv

Dataset 3
sales_dataset_c.csv
```

From the History page, selecting a dataset changes:

```python
session["current_dataset"]
```

The dashboard then uses that ID when querying `sales_data`.

This allows users to switch datasets without uploading the CSV again.

---

# 📂 Project Structure

```text
sales_dashboard/
│
├── app.py
├── auth.py
├── upload.py
├── config.py
├── tables.py
├── user.py
├── reset.py
├── dbreset.py
├── requirements.txt
├── .gitignore
│
├── static/
│   ├── style.css
│   └── script.js
│
└── templates/
    ├── dashboard.html
    ├── history.html
    ├── login.html
    └── register.html
```

---

# 📄 File Responsibilities

## `app.py`

Main Flask application.

Responsible for:

- Creating the Flask application
- Setting the Flask secret key
- Registering blueprints
- Starting the development server

---

## `auth.py`

Handles authentication and dashboard routes.

Includes:

- Home route
- Registration page
- User registration
- Login page
- Login validation
- Dashboard
- Dataset history
- Dataset switching
- Dataset deletion
- Logout

---

## `upload.py`

Handles CSV uploads.

Responsibilities include:

- Receiving CSV files
- Validating file type
- Reading CSV data
- Cleaning column names
- Removing duplicates
- Removing missing values
- Validating required columns
- Generating dataset IDs
- Uploading files to S3
- Inserting records into MySQL
- Saving upload history

---

## `config.py`

Contains application configuration for:

- MySQL/AWS RDS
- AWS S3
- Database connection
- S3 client

Sensitive credentials should not be committed to GitHub.

---

## `tables.py`

Creates the required database tables.

Run this file during initial database setup.

---

## `user.py`

Contains user-related database functionality used by the project.

---

## `dashboard.html`

Main analytics dashboard.

Contains:

- KPI cards
- Dataset information
- CSV upload form
- Product sales chart
- Category sales chart
- Top products table
- Navigation

---

## `history.html`

Displays previously uploaded datasets.

Provides:

- Dataset information
- Open dataset functionality
- Delete dataset functionality

---

## `script.js`

Contains client-side Chart.js functionality.

It receives data from Flask and creates:

- Product sales bar chart
- Category sales pie chart

---

## `style.css`

Contains the application's frontend styling and dashboard layout.

---

# 🛠️ Technology Stack

| Technology | Usage |
|---|---|
| Python | Backend programming |
| Flask | Web framework |
| Pandas | Data processing |
| MySQL | Relational database |
| AWS RDS | Cloud database |
| AWS S3 | Cloud file storage |
| Boto3 | AWS SDK for Python |
| HTML5 | Page structure |
| CSS3 | Styling |
| JavaScript | Client-side functionality |
| Chart.js | Data visualization |

---

# 💻 Requirements

Before running the project, make sure you have:

- Python 3.x
- pip
- MySQL/AWS RDS
- AWS account
- AWS S3 bucket
- Internet connection

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/sales-dashboard.git
```

Navigate into the project:

```bash
cd sales-dashboard
```

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
```

Activate:

```bash
venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv venv
```

Activate:

```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

---

# ☁️ AWS Setup

The application uses two AWS services.

## Amazon S3

Create an S3 bucket for uploaded CSV files.

Example:

```text
sales-dashboard-data
```

The application stores uploaded files inside:

```text
uploads/
```

---

## Amazon RDS

Create an RDS MySQL database.

You will need:

```text
RDS Endpoint
Database Username
Database Password
Database Name
Database Port
```

Default MySQL port:

```text
3306
```

Make sure the RDS security group allows connections from your development environment.

---

# 🔐 Configuration

The application requires database and AWS configuration.

Use environment variables for sensitive information.

Example:

```env
DB_HOST=your-rds-endpoint
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_NAME=sales_dashboard
DB_PORT=3306

S3_BUCKET=your-s3-bucket
AWS_REGION=your-aws-region
```

### Important

Never commit real credentials to GitHub.

Do not upload:

```text
.env
```

or any file containing:

```text
AWS Access Key
AWS Secret Key
Database Password
RDS Credentials
Production Secret Key
```

---

# 🗄️ Initialize the Database

After configuring your database, run:

```bash
python tables.py
```

You should see:

```text
All tables created successfully!
```

---

# ▶️ Run the Application

Start the Flask application:

```bash
python app.py
```

The application will normally be available at:

```text
http://127.0.0.1:5000
```

Open the address in your browser.

---

# 📄 CSV Dataset Format

The uploaded CSV should contain these required columns:

```text
order_id
order_date
product
category
quantity
sales
profit
```

Example:

```csv
order_id,order_date,product,category,quantity,sales,profit
ORD001,2026-01-05,Laptop,Electronics,2,1500,300
ORD002,2026-01-06,Office Chair,Furniture,1,450,90
ORD003,2026-01-07,Keyboard,Accessories,3,180,45
ORD004,2026-01-08,Monitor,Electronics,2,700,140
ORD005,2026-01-09,Desk,Furniture,1,850,170
```

The application also supports:

```text
product_name
```

and converts it internally to:

```text
product
```

---

# 🧹 Data Cleaning

Before storing the dataset, the application performs basic preprocessing.

### Column Name Cleaning

For example:

```text
Order ID
```

becomes:

```text
order_id
```

Special characters are removed and column names are normalized.

### Duplicate Removal

Duplicate rows are removed using Pandas:

```python
df.drop_duplicates()
```

### Missing Data

Rows containing missing values are removed:

```python
df.dropna()
```

---

# 📊 Example Dashboard Workflow

### Step 1 — Register

Create an account.

### Step 2 — Login

Log into the application.

### Step 3 — Upload CSV

Select a sales CSV file.

### Step 4 — Processing

The application:

```text
Validate
   ↓
Clean
   ↓
Generate Dataset ID
   ↓
Upload to S3
   ↓
Insert into MySQL
   ↓
Save History
```

### Step 5 — Dashboard

The dashboard displays:

- Total Orders
- Total Sales
- Total Profit
- Total Quantity
- Average Sales
- Top Products
- Sales Charts

### Step 6 — Dataset History

Open the History page to see all uploaded datasets.

### Step 7 — Switch Dataset

Click **Open** on another dataset.

The dashboard updates to display that dataset.

---

# 🔒 GitHub Security

The following files and folders should not be committed:

```text
venv/
__pycache__/
.env
uploads/
processed/
reports/
```

Recommended `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]

# Virtual Environment
venv/
.venv/
env/

# Environment Variables
.env
.env.*

# Uploaded / Generated Files
uploads/
processed/
reports/

# Local CSV files
*.csv

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

---

# ⚠️ Credential Safety

Never put credentials directly into publicly accessible source code.

Avoid:

```python
DB_PASSWORD = "actual-password"
```

or:

```python
AWS_SECRET_KEY = "actual-secret"
```

Use environment variables instead.

If credentials have accidentally been committed to a public repository, they should be rotated immediately.

---

# 🧪 Testing

The application can be tested using multiple CSV datasets.

For example:

```text
Dataset 1
tech_retail_sales.csv

Dataset 2
lifestyle_retail_sales.csv
```

After uploading both datasets, verify:

### Dataset 1

- KPIs are calculated
- Charts display correctly
- Top products are displayed

### Dataset 2

- KPIs change
- Products change
- Categories change
- Charts update

### Dataset Switching

Open Dataset 1:

```text
Dashboard → Dataset 1
```

Open Dataset 2:

```text
Dashboard → Dataset 2
```

The dashboard should update accordingly.

---

# 🧪 Database Testing

After uploading two datasets, the database should contain multiple dataset IDs.

Example:

```text
upload_history

id    dataset_id    file_name
1     1             tech_retail_sales.csv
2     2             lifestyle_retail_sales.csv
```

The shared `sales_data` table will contain records for both:

```text
dataset_id = 1
dataset_id = 2
```

The dashboard retrieves only the selected dataset.

---

# 📌 Current Limitations

The current version focuses on the core upload and analytics functionality.

Current limitations include:

- Basic authentication
- No advanced role management
- Basic CSV validation
- No advanced dashboard filtering
- No forecasting
- No report export functionality
- No pagination for large dataset previews

These are planned for future versions.

---

# 🔮 Future Enhancements

The project can be extended with the following features.

## Dashboard Filters

Add:

- Category filter
- Product filter
- Date range
- Dataset filter
- Year
- Month
- Quarter

---

## Dataset Preview

Add a preview section displaying the uploaded records.

Example:

```text
Order ID | Date | Product | Category | Sales | Profit
```

Support pagination and configurable row counts.

---

## Monthly Sales Trend

Add a line chart showing sales performance over time.

Example analysis:

```text
January → Sales
February → Sales
March → Sales
April → Sales
```

---

## Advanced KPIs

Potential additional metrics:

- Highest Sale
- Highest Profit
- Best Product
- Best Category
- Lowest Performing Product
- Lowest Performing Category
- Average Profit Margin
- Monthly Growth

---

## Interactive Charts

Enable chart-based filtering.

For example:

```text
Click Category
       ↓
Dashboard filters to that category
```

or:

```text
Click Product
       ↓
Dashboard filters to that product
```

---

## Reporting

Future versions can support:

- PDF reports
- Excel exports
- CSV exports
- Automated analytics reports

---

## Sales Forecasting

Future versions can use historical sales data to estimate future sales trends.

---

# 🎯 Project Objectives

The main objectives of this project are:

1. Build a cloud-based sales analytics platform.
2. Integrate AWS S3 for cloud file storage.
3. Integrate AWS RDS MySQL for cloud database storage.
4. Process CSV datasets using Pandas.
5. Create an interactive Flask dashboard.
6. Visualize sales data using Chart.js.
7. Implement dataset management and switching.
8. Use a scalable shared-table database architecture.
9. Convert raw sales data into useful business insights.

---

# 📚 Learning Outcomes

This project provides practical experience with:

- Python
- Flask
- Pandas
- MySQL
- SQL
- AWS S3
- AWS RDS
- Boto3
- HTML
- CSS
- JavaScript
- Chart.js
- Cloud application architecture
- Database design
- CSV data processing
- Data visualization
- Session management
- CRUD operations

---

# 🏆 Why This Project Matters

The project demonstrates how multiple technologies can be combined to build a complete data-driven cloud application.

Instead of simply displaying a static dataset, the application provides a complete workflow:

```text
Raw Data
   ↓
Upload
   ↓
Cloud Storage
   ↓
Data Processing
   ↓
Database Storage
   ↓
Analytics
   ↓
Visualization
   ↓
Business Insights
```

This makes the project useful as a practical demonstration of **full-stack development, cloud computing, database management, and data analytics**.

---

# 👨‍💻 Author

## Yugansh Sapra

Computer Science Student

GitHub:

https://github.com/YOUR_USERNAME

---

# 📜 License

This project is created for **educational, learning, and portfolio purposes**.

You are free to modify and improve the project for your own learning and development.

---

# ⭐ Acknowledgements

This project uses the following open-source technologies:

- Flask
- Pandas
- MySQL
- Boto3
- Chart.js
- Amazon Web Services

---

## ⭐ If You Like This Project

If you find this project useful or interesting, consider giving the repository a ⭐ on GitHub.
