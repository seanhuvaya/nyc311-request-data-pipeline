import os
import yaml

from dotenv import load_dotenv

load_dotenv()


class YamlConfig:
    def __init__(self, yaml_path: str):
        self.yaml_path = yaml_path
        try:
            with open(self.yaml_path, "r") as f:
                self.config = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError as fe:
            raise Exception(f"Yaml config file not found: {fe}")
        except yaml.YAMLError as e:
            raise Exception(f"Error parsing YAML: {e}")


class EnvConfig:
    APP_TOKEN = os.getenv("APP_TOKEN")


yml_config = YamlConfig(os.path.join("config/config.yml"))
env_config = EnvConfig()


