from flask import Flask, render_template, request, redirect, jsonify
import pandas as pd
from datetime import datetime
import openai
import logging
import os
import json
from dotenv import load_dotenv
import traceback

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Initialize the conversation history
conversation = [
    {"role": "system", "content": "You are a helpful assistant."}
]

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
)
logger = logging.getLogger(__name__)

# Define file paths
TASKS_FILE = 'tasks.csv'
CATEGORIES_FILE = 'categories.csv'
priority_mapping = {'High': 1, 'Medium': 2, 'Low': 3}

# Initialize CSV files if they don't exist
def initialize_csv_files():
    try:
        tasks = pd.read_csv(TASKS_FILE)
        expected_columns = ["id", "task", "priority", "status", "due_date", "category"]
        if list(tasks.columns) != expected_columns:
            raise ValueError(f"Incorrect columns in {TASKS_FILE}. Expected {expected_columns}, got {list(tasks.columns)}")
    except (FileNotFoundError, ValueError):
        pd.DataFrame(columns=["id", "task", "priority", "status", "due_date", "category"]).to_csv(TASKS_FILE, index=False)
        logger.info(f"Initialized {TASKS_FILE} with columns ['id', 'task', 'priority', 'status', 'due_date', 'category']")

    try:
        categories = pd.read_csv(CATEGORIES_FILE)
        expected_columns = ["id", "category", "type"]
        if list(categories.columns) != expected_columns:
            raise ValueError(f"Incorrect columns in {CATEGORIES_FILE}. Expected {expected_columns}, got {list(categories.columns)}")
    except (FileNotFoundError, ValueError):
        pd.DataFrame(columns=["id", "category", "type"]).to_csv(CATEGORIES_FILE, index=False)
        logger.info(f"Initialized {CATEGORIES_FILE} with columns ['id', 'category', 'type']")

# Helper function to read tasks
def read_tasks():
    try:
        return pd.read_csv(TASKS_FILE)
    except Exception as e:
        logger.error(f"Error reading {TASKS_FILE}: {e}")
        return pd.DataFrame(columns=["id", "task", "priority", "status", "due_date", "category"])

# Helper function to read categories
def read_categories():
    try:
        return pd.read_csv(CATEGORIES_FILE)
    except Exception as e:
        logger.error(f"Error reading {CATEGORIES_FILE}: {e}")
        return pd.DataFrame(columns=["id", "category", "type"])

# Helper function to save tasks
def save_tasks(df):
    try:
        df.to_csv(TASKS_FILE, index=False)
        logger.info(f"Saved tasks to {TASKS_FILE}")
    except Exception as e:
        logger.error(f"Error saving to {TASKS_FILE}: {e}")

# Helper function to save categories
def save_categories(df):
    try:
        df.to_csv(CATEGORIES_FILE, index=False)
        logger.info(f"Saved categories to {CATEGORIES_FILE}")
    except Exception as e:
        logger.error(f"Error saving to {CATEGORIES_FILE}: {e}")

# Initialize CSV files on startup
initialize_csv_files()

# Route for the main page
@app.route("/")
def index():
    tasks = read_tasks()
    categories = read_categories()

    # Group categories by type
    grouped_categories = categories.groupby('type')['category'].apply(list).to_dict()

    # Prepare tasks grouped by type
    tasks_by_type = {}
    for type_, category_list in grouped_categories.items():
        tasks_in_category = tasks[tasks['category'].isin(category_list)].copy()
        # Map 'priority' to a sort key
        tasks_in_category['priority_order'] = tasks_in_category['priority'].map(priority_mapping)
        # Sort by 'priority_order'
        tasks_in_category = tasks_in_category.sort_values(by='priority_order')
        # Convert to dict and remove the 'priority_order' column
        tasks_by_type[type_] = tasks_in_category.drop(columns=['priority_order']).to_dict(orient='records')

    # Pass the full list of categories for the dropdown
    all_categories = categories.to_dict(orient='records')

    return render_template("index.html", tasks_by_type=tasks_by_type, all_categories=all_categories)

# Route to manage categories
@app.route("/categories")
def manage_categories():
    categories = read_categories()
    # Group categories by type, including all category data
    grouped_categories = categories.groupby('type').apply(lambda x: x.to_dict(orient='records')).to_dict()
    return render_template("categories.html", grouped_categories=grouped_categories)

# Route to add a new category
@app.route("/add_category", methods=["POST"])
def add_category():
    category = request.form.get("category").strip()
    type_ = request.form.get("type").strip()
    categories = read_categories()

    if not category or not type_:
        logger.warning("Category name or type missing in add_category request.")
        return redirect("/categories")

    # Check if category already exists
    if not categories[categories['category'].str.lower() == category.lower()].empty:
        logger.info(f"Category '{category}' already exists.")
        return redirect("/categories")

    # Automatically assign a new ID
    new_id = categories["id"].max() + 1 if not categories.empty else 1
    new_category = pd.DataFrame([[new_id, category, type_]], columns=["id", "category", "type"])
    categories = pd.concat([categories, new_category], ignore_index=True)

    save_categories(categories)
    logger.info(f"Added new category: {category} of type {type_}")
    return redirect("/categories")

