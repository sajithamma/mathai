# models.py
from pydantic import BaseModel
from typing import List, Dict
from enum import Enum


class Option(BaseModel):
    option_label: str  # e.g., "A", "B", "C", "D"
    option_text: str
    is_correct: bool
    explanation: str


class Question(BaseModel):
    question_id: str
    question_text: str
    options: List[Option]
    topic: str
    subtopic: str
    criterion: str
    difficulty_level: int


class QuestionAttempt(BaseModel):
    question_id: str
    topic: str
    subtopic: str
    criterion: str
    difficulty_level: int
    student_answer: str
    is_correct: bool
    score: float
    indicators: List[str]

class QuestionsResponse(BaseModel):
    questions: List[Question]

class StudentSnapshot(BaseModel):
    student_id: str
    levels: Dict[str, int]
    weak_areas: List[str]
    strong_areas: List[str]
    desired_difficulty_level: int
    recent_history: List[QuestionAttempt]  # Last 10 attempts
