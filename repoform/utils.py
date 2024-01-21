import json
import yaml
import xml.etree.ElementTree as ET

def load_content_by_file_type(file_name: str, content: str):
    if file_name.endswith('.json'):
        return json.loads(content)
    elif file_name.endswith(('.yaml', '.yml')):
        return yaml.safe_load(content)
    elif file_name.endswith('.xml'):
        return ET.fromstring(content)
    else:
        raise ValueError(f"Unsupported file format for: {file_name}")

def dump_content_by_file_type(file_name: str, content: str):
    if file_name.endswith('.json'):
        return json.dumps(content, indent=4)
    elif file_name.endswith(('.yaml', '.yml')):
        return yaml.dump(content, default_flow_style=False)
    elif file_name.endswith('.xml'):
        return ET.tostring(content).decode()
    else:
        raise ValueError(f"Unsupported file format for: {file_name}")
