from flask import Blueprint, render_template, request, redirect, url_for
from app.db import db

user_blueprint = Blueprint('user', __name__, url_prefix="/questionnaire")

# όλων των ερωτηματολογίων
@user_blueprint.route("/", methods=["GET"])
def list_questionnaires():
    title = request.args.get('title', '')
    student_name = request.args.get('student_name', '')
    department = request.args.get('department', '')
    min_answers = request.args.get('min_answers', type=int)
    max_answers = request.args.get('max_answers', type=int)
    sort_order = request.args.get('sort_order', '')

    # Δημιουργία του query για MongoDB
    query = {}
    if title:
        query['title'] = {'$regex': title, '$options': 'i'}  
    if student_name:
        query['student_name'] = {'$regex': student_name, '$options': 'i'}
    if department:
        query['department'] = {'$regex': department, '$options': 'i'}
    if min_answers is not None:
        query['answer_count'] = {'$gte': min_answers}
    if max_answers is not None:
        query['answer_count'] = {'$lte': max_answers}

    sort_by = []
    if sort_order == 'asc':
        sort_by = [('answer_count', 1)]
    elif sort_order == 'desc':
        sort_by = [('answer_count', -1)]

    # Ενσωμάτωση του aggregation pipeline με $lookup για inner join
    pipeline = [
        {
            '$lookup': {
                'from': 'Students',               
                'localField': 'student_id',        
                'foreignField': 'reg_number',      
                'as': 'student_info'               
            }
        },
        {
            '$unwind': '$student_info'               
        },
        {
            '$match': query                           
        },
        {
            '$project': {
            'questionnaire_id': '$questionnaire_id',  
            'title': 1,
            'answer_count': 1,
            'student_name': '$student_info.name',
            'department': '$student_info.department'
            }
        }
    ]

    # Προσθήκη ταξινόμησης εάν απαιτείται
    if sort_by:
        pipeline.append({'$sort': dict(sort_by)})

    # Εκτέλεση του aggregation pipeline για να πάρουμε τα αποτελέσματα
    questionnaires = db.Questionnaires.aggregate(pipeline)

    return render_template("/questionnaire_templates/list_questionnaires.html",
                           questionnaires=questionnaires,
                           title=title,
                           student_name=student_name,
                           department=department,
                           min_answers=min_answers,
                           max_answers=max_answers,
                           sort_order=sort_order)

# Αναζήτηση με φίλτρα
@user_blueprint.route("/search", methods=["GET"])
def search_questionnaires():
    title = request.args.get('title', '')
    student_name = request.args.get('student_name', '')
    department = request.args.get('department', '')
    min_answers = request.args.get('min_answers', type=int)
    max_answers = request.args.get('max_answers', type=int)
    sort_order = request.args.get('sort_order', '')

    match_conditions = []

    if title:
        match_conditions.append({'title': {'$regex': title, '$options': 'i'}})
    if student_name:
        match_conditions.append({'student_info.name': {'$regex': student_name, '$options': 'i'}})
    if department:
        match_conditions.append({'student_info.department': {'$regex': department, '$options': 'i'}})
    if min_answers is not None:
        match_conditions.append({'answer_count': {'$gte': min_answers}})
    if max_answers is not None:
        match_conditions.append({'answer_count': {'$lte': max_answers}})

    sort_by = []
    if sort_order == 'asc':
        sort_by = [('answer_count', 1)]
    elif sort_order == 'desc':
        sort_by = [('answer_count', -1)]

    pipeline = [
        {
            '$lookup': {
                'from': 'Students',
                'localField': 'student_id',
                'foreignField': 'reg_number',
                'as': 'student_info'
            }
        },
        {
            '$unwind': {
                'path': '$student_info',
                'preserveNullAndEmptyArrays': True
            }
        }
    ]

    if match_conditions:
        pipeline.append({'$match': {'$and': match_conditions}})

    pipeline.append({
        '$project': {
            'questionnaire_id': 1,
            'title': 1,
            'answer_count': 1,
            'student_name': {
                '$cond': {
                    'if': { '$eq': ['$student_id', 0] },
                    'then': 'admin',
                    'else': '$student_info.name'
                }
            },
            'department': {
                '$cond': {
                    'if': { '$eq': ['$student_id', 0] },
                    'then': 'admin',
                    'else': '$student_info.department'
                }
            }
        }
    })

    if sort_by:
        pipeline.append({'$sort': dict(sort_by)})

    questionnaires = db.Questionnaires.aggregate(pipeline)

    return render_template("/questionnaire_templates/list_questionnaires.html",
        questionnaires=questionnaires,
        title=title,
        student_name=student_name,
        department=department,
        min_answers=min_answers,
        max_answers=max_answers,
        sort_order=sort_order)
#  Προβολή συγκεκριμένου ερωτηματολογίου μέσω URL
@user_blueprint.route("/<int:questionnaire_id>", methods=["GET"])
def view_questionnaire(questionnaire_id):
    questionnaire = db.Questionnaires.find_one({"questionnaire_id": questionnaire_id})
    
    if not questionnaire:
        return "Το ερωτηματολόγιο δεν βρέθηκε", 404

    return render_template("/questionnaire_templates/view_questionnaire.html", questionnaire=questionnaire)

#  Υποβολή απαντήσεων σε ερωτηματολόγιο
@user_blueprint.route("/<int:questionnaire_id>/answer", methods=["POST"])
def submit_answers(questionnaire_id):
    questionnaire = db.Questionnaires.find_one({"questionnaire_id": questionnaire_id})
    if not questionnaire:
        return "Το ερωτηματολόγιο δεν βρέθηκε", 404

    answers = []
    for question in questionnaire["questions"]:
        answer = request.form.get(f"q{question['question_num']}")
        if answer is not None:
            answers.append({
                "question_num": question["question_num"],
                "content": answer
            })

    new_answer = {
        "questionnaire_id": questionnaire_id,
        "from_student": False,  # Για απλό χρήστη
        "answers": answers
    }

    db.answered_questionnaires.insert_one(new_answer)
    db.Questionnaires.update_one({"questionnaire_id": questionnaire_id}, {"$inc": {"answer_count": 1}})

    return redirect(url_for("user.list_questionnaires"))

