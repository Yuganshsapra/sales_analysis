from flask import Blueprint, render_template, request, redirect, session, jsonify, send_file, flash
from config import get_connection, s3, S3_BUCKET
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib
matplotlib.use("Agg")  # non-interactive backend so this works on a headless server
import matplotlib.pyplot as plt
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Table,
    TableStyle,
    Spacer,
    Image
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch

import os
from datetime import datetime

# =====================================================
# Blueprint
# =====================================================
auth = Blueprint("auth", __name__)

REPORTS_DIR = "reports"

# =====================================================
# HOME
# =====================================================
@auth.route("/")
def home():
    return redirect("/login")

# =====================================================
# REGISTER PAGE
# =====================================================
@auth.route("/register")
def register():
    return render_template("register.html")

# =====================================================
# REGISTER USER
# =====================================================
@auth.route("/register", methods=["POST"])
def save_user():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # ------------------------------------------
        # Check Existing User
        # ------------------------------------------
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already registered!", "danger")
            return redirect("/register")

        # ------------------------------------------
        # Insert New User (password hashed, not stored in plain text)
        # ------------------------------------------
        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()

    return redirect("/login")

# =====================================================
# LOGIN PAGE
# =====================================================
@auth.route("/login")
def login():
    return render_template("login.html")

# =====================================================
# LOGIN USER
# =====================================================
@auth.route("/login", methods=["POST"])
def check_login():
    email = request.form["email"]
    password = request.form["password"]

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Select the password column explicitly by name -- SELECT * relies on
        # column order matching (id, name, email, password), which is fragile
        # and was the cause of logins always failing.
        cursor.execute("SELECT password FROM users WHERE email=%s", (email,))
        row = cursor.fetchone()

        if not row:
            flash("Invalid Email or Password!", "danger")
            return redirect("/login")

        stored_password = row[0]

        try:
            password_ok = check_password_hash(stored_password, password)
        except ValueError:
            # stored_password isn't a valid werkzeug hash -- almost certainly
            # a legacy plaintext password saved before hashing was added.
            password_ok = (stored_password == password)
            if password_ok:
                # Migrate this account to a proper hash now that we've
                # verified the plaintext password matches.
                new_hash = generate_password_hash(password)
                cursor.execute(
                    "UPDATE users SET password=%s WHERE email=%s",
                    (new_hash, email)
                )
                connection.commit()

        if not password_ok:
            flash("Invalid Email or Password!", "danger")
            return redirect("/login")
    finally:
        cursor.close()
        connection.close()

    session["user"] = email
    session.pop("current_dataset", None)
    return redirect("/dashboard")

