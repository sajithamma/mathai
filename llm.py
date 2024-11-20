# llm.py
import os
from openai import OpenAI
from dotenv import load_dotenv
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
        with open('instructions.txt', 'r') as f:
            self.system_instructions = f.read()

    def generate_questions(self, snapshot: StudentSnapshot, verbose: bool = True) -> List[Question]:
        # Prepare the prompt
        snapshot_json = snapshot.model_dump_json()
        messages = [
            {
                "role": "system",
                "content": self.system_instructions,
            },
            {
                "role": "user",
                "content": f"""
Generate 3 multiple-choice calculus questions.

Student Snapshot:
{snapshot_json}

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
            # Convert messages to a serializable format
            messages_serializable = [message.copy() for message in messages]
            if 'content' in messages[1]:
                messages_serializable[1]['content'] = messages[1]['content']
            print(json.dumps(messages_serializable, indent=2))

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
                    print(q.model_dump_json(indent=2))
            return questions
        except Exception as e:
            print(f"Error during question generation: {e}")
            return []

    def evaluate_answer(self, question: Question, student_answer: str, snapshot: StudentSnapshot, verbose: bool = True):
        question_json = question.model_dump_json()
        snapshot_json = snapshot.model_dump_json()
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
{question_json}

Student's Answer: "{student_answer}"

Student Snapshot:
{snapshot_json}

Requirements:
- Provide feedback on the correctness of the answer.
- Return only the updated fields of the student's snapshot in JSON format.
- Output format must match the partial StudentSnapshot model.
""",
            },
        ]

        if verbose:
            print("\n[DEBUG] Evaluating answer with the following prompt:")
            # Convert messages to a serializable format
            messages_serializable = [message.copy() for message in messages]
            if 'content' in messages[1]:
                messages_serializable[1]['content'] = messages[1]['content']
            print(json.dumps(messages_serializable, indent=2))

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
                print(updated_snapshot.model_dump_json(indent=2))
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
    # if questions:
    #     for idx, question in enumerate(questions, start=1):
    #         print(f"\nQuestion {idx}: {question.question_text}")
    #         for option in question.options:
    #             print(f"{option.option_label}. {option.option_text}")
    #         # Simulate student's answer (for testing, select 'A')
    #         student_answer = 'A'
    #         print(f"\nSimulated Student Answer: {student_answer}")

    #         # Test evaluate_answer
    #         print("\nTesting evaluate_answer...")
    #         updated_snapshot = llm.evaluate_answer(question, student_answer, snapshot, verbose=verbose)
    #         if updated_snapshot:
    #             # Update the snapshot with the returned changes
    #             snapshot = snapshot.copy(update=updated_snapshot.dict(exclude_unset=True))
    #             print("\n[DEBUG] Updated Student Snapshot:")
    #             print(snapshot.model_dump_json(indent=2))
    #         else:
    #             print("Failed to evaluate answer.")
    # else:
    #     print("Failed to generate questions.")
