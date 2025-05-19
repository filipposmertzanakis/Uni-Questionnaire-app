from flask import Blueprint, render_template, request, redirect, url_for, session
from app.db import db
from app.utils.questionnaire_utils import handle_questionnaire_creation
from app.utils.questionnaire_utils import edit_questionnaire_util
from app.utils.questionnaire_utils import view_answers_util

student_blueprint = Blueprint('student', __name__, url_prefix="/student")

#  Login Φοιτητή
@student_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        student = db.Students.find_one({"username": username, "password": password})
        if student:
            session["student_id"] = student["reg_number"]
            return redirect(url_for("student.dashboard"))
        else:

            return "Λάθος στοιχεία", 401

    return render_template("student_templates/login.html")

#  Logout Φοιτητή
@student_blueprint.route("/logout")
def logout():
    session.pop("student_id", None)
    session.pop("admin_logged_in", None)
    return redirect(url_for("student.login"))

# Dashboard Φοιτητή
@student_blueprint.route("/dashboard")
def dashboard():
    
    if  "student_id" not in session and "admin_logged_in" not in session:
        return redirect(url_for("student.login"))

    student_id = session["student_id"]
    questionnaires = db.Questionnaires.find({"student_id": student_id})

    return render_template("student_templates/student_dashboard.html", questionnaires=questionnaires)




# Δημιουργία νέου Ερωτηματολογίου
@student_blueprint.route("/create", methods=["GET", "POST"])
def create_questionnaire():
    if not session.get("student_id") and not session.get("admin_logged_in"):
        return redirect(url_for("student.login"))
    
    result = handle_questionnaire_creation(request, session)
    if result == "submitted":
        return redirect(url_for("student.dashboard"))
    return result

#  Επεξεργασία τίτλου Ερωτηματολογίου
@student_blueprint.route("/questionnaire/<int:questionnaire_id>/edit", methods=["GET", "POST"])
def edit_questionnaire(questionnaire_id):
    result = edit_questionnaire_util(questionnaire_id)
    if result == "edit_successful":
        return redirect(url_for("student.dashboard"))
    return result
    

#  Διαγραφή Ερωτηματολογίου και Απαντήσεων
@student_blueprint.route("/questionnaire/<int:questionnaire_id>/delete", methods=["POST"])
def delete_questionnaire(questionnaire_id):
    if "student_id" not in session and "admin_logged_in" not in session:
        return redirect(url_for("student.login"))

    db.Questionnaires.delete_one({"questionnaire_id": questionnaire_id, "student_id": session["student_id"]})
    db.answered_questionnaires.delete_many({"questionnaire_id": questionnaire_id})
    
    return redirect(url_for("student.dashboard"))

#  Προβολή Στατιστικών
@student_blueprint.route("/questionnaire/<int:questionnaire_id>/stats")
def questionnaire_stats(questionnaire_id):
    if "student_id" not in session and "admin_logged_in" not in session:
        return redirect(url_for("student.login"))

    answers = list(db.answered_questionnaires.find({"questionnaire_id": questionnaire_id}))
    questionnaire = db.Questionnaires.find_one({"questionnaire_id": questionnaire_id, "student_id": session["student_id"]})

    if not questionnaire:
        return "Ερωτηματολόγιο δεν βρέθηκε", 404

    return render_template("student_templates/student_questionnaire_stats.html", questionnaire=questionnaire, answers=answers)


#  Προβολή Απαντήσεων Ερωτηματολογίου
@student_blueprint.route("/questionnaire/<int:questionnaire_id>/answers")
def view_answers(questionnaire_id):
    if "student_id" not in session and "admin_logged_in" not in session:
        return redirect(url_for("student.login"))
    result = view_answers_util(questionnaire_id)
    return result

# αλλαγή κωδικού πρόσβασης
@student_blueprint.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "student_id" not in session and "admin_logged_in" not in session:
        return redirect(url_for("student.login"))
    if request.method == "POST":
        new_password = request.form["new_password"]
        db.Students.update_one({"reg_number": session["student_id"]}, {"$set": {"password": new_password}})
        return redirect(url_for("student.dashboard"))
    return render_template("student_templates/student_change_password.html")