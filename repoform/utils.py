import os
import json
import yaml
import xml.etree.ElementTree as ET
from lxml import etree
from xml.dom import minidom

@staticmethod
def load_data(directory_path: str) -> dict:
    data = {}
    for filename in os.listdir(directory_path):
        if filename.endswith('.yaml') or filename.endswith('.yml'):
            file_path = os.path.join(directory_path, filename)
            with open(file_path, 'r') as file:
                file_data = yaml.safe_load(file)
                if isinstance(file_data, dict):
                    key = os.path.splitext(filename)[0]  # Using filename (without extension) as key
                    data[key] = file_data
    return data

def load_content_by_file_type(file_name: str, content: str):
    if file_name.endswith('.json'):
        return json.loads(content)
    elif file_name.endswith(('.yaml', '.yml')):
        return yaml.safe_load(content)
    elif file_name.endswith('.xml'):
        # return ET.fromstring(content)
        return etree.fromstring(content)
    else:
        raise ValueError(f"Unsupported file format for: {file_name}")

def dump_content_by_file_type(file_name: str, content: str):
    if file_name.endswith('.json'):
        return json.dumps(content, indent=4)
    elif file_name.endswith(('.yaml', '.yml')):
        return yaml.dump(content, default_flow_style=False)
    elif file_name.endswith('.xml'):
        # return ET.tostring(content).decode()
        xml_str = etree.tostring(content, pretty_print=True, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml_str = dom.toprettyxml(indent="    ")

        cleaned_lines = (line for line in pretty_xml_str.split('\n') if line.strip())
        cleaned_xml_str = '\n'.join(cleaned_lines)
        return cleaned_xml_str
    else:
        raise ValueError(f"Unsupported file format for: {file_name}")
