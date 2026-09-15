from flask import Flask

from auth import auth
from upload import upload

app = Flask(__name__)

app.secret_key = "sales_dashboard_project"

app.register_blueprint(auth)
app.register_blueprint(upload)


if __name__ == "__main__":
    app.run(debug=True)