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

    def create_branch(self, branch_name: str, ref: str = "main"):
        if not self.branch_exists:
            self.project.branches.create({"branch": branch_name, "ref": ref})
        

    def delete_branch(self, branch_name: str):
        branch = self.project.branches.get(branch_name)
        branch.delete()

    @property
    def branch_exists(self):
        try:
            self.project.branches.get(self.branch)
            return True
        except Exception:
            return False

    def create_or_update_merge_request(self, source_branch: str, target_branch: str, title: str, description: str = None):
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

        return mr
    
    def merge_merge_request(self, mr_id: int):
        mr = self.project.mergerequests.get(mr_id)
        if mr and mr.can_merge():
            mr.merge()
