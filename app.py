from flask import Flask, render_template, request
import sqlite3
from main import *
app = Flask(__name__)


def get_lessons():
    connection = sqlite3.connect('course.db')
    cursor = connection.cursor()

    sql_query = """
        SELECT 
            general_lesson_name
        FROM 
            courses
    """
    cursor.execute(sql_query)
    lessons = cursor.fetchall()
 
    lesson = [    ]
    for i in lessons:
        if i not in lesson:
            lesson.append(i)

    cursor.close()
    connection.close()

    return lesson

def transform_schedule_data(schedule):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    transformed = []
    for matrix in schedule:
        day_schedule = {day: times for day, times in zip(days, matrix)}
        transformed.append(day_schedule)
    return transformed

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selected_lessons = request.form.getlist('lessons[]')
        # Assuming main() is adapted to return data suitable for rendering
        schedule,lessons_names = main(selected_lessons)
        transformed_schedule = transform_schedule_data(schedule)
        return render_template('schedule.html', schedule=transformed_schedule,lessons_names=lessons_names)
    else:
        # Display the form to choose lessons
        lessons = get_lessons()
        return render_template('index.html', lessons=lessons)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
