from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import os

router = APIRouter(prefix="/api/config", tags=["config"])


class LLMConfig(BaseModel):
    provider: str = "openai"
    model_name: str = "gpt-3.5-turbo"
    api_key: str = ""
    base_url: str = ""


class EmbeddingConfig(BaseModel):
    provider: str = "local"
    model_name: str = "BAAI/bge-large-zh-v1.5"
    api_key: str = ""
    base_url: str = ""


class FeishuConfig(BaseModel):
    app_id: str = ""
    app_secret: str = ""


class AppConfig(BaseModel):
    llm: LLMConfig
    embedding: EmbeddingConfig
    feishu: FeishuConfig


class AppConfigUpdate(BaseModel):
    llm: Optional[LLMConfig] = None
    embedding: Optional[EmbeddingConfig] = None
    feishu: Optional[FeishuConfig] = None


def get_env_file_path() -> Path:
    env_path = Path(__file__).parent.parent.parent / ".env"
    if not env_path.exists():
        env_example = Path(__file__).parent.parent.parent / ".env.example"
        if env_example.exists():
            return env_example
    return env_path


def parse_env_file(file_path: Path) -> dict:
    env_vars = {}
    if not file_path.exists():
        return env_vars
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    return env_vars


def write_env_file(file_path: Path, config: dict):
    lines = []
    lines.append("# LLM Configuration")
    lines.append(f"LLM_PROVIDER={config.get('LLM_PROVIDER', 'openai')}")
    lines.append(f"OPENAI_API_KEY={config.get('OPENAI_API_KEY', '')}")
    lines.append(f"OPENAI_API_BASE={config.get('OPENAI_API_BASE', '')}")
    lines.append(f"OPENAI_MODEL={config.get('OPENAI_MODEL', 'gpt-3.5-turbo')}")
    lines.append("")
    lines.append("# Embedding Configuration")
    lines.append(f"EMBEDDING_PROVIDER={config.get('EMBEDDING_PROVIDER', 'local')}")
    lines.append(f"EMBEDDING_MODEL={config.get('EMBEDDING_MODEL', 'BAAI/bge-large-zh-v1.5')}")
    lines.append(f"EMBEDDING_API_KEY={config.get('EMBEDDING_API_KEY', '')}")
    lines.append(f"EMBEDDING_API_BASE={config.get('EMBEDDING_API_BASE', '')}")
    lines.append("")
    lines.append("# Feishu Configuration")
    lines.append(f"FEISHU_APP_ID={config.get('FEISHU_APP_ID', '')}")
    lines.append(f"FEISHU_APP_SECRET={config.get('FEISHU_APP_SECRET', '')}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


@router.get("", response_model=AppConfig)
async def get_config():
    env_path = get_env_file_path()
    env_vars = parse_env_file(env_path)
    
    return AppConfig(
        llm=LLMConfig(
            provider=env_vars.get('LLM_PROVIDER', 'openai'),
            model_name=env_vars.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
            api_key=env_vars.get('OPENAI_API_KEY', ''),
            base_url=env_vars.get('OPENAI_API_BASE', '')
        ),
        embedding=EmbeddingConfig(
            provider=env_vars.get('EMBEDDING_PROVIDER', 'local'),
            model_name=env_vars.get('EMBEDDING_MODEL', 'BAAI/bge-large-zh-v1.5'),
            api_key=env_vars.get('EMBEDDING_API_KEY', ''),
            base_url=env_vars.get('EMBEDDING_API_BASE', '')
        ),
        feishu=FeishuConfig(
            app_id=env_vars.get('FEISHU_APP_ID', ''),
            app_secret=env_vars.get('FEISHU_APP_SECRET', '')
        )
    )


@router.put("")
async def update_config(config: AppConfigUpdate):
    env_path = get_env_file_path()
    env_vars = parse_env_file(env_path)
    
    if config.llm:
        env_vars['LLM_PROVIDER'] = config.llm.provider
        env_vars['OPENAI_MODEL'] = config.llm.model_name
        env_vars['OPENAI_API_KEY'] = config.llm.api_key
        env_vars['OPENAI_API_BASE'] = config.llm.base_url
    
    if config.embedding:
        env_vars['EMBEDDING_PROVIDER'] = config.embedding.provider
        env_vars['EMBEDDING_MODEL'] = config.embedding.model_name
        env_vars['EMBEDDING_API_KEY'] = config.embedding.api_key
        env_vars['EMBEDDING_API_BASE'] = config.embedding.base_url
    
    if config.feishu:
        env_vars['FEISHU_APP_ID'] = config.feishu.app_id
        env_vars['FEISHU_APP_SECRET'] = config.feishu.app_secret
    
    write_env_file(env_path, env_vars)
    
    return {"message": "配置已保存，重启服务后生效"}
