**repoform** is an orchestration framework designed to streamline the management of multi-repository environments within GitOps workflows. By automating complex processes and integrating actions across numerous repositories, repoform ensures a seamless and error-free deployment experience. Currently, repoform is optimized for environments using GitLab, as it leverages the GitLab API for repository operations. Other 

## Key Features

- **Multi-Repo Management**: Synchronize and manage changes across multiple repositories with ease.
- **GitOps Principles Alignment**: Adheres to GitOps practices, providing transparent, auditable, and declarative configurations.
- **Flexibility & Extensibility**: Tailors to diverse IT operations, from straightforward deployments to intricate multi-cluster configurations.
- **Automation & Efficiency**: Minimizes manual tasks with automated processes, freeing teams to focus on innovation.
- **Integrated Validation & Reconciliation**: Guarantees configuration consistency and correctness across all repositories.

## Ideal Use Cases

- Teams implementing or enhancing GitOps practices.
- Complex environments with multi-repository structures.
- Organizations aiming to automate and optimize IT operations.
- DevOps teams seeking higher efficiency and reduced errors in deployment processes.

## Quick Start

Define your ```repoform-config.yaml```

```yaml
version: "1.0"

gitlab_url: "https://gitlab.example.com"
repository_sources:
  - name: "example-repo"
    project_id: "12345"
    branch: "main"
    actions: [...]
```

Define your high level data under ```data/<file-name>.yaml```

```yaml
nginx_replicas: 3
```

Define user methods to do changes on specified repositories under ```scripts/<file-name>.py```

```python
from repoform import RepoForm

repoform = RepoForm()

@repoform.reconcile(repo="prod-1", file="apps/nginx/nginx-values.yaml")
def modify_nginx_values(data, file_content: dict):
    """
    Modifies the configuration of an Nginx deployment in a given YAML file.

    This function updates the number of replicas for the Nginx deployment
    based on the provided data. It expects the 'nginx_replicas' field in the
    'data' dictionary to determine the new replica count.

    Parameters:
    data (dict): A dictionary containing various configuration parameters.
                 Expected to contain the 'nginx_replicas' key with an integer value.
    file_content (dict): The current content of the nginx-values.yaml file
                         represented as a dictionary. This content will be modified.

    Returns:
    dict: The updated content of the nginx-values.yaml file.
    """
    # Update the number of replicas
    file_content["replicaCount"] = data["nginx_replicas"]

    return file_content
```

### Running in GitLab CI/CD Pipeline

```yaml
image: ghcr.io/samyn92/repoform:0.1.0-beta

stages:
  - plan
  - apply

plan_changes:
  stage: plan
  script:
    - export PYTHONPATH="${PYTHONPATH}:/scripts"
    - repoform plan scripts data

apply_changes:
  stage: apply
  when: manual
  script:
    - export PYTHONPATH="${PYTHONPATH}:/scripts"
    - repoform apply scripts data
```


```log
$ repoform plan scripts data
repoform.app - INFO - Loading configuration from 'repoform_config.yaml'...
repoform.app - INFO - Loading repository data...
repoform.app - INFO - [SUCCESS] Repository data loaded successfully.
repoform.app - INFO - Loading user-defined methods from 'scripts'...
repoform.app - INFO - [SUCCESS] User-defined methods loaded successfully.
repoform.app - INFO - [SUCCESS] Configuration and data loaded successfully.
repoform.app - INFO - RepoForm initialized successfully.
repoform.app - INFO - Planning changes...
repoform.app - INFO - Processing file 'apps/nginx/nginx_values.yaml' in repository 'prod-1'...
repoform.app - INFO - Differences found in 'apps/nginx/nginx_values.yaml' of 'prod-1'
repoform.app - INFO - [SUCCESS] File processed successfully: 'apps/nginx_values.yaml' in repository 'prod-1'
repoform.app - INFO - Planned changes for 'apps/nginx/nginx_values.yaml' in 'prod-1'
repoform.app - INFO - [SUCCESS] Changes planned successfully.
Planning done!
```

```log
$ repoform apply scripts data
repoform.app - INFO - Loading configuration from 'repoform_config.yaml'...
repoform.app - INFO - Loading repository data...
repoform.app - INFO - [SUCCESS] Repository data loaded successfully.
repoform.app - INFO - Loading user-defined methods from 'scripts'...
repoform.app - INFO - [SUCCESS] User-defined methods loaded successfully.
repoform.app - INFO - [SUCCESS] Configuration and data loaded successfully.
repoform.app - INFO - RepoForm initialized successfully.
repoform.app - INFO - Applying changes...
repoform.app - INFO - Processing file 'apps/nginx/nginx_values.yaml' in repository 'pod-1'...
repoform.app - INFO - Differences found in 'apps/nginx/nginx_values.yaml' of 'pod-1'
repoform.app - INFO - [SUCCESS] File processed successfully: 'apps/nginx/nginx_values.yaml' in repository 'pod-1'
repoform.app - INFO - Changes detected, updating file: apps/nginx/nginx_values.yaml in repo: pod-1
repoform.app - INFO - File 'apps/nginx/nginx_values.yaml' in repository 'pod-1' updated successfully.
repoform.app - INFO - [SUCCESS] Changes applied successfully to all repositories.
Changes done!
```