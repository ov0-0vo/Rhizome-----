from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import os
import re

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


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "****"
    return "****" + value[-4:]


def is_masked(value: str) -> bool:
    if not value:
        return False
    return value.startswith("****") and len(value) > 4 and value[4:].isalnum()


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


SECRET_KEYS = {
    'OPENAI_API_KEY', 'EMBEDDING_API_KEY',
    'FEISHU_APP_SECRET', 'TAVILY_API_KEY'
}


def write_env_file(file_path: Path, config: dict, existing_env: dict = None):
    if existing_env is None:
        existing_env = {}
    
    merged = dict(existing_env)
    for key, value in config.items():
        if key in SECRET_KEYS and is_masked(value):
            if key in merged and merged[key]:
                continue
        merged[key] = value
    
    lines = []
    seen_keys = set()
    
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.rstrip('\n')
                if stripped and not stripped.startswith('#') and '=' in stripped:
                    key = stripped.split('=', 1)[0].strip()
                    seen_keys.add(key)
                    if key in merged:
                        lines.append(f"{key}={merged[key]}")
                    else:
                        lines.append(stripped)
                else:
                    lines.append(stripped)
    
    for key, value in merged.items():
        if key not in seen_keys:
            lines.append(f"{key}={value}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def validate_config(config: AppConfigUpdate) -> list:
    errors = []
    
    if config.llm:
        valid_providers = {'openai', 'anthropic', 'ollama', 'azure'}
        if config.llm.provider not in valid_providers:
            errors.append(f"不支持的 LLM 提供商: {config.llm.provider}，支持: {', '.join(valid_providers)}")
        if not config.llm.model_name.strip():
            errors.append("模型名称不能为空")
        if config.llm.provider in ('openai', 'anthropic', 'azure') and not is_masked(config.llm.api_key) and not config.llm.api_key.strip():
            errors.append(f"{config.llm.provider} 需要 API Key")
        if config.llm.base_url and not re.match(r'https?://', config.llm.base_url):
            errors.append("API Base URL 格式无效")
    
    if config.embedding:
        valid_providers = {'local', 'openai', 'ollama', 'azure'}
        if config.embedding.provider not in valid_providers:
            errors.append(f"不支持的嵌入提供商: {config.embedding.provider}")
        if config.embedding.base_url and not re.match(r'https?://', config.embedding.base_url):
            errors.append("嵌入 API Base URL 格式无效")
    
    return errors


@router.get("", response_model=AppConfig)
async def get_config():
    env_path = get_env_file_path()
    env_vars = parse_env_file(env_path)
    
    return AppConfig(
        llm=LLMConfig(
            provider=env_vars.get('LLM_PROVIDER', 'openai'),
            model_name=env_vars.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
            api_key=mask_secret(env_vars.get('OPENAI_API_KEY', '')),
            base_url=env_vars.get('OPENAI_API_BASE', '')
        ),
        embedding=EmbeddingConfig(
            provider=env_vars.get('EMBEDDING_PROVIDER', 'local'),
            model_name=env_vars.get('EMBEDDING_MODEL', 'BAAI/bge-large-zh-v1.5'),
            api_key=mask_secret(env_vars.get('EMBEDDING_API_KEY', '')),
            base_url=env_vars.get('EMBEDDING_API_BASE', '')
        ),
        feishu=FeishuConfig(
            app_id=env_vars.get('FEISHU_APP_ID', ''),
            app_secret=mask_secret(env_vars.get('FEISHU_APP_SECRET', ''))
        )
    )


@router.put("")
async def update_config(config: AppConfigUpdate):
    errors = validate_config(config)
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))
    
    env_path = get_env_file_path()
    existing_env = parse_env_file(env_path)
    env_vars = dict(existing_env)
    
    if config.llm:
        env_vars['LLM_PROVIDER'] = config.llm.provider
        env_vars['OPENAI_MODEL'] = config.llm.model_name
        if not is_masked(config.llm.api_key):
            env_vars['OPENAI_API_KEY'] = config.llm.api_key
        env_vars['OPENAI_API_BASE'] = config.llm.base_url
    
    if config.embedding:
        env_vars['EMBEDDING_PROVIDER'] = config.embedding.provider
        env_vars['EMBEDDING_MODEL'] = config.embedding.model_name
        if not is_masked(config.embedding.api_key):
            env_vars['EMBEDDING_API_KEY'] = config.embedding.api_key
        env_vars['EMBEDDING_API_BASE'] = config.embedding.base_url
    
    if config.feishu:
        env_vars['FEISHU_APP_ID'] = config.feishu.app_id
        if not is_masked(config.feishu.app_secret):
            env_vars['FEISHU_APP_SECRET'] = config.feishu.app_secret
    
    write_env_file(env_path, env_vars, existing_env)
    
    return {"message": "配置已保存，重启服务后生效"}
