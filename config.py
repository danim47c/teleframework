
from yaml import load as yaml_load, FullLoader as yaml_loader

with open('config.yaml', 'r') as config_file:
  config = yaml_load(
    stream=config_file,
    Loader=yaml_loader
  )