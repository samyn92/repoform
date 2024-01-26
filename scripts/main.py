
from repoform.repository import RepositoryManager
from repoform.state import State

from repoform.app import RepoForm

repoform = RepoForm()

@repoform.data_from("data")
def modify_content(data):

    repo_name = "t5g-campus-1.refaz.bn"
    file_name = "apps/t5g/smf/t5g-smf_values.yaml"

    repo_manager: RepositoryManager = RepositoryManager.get(repo_name)

    branch_name = "feature/update-" + file_name.replace("/", "-")
    repo_manager.create_branch(branch_name)
    
    commit_message = f"Update {file_name}"

    updated_content = SmfApnDnn().render(data)

    repo_manager.update_file(file_name, updated_content, commit_message, branch_name)

    merge_request_title = "Update " + file_name
    repo_manager.create_or_update_merge_request(source_branch=branch_name, target_branch=repo_manager.branch, title=merge_request_title)


class SmfApnDnn(State):
    def __init__(self):
        super().__init__(self.template())

    @classmethod
    def template_v1(cls, data: dict):
        version = "v1"

        return {
            "apn": "apn",
            "dnn": "dnn"
        }