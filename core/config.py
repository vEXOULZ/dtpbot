import yaml

with open('./environment.yaml', 'r', encoding='utf-8') as f:
    yaml_data = yaml.safe_load(f)

CLIENT_ID = yaml_data['CLIENT_ID']
SQLALCHEMY = yaml_data['SQLALCHEMY']

GODS = yaml_data['GODS']
BOTNAME = yaml_data['BOTNAME']