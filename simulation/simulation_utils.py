import asyncio
import os
import random
from typing import Any, Dict, List

from pymongo import MongoClient

from llm_provider.creation_prompt import SITUATION_PROMPT
from llm_provider.llm_call import LLMCall
from pydantic_classes import LLMCallInput, Provider, ReasoningEffort


class SimulationUtils:
    def __init__(self):
        self.db_client = MongoClient(os.getenv("MON"), serverSelectionTimeoutMS=5000)
        self.llm_client = LLMCall()

    def fetch_personalities_of_students(
        self, collection: str, database_name: str = "personalities"
    ) -> List[Dict[str, Any]]:
        """To return all the personalities of the students of a particular class.

        Parameters
        ----------
            collection: str
                Location of the classroom, which is used as a collection name
            database_name: str
                Name of the database where the user personalities are stored

        Returns
        -------
            Dict[str, str]
                A dictionary with a key value pair of name and personality
        """
        personalities: List[Dict[str, Any]] = list(
            self.db_client[database_name][collection].find()
        )
        return personalities

    async def ask_doubts(
        self,
        personalities: List[Dict[str, Any]],
        situation: str,
        no_of_students: int = 4,
    ) -> List[Dict[str, Any]]:
        """Randomly choses a `number_of_students` to ask a doubt to the teacher from the list of `personalities` provided to us

        Parameters
        ----------
            personalities: List[Dict[str, Any]]
                The personality prompt of all the students in the classroom
            no_of_students: int
                Number of students that will get an oppotunity to ask a doubt. Defaults to 4.

        Returns
        -------
            List[Dict[str, Any]]
                Contains the name of the student, their decision to ask a doubt and the doubt (if they choose to ask one)
        """
        chosen_students = random.sample(personalities, no_of_students)
        prompts = []
        for student in chosen_students:
            developer_message = student["prompt"]
            user_message = SITUATION_PROMPT.format(
                name=student["prompt"], situation_description=situation
            )
            message_to_llm = LLMCallInput(
                developer_prompt_provided=True,
                developer_prompt_to_llm=developer_message,
                user_prompt_to_llm=user_message,
                model_provider=Provider.LIGHTNING,
                model_name="lightning-ai/gpt-oss-20b",
                reasoning_effort=ReasoningEffort.HIGH,
            )
            prompts.append(message_to_llm)
        semaphore_count = os.getenv("SEMAPHORE_COUNT")
        if semaphore_count is not None:
            semaphore = asyncio.Semaphore(int(semaphore_count))
            student_doubts = await asyncio.gather(
                *(self.llm_client.generate(prompt, semaphore) for prompt in prompts)
            )
        else:
            student_doubts = await asyncio.gather(
                *(self.llm_client.generate(prompt, semaphore) for prompt in prompts)
            )
        return [
            {
                "student_name": student["name"],
                "student_doubt_dict": student_doubt.response,
            }
            for student, student_doubt in zip(chosen_students, student_doubts)
        ]