# Route to add a new task
@app.route("/add", methods=["POST"])
def add_task():
    task = request.form.get("task", "").strip()
    priority = request.form.get("priority", "").strip()
    due_date = request.form.get("due_date", "").strip()
    category = request.form.get("category", "").strip()
    tasks = read_tasks()

    # Validate inputs
    if not task or not priority or not due_date or not category:
        logger.warning("Missing fields in add_task request.")
        return redirect("/")

    # Validate priority
    if priority not in priority_mapping:
        logger.warning(f"Invalid priority '{priority}' in add_task request.")
        return redirect("/")

    # Parse and validate the due date
    try:
        due_date = datetime.strptime(due_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        logger.warning(f"Invalid due date format '{due_date}' in add_task request.")
        due_date = ""

    new_id = tasks["id"].max() + 1 if not tasks.empty else 1
    new_task = pd.DataFrame([[new_id, task, priority, "Not Started", due_date, category]],
                            columns=["id", "task", "priority", "status", "due_date", "category"])

    tasks = pd.concat([tasks, new_task], ignore_index=True)
    save_tasks(tasks)
    logger.info(f"Added new task: {task}")
    return redirect("/")

# Route to delete a task
@app.route("/delete_task/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    tasks = read_tasks()
    if task_id not in tasks["id"].values:
        logger.warning(f"Tried to delete non-existent task ID {task_id}.")
        return redirect("/")
    
    tasks = tasks[tasks["id"] != task_id]
    save_tasks(tasks)
    logger.info(f"Deleted task ID {task_id}.")
    return redirect("/")

# Route to update the status of a task
@app.route("/update_status/<int:task_id>", methods=["POST"])
def update_status(task_id):
    new_status = request.form.get("status").strip()
    valid_statuses = ['Not Started', 'In Progress', 'Completed']
    tasks = read_tasks()

    if new_status not in valid_statuses:
        logger.warning(f"Invalid status '{new_status}' in update_status request.")
        return redirect("/")
    
    if task_id in tasks["id"].values:
        tasks.loc[tasks["id"] == task_id, "status"] = new_status
        save_tasks(tasks)
        logger.info(f"Updated status of task ID {task_id} to '{new_status}'.")
    else:
        logger.warning(f"Tried to update non-existent task ID {task_id}.")

    return redirect("/")

# Route to delete a single category
@app.route("/delete_category/<int:category_id>", methods=["POST"])
def delete_category(category_id):
    categories = read_categories()
    tasks = read_tasks()
    
    # Get the category name before deleting it
    category_row = categories[categories["id"] == category_id]
    if category_row.empty:
        logger.warning(f"Tried to delete non-existent category ID {category_id}.")
        return redirect("/categories")
    
    category_name = category_row["category"].values[0]
    
    # Delete the category
    categories = categories[categories["id"] != category_id]
    save_categories(categories)
    logger.info(f"Deleted category ID {category_id}: '{category_name}'.")
    
    # Delete tasks associated with the deleted category
    tasks = tasks[tasks["category"] != category_name]
    save_tasks(tasks)
    logger.info(f"Deleted all tasks associated with category '{category_name}'.")
    
    return redirect("/categories")

# Route to delete an entire category type
@app.route("/delete_type/<type_name>", methods=["POST"])
def delete_type(type_name):
    categories = read_categories()
    # Filter out all categories with the specified type
    categories = categories[categories["type"] != type_name]
    save_categories(categories)
    logger.info(f"Deleted all categories of type '{type_name}'.")
    return redirect("/categories")

# Route for the calendar page
@app.route("/calendar")
def calendar_view():
    tasks = read_tasks()

    # Prepare task data for the calendar
    events = []
    for _, row in tasks.iterrows():
        due_date = row.get('due_date', '')
        if pd.notnull(due_date) and due_date != '':
            try:
                # Ensure the due_date is in the correct format
                datetime.strptime(due_date, "%Y-%m-%d")
                event = {
                    'title': row['task'],
                    'start': due_date,
                    'id': row['id'],
                    'url': f"/task/{row['id']}"
                }
                events.append(event)
            except ValueError:
                # Skip tasks with invalid due_date format
                logger.warning(f"Invalid due date format '{due_date}' for task ID {row['id']}. Skipping event.")
                continue
    logger.info(f"Prepared {len(events)} calendar events.")
    return render_template("calendar.html", events=events)

# Route for task details
@app.route("/task/<int:task_id>")
def task_detail(task_id):
    tasks = read_tasks()
    task = tasks[tasks["id"] == task_id].to_dict(orient='records')
    if task:
        logger.info(f"Fetched details for task ID {task_id}.")
        return render_template("task_detail.html", task=task[0])
    else:
        logger.warning(f"Tried to access non-existent task ID {task_id}.")
        return "Task not found", 404

# Route for the assistant (chatbot) page
@app.route("/assistant")
def assistant():
    return render_template("assistant.html")

# Route to handle chatbot messages
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Add user message to conversation history
    conversation.append({"role": "user", "content": user_message})

    # Get response from OpenAI API
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=conversation
        )
        assistant_reply = response.choices[0].message.content

        # Add assistant reply to conversation history
        conversation.append({"role": "assistant", "content": assistant_reply})

        # Return the assistant's reply
        return jsonify({"response": assistant_reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
