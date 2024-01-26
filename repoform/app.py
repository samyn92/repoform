import os
import functools
import logging
import importlib
import difflib
from copy import deepcopy


from deepdiff import DeepDiff

from repoform.config import load_config
from repoform.loaders import YAMLFilesToDictLoader
from repoform.repository import RepositoryManager

def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


@singleton
class RepoForm:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.validate_methods = {}
        self.apply_methods = []


    def load(self, modules_path: str):
        try:
            config_path = os.getenv('REPOFORM_CONFIG', 'repoform_config.yaml')
            self.logger.debug("Loading configuration from '%s'...", config_path)
            self.config = load_config(config_path)
            self.logger.debug("Loading modules from '%s'...", modules_path)
            self.load_user_methods(modules_path)

            for repo_source in self.config.repository_sources:
                self.logger.debug("Initializing repository manager for %s", repo_source.name)
                RepositoryManager(
                    name=repo_source.name,
                    project_id=repo_source.project_id,
                    actions=repo_source.actions,
                    branch=repo_source.branch,
                    gitlab_url=self.config.gitlab_url
                )
            
        except Exception as e:
            self.logger.error("[FAIL] Repoform initialization failed: %s", str(e))
            raise
        else:
            self.logger.info("[SUCCESS] RepoForm initialized successfully.")
            
        
    def load_user_methods(self, directory: str):
        self.logger.debug("Loading user-defined methods from '%s'...", directory)
        script_dir = os.path.join(os.getcwd(), directory)
        for filename in os.listdir(script_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = filename[:-3]  # Remove '.py' from filename
                importlib.import_module(f"{directory}.{module_name}")
                self.logger.debug("Loaded module '%s'", module_name)
        self.logger.debug("[SUCCESS] User-defined methods loaded successfully.")

    def validate(self, data_path: str):
        def decorator_validate(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            self.validate_methods.append(data_path)
            return wrapper
        return decorator_validate
    
    
    def data_from(self, data_path: str):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                data = YAMLFilesToDictLoader.load_data(data_path)
                return func(data, *args, **kwargs)
            self.apply_methods.append(wrapper)
            return wrapper
        return decorator
    

    def apply_changes(self):
        self.logger.info("Applying changes...")
        try:
            for method in self.apply_methods:
                method()
        except Exception as e:
            self.logger.error("[FAIL] Error applying changes: %s", str(e))
            raise
        else:
            self.logger.info("[SUCCESS] Changes applied successfully to all repositories.")
