
from yaml import load as yaml_load, FullLoader as yaml_loader
"""
with open('config.yaml', 'r') as config_file:
  config = yaml_load(
    stream=config_file,
    Loader=yaml_loader
  )
"""
config = {
  "bot_token": "1006153956:AAG6kUpYsCZ4TDlnue37DvE5rRzI-OejQ-c",
  "database_path": "database.db",
  "logging": {
    "path": "logs.log",
    "level": 0,
    "file_log_enabled": False
  }
}