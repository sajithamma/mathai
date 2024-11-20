# main.py
import sys
import curses
from models import StudentSnapshot, QuestionAttempt, Question, Level
from llm import OpenAILLM
from storage import (
    init_db,
    save_snapshot_to_db,
    load_snapshot_from_db,
    save_question_to_db,
    save_attempt_to_db,
)

def display_snapshot(stdscr, snapshot):
    # Get terminal dimensions
    height, width = stdscr.getmaxyx()
    
    # Prepare snapshot information
    levels_dict = {level.name: level.value for level in snapshot.levels}
    levels_str = ', '.join(f"{k}: {v}" for k, v in levels_dict.items())
    weak_areas = ', '.join(snapshot.weak_areas) if snapshot.weak_areas else 'None'
    strong_areas = ', '.join(snapshot.strong_areas) if snapshot.strong_areas else 'None'
    
    # Construct the snapshot string
    snapshot_lines = [
        f"Student ID: {snapshot.student_id}",
        f"Desired Difficulty Level: {snapshot.desired_difficulty_level}",
        f"Levels: {levels_str}",
        f"Weak Areas: {weak_areas}",
        f"Strong Areas: {strong_areas}"
    ]
    
    # Display the snapshot at the top right
    y = 0
    for line in snapshot_lines:
        x = width - len(line) - 2  # Adjust the x-coordinate to right-align
        if x < 0:
            x = 0  # Prevent negative x-coordinate
        stdscr.addstr(y, x, line)
        y += 1

def main_curses(stdscr):
    # Initialize the database and LLM
    init_db()
    llm = OpenAILLM()
    verbose = False  # Set to False since we'll handle output via curses
    
    # Get the student's username
    stdscr.addstr("Welcome to the Adaptive Learning System!\n")
    stdscr.addstr("Please enter your username: ")
    stdscr.refresh()
    curses.echo()
    student_id = stdscr.getstr().decode('utf-8').strip()
    curses.noecho()
    
    # Load or create student snapshot
    snapshot = load_snapshot_from_db(student_id)
    if snapshot:
        welcome_message = f"Welcome back, {student_id}!"
    else:
        welcome_message = f"Hello, {student_id}! Let's get started."
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
    
    stdscr.clear()
    stdscr.addstr(0, 0, welcome_message)
    stdscr.refresh()
    curses.napms(1000)
    
    # Main loop
    while True:
        # Clear the screen
        stdscr.clear()
        
        # Display the student's snapshot at the top right
        display_snapshot(stdscr, snapshot)
        
        # Generate questions
        questions = llm.generate_questions(snapshot, verbose=verbose)
        
        if not questions:
            stdscr.addstr("No questions generated. Exiting.")
            stdscr.refresh()
            curses.napms(2000)
            break
        
        for question in questions:
            # Save the question to the database
            save_question_to_db(question)
            
            # Display the question
            stdscr.clear()
            display_snapshot(stdscr, snapshot)
            stdscr.addstr(5, 0, f"Question: {question.question_text}\n")
            option_y = 7  # Starting y-coordinate for options
            for option in question.options:
                stdscr.addstr(option_y, 0, f"{option.option_label}. {option.option_text}")
                option_y += 1
            
            # Prompt for the answer
            while True:
                stdscr.addstr(option_y + 1, 0, "Your answer (A/B/C/D or 'exit' to quit): ")
                stdscr.clrtoeol()
                stdscr.refresh()
                curses.echo()
                student_answer = stdscr.getstr().decode('utf-8').strip().upper()
                curses.noecho()
                
                if student_answer == 'EXIT':
                    stdscr.addstr(option_y + 2, 0, "Exiting the program. Goodbye!")
                    stdscr.refresh()
                    curses.napms(2000)
                    curses.endwin()
                    sys.exit(0)
                
                # Validate the answer
                valid_options = [opt.option_label.upper() for opt in question.options]
                if student_answer not in valid_options:
                    stdscr.addstr(option_y + 2, 0, "Invalid option selected. Please try again.")
                    stdscr.clrtoeol()
                    stdscr.refresh()
                    curses.napms(1500)
                    stdscr.move(option_y + 2, 0)
                    stdscr.clrtoeol()
                    continue  # Ask the same question again
                else:
                    break  # Valid answer provided; exit the input loop
            
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
                    stdscr.addstr(option_y + 2, 0, f"Explanation: {selected_option.explanation}")
                    stdscr.refresh()
                    curses.napms(3000)
                    
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
                    stdscr.addstr(option_y + 2, 0, "An error occurred while processing your answer.")
                    stdscr.refresh()
                    curses.napms(2000)
            else:
                stdscr.addstr(option_y + 2, 0, "Error evaluating the answer.")
                stdscr.refresh()
                curses.napms(2000)
            
            stdscr.addstr(option_y + 4, 0, "Press any key to continue to the next question...")
            stdscr.refresh()
            stdscr.getch()
        
        # Decide whether to continue or exit
        stdscr.addstr(option_y + 6, 0, "Do you want to continue? (yes/no): ")
        stdscr.clrtoeol()
        stdscr.refresh()
        curses.echo()
        continue_choice = stdscr.getstr().decode('utf-8').strip().lower()
        curses.noecho()
        
        if continue_choice not in ['yes', 'y']:
            stdscr.addstr(option_y + 7, 0, "Thank you for using the Adaptive Learning System. Goodbye!")
            stdscr.refresh()
            curses.napms(2000)
            break

if __name__ == "__main__":
    curses.wrapper(main_curses)
