from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.routes.auth import get_current_user
from app.services.ai_service import ask_ai
from app.db import mongo
from bson import ObjectId
from datetime import datetime
import PyPDF2
import os

router = APIRouter()


def serialize_interview_summary(interview: dict) -> dict:
    return {
        "_id": str(interview.get("_id")),
        "role": interview.get("role"),
        "experience": interview.get("experience"),
        "mode": interview.get("mode"),
        "finalScore": interview.get("finalScore", 0),
        "status": interview.get("status"),
        "createdAt": interview.get("createdAt").isoformat() if interview.get("createdAt") else None,
    }


@router.post("/analyze-resume")
async def analyze_resume(resume: UploadFile = File(...)):
    if not resume:
        raise HTTPException(status_code=400, detail="Resume required")
    tmp_path = f"temp_{int(datetime.utcnow().timestamp())}_{resume.filename}"
    with open(tmp_path, "wb") as f:
        f.write(await resume.read())

    try:
        reader = PyPDF2.PdfReader(tmp_path)
        resume_text = "\n".join([p.extract_text() or "" for p in reader.pages])
        resume_text = " ".join(resume_text.split())

        messages = [
            {"role": "system", "content": "Extract structured data from resume. Return strictly JSON:\n{\n \"role\": \"string\",\n \"experience\": \"string\",\n \"projects\": [\"project1\"],\n \"skills\": [\"skill1\"]\n}"},
            {"role": "user", "content": resume_text}
        ]

        parsed = {"role": "Software Engineer", "experience": "1 year", "projects": [], "skills": []}
        try:
            ai_resp = await ask_ai(messages)
            import json
            parsed = json.loads(ai_resp)
        except Exception:
            # fallback simple parsing
            lower = resume_text.lower()
            guessed = [s for s in ["javascript", "react", "node", "mongodb", "express", "python", "java", "sql"] if s in lower]
            parsed = {"role": "Software Engineer", "experience": "1 year", "projects": [], "skills": guessed}

        return {"role": parsed.get("role"), "experience": parsed.get("experience"), "projects": parsed.get("projects"), "skills": parsed.get("skills"), "resumeText": resume_text}
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


@router.post("/resume")
async def analyze_resume_alias(resume: UploadFile = File(...)):
    return await analyze_resume(resume)


@router.post("/generate-questions")
async def create_interview_alias(payload: dict, current_user=Depends(get_current_user)):
    return await create_interview(payload, current_user)


@router.post("/create")
async def create_interview(payload: dict, current_user=Depends(get_current_user)):
    role = (payload.get("role") or "").strip()
    experience = (payload.get("experience") or "").strip()
    mode = (payload.get("mode") or "").strip()
    resume_text = payload.get("resumeText") or ""
    projects = payload.get("projects") or []
    skills = payload.get("skills") or []

    if not role or not experience or not mode:
        raise HTTPException(status_code=400, detail="Role, Experience and Mode are required.")

    user = await mongo.db.users.find_one({"_id": ObjectId(current_user["id"])})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_dev = os.environ.get("NODE_ENV") != "production"
    if not is_dev and (user.get("credits", 0) < 50):
        raise HTTPException(status_code=400, detail="Not enough credits. Minimum 50 required.")

    project_text = ", ".join(projects) if projects else "None"
    skills_text = ", ".join(skills) if skills else "None"
    safe_resume = resume_text.strip() or "None"

    user_prompt = f"Role:{role}\nExperience:{experience}\nInterviewMode:{mode}\nProjects:{project_text}\nSkills:{skills_text},\nResume:{safe_resume}"

    messages = [
        {"role": "system", "content": "You are a real human interviewer conducting a professional interview. Generate exactly 5 interview questions. Return one question per line."},
        {"role": "user", "content": user_prompt}
    ]

    try:
        ai_response = await ask_ai(messages)
    except Exception:
        ai_response = "\n".join(["Explain a project you worked on in detail."] * 5)

    questions_array = [q.strip() for q in ai_response.split("\n") if q.strip()][:5]
    if not questions_array:
        raise HTTPException(status_code=500, detail="AI failed to generate questions.")

    if not is_dev:
        await mongo.db.users.update_one({"_id": ObjectId(current_user["id"])}, {"$inc": {"credits": -50}})

    questions_docs = []
    diffs = ["easy", "easy", "medium", "medium", "hard"]
    times = [60, 60, 90, 90, 120]
    for i, q in enumerate(questions_array):
        questions_docs.append({"question": q, "difficulty": diffs[i], "timeLimit": times[i], "answer": "", "feedback": "", "score": 0, "confidence": 0, "communication": 0, "correctness": 0})

    interview_doc = {"userId": ObjectId(current_user["id"]), "role": role, "experience": experience, "mode": mode, "resumeText": safe_resume, "questions": questions_docs, "finalScore": 0, "status": "Incompleted", "createdAt": datetime.utcnow(), "updatedAt": datetime.utcnow()}
    res = await mongo.db.interviews.insert_one(interview_doc)

    return {"interviewId": str(res.inserted_id), "creditsLeft": (user.get("credits") - 50) if not is_dev else user.get("credits"), "userName": user.get("name"), "questions": questions_docs}


