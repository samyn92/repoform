from typing import Optional, List
from pydantic import BaseModel, ValidationError
import yaml



class ActionConfig(BaseModel):
    type: str
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    channel: Optional[str] = None
    message: Optional[str] = None

class RepositorySource(BaseModel):
    name: str
    project_id: int
    branch: str
    actions: List[ActionConfig] = []

class TmplformConfig(BaseModel):
    version: str
    gitlab_url: str
    repository_sources: List[RepositorySource]



def load_config(config_path: str) -> TmplformConfig:
    try:
        with open(config_path, 'r') as file:
            config_data = yaml.safe_load(file)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML file: {config_path} {e}")

    try:
        config = TmplformConfig.model_validate(config_data)
        return config
    except ValidationError as e:
        raise ValueError(f"Invalid configuration file: {e}")
