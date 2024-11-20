# llm.py
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List
from models import StudentSnapshot, Question, QuestionAttempt, QuestionsResponse, Level
import json
import sys  # Add this at the top of llm.py


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
            print("\n[DEBUG] Generating questions...please wait.")
            # Convert messages to a serializable format
            messages_serializable = [message.copy() for message in messages]
            if 'content' in messages[1]:
                messages_serializable[1]['content'] = messages[1]['content']
            #print(json.dumps(messages_serializable, indent=2))

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
                print("\n[DEBUG] Questions Generated")
                # for q in questions:
                #     print(q.model_dump_json(indent=2))
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
            - Return the full updated StudentSnapshot in JSON format.
            - Output format must match the StudentSnapshot model.
            """,
        },
    ]
        

        if verbose:
            print("\n[DEBUG] Evaluating answer")
            # Convert messages to a serializable format
            messages_serializable = [message.copy() for message in messages]
            if 'content' in messages[1]:
                messages_serializable[1]['content'] = messages[1]['content']
            #print(json.dumps(messages_serializable, indent=2))

        try:
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=messages,
                response_format=StudentSnapshot,
            )

            # Access and parse the response
            updated_snapshot = completion.choices[0].message.parsed
            #print(updated_snapshot)
            if verbose:
                print("\n[DEBUG] Updated snapshot:")
                #print(updated_snapshot.model_dump_json(indent=2))
            return updated_snapshot
        except Exception as e:
            print(f"Error during answer evaluation: {e}")
            return None

if __name__ == '__main__':
    # Initialize the OpenAILLM instance
    llm = OpenAILLM()
    verbose = True  # Set to False to reduce output

    # Parse command line arguments
    args = sys.argv[1:]  # Get the arguments after the script name

    # Create a sample StudentSnapshot
    snapshot = StudentSnapshot(
    student_id="test_student",
    levels=[
        Level(name="logic_based", value=2),
        Level(name="real_life_based", value=2),
        Level(name="abstract_based", value=2)
    ],
    weak_areas=["Chain Rule", "Implicit Differentiation"],
    strong_areas=["Basic Differentiation"],
    desired_difficulty_level=2,
    recent_history=[]
)

    if args[0] == 'generate':
        # Test generate_questions
        print("Testing generate_questions...")
        questions = llm.generate_questions(snapshot, verbose=verbose)
        if questions:
            # (Optional) print or process the generated questions
            pass
        else:
            print("Failed to generate questions.")

    if args[0] == 'evaluate':
        # Test evaluate_answer using the provided sample question
        print("Testing evaluate_answer...")
        # Sample question JSON (as provided)
        sample_question_json = '''
        {
          "question_id": "Q3",
          "question_text": "Given f(x) = sin(x^2), find f'(x) using the chain rule.",
          "options": [
            {
              "option_label": "A",
              "option_text": "f'(x) = 2x cos(x^2)",
              "is_correct": true,
              "explanation": "Correct. Using chain rule, derivative of sin(u) is cos(u) * du/dx where u = x^2, thus derivative is 2x cos(x^2)."
            },
            {
              "option_label": "B",
              "option_text": "f'(x) = cos(x^2)",
              "is_correct": false,
              "explanation": "Incorrect. This incorrectly omits the derivative of the inner function x^2."
            },
            {
              "option_label": "C",
              "option_text": "f'(x) = -2x cos(x^2)",
              "is_correct": false,
              "explanation": "Incorrect sign; the differentiation process should not introduce a negative sign here."
            },
            {
              "option_label": "D",
              "option_text": "f'(x) = 2 cos(x^2)",
              "is_correct": false,
              "explanation": "Incorrect. Missing the multiplier x from the chain rule application."
            }
          ],
          "topic": "Differentiation",
          "subtopic": "Chain Rule",
          "criterion": "logic_based",
          "difficulty_level": 2
        }
        '''
        # Parse the sample question JSON into a Question object
        sample_question = Question.model_validate_json(sample_question_json)

        # Display the question
        print(f"\nQuestion: {sample_question.question_text}")
        for option in sample_question.options:
            print(f"{option.option_label}. {option.option_text}")

        # Simulate student's answer (for testing)
        student_answer = 'A'  # You can change this as needed
        print(f"\nSimulated Student Answer: {student_answer}")

        # Test evaluate_answer
        updated_snapshot = llm.evaluate_answer(sample_question, student_answer, snapshot, verbose=verbose)
        if updated_snapshot:
            # Merge the original snapshot data with the updated data
            snapshot_data = snapshot.dict()
            updated_data = updated_snapshot.dict()
            snapshot_data.update(updated_data)
            
            # Re-parse the combined data into a StudentSnapshot instance
            snapshot = StudentSnapshot.parse_obj(snapshot_data)
            
            print("\n[DEBUG] Updated Student Snapshot:")
            print(snapshot.model_dump_json(indent=2))
        else:
            print("Failed to evaluate answer.")

    if args and args[0] not in ['generate', 'evaluate']:
        print("Usage: python llm.py [generate|evaluate]")
