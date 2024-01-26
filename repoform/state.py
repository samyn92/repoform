from jinja2 import Template

class State:
    def __init__(self):
        self.templates = {}

    def render_template(self, template_string, data):
        version = data.get('version')
        data = data.get('data')

        template = self.templates.get(version)
        if template is None:
            raise ValueError(f"No template found for version {version}")

        desired_state = template.render(data)
        return desired_state
    
    def get_template(self, version: str):
        return self.templates.get(version)

    def add_template(self, version, template):
        self.templates[version] = template


    

# Example usage
initial_state = {'some': 'state'}
updater = State(initial_state)

# Adding templates for different versions
updater.add_template("v1", "{{ data['key'] }} is the key for version 1")
updater.add_template("v2", "{{ data['key'] }} and {{ data['extra'] }} for version 2")

# Example high-level data with versioning
high_level_data_v1 = {'version': 'v1', 'data': {'key': 'value1'}}
high_level_data_v2 = {'version': 'v2', 'data': {'key': 'value2', 'extra': 'additional'}}

# Generate and apply desired state for version 1
desired_state_v1 = updater.generate_desired_state(high_level_data_v1)
updater.apply_state(desired_state_v1)
print(updater.read())

# Generate and apply desired state for version 2
desired_state_v2 = updater.generate_desired_state(high_level_data_v2)
updater.apply_state(desired_state_v2)
print(updater.read())