@router.post("/submit")
async def submit_answer(data: dict, current_user=Depends(get_current_user)):
    interview_id = data.get("interviewId")
    question_index = int(data.get("questionIndex"))
    answer = data.get("answer")
    time_taken = data.get("timeTaken", 0)

    interview = await mongo.db.interviews.find_one({"_id": ObjectId(interview_id)})
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if question_index < 0 or question_index >= len(interview.get("questions", [])):
        raise HTTPException(status_code=400, detail="Invalid question index")

    question = interview["questions"][question_index]

    if not answer:
        question.update({"score": 0, "feedback": "You did not submit an answer.", "answer": ""})
        await mongo.db.interviews.update_one({"_id": interview["_id"]}, {"$set": {f"questions.{question_index}": question}})
        return {"feedback": question.get("feedback")}

    if time_taken > question.get("timeLimit", 0):
        question.update({"score": 0, "feedback": "Time limit exceeded. Answer not evaluated.", "answer": answer})
        await mongo.db.interviews.update_one({"_id": interview["_id"]}, {"$set": {f"questions.{question_index}": question}})
        return {"feedback": question.get("feedback")}

    messages = [
        {"role": "system", "content": "You are a professional human interviewer evaluating a candidate's answer. Return ONLY valid JSON with fields confidence, communication, correctness, finalScore, feedback."},
        {"role": "user", "content": f"Question: {question.get('question')}\nAnswer: {answer}"}
    ]

    try:
        ai_resp = await ask_ai(messages)
        import json
        parsed = json.loads(ai_resp)
    except Exception:
        parsed = {"confidence": 5, "communication": 5, "correctness": 5, "finalScore": 5, "feedback": "Good answer, keep practicing."}

    question.update({"answer": answer, "confidence": parsed.get("confidence", 0), "communication": parsed.get("communication", 0), "correctness": parsed.get("correctness", 0), "score": parsed.get("finalScore", 0), "feedback": parsed.get("feedback", "")})
    await mongo.db.interviews.update_one({"_id": interview["_id"]}, {"$set": {f"questions.{question_index}": question}})

    return {"feedback": question.get("feedback")}


@router.post("/submit-answer")
async def submit_answer_alias(data: dict, current_user=Depends(get_current_user)):
    return await submit_answer(data, current_user)


@router.post("/finish")
async def finish_interview(data: dict, current_user=Depends(get_current_user)):
    interview_id = data.get("interviewId")
    interview = await mongo.db.interviews.find_one({"_id": ObjectId(interview_id)})
    if not interview:
        raise HTTPException(status_code=400, detail="failed to find Interview")

    questions = interview.get("questions", [])
    total_questions = len(questions)
    total_score = sum([q.get("score", 0) for q in questions])
    total_conf = sum([q.get("confidence", 0) for q in questions])
    total_comm = sum([q.get("communication", 0) for q in questions])
    total_corr = sum([q.get("correctness", 0) for q in questions])

    final_score = total_score / total_questions if total_questions else 0
    avg_conf = total_conf / total_questions if total_questions else 0
    avg_comm = total_comm / total_questions if total_questions else 0
    avg_corr = total_corr / total_questions if total_questions else 0

    await mongo.db.interviews.update_one({"_id": interview["_id"]}, {"$set": {"finalScore": final_score, "status": "completed", "updatedAt": datetime.utcnow()}})

    return {"finalScore": round(final_score, 1), "confidence": round(avg_conf, 1), "communication": round(avg_comm, 1), "correctness": round(avg_corr, 1), "questionWiseScore": [{"question": q.get("question"), "score": q.get("score", 0), "feedback": q.get("feedback", ""), "confidence": q.get("confidence", 0), "communication": q.get("communication", 0), "correctness": q.get("correctness", 0)} for q in questions]}


@router.get("/my-interviews")
async def get_my_interviews(current_user=Depends(get_current_user)):
    interviews = await mongo.db.interviews.find({"userId": ObjectId(current_user["id"])}, {"role":1,"experience":1,"mode":1,"finalScore":1,"status":1,"createdAt":1}).sort([("createdAt", -1)]).to_list(length=100)
    return [serialize_interview_summary(interview) for interview in interviews]


@router.get("/report/{id}")
async def get_interview_report(id: str, current_user=Depends(get_current_user)):
    interview = await mongo.db.interviews.find_one({"_id": ObjectId(id)})
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    questions = interview.get("questions", [])
    total_questions = len(questions)
    total_conf = sum([q.get("confidence", 0) for q in questions])
    total_comm = sum([q.get("communication", 0) for q in questions])
    total_corr = sum([q.get("correctness", 0) for q in questions])

    avg_conf = total_conf / total_questions if total_questions else 0
    avg_comm = total_comm / total_questions if total_questions else 0
    avg_corr = total_corr / total_questions if total_questions else 0

    return {"finalScore": interview.get("finalScore"), "confidence": round(avg_conf,1), "communication": round(avg_comm,1), "correctness": round(avg_corr,1), "questionWiseScore": questions}


@router.get("/get-interview")
async def get_my_interviews_alias(current_user=Depends(get_current_user)):
    return await get_my_interviews(current_user)
