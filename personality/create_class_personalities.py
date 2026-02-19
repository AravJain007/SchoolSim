import os
from typing import Dict, List, Optional

from pymongo import MongoClient
from pymongo.results import InsertManyResult

from llm_provider.creation_prompt import CHARACTER_IMPERSONATION_PROMPT
from personality.classroom_service import ClassroomService
from pydantic_classes import ClassroomDetails


class CreatePersonalities:
    def __init__(self):
        self.classroom_client = ClassroomService()
        self.db_client = MongoClient(
            os.getenv("MONGO_SERVER"), serverSelectionTimeoutMS=5000
        )

    def close_client(self):
        self.db_client.close()

    def save_personality_prompt(
        self,
        personality_prompts: List[Dict],
        collection: str,
        database_name: str = "personalities",
    ) -> InsertManyResult:
        """Save personality prompts to MongoDB.

        Parameters
        ----------
            personality_prompts: List[Dict]
                Personality prompt dicts for each student
            collection: str
                MongoDB collection name
            database_name: str
                MongoDB database name

        Returns
        -------
            InsertManyResult
                The IDs of the stored data
        """
        result = self.db_client[database_name][collection].insert_many(
            personality_prompts
        )
        return result

    def build_personality_prompts(
        self, classroom_details: ClassroomDetails
    ) -> List[Dict]:
        """Build personality prompts for all students using only Big5 personality data.

        Parameters
        ----------
            classroom_details: ClassroomDetails
                Details of the class

        Returns
        -------
            List[Dict]
                List of dicts with student info and their personality prompt
        """
        results = []
        for student_detail in classroom_details.students:
            results.append(
                {
                    "name": student_detail.name,
                    "college_id": student_detail.college_id,
                    "classroom": student_detail.info["classLocation"],
                    "professor_name": student_detail.info["teacherName"],
                    "prompt": CHARACTER_IMPERSONATION_PROMPT.format(
                        name=student_detail.name,
                        big5_personality_text=student_detail.personality_text,
                    ),
                }
            )
        return results

    async def create_personalities(
        self, class_number: str, professor_name: str, limit: Optional[int] = None
    ) -> List[Dict]:
        """Fetch students from MongoDB and build their personality prompts.

        Parameters
        ----------
            class_number: str
                Students class number used to query the DB
            professor_name: str
                Professors name used to query the DB
            limit: Optional[int]
                Maximum number of students to process

        Returns
        -------
            List[Dict]
                List of dicts with student info and personality prompt
        """
        classroom_details = self.classroom_client.get_classroom_details(
            location=class_number, professor_name=professor_name, limit=limit
        )
        return self.build_personality_prompts(classroom_details)
