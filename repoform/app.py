import os
import functools
import logging
import importlib

from repoform.repository import RepositoryManager
from repoform.utils import load_data

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
            self.logger.debug("Loading modules from '%s'...", modules_path)
            self.load_user_methods(modules_path)
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
                data = load_data(data_path)
                return func(data, *args, **kwargs)
            self.apply_methods.append(wrapper)
            return wrapper
        return decorator
    

    def load_repositories(self, repo_ids: list[str]):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                repositories = [RepositoryManager(repo_id) for repo_id in repo_ids]
                return func(*args, repositories=repositories, **kwargs)
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
