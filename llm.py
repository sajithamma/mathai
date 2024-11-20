# llm.py
import os
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
from models import StudentSnapshot, Question, QuestionAttempt, QuestionsResponse
import json

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class LLM:
    """Base class/interface for LLMs, providing methods for generating questions and evaluating answers."""
    
    def generate_questions(self, snapshot: StudentSnapshot) -> List[Question]:
        """Generates a list of questions tailored to the student's snapshot."""
        raise NotImplementedError("This method should be implemented by subclasses")
    
    def evaluate_answer(self, question: Question, student_answer: str, snapshot: StudentSnapshot):
        """Evaluates the student's answer and returns updates to the snapshot."""
        raise NotImplementedError("This method should be implemented by subclasses")


class OpenAILLM(LLM):
    """OpenAI LLM implementation using the latest API with response_format."""
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
    
    def generate_questions(self, snapshot: StudentSnapshot, verbose: bool = True) -> List[Question]:
        # Prepare the prompt
        messages = [
            {
                "role": "system",
                "content": "You are an AI tutor that generates multiple-choice calculus questions tailored to the student's needs.",
            },
            {
                "role": "user",
                "content": f"""
Generate 3 multiple-choice calculus questions.

Student Snapshot:
{snapshot.json()}

Requirements:
- Focus on the student's weak areas and recent errors.
- Use the desired difficulty level.
- Provide 4 options for each question, with explanations for each.
- Ensure explanations clarify why an option is correct or incorrect.
- Output format must be a JSON object matching the QuestionsResponse model.
""",
            },
        ]
        
        if verbose:
            print("\n[DEBUG] Generating questions with the following prompt:")
            print(json.dumps(messages, indent=2))
        
        try:
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=messages,
                response_format=QuestionsResponse,  # Use the QuestionsResponse class
            )
            
            # Access and parse the response
            questions_response = completion.choices[0].message.parsed
            questions = questions_response.questions  # Extract the list of questions
            if verbose:
                print("\n[DEBUG] Generated questions:")
                for q in questions:
                    print(q.json(indent=2))
            return questions
        except Exception as e:
            print(f"Error during question generation: {e}")
            return []
    
    def evaluate_answer(self, question: Question, student_answer: str, snapshot: StudentSnapshot, verbose: bool = True):
        messages = [
            {
                "role": "system",
                "content": "You are an AI tutor that evaluates student's answers and updates their learning progress.",
            },
            {
                "role": "user",
                "content": f"""
Evaluate the student's answer to the following question.

Question:
{question.json()}

Student's Answer: "{student_answer}"

Student Snapshot:
{snapshot.json()}

Requirements:
- Provide feedback on the correctness of the answer.
- Return only the updated fields of the student's snapshot in JSON format.
- Output format must match the partial StudentSnapshot model.
""",
            },
        ]
        
        if verbose:
            print("\n[DEBUG] Evaluating answer with the following prompt:")
            print(json.dumps(messages, indent=2))
        
        try:
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=messages,
                response_format=StudentSnapshot,
            )
            
            # Access and parse the response
            updated_snapshot = completion.choices[0].message.parsed
            if verbose:
                print("\n[DEBUG] Updated snapshot:")
                print(updated_snapshot.json(indent=2))
            return updated_snapshot
        except Exception as e:
            print(f"Error during answer evaluation: {e}")
            return None


# Testing code
if __name__ == '__main__':
    # Initialize the OpenAILLM instance
    llm = OpenAILLM()
    verbose = True  # Set to False to reduce output

    # Create a sample StudentSnapshot
    snapshot = StudentSnapshot(
        student_id="test_student",
        levels={"logic_based": 2, "real_life_based": 2, "abstract_based": 2},
        weak_areas=["Chain Rule", "Implicit Differentiation"],
        strong_areas=["Basic Differentiation"],
        desired_difficulty_level=2,
        recent_history=[]
    )

    # Test generate_questions
    print("Testing generate_questions...")
    questions = llm.generate_questions(snapshot, verbose=verbose)
    if questions:
        for idx, question in enumerate(questions, start=1):
            print(f"\nQuestion {idx}: {question.question_text}")
            for option in question.options:
                print(f"{option.option_label}. {option.option_text}")
            # Simulate student's answer (for testing, select 'A')
            student_answer = 'A'
            print(f"\nSimulated Student Answer: {student_answer}")

            # Test evaluate_answer
            print("\nTesting evaluate_answer...")
            updated_snapshot = llm.evaluate_answer(question, student_answer, snapshot, verbose=verbose)
            if updated_snapshot:
                # Update the snapshot with the returned changes
                snapshot = snapshot.copy(update=updated_snapshot.dict(exclude_unset=True))
                print("\n[DEBUG] Updated Student Snapshot:")
                print(snapshot.json(indent=2))
            else:
                print("Failed to evaluate answer.")
    else:
        print("Failed to generate questions.")
