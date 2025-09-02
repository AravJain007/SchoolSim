import os
import random
from typing import Any, Dict, List

import numpy as np
from pymongo import MongoClient

from llm_provider.llm_call import LLMCall


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

    def ask_doubts(
        self,
        personalities: List[Dict[str, Any]],
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
