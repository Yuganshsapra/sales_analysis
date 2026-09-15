# Sales Analytics Dashboard

A cloud-based sales analytics web application built with Flask, MySQL, AWS S3, AWS RDS, Pandas, JavaScript, and Chart.js.

The application allows users to upload sales datasets, store CSV files in AWS S3, store processed records in a shared MySQL database, and analyze the data through an interactive dashboard.

---

## Features

### User Authentication
- User registration
- User login
- Session-based authentication
- Logout functionality

### Dataset Management
- Upload CSV sales datasets
- CSV validation and cleaning
- Automatic dataset ID generation
- Store uploaded CSV files in AWS S3
- Store dataset records in MySQL
- View upload history
- Open previously uploaded datasets
- Switch between datasets without uploading the CSV again
- Delete datasets

### Dashboard Analytics
- Total Orders
- Total Sales
- Total Profit
- Total Quantity
- Average Sales
- Top 5 Products

### Data Visualization
- Top 10 Products by Sales
- Sales by Category
- Interactive Bar Chart
- Interactive Pie Chart
- Dynamic visualization based on the selected dataset

---

## Technology Stack

| Technology | Purpose |
|------------|---------|
| Python | Backend programming |
| Flask | Web application framework |
| Pandas | CSV processing and data cleaning |
| MySQL | Database |
| AWS RDS | Cloud-hosted MySQL database |
| AWS S3 | Cloud CSV storage |
| Boto3 | AWS integration |
| HTML | Frontend structure |
| CSS | Frontend styling |
| JavaScript | Client-side functionality |
| Chart.js | Data visualization |

---

## System Architecture

The application follows a cloud-based architecture:

```text
User
  |
  v
Flask Web Application
  |
  +--------------------+
  |                    |
  v                    v
AWS S3              AWS RDS MySQL
  |                    |
  |                    +----------------+
  |                                     |
  v                                     v
CSV Files                         sales_data
                                  upload_history
                                  users
