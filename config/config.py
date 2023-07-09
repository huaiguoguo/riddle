import os
import yaml


def root_path() -> str:
    return os.path.dirname(os.path.dirname(__file__))


def load_config(dir_path, filename):
    # 获取当前脚本的绝对路径
    # dir_path = os.path.dirname(os.path.abspath(__file__))

    # 构造config.yaml的路径
    config_path = os.path.join(dir_path, filename)

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.load(f, Loader=yaml.FullLoader)


# config = load_config('../config.yaml')

def get_config(config_name: str = 'config.yaml', path: str = ''):
    dir_path = root_path()
    if len(path.strip()) > 0:
        dir_path = os.path.dirname(os.path.abspath(__file__))
    # print(f"config: {dir_path}/{config_name}")
    return load_config(dir_path, config_name)
