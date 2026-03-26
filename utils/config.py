import configparser
import os
import dotenv

dotenv.load_dotenv()


class AppConfig:
    def __init__(self, use_updated_system=False, file_name="secrets.ini", cfg_dir=os.path.expanduser("~")):
        self.use_updated_system = use_updated_system
        if not self.use_updated_system:
            if cfg_dir is None:
                cfg_dir = os.path.expanduser("~")
            self.cfg_dir = os.path.join(cfg_dir, ".pyconfig")
            self.config_file = os.path.join(self.cfg_dir, file_name)
            if not os.path.isdir(self.cfg_dir):
                raise Exception("Directory {} does not exist".format(self.cfg_dir))

            if not os.path.isfile(self.config_file):
                raise Exception("Configuration file {} does not exist".format(self.config_file))

            self.config = configparser.ConfigParser()
            self.config.read(self.config_file)

    def get_bot_key(self):
        if not self.use_updated_system:
            main_section = self.config['main']
            return main_section['bonk_bot_token']
        else:
            return os.getenv("BONK_BOT_TOKEN")

    def get_bonk_panel_api_key(self):
        if not self.use_updated_system:
            main_section = self.config['main']
            return main_section['bonk_panel_api_key']
        else:
            return os.getenv("BONK_PANEL_API_KEY")

    def get_config_dir(self):
        if not self.use_updated_system:
            return self.cfg_dir
        return None


if __name__ == '__main__':
    app_config = AppConfig()
    print(app_config.get_bot_key())
