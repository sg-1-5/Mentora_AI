<img width="1692" height="990" alt="Screenshot 2026-05-14 at 4 21 12 PM" src="https://github.com/user-attachments/assets/fbcbae41-bcd7-44c2-83b0-2b7801c007be" />
<img width="1479" height="896" alt="Screenshot 2026-05-14 at 4 23 12 PM" src="https://github.com/user-attachments/assets/22ded7d7-154a-496f-84f4-3df2fdb93886" />


# Mentora_AI

An AI-powered mock interview platform that helps users practice technical and HR interviews with real-time question generation, resume analysis, and performance tracking.

---

##  Overview

InterviewIQ.AI simulates real interview scenarios using AI. Users can sign in with Google, upload their resume, select a role and experience level, and participate in a personalized mock interview.

The platform analyzes responses and stores interview history so users can track their progress over time.

---

##  Features

- 🔐 Google Authentication using Firebase
- 📄 Resume Upload and Analysis
- 🤖 AI-Generated Interview Questions
- 🎤 Smart Voice Interview Interface
- 📊 Performance Analytics
- 🕒 Timer-Based Interview Simulation
- 📚 Interview History Tracking
- 💳 Payment Integration with Razorpay
- 🌍 Fully Deployed on Render

---

## Tech Stack

### Frontend
- React.js
- Vite
- Redux Toolkit
- Axios
- Tailwind CSS

### Backend
- Python
- FastAPI
- MongoDB
- JWT Authentication
- Cookie-based Sessions

### Third-Party Services
- Firebase Authentication
- Razorpay
- Gemini/OpenAI API

### Deployment
- Render (Frontend + Backend)

---

##  System Architecture



```text
┌─────────────────────────────────────────────────────────────┐
│                         User Browser                       │
│                    (Chrome / Safari / Brave)               │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                   │
│                                                             │
│ • Google Authentication (Firebase)                         │
│ • Interview Setup Form                                     │
│ • Resume Upload                                            │
│ • AI Interview Interface                                   │
│ • Performance Dashboard                                    │
│ • Interview History                                        │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              │ Axios API Calls + JWT Cookie
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Python + FastAPI Backend                  │
│                                                             │
│ • Authentication APIs                                      │
│ • User Management APIs                                     │
│ • Interview APIs                                           │
│ • Resume Analysis APIs                                     │
│ • Payment APIs                                             │
│ • Report Generation APIs                                   │
└───────┬───────────────┬───────────────┬─────────────────────┘
        │               │               │
        ▼               ▼               ▼

┌───────────────┐  ┌───────────────┐  ┌─────────────────────┐
│   MongoDB     │  │ Gemini/OpenAI │  │      Razorpay       │
│               │  │     API       │  │                     │
│ • Users       │  │               │  │ • Subscription      │
│ • Interviews  │  │ • Question    │  │ • Payment Gateway   │
│ • Reports     │  │   Generation  │  │                     │
│ • History     │  │ • Feedback    │  │                     │
└───────────────┘  └───────────────┘  └─────────────────────┘

        ▲
        │
        │
┌─────────────────────────────┐
│       Firebase Auth         │
│                             │
│ • Google Sign-In            │
│ • User Authentication       │
└─────────────────────────────┘
