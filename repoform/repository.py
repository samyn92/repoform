import os
import gitlab

from repoform.utils import load_content_by_file_type, dump_content_by_file_type

class RepositoryManager:
    instances = {}

    def __init__(
        self,
        name: str,
        project_id: str,
        actions: list,
        branch: str = "main",
        gitlab_url: str = None
    ):
        gitlab_url = os.environ.get("GITLAB_URL", gitlab_url)
        private_token = os.environ.get("GITLAB_PRIVATE_TOKEN")
        if private_token is None:
            raise ValueError("Environment variable GITLAB_PRIVATE_TOKEN is not set")        
        self.gl = gitlab.Gitlab(gitlab_url, private_token=private_token)

        self.name = name
        self.project_id = project_id
        self.branch = branch
        self.actions = actions
        self.project = self.gl.projects.get(project_id)

        self.__class__.instances[name] = self

    def __repr__(self):
        return f"RepositoryManager({self.name})"

    @classmethod
    def get(cls, name: str):
        return cls.instances.get(name)

    def get_file_content(self, file_path: str, ref: str) -> str:
        file = self.project.files.get(file_path=file_path, ref=ref)
        raw_content = file.decode().decode("utf-8")
        return load_content_by_file_type(file_path, raw_content)

    def update_file(self, file_path: str, content: str, commit_message: str, branch: str = None):
        branch = branch or self.branch
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


class Branch:
    def __init__(self, repo_manager, branch_name):
        self.repo_manager = repo_manager
        self.branch_name = branch_name
        self.branch = None

    def create(self, ref='main'):
        """ Create a new branch from a reference (default is 'main'). """
        self.branch = self.repo_manager.project.branches.create({
            'branch': self.branch_name,
            'ref': ref
        })

    def exists(self):
        """ Check if the branch already exists in the repository. """
        try:
            self.branch = self.repo_manager.project.branches.get(self.branch_name)
            return True
        except Exception:
            return False

    def delete(self):
        """ Delete the branch from the repository. """
        if self.exists():
            self.branch.delete()



class MergeRequest:
    
    def __init__(self, repo_manager, title, source_branch, target_branch, description=None):
        self.repo_manager = repo_manager
        self.title = title
        self.source_branch = source_branch
        self.target_branch = target_branch
        self.description = description or ""
        self.mr = None

    def create_or_update(self):

        existing_mrs = self.repo_manager.project.mergerequests.list(
            source_branch=self.source_branch,
            target_branch=self.target_branch,
            state="opened"
        )

        if existing_mrs:

            self.mr = existing_mrs[0]
            self.mr.description = self.description
            self.mr.title = self.title
            self.mr.save()
        else:

            self.mr = self.repo_manager.project.mergerequests.create({
                'source_branch': self.source_branch,
                'target_branch': self.target_branch,
                'title': self.title,
                'description': self.description
            })

    def merge(self):
        if self.mr and self.mr.can_merge():
            self.mr.merge()
