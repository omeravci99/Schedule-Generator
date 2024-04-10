
import pandas as pd
import sqlite3

# This function is used to setup the database and populate the time_slots table with pre-defined slots
def setup_database():
    conn = sqlite3.connect('course.db')
    cursor = conn.cursor()

    # Create tables for courses, time slots, and their relationships
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS courses (
            section_id INT PRIMARY KEY,
            section_name TEXT,
            general_lesson_name TEXT,
            must_count INT,
            credit INT
        );

        CREATE TABLE IF NOT EXISTS time_slots (
            time_id INT PRIMARY KEY,
            day_of_week VARCHAR(255),
            hour_of_day TIME
        );

        CREATE TABLE IF NOT EXISTS courses_time_slots (
            course_id INT,
            start_time_id INT,
            end_time_id INT,
            PRIMARY KEY (course_id, start_time_id, end_time_id),
            FOREIGN KEY (course_id) REFERENCES courses(section_id),
            FOREIGN KEY (start_time_id) REFERENCES time_slots(time_id),
            FOREIGN KEY (end_time_id) REFERENCES time_slots(time_id)
        );
    ''')

    # Ensure that the range includes 8:40 by starting at 8 and including necessary slots
    cursor.executescript('''
        INSERT OR IGNORE INTO time_slots (time_id, day_of_week, hour_of_day)
        VALUES ''' + ','.join([f"({i + 1}, '{day}', '{hour:02d}:40')" for i, (day, hour) in enumerate(
            [(day, hour) for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'] for hour in range(8, 21)])]) + ';'
    )

    conn.commit()
    return conn

# This function is used to process the course data from the Excel files
def process_course_data():
    i = 1000
    excel_files = ['Engineering','Language','Arhitecture','Aviation','SocialScience','AppliedScience','Business']
    courses = []
    courses_time_slots = []
    for files in excel_files:
        df = pd.read_excel(f'lessons/{files}.xlsx')
        for index, row in df.iterrows():
            time_data = str(row.iloc[10]).split("\n")
            if time_data[0] != 'nan':
                # This section is for courses table data
                day, hours = time_data[0].split("|")
                hour1, hour2 = hours.split("-")
                must_count = (len(time_data) - 1) * (int(hour2.split(":")[0])-int(hour1.split(":")[0]))
                courses.append((i, f"{row.iloc[0]}{row.iloc[1]}-{row.iloc[2]}", f"{row.iloc[0]}{row.iloc[1]}", must_count, row.iloc[5]))
                i += 1

                # This section is for courses_time_slots table data
                for item in filter(None, time_data):
                    item = item.split("|")
                    day, time = item[0].strip(), item[1].strip().split("-")
                    start_time_id = (['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma'].index(day) * 13) + int(time[0].split(":")[0]) - 7
                    end_time_id = (['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma'].index(day) * 13) + int(time[1].split(":")[0]) - 8
                    courses_time_slots.append((i-1, start_time_id, end_time_id))
            else:
                print("No time data found for this course", row.iloc[0], row.iloc[1], row.iloc[2])
            
    return courses, courses_time_slots

# This function is used to insert the course and course_time_slot data into the database
def main():
    conn = setup_database()
    courses,courses_time_slots = process_course_data()

    for course in courses:
        print("Inserting course with section_id:", course[0])
        try:
            conn.execute("INSERT INTO courses VALUES (?, ?, ?, ?, ?)", course)
            conn.commit()
        except sqlite3.IntegrityError as e:
            print(f"Failed to insert course with section_id {course[0]}: {e}")
            
    for course_time_slot in courses_time_slots:
        print("Inserting course_time_slot with course_id:", course_time_slot[0])
        try:
            conn.execute("INSERT INTO courses_time_slots VALUES (?, ?, ?)", course_time_slot)
            conn.commit()
        except sqlite3.IntegrityError as e:
            print(f"Failed to insert course_time_slot with course_id {course_time_slot[0]}: {e}")

if __name__ == '__main__':
    main()