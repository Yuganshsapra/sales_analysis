// ===========================================
// Dataset Comparison - Sales Chart
// ===========================================

const salesCompareCanvas = document.getElementById("salesCompareChart");

if (
    salesCompareCanvas &&
    typeof compareSalesLabels !== "undefined"
) {

    new Chart(salesCompareCanvas, {

        type: "line",

        data: {

            labels: compareSalesLabels,

            datasets: [

                {

                    label: "Dataset A",

                    data: compareSalesA,

                    borderColor: "#2563EB",

                    backgroundColor: "rgba(37,99,235,0.15)",

                    borderWidth: 3,

                    tension: 0.35,

                    fill: false

                },

                {

                    label: "Dataset B",

                    data: compareSalesB,

                    borderColor: "#16A34A",

                    backgroundColor: "rgba(22,163,74,0.15)",

                    borderWidth: 3,

                    tension: 0.35,

                    fill: false

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
// Dataset Comparison - Profit Chart
// ===========================================

const profitCompareCanvas = document.getElementById("profitCompareChart");

if (
    profitCompareCanvas &&
    typeof compareProfitLabels !== "undefined"
) {

    new Chart(profitCompareCanvas, {

        type: "line",

        data: {

            labels: compareProfitLabels,

            datasets: [

                {

                    label: "Dataset A",

                    data: compareProfitA,

                    borderColor: "#2563EB",

                    backgroundColor: "rgba(37,99,235,0.15)",

                    borderWidth: 3,

                    tension: 0.35,

                    fill: false

                },

                {

                    label: "Dataset B",

                    data: compareProfitB,

                    borderColor: "#16A34A",

                    backgroundColor: "rgba(22,163,74,0.15)",

                    borderWidth: 3,

                    tension: 0.35,

                    fill: false

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

            },

            scales: {

                y: {

                    beginAtZero: true

                }

            }

        }

    });

}