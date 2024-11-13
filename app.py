from flask import Flask, render_template, request, redirect, jsonify, url_for
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Initialize an empty to-do list DataFrame
TODO_COLUMNS = ["Task", "Priority", "Status", "Due Date", "Category"]
todo_df = pd.DataFrame(columns=TODO_COLUMNS)

# Initialize a list of categories
categories = ["Work", "Personal", "Shopping"]

# Function to sort tasks by priority and due date
def sort_tasks(df):
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    df["Priority Rank"] = df["Priority"].map(priority_order)
    df["Due Date"] = pd.to_datetime(df["Due Date"], errors="coerce")
    df = df.sort_values(by=["Priority Rank", "Due Date"]).drop(columns=["Priority Rank"]).reset_index(drop=True)
    return df

# Route for the main page
@app.route("/")
def index():
    tasks = sort_tasks(todo_df).to_dict(orient="records")
    return render_template("index.html", tasks=tasks, categories=categories)

# Route to add a new task
@app.route("/add", methods=["POST"])
def add_task():
    global todo_df
    task = request.form.get("task")
    priority = request.form.get("priority")
    due_date = request.form.get("due_date")
    category = request.form.get("category")

    # Validate the date format
    try:
        due_date = datetime.strptime(due_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        due_date = ""

    if task.strip():
        new_task = pd.DataFrame([[task, priority, "Not Started", due_date, category]], columns=TODO_COLUMNS)
        todo_df = pd.concat([todo_df, new_task], ignore_index=True)
        todo_df = sort_tasks(todo_df)

    return redirect("/")

# Route to delete a task by index
@app.route("/delete/<int:index>", methods=["POST"])
def delete_task(index):
    global todo_df
    if 0 <= index < len(todo_df):
        todo_df = todo_df.drop(index).reset_index(drop=True)
    return redirect("/")

# Route to update the status of a task
@app.route("/update_status/<int:index>", methods=["POST"])
def update_status(index):
    global todo_df
    new_status = request.form.get("status")
    if 0 <= index < len(todo_df):
        todo_df.at[index, "Status"] = new_status
    return jsonify(success=True)

# Route for the Manage Categories page
@app.route("/categories")
def manage_categories():
    return render_template("categories.html", categories=categories)

# Route to add a new category
@app.route("/add_category", methods=["POST"])
def add_category():
    global categories
    new_category = request.form.get("category")
    if new_category and new_category not in categories:
        categories.append(new_category)
    return redirect("/categories")

# Route to delete a category
@app.route("/delete_category/<string:category>", methods=["POST"])
def delete_category(category):
    global categories, todo_df
    if category in categories:
        categories.remove(category)
        # Optionally, remove tasks with the deleted category
        todo_df = todo_df[todo_df["Category"] != category].reset_index(drop=True)
    return redirect("/categories")

# Run the app on localhost
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