# =====================================================
# DASHBOARD
# =====================================================
@auth.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    connection = get_connection()
    cursor = connection.cursor()

    # =====================================================
    # Dashboard Variables
    # =====================================================
    latest_upload = None
    upload_status = session.pop("upload_status", None)

    # =====================================================
    # Dashboard Filters
    # =====================================================
    selected_category = request.args.get("category", "").strip()
    selected_product = request.args.get("product", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    categories = []
    products = []

    # =====================================================
    # KPI Dictionary
    # =====================================================
    kpis = {
        "total_orders": 0,
        "total_sales": 0,
        "highest_sale": 0,
        "lowest_sale": 0,
        "total_profit": 0,
        "highest_profit": 0,
        "lowest_profit": 0,
        "average_profit": 0,
        "total_quantity": 0,
        "average_sales": 0,
        "best_product": "-",
        "worst_product": "-",
        "best_category": "-",
        "worst_category": "-"
    }

    # =====================================================
    # Dashboard Data
    # =====================================================
    top_products = []
    sales_labels = []
    sales_values = []
    category_labels = []
    category_values = []
    monthly_labels = []
    monthly_values = []

    # =====================================================
    # Performance Summary
    # =====================================================
    performance = {
        "sales_status": "No Data",
        "profit_status": "No Data",
        "best_product": "-",
        "best_category": "-",
        "average_order_value": 0,
        "total_orders": 0,
        "total_categories": 0,
        "dataset_name": "-"
    }

    try:
        # ==========================================
        # Load Current Dataset
        # ==========================================
        if "current_dataset" in session:
            dataset_id = session["current_dataset"]
            cursor.execute(
                "SELECT id, file_name, dataset_id, total_rows, total_columns, upload_time "
                "FROM upload_history WHERE dataset_id=%s LIMIT 1",
                (dataset_id,)
            )
            latest_upload = cursor.fetchone()
        else:
            cursor.execute(
                """
                SELECT id, file_name, dataset_id, total_rows, total_columns, upload_time
                FROM upload_history
                WHERE uploaded_by=%s
                ORDER BY upload_time DESC
                LIMIT 1
                """,
                (session["user"],)
            )
            latest_upload = cursor.fetchone()

            if latest_upload:
                dataset_id = latest_upload[2]
                session["current_dataset"] = dataset_id
                performance["dataset_name"] = latest_upload[1]
            else:
                session.pop("current_dataset", None)

        if latest_upload:
            dataset_id = latest_upload[2]
            performance["dataset_name"] = latest_upload[1]

            # ==========================================
            # Build Common WHERE Clause
            # ==========================================
            conditions = ["dataset_id=%s"]
            params = [dataset_id]

            if selected_category:
                conditions.append("category=%s")
                params.append(selected_category)
            if selected_product:
                conditions.append("product=%s")
                params.append(selected_product)
            if start_date:
                conditions.append("order_date >= %s")
                params.append(start_date)
            if end_date:
                conditions.append("order_date <= %s")
                params.append(end_date)

            where_clause = "WHERE " + " AND ".join(conditions)

            # ==========================================
            # Load Categories
            # ==========================================
            cursor.execute(
                "SELECT DISTINCT category FROM sales_data WHERE dataset_id=%s ORDER BY category",
                (dataset_id,)
            )
            categories = [row[0] for row in cursor.fetchall()]

            # ==========================================
            # Load Products
            # ==========================================
            cursor.execute(
                "SELECT DISTINCT product FROM sales_data WHERE dataset_id=%s ORDER BY product",
                (dataset_id,)
            )
            products = [row[0] for row in cursor.fetchall()]

            # ==========================================
            # KPIs
            # ==========================================
            cursor.execute(f"SELECT COUNT(*) FROM sales_data {where_clause}", tuple(params))
            kpis["total_orders"] = cursor.fetchone()[0]

            cursor.execute(f"SELECT IFNULL(SUM(sales),0) FROM sales_data {where_clause}", tuple(params))
            kpis["total_sales"] = round(float(cursor.fetchone()[0]), 2)

            cursor.execute(f"SELECT IFNULL(MAX(sales),0) FROM sales_data {where_clause}", tuple(params))
            kpis["highest_sale"] = round(float(cursor.fetchone()[0]), 2)

            cursor.execute(f"SELECT IFNULL(MIN(sales),0) FROM sales_data {where_clause}", tuple(params))
            kpis["lowest_sale"] = round(float(cursor.fetchone()[0]), 2)

            cursor.execute(f"SELECT IFNULL(SUM(profit),0) FROM sales_data {where_clause}", tuple(params))
            kpis["total_profit"] = round(float(cursor.fetchone()[0]), 2)

            cursor.execute(f"SELECT IFNULL(MAX(profit),0) FROM sales_data {where_clause}", tuple(params))
            kpis["highest_profit"] = round(float(cursor.fetchone()[0]), 2)

            cursor.execute(f"SELECT IFNULL(MIN(profit),0) FROM sales_data {where_clause}", tuple(params))
            kpis["lowest_profit"] = round(float(cursor.fetchone()[0]), 2)

            cursor.execute(f"SELECT IFNULL(AVG(profit),0) FROM sales_data {where_clause}", tuple(params))
            kpis["average_profit"] = round(float(cursor.fetchone()[0]), 2)

            cursor.execute(f"SELECT IFNULL(SUM(quantity),0) FROM sales_data {where_clause}", tuple(params))
            quantity = cursor.fetchone()[0]
            kpis["total_quantity"] = quantity if quantity else 0

            cursor.execute(f"SELECT IFNULL(AVG(sales),0) FROM sales_data {where_clause}", tuple(params))
            kpis["average_sales"] = round(float(cursor.fetchone()[0]), 2)

            # Best/Worst Product
            cursor.execute(
                f"SELECT product, SUM(sales) AS total_sales FROM sales_data {where_clause} "
                f"GROUP BY product ORDER BY total_sales DESC LIMIT 1",
                tuple(params)
            )
            result = cursor.fetchone()
            if result:
                kpis["best_product"] = result[0]

            cursor.execute(
                f"SELECT product, SUM(sales) AS total_sales FROM sales_data {where_clause} "
                f"GROUP BY product ORDER BY total_sales ASC LIMIT 1",
                tuple(params)
            )
            result = cursor.fetchone()
            if result:
                kpis["worst_product"] = result[0]

            # Best/Worst Category
            cursor.execute(
                f"SELECT category, SUM(sales) AS total_sales FROM sales_data {where_clause} "
                f"GROUP BY category ORDER BY total_sales DESC LIMIT 1",
                tuple(params)
            )
            result = cursor.fetchone()
            if result:
                kpis["best_category"] = result[0]

            cursor.execute(
                f"SELECT category, SUM(sales) AS total_sales FROM sales_data {where_clause} "
                f"GROUP BY category ORDER BY total_sales ASC LIMIT 1",
                tuple(params)
            )
            result = cursor.fetchone()
            if result:
                kpis["worst_category"] = result[0]

            # Top 5 Products
            cursor.execute(
                f"SELECT product, SUM(sales) AS total_sales FROM sales_data {where_clause} "
                f"GROUP BY product ORDER BY total_sales DESC LIMIT 5",
                tuple(params)
            )
            top_products = cursor.fetchall()

            # Charts
            cursor.execute(
                f"SELECT product, SUM(sales) AS total_sales FROM sales_data {where_clause} "
                f"GROUP BY product ORDER BY total_sales DESC LIMIT 10",
                tuple(params)
            )
            sales_chart = cursor.fetchall()
            sales_labels = [row[0] for row in sales_chart]
            sales_values = [float(row[1]) for row in sales_chart]

            cursor.execute(
                f"SELECT category, SUM(sales) AS total_sales FROM sales_data {where_clause} "
                f"GROUP BY category ORDER BY total_sales DESC",
                tuple(params)
            )
            category_chart = cursor.fetchall()
            category_labels = [row[0] for row in category_chart]
            category_values = [float(row[1]) for row in category_chart]

            cursor.execute(
                f"SELECT DATE_FORMAT(order_date,'%%b %%Y') AS month, SUM(sales) AS total_sales "
                f"FROM sales_data {where_clause} "
                f"GROUP BY YEAR(order_date), MONTH(order_date) "
                f"ORDER BY YEAR(order_date), MONTH(order_date)",
                tuple(params)
            )
            monthly_chart = cursor.fetchall()
            monthly_labels = [row[0] for row in monthly_chart]
            monthly_values = [float(row[1]) for row in monthly_chart]

            # ==========================================
            # PERFORMANCE SUMMARY
            # ==========================================
            if kpis["total_orders"] > 0:
                performance["average_order_value"] = round(kpis["total_sales"] / kpis["total_orders"], 2)

            cursor.execute(f"SELECT COUNT(DISTINCT category) FROM sales_data {where_clause}", tuple(params))
            performance["total_categories"] = cursor.fetchone()[0]

            performance["best_product"] = kpis["best_product"]
            performance["best_category"] = kpis["best_category"]
            performance["total_orders"] = kpis["total_orders"]

            sales = kpis["total_sales"]
            if sales >= 1000000:
                performance["sales_status"] = "🟢 Excellent"
            elif sales >= 500000:
                performance["sales_status"] = "🟡 Good"
            elif sales >= 100000:
                performance["sales_status"] = "🟠 Average"
            else:
                performance["sales_status"] = "🔴 Needs Improvement"

            margin = (kpis["total_profit"] / kpis["total_sales"] * 100) if kpis["total_sales"] > 0 else 0
            if margin >= 20:
                performance["profit_status"] = "🟢 Excellent"
            elif margin >= 10:
                performance["profit_status"] = "🟡 Healthy"
            elif margin >= 5:
                performance["profit_status"] = "🟠 Average"
            else:
                performance["profit_status"] = "🔴 Low"

    except Exception as e:
        print("Dashboard Error:", e)

    finally:
        cursor.close()
        connection.close()

    return render_template(
        "dashboard.html",
        user=session["user"],
        latest_upload=latest_upload,
        upload_status=upload_status,
        kpis=kpis,
        performance=performance,
        top_products=top_products,
        sales_labels=sales_labels,
        sales_values=sales_values,
        category_labels=category_labels,
        category_values=category_values,
        monthly_labels=monthly_labels,
        monthly_values=monthly_values,
        categories=categories,
        products=products,
        selected_category=selected_category,
        selected_product=selected_product,
        start_date=start_date,
        end_date=end_date
    )

# =====================================================
# GET PRODUCTS (AJAX)
# =====================================================
@auth.route("/get_products")
def get_products():
    if "user" not in session:
        return jsonify([])

    dataset_id = session.get("current_dataset")
    if not dataset_id:
        return jsonify([])

    category = request.args.get("category", "").strip()
    connection = get_connection()
    cursor = connection.cursor()

    try:
        if category:
            cursor.execute(
                "SELECT DISTINCT product FROM sales_data WHERE dataset_id=%s AND category=%s ORDER BY product",
                (dataset_id, category)
            )
        else:
            cursor.execute(
                "SELECT DISTINCT product FROM sales_data WHERE dataset_id=%s ORDER BY product",
                (dataset_id,)
            )
        products = [row[0] for row in cursor.fetchall()]
        return jsonify(products)
    finally:
        cursor.close()
        connection.close()

# =====================================================
# OPEN DATASET PREVIEW
# =====================================================
@auth.route("/preview/<int:id>")
def preview_dataset(id):
    if "user" not in session:
        return redirect("/login")

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT dataset_id FROM upload_history WHERE id=%s AND uploaded_by=%s",
        (id, session["user"])
    )
    dataset = cursor.fetchone()
    cursor.close()
    connection.close()

    if dataset:
        session["current_dataset"] = dataset[0]
    return redirect("/preview")

