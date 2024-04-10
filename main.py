import sqlite3
import numpy as np
from tabulate import tabulate

# Modify this function to return the section mapping as well
def process_course_data(course_data):
    processed_data = {}
    must_count_values = {}
    section_name_mapping = {}  # Dictionary to store section name mappings

    for record in course_data:
        section_id, section_name, lesson_name, day_of_week, start_time, end_time, must_count = record
        unique_key = f"{section_name}_{lesson_name}"
        must_count_values[section_id] = must_count
        section_name_mapping[section_id] = section_name  # Store the mapping

        if unique_key not in processed_data:
            processed_data[unique_key] = {
                'ders_id': section_id,
                'section_name': section_name,
                'ders_adi': lesson_name,
                'saatler': {day_of_week: [start_time, end_time]},
                'must_count': must_count
            }
        else:
            processed_data[unique_key]['saatler'][day_of_week] = [start_time, end_time]

    return list(processed_data.values()), must_count_values, section_name_mapping

# Update the sql_handler function to capture the section name mapping
def sql_handler(lessons):
    all_courses = {}
    must_count_dict = {}
    section_name_mapping = {}
    
    with sqlite3.connect('course.db') as connection:
        cursor = connection.cursor()
        for lesson in lessons:
            try:
                cursor.execute("""
                    SELECT 
                        c.section_id, 
                        c.section_name, 
                        c.general_lesson_name, 
                        ts1.day_of_week, 
                        ts1.hour_of_day AS start_time,
                        ts2.hour_of_day AS end_time,
                        c.must_count
                    FROM 
                        courses AS c
                        JOIN courses_time_slots AS cts ON c.section_id = cts.course_id
                        JOIN time_slots AS ts1 ON cts.start_time_id = ts1.time_id
                        JOIN time_slots AS ts2 ON cts.end_time_id = ts2.time_id
                    WHERE 
                        c.general_lesson_name = ?
                """, (lesson,))
                data = cursor.fetchall()
                processed_data, must_count_values, temp_section_name_mapping = process_course_data(data)
                all_courses[lesson] = processed_data
                must_count_dict.update(must_count_values)
                section_name_mapping.update(temp_section_name_mapping)
            except sqlite3.DatabaseError as e:
                print(f"Database error: {e}")
            except Exception as e:
                print(f"General error: {e}")
    return all_courses, must_count_dict, section_name_mapping
# This function is used for creating constant scchedule which has one section 
def create_constant_schedule(lessons):
    constant_matrix = np.zeros((5, 13), dtype=int)
    for lesson in lessons:
        if len(lesson) == 1:
            current_lesson = lesson[0]
            for key in current_lesson['saatler']:
                for i in range(int(current_lesson['saatler'][key][0].split(":")[0]), int(current_lesson['saatler'][key][1].split(":")[0])+1):
                    if key == "Monday":
                        constant_matrix[0][i - 8] = current_lesson['ders_id']
                    elif key == "Tuesday":
                        constant_matrix[1][i - 8] = current_lesson['ders_id']
                    elif key == "Wednesday":
                        constant_matrix[2][i - 8] = current_lesson['ders_id']
                    elif key == "Thursday":
                        constant_matrix[3][i - 8] = current_lesson['ders_id']
                    elif key == "Friday":
                        constant_matrix[4][i - 8] = current_lesson['ders_id']        
    return constant_matrix

# This function is used to handle the lessons which has more than one section      
def onn_lesson_handler(all_matrix,lesson):
    all_matrix_copy = all_matrix.copy() 
    all_matrix.clear()
    for matrix in all_matrix_copy:
        for section in lesson:
            new_matrix = matrix.copy()
            current_lesson = section
            for key in current_lesson["saatler"]:
                for i in range(int(current_lesson["saatler"][key][0].split(":")[0]), int(current_lesson["saatler"][key][1].split(":")[0])+1):
                    if key == "Monday":
                        if matrix[0][i - 8] == 0:
                            new_matrix[0][i - 8] = current_lesson["ders_id"]
                    elif key == "Tuesday":
                        if matrix[1][i - 8] == 0:
                            new_matrix[1][i - 8] = current_lesson["ders_id"]
                    elif key == "Wednesday":
                        if matrix[2][i - 8] == 0:
                            new_matrix[2][i - 8] = current_lesson["ders_id"]
                    elif key == "Thursday":
                        if matrix[3][i - 8] == 0:
                            new_matrix[3][i - 8] = current_lesson["ders_id"]
                    elif key == "Friday":
                        if matrix[4][i - 8] == 0:
                            new_matrix[4][i - 8] = current_lesson["ders_id"]
                        
                    
            all_matrix.append(new_matrix)

# This function is used to check if the given matrix is valid or not
def valid_checker(all_matrix, must_count):
    valid_matrices = []
    for matrix in all_matrix:
        # Flatten the matrix and filter out zeros
        flattened = matrix.flatten()
        non_zeros = flattened[flattened != 0]

        # Count occurrences of each section ID in the flattened matrix
        counts = {}
        for section_id in non_zeros:
            if section_id in counts:
                counts[section_id] += 1
            else:
                counts[section_id] = 1

        # Check if all counts match the must_count values
        is_valid = all(counts.get(section_id, 0) == must_count.get(section_id, 0) for section_id in counts)

        # If the matrix is valid, add it to the list of valid matrices
        if is_valid:
            valid_matrices.append(matrix)

    return valid_matrices

# This function is used to print the possible schedules
def main(lessons):
    course_data, must_count, section_name_mapping = sql_handler(lessons)

    taken_courses = []
    for ders in course_data.values():
        taken_courses.append(ders)

    constant_matrix = create_constant_schedule(taken_courses)
    all_matrix = [constant_matrix]
    for lesson in taken_courses:
        onn_lesson_handler(all_matrix,lesson)

    valid_matrices = valid_checker(all_matrix,must_count)
    return valid_matrices, section_name_mapping



if __name__ == '__main__':
    lessons = ["MATH104","IE101","MATH211","CS105","PHYS102"]
    main(lessons)
