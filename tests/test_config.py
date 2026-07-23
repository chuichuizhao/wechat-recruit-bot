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


def test_ai_config_accepts_env_supplied_model_name():
    settings = replace(
        Settings.load(),
        dashscope_api_key="test-key",
        qwen_vl_model="configured-model",
    )

    settings.require_ai_config()
