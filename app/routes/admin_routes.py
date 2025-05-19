from flask import Blueprint, render_template, request, redirect, url_for, session
from app.db import db
from app.utils.questionnaire_utils import handle_questionnaire_creation
from app.utils.questionnaire_utils import edit_questionnaire_util
from app.utils.questionnaire_utils import view_answers_util

admin_blueprint = Blueprint('admin', __name__, url_prefix="/admin")

#  Login Admin
@admin_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Σταθερό username/password
        if username == "admin" and password == "admin123":
            session["admin_logged_in"] = True
            return redirect(url_for("admin.dashboard"))
        else:
            return "Λάθος στοιχεία", 401

    return render_template("admin_templates/admin_login.html")

# Logout Admin
@admin_blueprint.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin.login"))

# Dashboard Admin
@admin_blueprint.route("/dashboard")
def dashboard():
    if "admin_logged_in" not in session:
        return redirect(url_for("admin.login"))

    questionnaires = db.Questionnaires.find({"student_id": 0})

    return render_template("admin_templates/admin_dashboard.html", questionnaires=questionnaires)


#  Δημιουργία Φοιτητή
@admin_blueprint.route("/create-student", methods=["GET", "POST"])
def create_student():
    if "admin_logged_in" not in session:
        return redirect(url_for("admin.login"))

    if request.method == "POST":
        reg_number = int(request.form["reg_number"])
        username = request.form["username"]
        password = request.form["password"]
        name = request.form["name"]
        surname = request.form["surname"]
        department = request.form["department"]

        new_student = {
            "reg_number": reg_number,
            "username": username,
            "password": password,
            "name": name,
            "surname": surname,
            "department": department
        }

        db.Students.insert_one(new_student)
        return redirect(url_for("admin.dashboard"))

    return render_template("admin_templates/admin_create_student.html")

#  Διαγραφή Φοιτητή
@admin_blueprint.route("/delete-student/<int:reg_number>", methods=["POST"])
def delete_student(reg_number):
    if "admin_logged_in" not in session:
        return redirect(url_for("admin.login"))
    # διαγράφω και οτι εχει να κάνει με το φοιτητή
    db.Students.delete_one({"reg_number": reg_number})
    db.Questionnaires.delete_many({"student_id": reg_number})
    db.answered_questionnaires.delete_many({"student_id": reg_number})

    return redirect(url_for("admin.dashboard"))

# Δημιουργία Ερωτηματολογίου
@admin_blueprint.route("/create", methods=["GET", "POST"])
def admin_create_questionnaire():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin.login"))
    
    result = handle_questionnaire_creation(request, session)
    if result == "submitted":
        return redirect(url_for("admin.dashboard"))
    return result

# Επεξεργασία Ερωτηματολογίου
@admin_blueprint.route("/questionnaire/<int:questionnaire_id>/edit", methods=["GET", "POST"])
def edit_questionnaire(questionnaire_id):
    result = edit_questionnaire_util(questionnaire_id)
    if result == "edit_successful":
        return redirect(url_for("admin.dashboard"))
    return result

# Διαγραφή Ερωτηματολογίου
@admin_blueprint.route("/questionnaire/<int:questionnaire_id>/delete", methods=["POST"])
def delete_questionnaire(questionnaire_id):
    if "student_id" not in session and "admin_logged_in" not in session:
        return redirect(url_for("admin.login"))

    db.Questionnaires.delete_one({"questionnaire_id": questionnaire_id})
    db.answered_questionnaires.delete_many({"questionnaire_id": questionnaire_id})
    
    return redirect(url_for("admin.dashboard"))


# Προβολή Απαντήσεων Ερωτηματολογίου
@admin_blueprint.route("/questionnaire/<int:questionnaire_id>/answers")
def view_answers(questionnaire_id):
    if "student_id" not in session and "admin_logged_in" not in session:
        return redirect(url_for("student.login"))
    result = view_answers_util(questionnaire_id)
    return result

# Προβολή Φοιτητών
@admin_blueprint.route("/view_students", methods=["GET"])
def view_students():
    if "admin_logged_in" not in session:
        return redirect(url_for("admin.login"))

    search_name = request.args.get("name", "").strip()

    if search_name:
        students = db.Students.find({"name": {"$regex": search_name, "$options": "i"}})
    else:
        students = db.Students.find()

    return render_template("admin_templates/admin_students.html", students=students, search_name=search_name)

