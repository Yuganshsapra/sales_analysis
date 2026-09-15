// ===========================================
// Sales Dashboard Charts
// ===========================================

let monthlyChart = null;
let salesChart = null;
let categoryChart = null;

// ===========================================
// Monthly Sales Trend
// ===========================================

const monthlyCanvas = document.getElementById("monthlyChart");

if (
    monthlyCanvas &&
    typeof monthlyLabels !== "undefined" &&
    monthlyLabels.length > 0
) {

    if (monthlyChart) {
        monthlyChart.destroy();
    }

    monthlyChart = new Chart(monthlyCanvas, {

        type: "line",

        data: {

            labels: monthlyLabels,

            datasets: [

                {

                    label: "Monthly Sales",

                    data: monthlyValues,

                    borderColor: "#2563EB",

                    backgroundColor: "rgba(37,99,235,0.15)",

                    fill: true,

                    tension: 0.35,

                    pointRadius: 5,

                    pointBackgroundColor: "#2563EB"

                }

            ]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            plugins: {

                legend: {

                    display: true

                }

            },

            scales: {

                y: {

                    beginAtZero: true

                }

            }

        }

    });

}

// ===========================================
// Product Sales Bar Chart
// ===========================================

const salesCanvas = document.getElementById("salesChart");

if (
    salesCanvas &&
    typeof salesLabels !== "undefined" &&
    salesLabels.length > 0
) {

    if (salesChart) {
        salesChart.destroy();
    }

    salesChart = new Chart(salesCanvas, {

        type: "bar",

        data: {

            labels: salesLabels,

            datasets: [

                {

                    label: "Sales",

                    data: salesValues,

                    backgroundColor: "#4F46E5",

                    borderColor: "#3730A3",

                    borderWidth: 1

                }

            ]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            plugins: {

                legend: {

                    display: false

                }

            },

            scales: {

                y: {

                    beginAtZero: true

                }

            }

        }

    });

}

// ===========================================
// Category Pie Chart
// ===========================================

const categoryCanvas = document.getElementById("categoryChart");

if (
    categoryCanvas &&
    typeof categoryLabels !== "undefined" &&
    categoryLabels.length > 0
) {

    if (categoryChart) {
        categoryChart.destroy();
    }

    categoryChart = new Chart(categoryCanvas, {

        type: "pie",

        data: {

            labels: categoryLabels,

            datasets: [

                {

                    data: categoryValues,

                    backgroundColor: [

                        "#4F46E5",

                        "#22C55E",

                        "#F59E0B",

                        "#EF4444",

                        "#06B6D4",

                        "#8B5CF6",

                        "#EC4899",

                        "#84CC16"

                    ]

                }

            ]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            plugins: {

                legend: {

                    position: "bottom"

                }

            }

        }

    });

}

// ===========================================
// Category → Product Dropdown
// ===========================================

const categorySelect = document.getElementById("category");
const productSelect = document.getElementById("product");

if (categorySelect && productSelect) {

    categorySelect.addEventListener("change", function () {

        const category = this.value;

        fetch(`/get_products?category=${encodeURIComponent(category)}`)

            .then(response => response.json())

            .then(products => {

                productSelect.innerHTML = "";

                const defaultOption = document.createElement("option");

                defaultOption.value = "";

                defaultOption.textContent = "All Products";

                productSelect.appendChild(defaultOption);

                products.forEach(product => {

                    const option = document.createElement("option");

                    option.value = product;

                    option.textContent = product;

                    productSelect.appendChild(option);

                });

            })

            .catch(error => {

                console.error("Error Loading Products:", error);

            });

    });

}

console.log("Dashboard Loaded");

    if (typeof monthlyLabels !== "undefined") {

        console.log("Monthly Labels:", monthlyLabels);

        console.log("Monthly Values:", monthlyValues);

    }

console.log("Sales Labels:", salesLabels);
console.log("Sales Values:", salesValues);

console.log("Category Labels:", categoryLabels);
console.log("Category Values:", categoryValues);
// ===========================================
// Prevent Multiple Uploads
// ===========================================

const uploadForm = document.getElementById("uploadForm");

const uploadBtn = document.getElementById("uploadBtn");

if (uploadForm && uploadBtn) {

    let uploading = false;

    uploadForm.addEventListener("submit", function (e) {

        if (uploading) {

            e.preventDefault();

            return;

        }

        uploading = true;

        uploadBtn.disabled = true;

        uploadBtn.innerHTML = "Uploading...⏳";

    });

}
// ===========================================
// Show / Hide Password
// ===========================================

function togglePassword(id, button) {

    const input = document.getElementById(id);

    if (input.type === "password") {

        input.type = "text";

        button.innerHTML = "🙈";

    }

    else {

        input.type = "password";

        button.innerHTML = "👁";

    }

}