# =====================================================
# DATASET PREVIEW
# =====================================================
@auth.route("/preview")
def preview():
    if "user" not in session:
        return redirect("/login")

    dataset_id = session.get("current_dataset")
    if not dataset_id:
        return redirect("/dashboard")

    page = request.args.get("page", 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM sales_data WHERE dataset_id=%s", (dataset_id,))
        total_rows = cursor.fetchone()[0]
        total_pages = max(1, (total_rows + per_page - 1) // per_page)

        cursor.execute(
            "SELECT file_name, dataset_id, upload_time FROM upload_history WHERE dataset_id=%s LIMIT 1",
            (dataset_id,)
        )
        dataset = cursor.fetchone()

        cursor.execute(
            "SELECT order_id, order_date, product, category, quantity, sales, profit "
            "FROM sales_data WHERE dataset_id=%s ORDER BY id LIMIT %s OFFSET %s",
            (dataset_id, per_page, offset)
        )
        preview_data = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    return render_template(
        "preview.html",
        dataset=dataset,
        preview_data=preview_data,
        page=page,
        total_pages=total_pages,
        total_rows=total_rows
    )

# =====================================================
# MONTHLY SALES DATA
# =====================================================
def get_monthly_sales(cursor, dataset_id):
    cursor.execute(
        """
        SELECT MONTH(order_date), MONTHNAME(order_date), SUM(sales)
        FROM sales_data
        WHERE dataset_id=%s
        GROUP BY MONTH(order_date), MONTHNAME(order_date)
        ORDER BY MONTH(order_date)
        """,
        (dataset_id,)
    )
    rows = cursor.fetchall()
    labels = []
    values = []
    for row in rows:
        labels.append(row[1][:3])
        values.append(float(row[2]))
    return labels, values

# =====================================================
# MONTHLY PROFIT DATA
# =====================================================
def get_monthly_profit(cursor, dataset_id):
    cursor.execute(
        """
        SELECT MONTH(order_date), MONTHNAME(order_date), SUM(profit)
        FROM sales_data
        WHERE dataset_id=%s
        GROUP BY MONTH(order_date), MONTHNAME(order_date)
        ORDER BY MONTH(order_date)
        """,
        (dataset_id,)
    )
    rows = cursor.fetchall()
    labels = []
    values = []
    for row in rows:
        labels.append(row[1][:3])
        values.append(float(row[2]))
    return labels, values

# =====================================================
# COMPARE DATASETS
# =====================================================
@auth.route("/compare", methods=["GET", "POST"])
def compare():
    if "user" not in session:
        return redirect("/login")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT dataset_id, file_name FROM upload_history WHERE uploaded_by=%s ORDER BY upload_time DESC",
        (session["user"],)
    )
    datasets = cursor.fetchall()
    comparison = None

    sales_labels = []
    sales_a = []
    sales_b = []
    profit_labels = []
    profit_a = []
    profit_b = []

    def get_summary(dataset_id):
        summary = {}
        cursor.execute(
            "SELECT COUNT(*), IFNULL(SUM(sales),0), IFNULL(SUM(profit),0), IFNULL(SUM(quantity),0), "
            "IFNULL(MAX(sales),0), IFNULL(AVG(sales),0), IFNULL(AVG(profit),0) "
            "FROM sales_data WHERE dataset_id=%s",
            (dataset_id,)
        )
        row = cursor.fetchone()
        summary["orders"] = row[0]
        summary["sales"] = float(row[1])
        summary["profit"] = float(row[2])
        summary["quantity"] = row[3]
        summary["highest_sale"] = float(row[4])
        summary["average_sale"] = round(float(row[5]), 2)
        summary["average_profit"] = round(float(row[6]), 2)
        summary["average_order"] = round(summary["sales"] / summary["orders"], 2) if summary["orders"] > 0 else 0
        summary["profit_margin"] = round((summary["profit"] / summary["sales"] * 100), 2) if summary["sales"] > 0 else 0

        cursor.execute(
            "SELECT product, SUM(sales) AS total_sales FROM sales_data WHERE dataset_id=%s "
            "GROUP BY product ORDER BY total_sales DESC LIMIT 1",
            (dataset_id,)
        )
        row = cursor.fetchone()
        summary["best_product"] = row[0] if row else "-"

        cursor.execute(
            "SELECT product, SUM(sales) AS total_sales FROM sales_data WHERE dataset_id=%s "
            "GROUP BY product ORDER BY total_sales ASC LIMIT 1",
            (dataset_id,)
        )
        row = cursor.fetchone()
        summary["worst_product"] = row[0] if row else "-"

        cursor.execute(
            "SELECT category, SUM(sales) AS total_sales FROM sales_data WHERE dataset_id=%s "
            "GROUP BY category ORDER BY total_sales DESC LIMIT 1",
            (dataset_id,)
        )
        row = cursor.fetchone()
        summary["best_category"] = row[0] if row else "-"

        cursor.execute(
            "SELECT category, SUM(sales) AS total_sales FROM sales_data WHERE dataset_id=%s "
            "GROUP BY category ORDER BY total_sales ASC LIMIT 1",
            (dataset_id,)
        )
        row = cursor.fetchone()
        summary["worst_category"] = row[0] if row else "-"
        return summary

    try:
        if request.method == "POST":
            dataset_a = request.form.get("dataset_a")
            dataset_b = request.form.get("dataset_b")

            if dataset_a and dataset_b:
                summary_a = get_summary(dataset_a)
                summary_b = get_summary(dataset_b)

                sales_labels_a, sales_a = get_monthly_sales(cursor, dataset_a)
                sales_labels_b, sales_b = get_monthly_sales(cursor, dataset_b)
                profit_labels_a, profit_a = get_monthly_profit(cursor, dataset_a)
                profit_labels_b, profit_b = get_monthly_profit(cursor, dataset_b)

                sales_labels = sales_labels_a
                profit_labels = profit_labels_a

                def calc_growth(a, b):
                    return round(((b - a) / a * 100), 2) if a > 0 else 0

                sales_growth = calc_growth(summary_a["sales"], summary_b["sales"])
                orders_growth = calc_growth(summary_a["orders"], summary_b["orders"])
                profit_growth = calc_growth(summary_a["profit"], summary_b["profit"])
                quantity_growth = calc_growth(summary_a["quantity"], summary_b["quantity"])

                sales_winner = "B" if summary_b["sales"] > summary_a["sales"] else "A"
                orders_winner = "B" if summary_b["orders"] > summary_a["orders"] else "A"
                profit_winner = "B" if summary_b["profit"] > summary_a["profit"] else "A"
                quantity_winner = "B" if summary_b["quantity"] > summary_a["quantity"] else "A"

                comparison = {
                    "dataset_a": summary_a,
                    "dataset_b": summary_b,
                    "growth": {
                        "sales": sales_growth,
                        "orders": orders_growth,
                        "profit": profit_growth,
                        "quantity": quantity_growth
                    },
                    "winner": {
                        "sales": sales_winner,
                        "orders": orders_winner,
                        "profit": profit_winner,
                        "quantity": quantity_winner
                    }
                }
    finally:
        cursor.close()
        connection.close()

    return render_template(
        "compare.html",
        datasets=datasets,
        comparison=comparison,
        sales_labels=sales_labels,
        sales_a=sales_a,
        sales_b=sales_b,
        profit_labels=profit_labels,
        profit_a=profit_a,
        profit_b=profit_b
    )

# =====================================================
# CHART GENERATION HELPER
# =====================================================
def create_sales_chart(labels, values, filename):
    plt.figure(figsize=(8, 4))
    plt.plot(labels, values, marker="o", linewidth=2)
    plt.title("Monthly Sales Trend")
    plt.xlabel("Month")
    plt.ylabel("Sales")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

# =====================================================
# Generate Dashboard Report
# =====================================================
def generate_dashboard_report(
    report_path,
    dataset_name,
    kpis,
    performance,
    top_products,
    verdicts,
    score,
    sales_chart_path=None
):
    doc = SimpleDocTemplate(report_path)

    styles = getSampleStyleSheet()

    title_style = styles["Heading1"]
    title_style.alignment = TA_CENTER

    heading_style = styles["Heading2"]
    normal = styles["BodyText"]

    elements = []

    # =====================================================
    # REPORT TITLE
    # =====================================================
    elements.append(Paragraph("Sales Dashboard Report", title_style))
    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Paragraph(f"<b>Generated On :</b> {datetime.now().strftime('%d %B %Y %I:%M %p')}", normal))
    elements.append(Paragraph(f"<b>Dataset :</b> {dataset_name}", normal))
    elements.append(Spacer(1, 0.30 * inch))

    # =====================================================
    # DASHBOARD KPIs
    # =====================================================
    elements.append(Paragraph("Dashboard KPIs", heading_style))
    elements.append(Spacer(1, 0.15 * inch))

    kpi_table = [["KPI", "Value"]]

    for key, value in kpis.items():
        if isinstance(value, (int, float)):
            if "sales" in key.lower() or "profit" in key.lower() or "average" in key.lower():
                value = f"INR {value:,.2f}"
            else:
                value = f"{value:,}"

        kpi_table.append([key.replace("_", " ").title(), value])

    table = Table(kpi_table, colWidths=[3.5 * inch, 2.3 * inch])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10)
        ])
    )
    elements.append(table)
    elements.append(Spacer(1, 0.30 * inch))

    # =====================================================
    # PERFORMANCE SUMMARY
    # =====================================================
    elements.append(Paragraph("Performance Summary", heading_style))
    elements.append(Spacer(1, 0.15 * inch))

    performance_table = [["Metric", "Value"]]

    for key, value in performance.items():
        if isinstance(value, (int, float)):
            if "margin" in key.lower():
                value = f"{value:.2f}%"
            elif "order" in key.lower():
                value = f"INR {value:,.2f}"
            else:
                value = f"{value:,.2f}"

        performance_table.append([key.replace("_", " ").title(), value])

    table = Table(performance_table, colWidths=[3.5 * inch, 2.3 * inch])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16A34A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10)
        ])
    )
    elements.append(table)
    elements.append(Spacer(1, 0.30 * inch))

    # =====================================================
    # MONTHLY SALES CHART (only if a chart image was actually generated)
    # =====================================================
    if sales_chart_path and os.path.exists(sales_chart_path):
        elements.append(Paragraph("Monthly Sales Trend", heading_style))
        elements.append(Spacer(1, 0.15 * inch))
        elements.append(Image(sales_chart_path, width=6 * inch, height=3 * inch))
        elements.append(Spacer(1, 0.30 * inch))

    # =====================================================
    # TOP 5 PRODUCTS
    # =====================================================
    elements.append(Paragraph("Top 5 Products", heading_style))
    elements.append(Spacer(1, 0.15 * inch))

    product_table = [["Product", "Sales"]]

    if top_products:
        for product in top_products:
            product_table.append([product[0], f"INR {float(product[1]):,.2f}"])
    else:
        product_table.append(["No Data", "-"])

    table = Table(product_table, colWidths=[4 * inch, 2 * inch])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F59E0B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10)
        ])
    )
    elements.append(table)
    elements.append(Spacer(1, 0.30 * inch))

    # =====================================================
    # BUSINESS SCORE
    # =====================================================
    elements.append(Paragraph("Business Score", heading_style))
    elements.append(Spacer(1, 0.15 * inch))
    elements.append(Paragraph(f"<b>Overall Score:</b> {score} / 100", normal))
    elements.append(Spacer(1, 0.30 * inch))

    # =====================================================
    # BUSINESS VERDICTS
    # =====================================================
    elements.append(Paragraph("Business Verdicts", heading_style))
    elements.append(Spacer(1, 0.15 * inch))

    if verdicts:
        for verdict in verdicts:
            elements.append(Paragraph(f"• {verdict}", normal))
    else:
        elements.append(Paragraph("No verdicts available.", normal))

    # =====================================================
    # BUILD PDF
    # =====================================================
    doc.build(elements)

