import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class FeishuConfig:
    app_id: str = field(default_factory=lambda: os.getenv("FEISHU_APP_ID", ""))
    app_secret: str = field(default_factory=lambda: os.getenv("FEISHU_APP_SECRET", ""))
    
    @property
    def enabled(self) -> bool:
        return bool(self.app_id and self.app_secret)


_feishu_config: FeishuConfig = None


def get_feishu_config() -> FeishuConfig:
    global _feishu_config
    if _feishu_config is None:
        _feishu_config = FeishuConfig()
    return _feishu_config


feishu_config = get_feishu_config()
