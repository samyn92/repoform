import os
import logging

import gitlab

from repoform.utils import load_content_by_file_type, dump_content_by_file_type


class RepositoryManager:
    instances = {}

    def __init__(
        self,
        project_id: str
    ):
        self.logger = logging.getLogger(__name__)

        gitlab_url = os.environ.get("GITLAB_URL")
        if gitlab_url is None:
            raise ValueError("Environment variable GITLAB_URL is not set")
        private_token = os.environ.get("GITLAB_PRIVATE_TOKEN")
        if private_token is None:
            raise ValueError("Environment variable GITLAB_PRIVATE_TOKEN is not set")      
        self.gl = gitlab.Gitlab(gitlab_url, private_token=private_token)

        self.project_id = project_id
        self.project = self.gl.projects.get(project_id)
        self.name = self.project.name

        self.__class__.instances[project_id] = self

    def __repr__(self):
        return f"Repository({self.project_id},{self.name})"

    @classmethod
    def get(cls, project_id: str):
        if project_id not in cls.instances:
            return cls(project_id)
        else:
            return cls.instances.get(project_id)

    def get_file_content(self, file_path: str, ref: str) -> str:
        file = self.project.files.get(file_path=file_path, ref=ref)
        raw_content = file.decode().decode("utf-8")
        return load_content_by_file_type(file_path, raw_content)

    def update_file(self, file_path: str, content: str, commit_message: str, branch: str):
        self.logger.info(f"Updating file {file_path} in {self.name}...")
        stringified_content = dump_content_by_file_type(file_path, content)
        file = self.project.files.get(file_path=file_path, ref=branch)
        file.content = stringified_content
        file.save(branch=branch, commit_message=commit_message)

    def create_file(self, file_path: str, content: str, commit_message: str, branch: str = None):
        branch = branch or self.branch
        self.project.files.create(
            {
                "file_path": file_path,
                "branch": branch,
                "content": content,
                "commit_message": commit_message,
            }
        )

    def create_branch(self, branch_name: str, ref: str = "main"):

        if not self.branch_exists(branch_name):
            self.logger.info(f"Creating branch {branch_name} from {ref}...")
            self.project.branches.create({"branch": branch_name, "ref": ref})
        else:
            self.logger.info(f"Branch {branch_name} already exists")
        

    def delete_branch(self, branch_name: str):
        branch = self.project.branches.get(branch_name)
        branch.delete()


    def branch_exists(self, branch_name: str):
        try:
            self.branch = self.project.branches.get(branch_name)
            return True
        except Exception:
            return False



    def create_or_update_merge_request(self, source_branch: str, target_branch: str, title: str, description: str = None):
        self.logger.info(f"Creating merge request from {source_branch} to {target_branch}...")
        existing_mrs = self.project.mergerequests.list(
            source_branch=source_branch,
            target_branch=target_branch,
            state="opened"
        )

        if existing_mrs:
            mr = existing_mrs[0]
            mr.description = description
            mr.title = title
            mr.save()
        else:
            mr = self.project.mergerequests.create({
                'source_branch': source_branch,
                'target_branch': target_branch,
                'title': title,
                'description': description
            })
        
        self.logger.info(f"Merge request created: {mr.web_url}")
        return mr
    
    def merge_merge_request(self, mr_id: int):
        mr = self.project.mergerequests.get(mr_id)
        if mr and mr.can_merge():
            mr.merge()
