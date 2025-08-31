import asyncio
import json
import os
from typing import Dict, List

from pymongo import MongoClient
from pymongo.results import InsertManyResult

from llm_provider.llm_call import LLMCall
from personality.classroom_service import ClassroomService
from personality.creation_prompt import RESUME_BIOGRAPHY_CREATION
from pydantic_classes import ClassroomDetails, LLMCallInput, Provider


class CreatePersonalities:
    def __init__(
        self,
        mongo_uri: str = "mongodb://localhost:27017/",
    ):
        self.classroom_client = ClassroomService()
        self.llm_client = LLMCall()
        self.db_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

    def close_client(self):
        self.db_client.close()

    def save_personality_prompt(
        self,
        biography_prompts: List[Dict],
        collcetion: str,
        database_name: str = "personalities",
    ) -> InsertManyResult:
        """This function saves the personality of the user in the Mongo DB server

        Parameters
        ----------
            student_details: List[Dict]
                Details of all the students in a class to create personalities

        Returns
        -------
            InsertManyResults
                The IDs of the stored data
        """
        result = self.db_client[database_name][collcetion].insert_many(
            biography_prompts
        )
        return result

    async def biography_creation(
        self, classroom_details: ClassroomDetails
    ) -> List[Dict]:
        """Helper function to create biographies of the entire classroom

        Parameters
        ----------
            classroom_details: ClassroomDetails
                Details of the class

        Returns:
            List[Dict]
                List of names of student and their created biographies
        """
        prompt_for_student_biographies: List[LLMCallInput] = []
        # Create the biography of the student first
        for student_detail in classroom_details.students:
            user_prompt_to_gpt = RESUME_BIOGRAPHY_CREATION.format(
                resume_text=student_detail.resume_text
            )
            llm_input = LLMCallInput(
                user_prompt_to_llm=user_prompt_to_gpt,
                model_provider=Provider.LIGHTNING,
                model_name="lightning-ai/gpt-oss-20b",
                reasoning_effort="high",
            )
            prompt_for_student_biographies.append(llm_input)
        semaphores = asyncio.Semaphore(int(os.getenv("SEMAPHORE_COUNT")))
        llm_outputs = await asyncio.gather(
            *(
                self.llm_client.generate(prompt, semaphores)
                for prompt in prompt_for_student_biographies
            )
        )
        results = []
        for student, biography in zip(classroom_details.students, llm_outputs):
            print(biography.status)
            results.append(
                {
                    "name": student.name,
                    "classroom": student.info["classLocation"],
                    "professor_name": student.info["teacherName"],
                    "biography": biography.response,
                }
            )
        return results

    async def create_personalities(
        self, class_number: str, professor_name: str, limit: int = None
    ) -> InsertManyResult:
        """This function using the ClassroomService to get the students information from MongoDB

        Parameters
        ----------
            class_number: str
                Students class number used to query the DB
            professor_name: str
                Professors name used to query the DB

        Returns
        -------
            StudentDetails
                Output Dictionary which contains all the necessary information for the user to create a user personality
        """
        classroom_details = self.classroom_client.get_classroom_details(
            location=class_number, professor_name=professor_name, limit=limit
        )
        list_of_biographies = await self.biography_creation(classroom_details)
        return list_of_biographies
