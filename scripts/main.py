
from repoform.repository import RepositoryManager
from repoform.state import State

from repoform.app import RepoForm

from copy import deepcopy
from deepdiff import DeepDiff

repoform = RepoForm()

@repoform.data_from("data_campusm")
def reconcile_customer(data):

    repo_name = "t5g-campus-1.refaz.bn"
    file_name = "apps/t5g/smf/t5g-smf_values.yaml"

    repo_manager: RepositoryManager = RepositoryManager.get(repo_name)

    state = SmfApnDnn.template(data)
    
    current_content = repo_manager.get_file_content(file_name, repo_manager.branch)

    new_content = deepcopy(current_content)
    new_content["app"]["config"]["apn_dnn"] = state

    diff = DeepDiff(current_content, new_content, ignore_order=True)

    if diff:
        # print(diff)
        branch_name = "feature/update-" + file_name.replace("/", "-")
        repo_manager.create_branch(branch_name)
        
        commit_message = f"Update {file_name}"

        print(f"Updating {file_name} in {repo_name}...")
        repo_manager.update_file(file_name, new_content, commit_message, branch_name)

        print(f"Creating merge request for {file_name} in {repo_name}...")
        merge_request_title = "Update " + file_name
        mr = repo_manager.create_or_update_merge_request(source_branch=branch_name, target_branch="main", title=merge_request_title)

        print(mr.web_url)


class SmfApnDnn(State):
    def __init__(self):
        super().__init__(self.template())

    @classmethod
    def template(cls, data: dict):

        apn_dnn_list = []
        ippools = []

        for customer in data.values():

            template_version = customer.get('template')
            if template_version == "campus-m/v0":
                customer['ip_pool_name'] = f"IpPool_{customer['dnn_name']}"
                customer['ip_network'] = customer['ip_pool'].split("/")[0]
                customer['ip_mask'] = int(customer['ip_pool'].split("/")[1])

                apn_dnn = cls.v0_template_apn_dnn(**customer)
                ip_pool = cls.v0_template_ip_pool(**customer)
            else:
                raise ValueError(f"No template found for version {template_version}")
            
            apn_dnn_list.append(apn_dnn)
            ippools.append(ip_pool)
        
        apn_dnn = {
            "apn_dnn_list": apn_dnn_list,
            "ippools": ippools
        }

        return apn_dnn
        

    @staticmethod
    def v0_template_ip_pool(**data):
        ip_pool = {
            "pool_name": data["ip_pool_name"],
            "pool_type": "STATIC",
            "description": data["ip_pool_name"],
            "pdn_type": 0,
            "group_name": "",
            "ip_network": data["ip_network"],
            "subnet_mask": data["ip_mask"],
            "subblock_subnet": 32
        }

        return ip_pool


    @staticmethod
    def v0_template_apn_dnn(**data):

        dnn = {
            "name": data["dnn_name"],
            "primary_pdu_type": "IPV4",
            "dual_addressing": True,
            "IP_QoS_DSCP_Mapping": [
                {
                    "index": 1,
                    "qci": 1,
                    "dscp": "DSCP_BE"
                }
            ],
            "ipm_pools": [data["ip_pool_name"]],
            "ruleSets": ["RB1"],
            "dns": {
                "primary": {
                    "ipv4": data["dns_primary_v4"],
                    "ipv6": data["dns_primary_v6"]
                },
                "secondary": {
                    "ipv4": data["dns_secondary_v4"],
                    "ipv6": data["dns_secondary_v6"]
                }
            },
            "accept_radius_disconnect": "enable",
            "apn_cfg_aaa_group_name": "aaa1",
            "apn_cfg_auth_mode": "PASSWORD_USE_PCO",
            "apn_cfg_accounting_mode": "RAD_DIAM",
            "refChgData": "Default-Charging-campus",
            "supi": {
                "start": "262060000000001",
                "end": "262069000000001"
            },
            "features": {
                "dcca_credit_control": [
                    {
                        "dcca_priority": 1,
                        "dcca_credit_control_selection_rule_name": "rule1",
                        "dcca_credit_control_peer_set_name": "ocsSet1",
                        "dcca_credit_control_gy_failure_profile_name": "gyF1",
                        "dcca_apn_name_to_be_included": "ANY"
                    }
                ],
                "upf_selection_rule": [
                    {
                        "rule_number": 1,
                        "priority": 1,
                        "pdnType": "IPV4",
                        "user_plane_group_name": "sxbGrp0"
                    },
                    {
                        "rule_number": 2,
                        "priority": 2,
                        "pdnType": "IPV6",
                        "user_plane_group_name": "sxbGrp0"
                    },
                    {
                        "rule_number": 3,
                        "priority": 3,
                        "pdnType": "IPV4V6",
                        "user_plane_group_name": "sxbGrp0"
                    }
                ],
                "operator_defined_qci": [
                    {
                        "qci_type": "NON-GBR",
                        "qci_value": 136
                    },
                    {
                        "qci_type": "NON-GBR",
                        "qci_value": 139
                    }
                ]
            }
        }

        return dnn
