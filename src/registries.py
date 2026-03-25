"""Registries — Provider / Channel / Tool 註冊表。

純資料定義模組，供 Bridge API 回傳前端渲染 Config Step 2。
Plugin JSON (openclaw/extensions/) 缺少 display metadata（標籤、placeholder、
品牌色、credential 欄位），因此以 hardcode 方式定義 spec §4.3 明確要求的項目。
"""

from __future__ import annotations

# ── Model Providers ───────────────────────────────────────
# primary=True → 主要清單；False → "More..." 收合區

PROVIDER_REGISTRY: list[dict] = [
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
        "env_var": None,
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
        "env_var": "AWS_ACCESS_KEY_ID",
        "placeholder": "AKIA...",
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
        "env_var": "HUGGINGFACE_API_KEY",
        "placeholder": "hf_...",
        "primary": False,
    },
]

# ── Messaging Channels ────────────────────────────────────

CHANNEL_REGISTRY: list[dict] = [
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
]

# ── Tool API Keys ─────────────────────────────────────────

TOOL_REGISTRY: list[dict] = [
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
