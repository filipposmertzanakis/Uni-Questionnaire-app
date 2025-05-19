from flask import Flask , jsonify , render_template , request
from app.routes.student_routes import student_blueprint
from app.routes.user_routes  import user_blueprint
from app.routes.admin_routes import admin_blueprint
from app.db import db

app = Flask(__name__)
app.secret_key = "supersecretkey"


# κανω register τα blueprints για να μπορω να τα χρησιμοποιησω
app.register_blueprint(student_blueprint ,url_prefix="/student")
app.register_blueprint(user_blueprint ,url_prefix="/questionnaire")
app.register_blueprint(admin_blueprint ,url_prefix="/admin")


@app.route('/')
def index():
        return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)



