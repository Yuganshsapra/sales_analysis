📊 Sales Analytics Dashboard

A cloud-based Sales Analytics Dashboard built with Flask, MySQL, AWS S3, AWS RDS, Pandas, HTML, CSS, JavaScript, and Chart.js.

The application allows users to upload sales datasets, store them securely in the cloud, view analytics through an interactive dashboard, and access previously uploaded datasets without uploading the CSV again.

🚀 Features
🔐 User Authentication
User registration
User login
Session-based authentication
Logout functionality
📂 Dataset Management
Upload CSV sales datasets
Automatic dataset ID generation
CSV validation and cleaning
Dataset upload history
Open previously uploaded datasets
Delete datasets
Switch between datasets without re-uploading
☁️ Cloud Integration
AWS S3 for CSV file storage
AWS RDS MySQL for database storage
Boto3 for AWS integration
📈 Dashboard Analytics

The dashboard provides:

Total Orders
Total Sales
Total Profit
Total Quantity
Average Sales
Top 5 Products
📊 Data Visualization
Top 10 Products by Sales — Bar Chart
Sales by Category — Pie Chart
Dynamic charts based on the selected dataset
🏗️ System Architecture
                    ┌───────────────┐
                    │     User      │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Flask Web App │
                    └───────┬───────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
        ┌──────────────┐        ┌──────────────┐
        │   AWS S3     │        │   AWS RDS    │
        │              │        │    MySQL     │
        │ CSV Storage  │        │              │
        └──────────────┘        └──────┬───────┘
                                       │
                                       ▼
                               ┌─────────────────┐
                               │   sales_data    │
                               │                 │
                               │ dataset_id      │
                               │ order_id        │
                               │ order_date      │
                               │ product         │
                               │ category        │
                               │ quantity        │
                               │ sales           │
                               │ profit          │
                               └─────────────────┘
🗄️ Database Design

The application uses three main tables.

users

Stores registered user information.

id
name
email
password
created_at
upload_history

Stores metadata for uploaded datasets.

id
file_name
dataset_id
s3_key
total_rows
total_columns
uploaded_by
upload_time
sales_data

Stores the actual sales records.

id
dataset_id
uploaded_by
order_id
order_date
product
category
quantity
sales
profit
Why dataset_id?

Instead of creating a new MySQL table for every uploaded CSV, the application uses one shared table.

CSV 1 ─┐
CSV 2 ─┼──► sales_data
CSV 3 ─┘

Each dataset is separated using dataset_id.

For example:

dataset_id = 1 → Dataset A
dataset_id = 2 → Dataset B
dataset_id = 3 → Dataset C

This makes the database easier to manage and scale.

🛠️ Tech Stack
Technology	Purpose
Python	Backend development
Flask	Web framework
Pandas	CSV processing
MySQL	Database
AWS RDS	Cloud database
AWS S3	Cloud file storage
Boto3	AWS SDK
HTML	Frontend
CSS	Styling
JavaScript	Client-side functionality
Chart.js	Data visualization
📁 Project Structure
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
Main Files

app.py

Initializes the Flask application
Registers application blueprints

auth.py

Registration and login
Dashboard
Dataset history
Dataset switching
Dataset deletion
Logout

upload.py

CSV upload
CSV validation
Data cleaning
AWS S3 upload
MySQL data insertion

config.py

Database configuration
AWS S3 configuration

tables.py

Creates the required MySQL tables

dashboard.html

Dashboard interface
KPI cards
Charts
Dataset information
Upload interface

history.html

Displays uploaded datasets
Open and delete functionality

script.js

Chart.js configuration
Dashboard visualizations
⚙️ Installation
1. Clone the repository
git clone https://github.com/YOUR_USERNAME/sales-dashboard.git
cd sales-dashboard
2. Create a virtual environment
Windows
python -m venv venv

Activate it:

venv\Scripts\activate
macOS/Linux
python3 -m venv venv
source venv/bin/activate
3. Install dependencies
pip install -r requirements.txt
🔐 Configuration

The project requires:

AWS S3 bucket
AWS credentials
AWS RDS MySQL database

Do not upload real credentials to GitHub.

Configure your local environment with:

DB_HOST=your-rds-endpoint
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_NAME=sales_dashboard
DB_PORT=3306

S3_BUCKET=your-s3-bucket
AWS_REGION=your-aws-region

Keep .env out of version control.

🗄️ Database Setup

After configuring your database, run:

python tables.py

This creates the required database tables.

▶️ Running the Application

Start the Flask application:

python app.py

Then open:

http://127.0.0.1:5000
📄 CSV Format

The application expects sales data containing:

order_id
order_date
product
category
quantity
sales
profit

Example:

order_id,order_date,product,category,quantity,sales,profit
ORD001,2026-01-05,Laptop,Electronics,2,1500,300
ORD002,2026-01-06,Office Chair,Furniture,1,450,90
ORD003,2026-01-07,Keyboard,Accessories,3,180,45

The application also supports product_name and normalizes it to product.

📊 Dashboard

After uploading a dataset, the application calculates the following KPIs:

┌───────────────┬───────────────┬───────────────┐
│ Total Orders  │ Total Sales   │ Total Profit  │
├───────────────┼───────────────┼───────────────┤
│ Total Quantity│ Average Sales │               │
└───────────────┴───────────────┴───────────────┘

It also displays:

Top 5 products
Top 10 products by sales
Sales distribution by category
🔄 Dataset History

Uploaded datasets are stored in the history section.

Users can:

Upload Dataset
       ↓
Generate Dataset ID
       ↓
Store CSV → AWS S3
       ↓
Store Records → MySQL
       ↓
Save Metadata → upload_history

Previously uploaded datasets can then be opened directly from the history page without uploading the CSV again.

🔒 Security

The following files and folders should not be committed:

venv/
__pycache__/
uploads/
processed/
reports/
.env

Do not expose:

AWS access keys
AWS secret keys
RDS passwords
Database credentials
Production Flask secret keys

Use environment variables for sensitive information.

🔮 Future Enhancements

Planned improvements include:

 Category, product, and date filters
 Dataset preview
 Monthly sales trend
 Advanced KPIs
 Year/month/quarter filtering
 Interactive chart drill-down
 Dashboard search
 PDF/Excel report generation
 Sales forecasting
🎯 Project Objective

The objective of this project is to build a practical cloud-based sales analytics platform that combines web development, data processing, database management, cloud storage, and data visualization.

The project demonstrates how raw sales data can be transformed into meaningful business insights through a centralized and scalable analytics application.

👨‍💻 Author

Yugansh Sapra