# =====================================================
# DOWNLOAD DASHBOARD REPORT
# =====================================================
@auth.route("/download_report")
def download_report():
    if "user" not in session:
        return redirect("/login")

    dataset_id = session.get("current_dataset")
    if not dataset_id:
        return redirect("/dashboard")

    connection = get_connection()
    cursor = connection.cursor()

    try:
        os.makedirs(REPORTS_DIR, exist_ok=True)

        # ==========================================
        # Dataset Name
        # ==========================================
        cursor.execute(
            "SELECT file_name FROM upload_history WHERE dataset_id=%s LIMIT 1",
            (dataset_id,)
        )
        row = cursor.fetchone()
        dataset_name = row[0] if row else "Unknown Dataset"

        # ==========================================
        # KPIs
        # ==========================================
        kpis = {}

        cursor.execute("SELECT COUNT(*) FROM sales_data WHERE dataset_id=%s", (dataset_id,))
        kpis["Total Orders"] = cursor.fetchone()[0]

        cursor.execute("SELECT IFNULL(SUM(sales),0) FROM sales_data WHERE dataset_id=%s", (dataset_id,))
        total_sales = round(float(cursor.fetchone()[0]), 2)
        kpis["Total Sales"] = total_sales

        cursor.execute("SELECT IFNULL(SUM(profit),0) FROM sales_data WHERE dataset_id=%s", (dataset_id,))
        total_profit = round(float(cursor.fetchone()[0]), 2)
        kpis["Total Profit"] = total_profit

        cursor.execute("SELECT IFNULL(SUM(quantity),0) FROM sales_data WHERE dataset_id=%s", (dataset_id,))
        total_quantity = cursor.fetchone()[0]
        kpis["Total Quantity"] = total_quantity

        cursor.execute("SELECT IFNULL(MAX(sales),0) FROM sales_data WHERE dataset_id=%s", (dataset_id,))
        kpis["Highest Sale"] = round(float(cursor.fetchone()[0]), 2)

        cursor.execute("SELECT IFNULL(AVG(sales),0) FROM sales_data WHERE dataset_id=%s", (dataset_id,))
        kpis["Average Sale"] = round(float(cursor.fetchone()[0]), 2)

        # ==========================================
        # Performance Summary
        # ==========================================
        performance = {}

        performance["Average Order Value"] = round(
            total_sales / kpis["Total Orders"], 2
        ) if kpis["Total Orders"] else 0

        performance["Profit Margin"] = round(
            (total_profit / total_sales) * 100, 2
        ) if total_sales else 0

        cursor.execute(
            """
            SELECT category, SUM(sales)
            FROM sales_data
            WHERE dataset_id=%s
            GROUP BY category
            ORDER BY SUM(sales) DESC
            LIMIT 1
            """,
            (dataset_id,)
        )
        row = cursor.fetchone()
        performance["Best Category"] = row[0] if row else "-"

        cursor.execute(
            """
            SELECT product, SUM(sales)
            FROM sales_data
            WHERE dataset_id=%s
            GROUP BY product
            ORDER BY SUM(sales) DESC
            LIMIT 1
            """,
            (dataset_id,)
        )
        row = cursor.fetchone()
        performance["Best Product"] = row[0] if row else "-"

        # ==========================================
        # Top Products
        # ==========================================
        cursor.execute(
            """
            SELECT product, SUM(sales)
            FROM sales_data
            WHERE dataset_id=%s
            GROUP BY product
            ORDER BY SUM(sales) DESC
            LIMIT 5
            """,
            (dataset_id,)
        )
        top_products = cursor.fetchall()

        # ==========================================
        # Monthly Sales Chart
        # ==========================================
        chart_path = None
        monthly_labels, monthly_values = get_monthly_sales(cursor, dataset_id)

        if monthly_labels and monthly_values:
            chart_path = os.path.join(REPORTS_DIR, f"sales_chart_{dataset_id}.png")
            create_sales_chart(monthly_labels, monthly_values, chart_path)

        # ==========================================
        # Business Score
        # ==========================================
        score = 0

        # Sales (40 marks)
        if total_sales >= 1000000:
            score += 40
        elif total_sales >= 500000:
            score += 30
        elif total_sales >= 100000:
            score += 20
        else:
            score += 10

        # Profit Margin (30 marks)
        if performance["Profit Margin"] >= 20:
            score += 30
        elif performance["Profit Margin"] >= 10:
            score += 20
        elif performance["Profit Margin"] >= 5:
            score += 10

        # Orders (30 marks)
        if kpis["Total Orders"] >= 5000:
            score += 30
        elif kpis["Total Orders"] >= 2000:
            score += 20
        elif kpis["Total Orders"] >= 500:
            score += 10

        # ==========================================
        # Business Verdicts
        # ==========================================
        verdicts = []

        if total_sales >= 1000000:
            verdicts.append("Sales performance is excellent.")
        elif total_sales >= 500000:
            verdicts.append("Sales performance is good.")
        else:
            verdicts.append("Sales require improvement.")

        if performance["Profit Margin"] >= 20:
            verdicts.append("Profit margin is excellent.")
        elif performance["Profit Margin"] >= 10:
            verdicts.append("Profit margin is healthy.")
        else:
            verdicts.append("Profit margin is low.")

        verdicts.append(f"{performance['Best Category']} is the best-performing category.")
        verdicts.append(f"{performance['Best Product']} is the best-selling product.")

        # ==========================================
        # Generate PDF
        # ==========================================
        report_path = os.path.join(REPORTS_DIR, f"Sales_Report_{dataset_id}.pdf")

        generate_dashboard_report(
            report_path,
            dataset_name,
            kpis,
            performance,
            top_products,
            verdicts,
            score,
            chart_path
        )

        return send_file(
            report_path,
            as_attachment=True,
            download_name=f"Sales_Report_{dataset_name}.pdf"
        )

    finally:
        cursor.close()
        connection.close()

