from dataclasses import replace

import pytest

from recruit_bot.config import Settings


def test_ai_config_requires_explicit_model_name():
    settings = replace(
        Settings.load(),
        dashscope_api_key="test-key",
        qwen_vl_model="",
    )

    with pytest.raises(RuntimeError, match="QWEN_VL_MODEL"):
        settings.require_ai_config()


def test_ai_config_requires_explicit_base_url():
    settings = replace(
        Settings.load(),
        dashscope_api_key="test-key",
        dashscope_base_url="",
        qwen_vl_model="configured-model",
    )

    with pytest.raises(RuntimeError, match="DASHSCOPE_BASE_URL"):
        settings.require_ai_config()


def test_ai_config_accepts_env_supplied_model_name():
    settings = replace(
        Settings.load(),
        dashscope_api_key="test-key",
        dashscope_base_url="https://api.example.com/v1",
        qwen_vl_model="configured-model",
    )

    settings.require_ai_config()
