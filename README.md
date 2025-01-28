# Personal Tracker

## Overview

I built a personal tracker web application designed to help users monitor and manage their tasks and categories efficiently.

## Features

- **Task Management**: Create, update, and delete tasks.
- **Category Organization**: Assign tasks to specific categories for better organization.
- **Calendar Integration**: Visualize the due dates of tasks on their calendar tab.
- **Data Persistence**: Store tasks and categories in CSV files for simplicity and portability.

## Technologies Used

- **Python**: Backend logic.
- **HTML, JS, and CSS**: Frontend structure and styling.

## Getting Started

### Prerequisites

- Python 3.x installed on your system.

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/archerlinn/personal_tracker.git
   cd personal_tracker
   ```

2. **Set Up Virtual Environment** (Optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

3. **Install Dependencies**:
   - Ensure you have the necessary Python packages installed. If a `requirements.txt` file is present:
     ```bash
     pip install -r requirements.txt
     ```

### Configuration

- **Environment Variables**:
  - Create a `.env` file in the root directory with necessary configurations. For example:
    ```
    FLASK_APP=app.py
    FLASK_ENV=development
    ```

### Running the Application

1. **Start the Flask Application**:
   ```bash
   flask run
   ```
   The application will be accessible at `http://127.0.0.1:5000/`.

## Usage

- Navigate to the homepage to view your tasks.
- Use the interface to add new tasks, assign them to categories, and manage existing tasks.

## File Structure

- `app.py`: Main application file.
- `templates/`: Contains HTML templates.
- `static/`: Contains static files like CSS.
- `instance/`: Contains instance-specific files, such as the SQLite database (if used).
- `categories.csv` and `tasks.csv`: CSV files storing category and task data, respectively.

## Future Improvements

Integrate a chatbot that can directly manage your tasks based on NLP

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your proposed changes.