# =====================================================
# DATASET HISTORY
# =====================================================
@auth.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, file_name, dataset_id, total_rows, total_columns, upload_time "
        "FROM upload_history WHERE uploaded_by=%s ORDER BY upload_time DESC",
        (session["user"],)
    )
    datasets = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template("history.html", datasets=datasets)

# =====================================================
# OPEN DATASET
# =====================================================
@auth.route("/open_dataset/<int:id>")
def open_dataset(id):
    if "user" not in session:
        return redirect("/login")

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT dataset_id FROM upload_history WHERE id=%s AND uploaded_by=%s",
        (id, session["user"])
    )
    dataset = cursor.fetchone()
    if dataset:
        session["current_dataset"] = dataset[0]
    cursor.close()
    connection.close()

    return redirect("/dashboard")

# =====================================================
# DELETE DATASET
# =====================================================
@auth.route("/delete_dataset/<int:id>")
def delete_dataset(id):
    if "user" not in session:
        return redirect("/login")

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT dataset_id, s3_key FROM upload_history WHERE id=%s AND uploaded_by=%s",
        (id, session["user"])
    )
    dataset = cursor.fetchone()

    if dataset:
        dataset_id = dataset[0]
        s3_key = dataset[1]
        cursor.execute("DELETE FROM sales_data WHERE dataset_id=%s", (dataset_id,))
        cursor.execute("DELETE FROM upload_history WHERE id=%s", (id,))
        connection.commit()
        try:
            s3.delete_object(Bucket=S3_BUCKET, Key=s3_key)
        except Exception as e:
            print("S3 Delete Error:", e)

        if session.get("current_dataset") == dataset_id:
            cursor.execute(
                "SELECT dataset_id FROM upload_history WHERE uploaded_by=%s ORDER BY upload_time DESC LIMIT 1",
                (session["user"],)
            )
            next_dataset = cursor.fetchone()
            if next_dataset:
                session["current_dataset"] = next_dataset[0]
            else:
                session.pop("current_dataset", None)

    cursor.close()
    connection.close()
    return redirect("/history")

# =====================================================
# LOGOUT
# =====================================================
@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/login")