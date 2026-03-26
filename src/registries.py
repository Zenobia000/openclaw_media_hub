"""Registries — Provider / Channel / Tool 註冊表。

純資料定義模組，供 Bridge API 回傳前端渲染設定畫面。
Plugin JSON 缺少顯示用 metadata（標籤、placeholder、品牌色、憑證欄位），
因此以 hardcode 方式定義。
"""

from __future__ import annotations

from typing import TypedDict


class ProviderEntry(TypedDict, total=False):
    """Model Provider 定義。"""

    name: str
    label: str
    env_var: str | None
    placeholder: str | None
    primary: bool


class ChannelField(TypedDict):
    """Channel 憑證欄位。"""

    key: str
    label: str


class ChannelEntry(TypedDict, total=False):
    """Messaging Channel 定義。"""

    name: str
    label: str
    icon: str
    icon_color: str
    fields: list[ChannelField]
    info_note: str
    primary: bool


class ToolEntry(TypedDict, total=False):
    """Tool API Key 定義。"""

    name: str
    label: str
    env_var: str | None
    placeholder: str | None


# ── AI 模型供應商 ────────────────────────────────────────
# primary=True → 主要清單；False → "More..." 收合區

PROVIDER_REGISTRY: list[ProviderEntry] = [
    # ── Primary ──
    {
        "name": "openai",
        "label": "OpenAI",
        "env_var": "OPENAI_API_KEY",
        "placeholder": "sk-...",
        "primary": True,
    },
    {
        "name": "anthropic",
        "label": "Anthropic",
        "env_var": "ANTHROPIC_API_KEY",
        "placeholder": "sk-ant-...",
        "primary": True,
    },
    {
        "name": "google",
        "label": "Google Gemini",
        "env_var": "GEMINI_API_KEY",
        "placeholder": "AIza...",
        "primary": True,
    },
    {
        "name": "openrouter",
        "label": "OpenRouter",
        "env_var": "OPENROUTER_API_KEY",
        "placeholder": "sk-or-...",
        "primary": True,
    },
    {
        "name": "ollama",
        "label": "Ollama",
        "env_var": "OLLAMA_API_KEY",
        "placeholder": None,
        "primary": True,
    },
    {
        "name": "moonshot",
        "label": "Moonshot (Kimi)",
        "env_var": "MOONSHOT_API_KEY",
        "placeholder": "sk-...",
        "primary": True,
    },
    # ── Secondary (More...) ──
    {
        "name": "amazon-bedrock",
        "label": "Amazon Bedrock",
        "env_var": None,
        "placeholder": None,
        "primary": False,
    },
    {
        "name": "mistral",
        "label": "Mistral",
        "env_var": "MISTRAL_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "nvidia",
        "label": "NVIDIA",
        "env_var": "NVIDIA_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "together",
        "label": "Together",
        "env_var": "TOGETHER_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "xai",
        "label": "xAI",
        "env_var": "XAI_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "minimax",
        "label": "MiniMax",
        "env_var": "MINIMAX_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "huggingface",
        "label": "Hugging Face",
        "env_var": "HF_TOKEN",
        "placeholder": "hf_...",
        "primary": False,
    },
    {
        "name": "fal",
        "label": "fal",
        "env_var": "FAL_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "qianfan",
        "label": "Qianfan (\u767e\u5ea6)",
        "env_var": "QIANFAN_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "byteplus",
        "label": "BytePlus",
        "env_var": "BYTEPLUS_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "volcengine",
        "label": "Volcano Engine",
        "env_var": "VOLCANO_ENGINE_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "zai",
        "label": "Z.AI (\u667a\u8b5c)",
        "env_var": "ZAI_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "venice",
        "label": "Venice AI",
        "env_var": "VENICE_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "xiaomi",
        "label": "Xiaomi",
        "env_var": "XIAOMI_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "kimi",
        "label": "Kimi",
        "env_var": "KIMI_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "github-copilot",
        "label": "GitHub Copilot",
        "env_var": "GH_TOKEN",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "chutes",
        "label": "Chutes",
        "env_var": "CHUTES_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "cloudflare-ai-gateway",
        "label": "Cloudflare AI Gateway",
        "env_var": "CLOUDFLARE_AI_GATEWAY_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "opencode",
        "label": "OpenCode",
        "env_var": "OPENCODE_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "sglang",
        "label": "SGLang",
        "env_var": "SGLANG_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "vllm",
        "label": "vLLM",
        "env_var": "VLLM_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "qwen-portal",
        "label": "Qwen Portal",
        "env_var": "QWEN_PORTAL_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "modelstudio",
        "label": "Model Studio",
        "env_var": "MODELSTUDIO_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "synthetic",
        "label": "Synthetic",
        "env_var": "SYNTHETIC_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "kilocode",
        "label": "Kilo Gateway",
        "env_var": "KILOCODE_API_KEY",
        "placeholder": "",
        "primary": False,
    },
    {
        "name": "vercel-ai-gateway",
        "label": "Vercel AI Gateway",
        "env_var": "AI_GATEWAY_API_KEY",
        "placeholder": "",
        "primary": False,
    },
]

# ── 訊息頻道 ─────────────────────────────────────────────

