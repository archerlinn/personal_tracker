from flask import Flask, render_template, request, redirect, jsonify
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Define file paths
TASKS_FILE = 'tasks.csv'
CATEGORIES_FILE = 'categories.csv'

# Initialize CSV files if they don't exist
def initialize_csv_files():
    try:
        tasks = pd.read_csv(TASKS_FILE)
        if list(tasks.columns) != ["id", "task", "priority", "status", "due_date", "category"]:
            raise ValueError("Incorrect columns in tasks.csv")
    except (FileNotFoundError, ValueError):
        pd.DataFrame(columns=["id", "task", "priority", "status", "due_date", "category"]).to_csv(TASKS_FILE, index=False)

    try:
        categories = pd.read_csv(CATEGORIES_FILE)
        if list(categories.columns) != ["id", "category", "type"]:
            raise ValueError("Incorrect columns in categories.csv")
    except (FileNotFoundError, ValueError):
        pd.DataFrame(columns=["id", "category", "type"]).to_csv(CATEGORIES_FILE, index=False)

# Helper function to read tasks
def read_tasks():
    try:
        return pd.read_csv(TASKS_FILE)
    except Exception:
        return pd.DataFrame(columns=["id", "task", "priority", "status", "due_date", "category"])

# Helper function to read categories
def read_categories():
    try:
        return pd.read_csv(CATEGORIES_FILE)
    except Exception:
        return pd.DataFrame(columns=["id", "category", "type"])

# Helper function to save tasks
def save_tasks(df):
    df.to_csv(TASKS_FILE, index=False)

# Helper function to save categories
def save_categories(df):
    df.to_csv(CATEGORIES_FILE, index=False)

# Initialize CSV files
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
        tasks_by_type[type_] = tasks[tasks['category'].isin(category_list)].to_dict(orient='records')

    # Pass the full list of categories for the dropdown
    all_categories = categories.to_dict(orient='records')

    return render_template("index.html", tasks_by_type=tasks_by_type, all_categories=all_categories)

@app.route("/categories")
def manage_categories():
    categories = read_categories()
    # Group categories by type
    grouped_categories = categories.groupby('type')['category'].apply(list).to_dict()
    return render_template("categories.html", grouped_categories=grouped_categories)

# Route to add a new category
@app.route("/add_category", methods=["POST"])
def add_category():
    category = request.form.get("category").strip()
    type_ = request.form.get("type").strip()
    categories = read_categories()

    if not category:
        return redirect("/categories")

    # Automatically assign a new ID
    new_id = categories["id"].max() + 1 if not categories.empty else 1
    new_category = pd.DataFrame([[new_id, category, type_]], columns=["id", "category", "type"])
    categories = pd.concat([categories, new_category], ignore_index=True)

    save_categories(categories)
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
        return redirect("/")

    # Parse and format the due date
    try:
        due_date = datetime.strptime(due_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        due_date = ""

    new_id = tasks["id"].max() + 1 if not tasks.empty else 1
    new_task = pd.DataFrame([[new_id, task, priority, "Not Started", due_date, category]],
                            columns=["id", "task", "priority", "status", "due_date", "category"])

    tasks = pd.concat([tasks, new_task], ignore_index=True)
    save_tasks(tasks)
    return redirect("/")


# Route to delete a task
@app.route("/delete_task/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    tasks = read_tasks()
    tasks = tasks[tasks["id"] != task_id]
    save_tasks(tasks)
    return redirect("/")

# Route to update the status of a task
@app.route("/update_status/<int:task_id>", methods=["POST"])
def update_status(task_id):
    new_status = request.form.get("status").strip()
    tasks = read_tasks()

    if task_id in tasks["id"].values:
        tasks.loc[tasks["id"] == task_id, "status"] = new_status
        save_tasks(tasks)

    return redirect("/")

# Route to delete a single category
@app.route("/delete_category/<int:category_id>", methods=["POST"])
def delete_category(category_id):
    categories = read_categories()
    categories = categories[categories["id"] != category_id]
    save_categories(categories)
    return redirect("/categories")

# Route to delete an entire category type
@app.route("/delete_type/<type_name>", methods=["POST"])
def delete_type(type_name):
    categories = read_categories()
    # Filter out all categories with the specified type
    categories = categories[categories["type"] != type_name]
    save_categories(categories)
    return redirect("/categories")

if __name__ == "__main__":
    app.run(debug=True)

