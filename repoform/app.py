import os
import functools
import logging
import importlib
import difflib
from copy import deepcopy


from deepdiff import DeepDiff

from repoform.config import load_config
from repoform.loaders import DataLoaderType, YAMLFilesToListLoader, YAMLFilesToDictLoader
from repoform.repository import RepositoryManager
from repoform.repository import Branch
from repoform.repository import MergeRequest


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

        self.validate_functions = {}
        self.reconcile_functions = {}


    def load(self, modules_path: str, data_path: str, data_loader_type: str):
        try:
            config_path = os.getenv('REPOFORM_CONFIG', 'repoform_config.yaml')
            self.logger.info("Loading configuration from '%s'...", config_path)
            self.config = load_config(config_path)

            self.load_data(data_path, data_loader_type)
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
            self.logger.info("[SUCCESS] Configuration and data loaded successfully.")
            
        except Exception as e:
            self.logger.error("Error loading configuration: %s", str(e))
            raise
        else:
            self.logger.info("RepoForm initialized successfully.")


    def load_data(self, data_path: str, data_loader_type: str):
        self.logger.info("Loading repository data...")
        try:
            if data_loader_type == DataLoaderType.YAMLFilesToListLoader:
                self.data = YAMLFilesToListLoader.load_data(data_path)
            elif data_loader_type == DataLoaderType.YAMLFilesToDictLoader:
                self.data = YAMLFilesToDictLoader.load_data(data_path)
            else:
                raise NotImplementedError(f"Loader {data_loader_type} not implemented.")
        except FileNotFoundError as e:
            self.logger.error("Error loading data: %s", str(e))
            raise
        except Exception as e:
            self.logger.error("Unexpected error: %s", str(e))
            raise
        else:
            self.logger.info("[SUCCESS] Repository data loaded successfully.")
        
    def load_user_methods(self, directory: str):
        self.logger.info("Loading user-defined methods from '%s'...", directory)
        try:
            script_dir = os.path.join(os.getcwd(), directory)
            for filename in os.listdir(script_dir):
                if filename.endswith('.py') and filename != '__init__.py':
                    module_name = filename[:-3]  # Remove '.py' from filename
                    importlib.import_module(f"{directory}.{module_name}")
                    self.logger.debug("Loaded module '%s'", module_name)
            self.logger.info("[SUCCESS] User-defined methods loaded successfully.")
        except Exception as e:
            self.logger.error("Error loading user-defined methods: %s", str(e))
            raise


    def log_registered_items(self):

        if self.reconcile_functions:
            self.logger.info("Registered Reconcile Methods:")
            for key in self.reconcile_functions:
                self.logger.info(f"    {key}: {self.reconcile_functions[key]}")
        else:
            self.logger.info("No reconcile methods registered.")

        if RepositoryManager.instances:
            self.logger.info("Registered Repository Managers:")
            for repo_name, repo_manager in RepositoryManager.instances.items():
                self.logger.info(f"    {repo_name}: {repo_manager}")
        else:
            self.logger.info("No repository managers registered.")

        if self.data:
            self.logger.info("Registered Data:")
            self.logger.info(self.data)
        else:
            self.logger.info("No data registered.")                

    def validate(self, repo_name, glob):
        def decorator_validate(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            self.validate_functions[(repo_name, glob)] = wrapper
            return wrapper
        return decorator_validate
    

    def reconcile(self, repo, file):
        def decorator_reconcile(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                modified_content = func(*args, **kwargs)
                return modified_content
            self.reconcile_functions[(repo, file)] = wrapper
            return wrapper
        return decorator_reconcile

    def process_file(self, repo_name, file_name, method):
        self.logger.info("Processing file '%s' in repository '%s'...", file_name, repo_name)
        try:
            repo_manager = RepositoryManager.get(repo_name)
            if repo_manager is None:
                self.logger.error("No repository manager found for '%s'", repo_name)
                return None, None

            current_content = repo_manager.get_file_content(file_name, repo_manager.branch)
            content_copy = deepcopy(current_content)
            self.logger.debug("Current content of '%s' in '%s' retrieved", file_name, repo_name)

            updated_content = method(self.data, content_copy)

            diff = DeepDiff(current_content, updated_content, ignore_order=True)

            if diff:
                self.logger.info("Differences found in '%s' of '%s'", file_name, repo_name)
            else:
                self.logger.debug("No differences found in '%s' of '%s'", file_name, repo_name)

        except Exception as e:
            self.logger.error("Error processing file '%s' in repository '%s': %s", file_name, repo_name, str(e))
            raise
        else:
            self.logger.info("[SUCCESS] File processed successfully: '%s' in repository '%s'", file_name, repo_name)
            return updated_content, diff


    def plan_changes(self):
        self.logger.info("Planning changes...")
        try:
            planned_changes = {}

            for (repo_name, file_name), reconcile_method in self.reconcile_functions.items():
                self.logger.debug("Evaluating '%s' in '%s' for potential changes", file_name, repo_name)
                updated_content, diff = self.process_file(repo_name, file_name, reconcile_method)
                if updated_content is not None:
                    planned_changes[(repo_name, file_name)] = diff
                    self.logger.info("Planned changes for '%s' in '%s'", file_name, repo_name)

            for key, value in planned_changes.items():
                self.logger.debug("Planned changes for %s: %s", key, value)
        except Exception as e:
            self.logger.error("Error planning changes: %s", str(e))
            raise
        else:
            self.logger.info("[SUCCESS] Changes planned successfully.")
    

    def apply_changes(self):
        self.logger.info("Applying changes...")
        try:
            for (repo_name, file_name), modify_method in self.reconcile_functions.items():

                updated_content, diff = self.process_file(repo_name, file_name, modify_method)
                repo_manager = RepositoryManager.get(repo_name)
                if updated_content is not None and diff:
                    self.logger.info("Changes detected, updating file: %s in repo: %s", file_name, repo_name)

                    branch_name = "feature/update-" + file_name.replace("/", "-")
                    branch = Branch(repo_manager, branch_name)
                    if not branch.exists():
                        branch.create(ref=repo_manager.branch)
                    
                    commit_message = f"Edited {file_name} in {', '.join(diff.affected_root_keys)}"

                    repo_manager.update_file(file_name, updated_content, commit_message, branch_name)

                    merge_request_title = "Update " + file_name
                    merge_request = MergeRequest(repo_manager, source_branch=branch_name, target_branch=repo_manager.branch, title=merge_request_title)
                    merge_request.create_or_update()
                    self.logger.info("File '%s' in repository '%s' updated successfully.", file_name, repo_name)
                else:
                    self.logger.fino("No changes detected for file: %s in repo: %s", file_name, repo_name)
        except Exception as e:
            self.logger.error("Error applying changes: %s", str(e))
            raise
        else:
            self.logger.info("[SUCCESS] Changes applied successfully to all repositories.")
