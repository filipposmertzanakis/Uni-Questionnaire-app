from flask import render_template , request, redirect, url_for, session
import random
from app.db import db 

def handle_questionnaire_creation(request, session):
    if request.method == "POST":
        if "title" in request.form:
            title = request.form["title"]
            description = request.form["description"]
            question_count = int(request.form["question_count"])

            questions = []
            for i in range(1, question_count + 1):
                q_type = request.form.get(f"type_{i}")
                q_desc = request.form.get(f"description_{i}")
                questions.append({
                    "type": q_type,
                    "description": q_desc,
                    "question_num": i
                })

            questionnaire_id = random.randint(1000, 9999)
            student_id = session["student_id"] if "student_id" in session else 0  # Default to 0 για admin
            # Εαν δεν ειναι φοιτητης τοτε ειναι admin και βαζω στο student_id : 0 
            new_questionnaire = {
                "student_id": student_id ,
                "questionnaire_id": questionnaire_id,
                "title": title,
                "description": description,
                "unique_url": f"127.0.0.1:5000/questionnaire/{questionnaire_id}",
                "questions": questions,
                "answer_count": 0,
            }
            print("Creating questionnaire:", new_questionnaire)

            db.Questionnaires.insert_one(new_questionnaire)
            return "submitted"
        else:
            question_count = int(request.form["question_count"])
            return render_template("student_templates/student_create_questionnaire_form.html", question_count=question_count)

    return render_template("student_templates/student_create_questionnaire.html")


def edit_questionnaire_util(questionnaire_id):
    if "student_id" not in session and "admin_logged_in" not in session:
        return redirect(url_for("student.login"))
    if "student_id" in session:
        questionnaire = db.Questionnaires.find_one({"questionnaire_id": questionnaire_id, "student_id": session["student_id"]})
    else:
        questionnaire = db.Questionnaires.find_one({"questionnaire_id": questionnaire_id })  

    if not questionnaire:
        return "Ερωτηματολόγιο δεν βρέθηκε", 404

    if request.method == "POST":
        new_title = request.form["title"]
        db.Questionnaires.update_one(
            {"questionnaire_id": questionnaire_id},
            {"$set": {"title": new_title}}
        )
        return "edit_successful"
    return render_template("student_templates/student_edit_questionnaire.html", questionnaire=questionnaire)


def view_answers_util(questionnaire_id):
 
    
    # Βρίσκουμε το ερωτηματολόγιο για τον φοιτητή
    # εαν ειναι φοιτητής μπορει να δει μονο τα δικα του ερωτηματολόγια , αλλιως ο admin μπορει να δει ολα τα ερωτηματολόγια
    if "student_id" in session:
        questionnaire = db.Questionnaires.find_one({"questionnaire_id": questionnaire_id, "student_id": session["student_id"]})
    else:
        questionnaire = db.Questionnaires.find_one({"questionnaire_id": questionnaire_id })  
    
    
    if not questionnaire:
        return "Ερωτηματολόγιο δεν βρέθηκε", 404
    
    answers = list(db.answered_questionnaires.find({"questionnaire_id": questionnaire_id}))
    

    total_responses = len(answers)
    user_responses = len([answer for answer in answers if not answer.get("from_student")])  # Users are identified by 'from_student: false'
    student_responses = total_responses - user_responses  # Rest are students

    # Υπολογίζουμε το ποσοστό 
    if total_responses > 0:
        user_percentage = (user_responses / total_responses) * 100
    else:
        user_percentage = 0

    # Συνδυάζουμε τις ερωτήσεις με τις αντίστοιχες απαντήσεις
    question_answer_pairs = []
    
    for answer in answers:
        for ans in answer['answers']:  # Το 'answers' είναι η λίστα με τις απαντήσεις
            # Αντιστοιχίζουμε την ερώτηση με την απάντηση της
            question = next(q for q in questionnaire['questions'] if q['question_num'] == ans['question_num'])
            question_answer_pairs.append({
                "question": question['description'],
                "answer": ans['content']
            })
    
    # Επιστρέφουμε το template με τα ζευγάρια ερώτησης και απάντησης
    return render_template(
        "student_templates/student_view_answers.html", 
        questionnaire=questionnaire,
        question_answer_pairs=question_answer_pairs,
        total_responses=total_responses,
        user_responses=user_responses,
        student_responses=student_responses,
        user_percentage=user_percentage
    )