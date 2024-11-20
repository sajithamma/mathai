# storage.py
import sqlite3
from models import StudentSnapshot, Question, QuestionAttempt
import json
from typing import Optional


DB_NAME = 'adaptive_learning.db'


def init_db():
    """Initializes the database with necessary tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create students table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        student_id TEXT PRIMARY KEY,
        snapshot TEXT
    )
    ''')
    
    # Create questions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        question_id TEXT PRIMARY KEY,
        question_data TEXT
    )
    ''')
    
    # Create attempts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        question_id TEXT,
        attempt_data TEXT,
        FOREIGN KEY(student_id) REFERENCES students(student_id),
        FOREIGN KEY(question_id) REFERENCES questions(question_id)
    )
    ''')
    
    conn.commit()
    conn.close()


def save_snapshot_to_db(snapshot: StudentSnapshot):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR REPLACE INTO students (student_id, snapshot)
    VALUES (?, ?)
    ''', (snapshot.student_id, snapshot.json()))
    
    conn.commit()
    conn.close()


def load_snapshot_from_db(student_id: str) -> Optional[StudentSnapshot]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT snapshot FROM students WHERE student_id = ?', (student_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        snapshot_json = row[0]
        snapshot = StudentSnapshot.parse_raw(snapshot_json)
        return snapshot
    else:
        return None


def save_question_to_db(question: Question):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR REPLACE INTO questions (question_id, question_data)
    VALUES (?, ?)
    ''', (question.question_id, question.json()))
    
    conn.commit()
    conn.close()


def save_attempt_to_db(student_id: str, question_id: str, attempt: QuestionAttempt):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO attempts (student_id, question_id, attempt_data)
    VALUES (?, ?, ?)
    ''', (student_id, question_id, attempt.json()))
    
    conn.commit()
    conn.close()
