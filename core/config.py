import yaml

with open('./environment.yaml', 'r', encoding='utf-8') as f:
    yaml_data = yaml.safe_load(f)

REDIS_URL = yaml_data['REDIS']['URL']