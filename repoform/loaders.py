import os
import enum

import yaml

class DataLoaderType(enum.Enum):
    YAMLFilesToListLoader = "YAMLFilesToListLoader"
    YAMLFilesToDictLoader = "YAMLFilesToDictLoader"

class YAMLFilesToListLoader:

    @staticmethod
    def load_data(directory_path: str) -> list[dict]:

        data = []
        for filename in os.listdir(directory_path):
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                file_path = os.path.join(directory_path, filename)
                with open(file_path, 'r') as file:
                    file_data = yaml.safe_load(file)
                    if isinstance(file_data, dict):
                        data.append(file_data)

        return data


class YAMLFilesToDictLoader:

    @staticmethod
    def load_data(directory_path: str) -> dict:
        data = {}
        for filename in os.listdir(directory_path):
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                file_path = os.path.join(directory_path, filename)
                with open(file_path, 'r') as file:
                    file_data = yaml.safe_load(file)
                    if isinstance(file_data, dict):
                        key = os.path.splitext(filename)[0]  # Using filename (without extension) as key
                        data[key] = file_data
        return data