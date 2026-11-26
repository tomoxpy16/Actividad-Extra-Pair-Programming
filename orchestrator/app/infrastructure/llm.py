"""Proveedores de LLM (patrón Strategy + Adapter).

Los agentes no conocen el proveedor concreto: dependen de la abstracción `LLMProvider`
(principio de inversión de dependencias). Si el proveedor falla, el agente cae a su
implementación determinista (táctica de degradación elegante).

Proveedores:
- `rules`     : sin LLM. Todo se resuelve con reglas deterministas (por defecto, funciona offline).
- `ollama`    : modelo local servido por Ollama (contenedor opcional del perfil `llm`).
- `anthropic` : Claude vía SDK oficial de Anthropic (requiere ANTHROPIC_API_KEY).
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx

log = logging.getLogger("kairos.llm")


class LLMUnavailable(RuntimeError):
    pass


class LLMProvider(ABC):
    name: str = "abstract"

    @property
    def enabled(self) -> bool:
        return True

    @abstractmethod
    def complete_json(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Devuelve un objeto JSON que cumple `schema`. Lanza LLMUnavailable si no puede."""

    def complete_text(self, system: str, user: str) -> str:
        raise LLMUnavailable("texto libre no soportado")


class NullProvider(LLMProvider):
    """Proveedor nulo (patrón Null Object): fuerza el camino determinista."""
    name = "rules"

    @property
    def enabled(self) -> bool:
        return False

    def complete_json(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        raise LLMUnavailable("LLM deshabilitado (LLM_PROVIDER=rules)")


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str, model: str, timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _chat(self, system: str, user: str, fmt: Any | None) -> str:
        body: dict[str, Any] = {
            "model": self.model,
            "stream": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "options": {"temperature": 0},
        }
        if fmt is not None:
            body["format"] = fmt
        try:
            r = httpx.post(f"{self.base_url}/api/chat", json=body, timeout=self.timeout)
            r.raise_for_status()
            return r.json()["message"]["content"]
        except Exception as exc:  # red caída, modelo no descargado, etc.
            raise LLMUnavailable(f"Ollama no disponible: {exc}") from exc

    def complete_json(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        raw = self._chat(system, user, schema)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMUnavailable(f"Ollama devolvió JSON inválido: {exc}") from exc

    def complete_text(self, system: str, user: str) -> str:
        return self._chat(system, user, None).strip()


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, model: str, api_key: str | None = None) -> None:
        import anthropic  # import perezoso: solo se necesita con este proveedor

        self._anthropic = anthropic
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self.model = model

    def _create(self, system: str, user: str, output_config: dict[str, Any], max_tokens: int):
        # Fallback del lado del servidor: si el modelo declina por política, la API
        # reintenta con un modelo alterno dentro de la misma llamada.
        return self.client.beta.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=system,
            output_config=output_config,
            messages=[{"role": "user", "content": user}],
        )

    @staticmethod
    def _text(response: Any) -> str:
        if response.stop_reason == "refusal":
            raise LLMUnavailable("el modelo declinó la solicitud")
        return "".join(b.text for b in response.content if getattr(b, "type", "") == "text")

    def complete_json(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._create(
                system,
                user,
                {"effort": "low", "format": {"type": "json_schema", "schema": schema}},
                max_tokens=8000,
            )
            return json.loads(self._text(response))
        except LLMUnavailable:
            raise
        except self._anthropic.APIConnectionError as exc:
            raise LLMUnavailable(f"sin conexión con Anthropic: {exc}") from exc
        except self._anthropic.APIStatusError as exc:
            raise LLMUnavailable(f"Anthropic respondió {exc.status_code}") from exc
        except json.JSONDecodeError as exc:
            raise LLMUnavailable(f"JSON inválido: {exc}") from exc

    def complete_text(self, system: str, user: str) -> str:
        try:
            return self._text(self._create(system, user, {"effort": "low"}, max_tokens=2000)).strip()
        except LLMUnavailable:
            raise
        except self._anthropic.APIError as exc:
            raise LLMUnavailable(str(exc)) from exc


def build_provider(kind: str, *, ollama_url: str, ollama_model: str, anthropic_model: str,
                   anthropic_api_key: str | None) -> LLMProvider:
    """Fábrica (Factory Method) del proveedor según configuración."""
    kind = (kind or "rules").lower()
    try:
        if kind == "ollama":
            return OllamaProvider(ollama_url, ollama_model)
        if kind == "anthropic":
            return AnthropicProvider(anthropic_model, anthropic_api_key)
    except Exception as exc:  # SDK ausente o mal configurado
        log.warning("No se pudo crear el proveedor %s (%s); se usa 'rules'", kind, exc)
    return NullProvider()
