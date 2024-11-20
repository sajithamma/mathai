# main.py
import sys
from models import StudentSnapshot, QuestionAttempt, Question, Level
from llm import OpenAILLM
from storage import (
    init_db,
    save_snapshot_to_db,
    load_snapshot_from_db,
    save_question_to_db,
    save_attempt_to_db,
)
import os

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def main():
    init_db()
    llm = OpenAILLM()
    verbose = True  # Set to False to disable verbose mode

    print("Welcome to the Adaptive Learning System!")
    student_id = input("Please enter your username: ").strip()
    
    # Load or create student snapshot
    snapshot = load_snapshot_from_db(student_id)
    if snapshot:
        print(f"Welcome back, {student_id}!")
    else:
        print(f"Hello, {student_id}! Let's get started.")
        snapshot = StudentSnapshot(
            student_id=student_id,
            levels=[
                Level(name="logic_based", value=1),
                Level(name="real_life_based", value=1),
                Level(name="abstract_based", value=1)
            ],
            weak_areas=[],
            strong_areas=[],
            desired_difficulty_level=1,
            recent_history=[]
        )
        save_snapshot_to_db(snapshot)
    
    while True:
        # Clear the console
        clear_console()
        
        # Display current levels and scores
        print(f"Student ID: {snapshot.student_id}")
        # Convert levels to a dictionary for display
        levels_dict = {level.name: level.value for level in snapshot.levels}
        print(f"Current Levels: {levels_dict}")
        print(f"Desired Difficulty Level: {snapshot.desired_difficulty_level}")
        print(f"Weak Areas: {', '.join(snapshot.weak_areas) if snapshot.weak_areas else 'None'}")
        print(f"Strong Areas: {', '.join(snapshot.strong_areas) if snapshot.strong_areas else 'None'}")
        
        # Generate questions
        questions = llm.generate_questions(snapshot, verbose=verbose)
        
        if not questions:
            print("No questions generated. Exiting.")
            sys.exit(1)
        
        for question in questions:
            # Save the question to the database
            save_question_to_db(question)
            
            print(f"\nQuestion: {question.question_text}\n")
            for option in question.options:
                print(f"{option.option_label}. {option.option_text}")
            
            student_answer = input("\nYour answer (A/B/C/D or 'exit' to quit): ").strip().upper()
            if student_answer == 'EXIT':
                print("Exiting the program. Goodbye!")
                sys.exit(0)
            
            # Validate the answer
            valid_options = [opt.option_label.upper() for opt in question.options]
            if student_answer not in valid_options:
                print("Invalid option selected. Please try again.")
                continue  # Ask the same question again
            
            # Evaluate the answer
            updated_snapshot = llm.evaluate_answer(question, student_answer, snapshot, verbose=verbose)
            
            if updated_snapshot:
                # Merge the original snapshot with the updated snapshot
                snapshot_data = snapshot.dict()
                updated_data = updated_snapshot.dict()
                snapshot_data.update(updated_data)
                snapshot = StudentSnapshot.parse_obj(snapshot_data)
                save_snapshot_to_db(snapshot)
                
                # Find the selected option
                selected_option = next((opt for opt in question.options if opt.option_label.upper() == student_answer), None)
                if selected_option:
                    # Provide feedback to the student
                    print(f"\nExplanation: {selected_option.explanation}")
                    
                    # Create a QuestionAttempt and save it
                    is_correct = selected_option.is_correct
                    score = 1.0 if is_correct else 0.0
                    attempt = QuestionAttempt(
                        question_id=question.question_id,
                        topic=question.topic,
                        subtopic=question.subtopic,
                        criterion=question.criterion,
                        difficulty_level=question.difficulty_level,
                        student_answer=student_answer,
                        is_correct=is_correct,
                        score=score,
                        indicators=[]
                    )
                    save_attempt_to_db(snapshot.student_id, question.question_id, attempt)
                    
                    # Update recent history
                    snapshot.recent_history.append(attempt)
                    # Keep only the last 10 attempts
                    snapshot.recent_history = snapshot.recent_history[-10:]
                    save_snapshot_to_db(snapshot)
                else:
                    print("An error occurred while processing your answer.")
            else:
                print("Error evaluating the answer.")
            
            input("\nPress Enter to continue to the next question...")
        
        # Decide whether to continue or exit
        continue_choice = input("\nDo you want to continue? (yes/no): ").strip().lower()
        if continue_choice not in ['yes', 'y']:
            print("Thank you for using the Adaptive Learning System. Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