CHANNEL_REGISTRY: list[ChannelEntry] = [
    # ── Primary ──
    {
        "name": "line",
        "label": "LINE",
        "icon": "L",
        "icon_color": "#06C755",
        "fields": [
            {"key": "LINE_CHANNEL_ACCESS_TOKEN", "label": "Channel Access Token"},
            {"key": "LINE_CHANNEL_SECRET", "label": "Channel Secret"},
        ],
        "primary": True,
    },
    {
        "name": "discord",
        "label": "Discord",
        "icon": "D",
        "icon_color": "#5865F2",
        "fields": [
            {"key": "DISCORD_BOT_TOKEN", "label": "Bot Token"},
        ],
        "primary": True,
    },
    {
        "name": "telegram",
        "label": "Telegram",
        "icon": "T",
        "icon_color": "#0088CC",
        "fields": [
            {"key": "TELEGRAM_BOT_TOKEN", "label": "Bot Token"},
        ],
        "primary": True,
    },
    {
        "name": "slack",
        "label": "Slack",
        "icon": "S",
        "icon_color": "#4A154B",
        "fields": [
            {"key": "SLACK_BOT_TOKEN", "label": "Bot Token"},
            {"key": "SLACK_APP_TOKEN", "label": "App Token"},
        ],
        "primary": True,
    },
    {
        "name": "whatsapp",
        "label": "WhatsApp",
        "icon": "W",
        "icon_color": "#25D366",
        "fields": [],
        "info_note": "Configure via 'channels login' after initialization",
        "primary": True,
    },
    # ── Secondary (More...) ──
    {
        "name": "matrix",
        "label": "Matrix",
        "icon": "M",
        "icon_color": "#0DBD8B",
        "fields": [{"key": "MATRIX_ACCESS_TOKEN", "label": "Access Token"}],
        "primary": False,
    },
    {
        "name": "signal",
        "label": "Signal",
        "icon": "Si",
        "icon_color": "#3A76F0",
        "fields": [{"key": "SIGNAL_API_URL", "label": "API URL"}],
        "primary": False,
    },
    {
        "name": "mattermost",
        "label": "Mattermost",
        "icon": "Mm",
        "icon_color": "#0058CC",
        "fields": [{"key": "MATTERMOST_BOT_TOKEN", "label": "Bot Token"}],
        "primary": False,
    },
    {
        "name": "zalo",
        "label": "Zalo",
        "icon": "Z",
        "icon_color": "#0068FF",
        "fields": [{"key": "ZALO_ACCESS_TOKEN", "label": "Access Token"}],
        "primary": False,
    },
    {
        "name": "irc",
        "label": "IRC",
        "icon": "IR",
        "icon_color": "#6B7280",
        "fields": [{"key": "IRC_SERVER", "label": "Server"}],
        "primary": False,
    },
    {
        "name": "feishu",
        "label": "Feishu",
        "icon": "F",
        "icon_color": "#3370FF",
        "fields": [{"key": "FEISHU_APP_ID", "label": "App ID"}],
        "primary": False,
    },
    {
        "name": "googlechat",
        "label": "Google Chat",
        "icon": "G",
        "icon_color": "#1A73E8",
        "fields": [{"key": "GOOGLE_CHAT_WEBHOOK", "label": "Webhook URL"}],
        "primary": False,
    },
    {
        "name": "msteams",
        "label": "MS Teams",
        "icon": "T",
        "icon_color": "#6264A7",
        "fields": [{"key": "MSTEAMS_WEBHOOK", "label": "Webhook URL"}],
        "primary": False,
    },
    {
        "name": "nostr",
        "label": "Nostr",
        "icon": "N",
        "icon_color": "#8B5CF6",
        "fields": [{"key": "NOSTR_PRIVATE_KEY", "label": "Private Key"}],
        "primary": False,
    },
    {
        "name": "nextcloud-talk",
        "label": "Nextcloud Talk",
        "icon": "NC",
        "icon_color": "#0082C9",
        "fields": [],
        "primary": False,
    },
    {
        "name": "synology-chat",
        "label": "Synology Chat",
        "icon": "Sy",
        "icon_color": "#B5B5B6",
        "fields": [],
        "primary": False,
    },
    {
        "name": "tlon",
        "label": "Tlon",
        "icon": "Tl",
        "icon_color": "#6B7280",
        "fields": [],
        "primary": False,
    },
    {
        "name": "bluebubbles",
        "label": "BlueBubbles",
        "icon": "BB",
        "icon_color": "#1B95E0",
        "fields": [],
        "primary": False,
    },
    {
        "name": "imessage",
        "label": "iMessage",
        "icon": "iM",
        "icon_color": "#34C759",
        "fields": [],
        "primary": False,
    },
    {
        "name": "zalouser",
        "label": "Zalo User",
        "icon": "ZU",
        "icon_color": "#0068FF",
        "fields": [],
        "primary": False,
    },
    {
        "name": "twitch",
        "label": "Twitch",
        "icon": "Tw",
        "icon_color": "#9146FF",
        "fields": [],
        "primary": False,
    },
]

# ── 工具 API 金鑰 ────────────────────────────────────────

TOOL_REGISTRY: list[ToolEntry] = [
    {
        "name": "brave",
        "label": "Brave Search",
        "env_var": "BRAVE_API_KEY",
        "placeholder": "BSA...",
    },
    {
        "name": "perplexity",
        "label": "Perplexity",
        "env_var": "PERPLEXITY_API_KEY",
        "placeholder": "pplx-...",
    },
    {
        "name": "firecrawl",
        "label": "Firecrawl",
        "env_var": "FIRECRAWL_API_KEY",
        "placeholder": "fc-...",
    },
    {
        "name": "tavily",
        "label": "Tavily",
        "env_var": "TAVILY_API_KEY",
        "placeholder": "tvly-...",
    },
    {
        "name": "elevenlabs",
        "label": "ElevenLabs",
        "env_var": "ELEVENLABS_API_KEY",
        "placeholder": "",
    },
    {
        "name": "deepgram",
        "label": "Deepgram",
        "env_var": "DEEPGRAM_API_KEY",
        "placeholder": "",
    },
]
