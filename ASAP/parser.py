from ASAP.student import StudentData


def add_students(students_data):
    female_students = []
    male_students = []
    for i in range(len(students_data)):
        if students_data.alcohol[i] == "Yes":
            alcohol = 1
        else:
            alcohol = 0
        sex = students_data.sex[i]
        student_data = {
            "matric": students_data.ID[i],
            "sex": sex,
            "country": students_data.country[i],
            "school": students_data.school[i],
            "sleep_pref": students_data.sleep[i],
            "suite_pref": students_data.suite_pref[i],
            "cleanliness_pref": students_data.cleanliness[i],
            "alcohol_pref": alcohol,
            "gender_pref": students_data.gender_pref[i],
        }
        new_student = StudentData(**student_data)
        if sex == "F":
            female_students.append(new_student)
        elif sex == "M":
            male_students.append(new_student)
        else:
            raise ValueError(f"Unrecognised gender: {sex}")
    return female_students, male_students