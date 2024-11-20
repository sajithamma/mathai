#  Adaptive Learning System - mathai (മത്തായി)

An interactive, terminal-based adaptive learning system that generates personalized calculus questions for students, evaluates their answers, and updates their learning progress in real-time using OpenAI's GPT-4 API.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Dependencies](#dependencies)
- [Configuration](#configuration)
- [Known Issues](#known-issues)
- [Contributing](#contributing)
- [License](#license)

## Overview

This adaptive learning system is designed to provide a personalized learning experience for students studying calculus. It generates customized multiple-choice questions based on the student's performance, evaluates their answers, and updates their learning progress. The system uses OpenAI's GPT-4 API to generate questions and evaluate answers, and it employs a local SQLite database to store student data and question history.

## Features

- **Personalized Question Generation**: Generates questions tailored to the student's weak areas and desired difficulty level.
- **Real-Time Answer Evaluation**: Evaluates student answers and provides immediate feedback.
- **Adaptive Learning Progress**: Updates the student's learning snapshot based on their performance.
- **Terminal-Based Interface**: Provides an interactive command-line interface using the `curses` library.
- **Data Persistence**: Stores student snapshots, questions, and attempts in a local SQLite database.
- **Real-Time Debugging**: Displays real-time debug messages and logs during question generation and evaluation.

## Architecture

The system is composed of several components:

- **`main.py`**: The entry point of the application. Handles user interaction and orchestrates the flow.
- **`models.py`**: Defines the data models using Pydantic for type validation.
- **`llm.py`**: Interfaces with OpenAI's GPT-4 API to generate questions and evaluate answers.
- **`storage.py`**: Manages data persistence using SQLite.
- **`instructions.txt`**: Contains system instructions for the LLM.
- **`requirements.txt`**: Lists all the Python dependencies required for the project.

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/adaptive-learning-system.git
   cd adaptive-learning-system

2. **Create a Virtual Environment**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Set Up OpenAI API Key**

   - Create an account on [OpenAI](https://platform.openai.com/signup).
   - Generate an API key from the dashboard.
   - Set the `OPENAI_API_KEY` environment variable to your API key.

5. **Run the Application**

```bash
python main.py
```

Follow the on-screen prompts:

* Enter your username when prompted.
* Answer the generated multiple-choice questions by typing A, B, C, or D.
* Type exit at any prompt to quit the application.

# Project Structure
```css
├── main.py
├── models.py
├── llm.py
├── storage.py
├── instructions.txt
├── requirements.txt
└── README.md

```

* main.py: Contains the main loop and handles user interaction using the curses library.
* models.py: Defines data models like StudentSnapshot, Question, Option, etc., using Pydantic.
* llm.py: Contains the LLM base class and the OpenAILLM implementation.
* storage.py: Handles database initialization and CRUD operations for student snapshots, questions, and attempts.
* instructions.txt: Provides system instructions for the LLM to generate questions appropriately.
* requirements.txt: Lists all project dependencies.
* README.md: Documentation for the project.

# Dependencies

* Python 3.8+
* Pydantic 2.x
* OpenAI Python SDK
* SQLite3
* curses library (pre-installed on Unix-like systems)

