import yaml

from git import Repo

with open('./environment.yaml', 'r', encoding='utf-8') as f:
    yaml_data = yaml.safe_load(f)

CLIENT_ID = yaml_data['CLIENT_ID']
SQLALCHEMY = yaml_data['SQLALCHEMY']

GODS = yaml_data['GODS']
BOTNAME = yaml_data['BOTNAME']
ENVIRONMENT = yaml_data['ENVIRONMENT']

GITCOMMIT = Repo('./').commit()
GITHASH = GITCOMMIT.hexsha[:7]
GITWHEN = GITCOMMIT.committed_datetime.strftime("%Y-%m-%d %H:%M:%S")
GITSUMMARY = GITCOMMIT.summary