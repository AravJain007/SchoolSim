from classroom_service import ClassroomService


def test_get_classroom_details():
    classroom = ClassroomService()
    output = classroom.get_classroom_details("SJT501")
    print(output)
