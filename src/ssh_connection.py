"""SSH Connection Manager — 連線生命週期管理 (ADR-004).

管理 paramiko SSH 連線的建立、斷線、重連、心跳與狀態。
連線狀態變化透過 on_state_change callback 通知上層（Bridge → 前端）。
"""

from __future__ import annotations

import asyncio
import enum
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

import paramiko

logger = logging.getLogger(__name__)


class ConnectionState(enum.Enum):
    """SSH 連線狀態。"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class SSHConnectionConfig:
    """SSH 連線設定。"""

    host: str
    username: str
    port: int = 22
    key_path: str | None = None
    password: str | None = None


class SSHConnection:
    """SSH 連線管理器。

    支援 key auth（優先）與 password auth，
    提供自動重連（最多 3 次）與 keepalive 心跳（30 秒）。
    """

    MAX_RECONNECT_ATTEMPTS = 3
    KEEPALIVE_INTERVAL = 30

    def __init__(
        self,
        config: SSHConnectionConfig,
        on_state_change: Callable[[ConnectionState], None] | None = None,
    ) -> None:
        self._config = config
        self._on_state_change = on_state_change
        self._client: paramiko.SSHClient | None = None
        self._sftp: paramiko.SFTPClient | None = None
        self._state = ConnectionState.DISCONNECTED

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def config(self) -> SSHConnectionConfig:
        return self._config

    def _set_state(self, new_state: ConnectionState) -> None:
        if self._state != new_state:
            self._state = new_state
            if self._on_state_change:
                self._on_state_change(new_state)

    async def connect(self) -> None:
        """建立 SSH 連線。key auth 優先，fallback password。"""
        await asyncio.to_thread(self._connect_sync)

    def _connect_sync(self) -> None:
        self._set_state(ConnectionState.CONNECTING)
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_kwargs: dict = {
                "hostname": self._config.host,
                "port": self._config.port,
                "username": self._config.username,
                "timeout": 10,
            }

            if self._config.key_path:
                connect_kwargs["key_filename"] = self._config.key_path
            elif self._config.password:
                connect_kwargs["password"] = self._config.password

            client.connect(**connect_kwargs)

            transport = client.get_transport()
            if transport:
                transport.set_keepalive(self.KEEPALIVE_INTERVAL)

            self._client = client
            self._sftp = None  # lazy init
            self._set_state(ConnectionState.CONNECTED)
            logger.info("SSH connected to %s:%d", self._config.host, self._config.port)
        except Exception:
            self._set_state(ConnectionState.ERROR)
            logger.exception("SSH connection failed")
            raise

    async def disconnect(self) -> None:
        """關閉 SSH 連線。"""
        await asyncio.to_thread(self._disconnect_sync)

    def _disconnect_sync(self) -> None:
        if self._sftp:
            try:
                self._sftp.close()
            except Exception:
                logger.debug("SFTP close error", exc_info=True)
            self._sftp = None

        if self._client:
            try:
                self._client.close()
            except Exception:
                logger.debug("SSH client close error", exc_info=True)
            self._client = None

        self._set_state(ConnectionState.DISCONNECTED)
        logger.info("SSH disconnected")

    async def reconnect(self) -> None:
        """重新建立連線，最多重試 3 次。"""
        await asyncio.to_thread(self._reconnect_sync)

    def _reconnect_sync(self) -> None:
        self._disconnect_sync()
        last_error: Exception | None = None

        for attempt in range(1, self.MAX_RECONNECT_ATTEMPTS + 1):
            try:
                logger.info("SSH reconnect attempt %d/%d", attempt, self.MAX_RECONNECT_ATTEMPTS)
                self._connect_sync()
                return
            except Exception as exc:
                last_error = exc
                if attempt < self.MAX_RECONNECT_ATTEMPTS:
                    time.sleep(min(2 ** attempt, 8))

        self._set_state(ConnectionState.ERROR)
        msg = f"SSH reconnect failed after {self.MAX_RECONNECT_ATTEMPTS} attempts"
        raise ConnectionError(msg) from last_error

    def _ensure_connected(self) -> paramiko.SSHClient:
        if self._client is None or self._state != ConnectionState.CONNECTED:
            msg = "SSH not connected"
            raise ConnectionError(msg)

        transport = self._client.get_transport()
        if transport is None or not transport.is_active():
            self._set_state(ConnectionState.ERROR)
            msg = "SSH transport is not active"
            raise ConnectionError(msg)

        return self._client

    def get_client(self) -> paramiko.SSHClient:
        """取得 SSH client，未連線時 raise ConnectionError。"""
        return self._ensure_connected()

    def get_sftp(self) -> paramiko.SFTPClient:
        """取得 SFTP client（lazy init），未連線時 raise ConnectionError。"""
        client = self._ensure_connected()
        if self._sftp is None:
            self._sftp = client.open_sftp()
        return self._sftp
