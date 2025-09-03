import asyncio
import json
from venv import create

from personality.classroom_service import ClassroomService
from personality.create_class_personalities import CreatePersonalities

classroom = ClassroomService()
create_personality = CreatePersonalities()


class TestPersonalityFolder:
    def test_get_classroom_details(self):
        output = classroom.get_classroom_details("SJT501", "Dr. B. Ashok")
        print(output)

    def test_create_personalities(self):
        classroom_details = classroom.get_classroom_details("SJT501", "Dr. B. Ashok")
        output = asyncio.run(create_personality.biography_creation(classroom_details))
        _ = create_personality.save_personality_prompt(output, "SJT501")
        print(output)
