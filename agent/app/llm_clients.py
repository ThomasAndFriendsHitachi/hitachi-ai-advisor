from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any
from urllib import error
from urllib import request

from .utils import extract_json_from_text


@dataclass
class LLMCallResult:
    provider: str
    model: str
    raw_text: str
    payload: dict[str, Any]


class BaseJSONLLMClient:
    provider: str = "base"

    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def is_available(self) -> bool:
        raise NotImplementedError

    def generate_json(self, system_prompt: str, user_prompt: str) -> LLMCallResult:
        raise NotImplementedError


class OpenAIJSONClient(BaseJSONLLMClient):
    provider = "openai"

    def __init__(self, api_key: str | None, model: str, base_url: str | None = None) -> None:
        super().__init__(api_key=api_key, model=model)
        self._client = None
        self.base_url = base_url
        if not api_key:
            return
        try:
            from openai import OpenAI  # type: ignore

            kwargs: dict[str, Any] = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url
            self._client = OpenAI(**kwargs)
        except Exception:
            self._client = None

    def is_available(self) -> bool:
        return self._client is not None

    def generate_json(self, system_prompt: str, user_prompt: str) -> LLMCallResult:
        if not self._client:
            raise RuntimeError("OpenAI client unavailable")

        text = ""
        try:
            response = self._client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
            )
            text = getattr(response, "output_text", "") or ""
        except Exception:
            # Compatibility fallback for older SDK chat API.
            chat = self._client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            text = chat.choices[0].message.content or "{}"

        payload = extract_json_from_text(text)
        if not isinstance(payload, dict):
            raise ValueError("OpenAI response JSON root must be an object")
        return LLMCallResult(provider=self.provider, model=self.model, raw_text=text, payload=payload)


class AnthropicJSONClient(BaseJSONLLMClient):
    provider = "anthropic"

    def __init__(self, api_key: str | None, model: str) -> None:
        super().__init__(api_key=api_key, model=model)
        self._client = None
        if not api_key:
            return
        try:
            from anthropic import Anthropic  # type: ignore

            self._client = Anthropic(api_key=api_key)
        except Exception:
            self._client = None

    def is_available(self) -> bool:
        return self._client is not None

    def generate_json(self, system_prompt: str, user_prompt: str) -> LLMCallResult:
        if not self._client:
            raise RuntimeError("Anthropic client unavailable")

        message = self._client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        text_parts: list[str] = []
        for block in getattr(message, "content", []):
            if getattr(block, "type", "") == "text":
                text_parts.append(getattr(block, "text", ""))
        text = "\n".join(part for part in text_parts if part)

        payload = extract_json_from_text(text)
        if not isinstance(payload, dict):
            raise ValueError("Anthropic response JSON root must be an object")
        return LLMCallResult(provider=self.provider, model=self.model, raw_text=text, payload=payload)


class OpenAICompatibleJSONClient(OpenAIJSONClient):
    provider = "openai_compatible"

    def __init__(self, api_key: str | None, model: str, base_url: str | None) -> None:
        # Many local servers accept any non-empty API key; default to placeholder if absent.
        effective_key = api_key or "local-api-key"
        super().__init__(api_key=effective_key, model=model, base_url=base_url)
        self.base_url = base_url

    def is_available(self) -> bool:
        if not (bool(self.base_url) and super().is_available()):
            return False

        probe_url = f"{self.base_url.rstrip('/')}/models"
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = request.Request(url=probe_url, headers=headers, method="GET")
        try:
            with request.urlopen(req, timeout=3) as resp:
                return 200 <= int(getattr(resp, "status", 0) or 0) < 500
        except error.HTTPError as exc:
            # 401/403/404 still proves server is reachable.
            return exc.code in {401, 403, 404}
        except Exception:
            return False


class OllamaJSONClient(BaseJSONLLMClient):
    provider = "ollama"

    def __init__(self, model: str, host: str | None) -> None:
        super().__init__(api_key=None, model=model)
        self.host = (host or "http://localhost:11434").rstrip("/")

    def is_available(self) -> bool:
        return bool(self.host)

    def generate_json(self, system_prompt: str, user_prompt: str) -> LLMCallResult:
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{self.host}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")

        parsed = json.loads(raw)
        message = parsed.get("message", {}) if isinstance(parsed, dict) else {}
        text = str(message.get("content") or "{}")

        json_payload = extract_json_from_text(text)
        if not isinstance(json_payload, dict):
            raise ValueError("Ollama response JSON root must be an object")
        return LLMCallResult(provider=self.provider, model=self.model, raw_text=text, payload=json_payload)


class HuggingFaceLocalJSONClient(BaseJSONLLMClient):
    provider = "hf_local"

    def __init__(self, model: str, model_dir: str | None = None, max_new_tokens: int = 1400) -> None:
        super().__init__(api_key=None, model=model)
        self.model_dir = model_dir
        self.max_new_tokens = max_new_tokens
        self._n_ctx = self._resolve_n_ctx()
        self._tokenizer = None
        self._model = None
        self._llama = None
        self._torch = None
        self._load_error: str | None = None

    @staticmethod
    def _resolve_n_ctx() -> int:
        raw = (os.getenv("HF_LOCAL_N_CTX") or "12288").strip()
        try:
            value = int(raw)
        except Exception:
            value = 12288
        # Keep a sensible lower bound for short prompts while allowing user override.
        return max(2048, value)

    def _resolve_model_source(self) -> tuple[str, bool]:
        direct = Path(self.model)
        if direct.exists():
            return str(direct), True

        if self.model_dir:
            candidate = Path(self.model_dir) / self.model.split("/")[-1]
            if candidate.exists():
                return str(candidate), True

        if self.model_dir:
            model_dir_path = Path(self.model_dir)
            if model_dir_path.exists() and model_dir_path.is_dir():
                gguf_files = sorted(model_dir_path.glob("*.gguf"))
                if gguf_files:
                    return str(gguf_files[0]), True

        return self.model, False

    def _ensure_loaded(self) -> None:
        if self._model is not None or self._load_error is not None:
            return

        source, local_files_only = self._resolve_model_source()
        try:
            if source.lower().endswith(".gguf"):
                from llama_cpp import Llama  # type: ignore

                self._llama = Llama(
                    model_path=source,
                    n_ctx=self._n_ctx,
                    n_threads=max(1, (os.cpu_count() or 4) // 2),
                    verbose=False,
                )
                return

            import torch  # type: ignore
            from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore

            self._torch = torch
            use_cuda = torch.cuda.is_available()
            dtype = torch.float16 if use_cuda else torch.float32

            tokenizer = AutoTokenizer.from_pretrained(
                source,
                local_files_only=local_files_only,
                trust_remote_code=True,
            )
            model = AutoModelForCausalLM.from_pretrained(
                source,
                local_files_only=local_files_only,
                trust_remote_code=True,
                torch_dtype=dtype,
                low_cpu_mem_usage=True,
            )
            if use_cuda:
                model = model.to("cuda")

            self._tokenizer = tokenizer
            self._model = model
        except Exception as exc:
            self._load_error = str(exc)

    def is_available(self) -> bool:
        self._ensure_loaded()
        if self._llama is not None:
            return True
        return self._model is not None and self._tokenizer is not None

    def _build_prompt(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        if self._tokenizer is not None and hasattr(self._tokenizer, "apply_chat_template"):
            try:
                return self._tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:
                pass

        return (
            "System:\n"
            f"{system_prompt}\n\n"
            "User:\n"
            f"{user_prompt}\n\n"
            "Assistant:\n"
            "Return only valid JSON."
        )

    def generate_json(self, system_prompt: str, user_prompt: str) -> LLMCallResult:
        self._ensure_loaded()
        if self._llama is not None:
            try:
                response = self._llama.create_chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )
                text = str(response["choices"][0]["message"]["content"])
            except Exception:
                response = self._llama.create_chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.0,
                )
                text = str(response["choices"][0]["message"]["content"])

            payload = extract_json_from_text(text)
            if not isinstance(payload, dict):
                raise ValueError("Hugging Face GGUF response JSON root must be an object")
            return LLMCallResult(provider=self.provider, model=self.model, raw_text=text, payload=payload)

        if self._model is None or self._tokenizer is None or self._torch is None:
            detail = f" Details: {self._load_error}" if self._load_error else ""
            raise RuntimeError(f"Hugging Face local client unavailable.{detail}")

        prompt = self._build_prompt(system_prompt=system_prompt, user_prompt=user_prompt)
        tokenized = self._tokenizer(prompt, return_tensors="pt")
        input_ids = tokenized["input_ids"]
        attention_mask = tokenized.get("attention_mask")

        if self._torch.cuda.is_available():
            input_ids = input_ids.to("cuda")
            if attention_mask is not None:
                attention_mask = attention_mask.to("cuda")

        eos_id = self._tokenizer.eos_token_id
        pad_id = self._tokenizer.pad_token_id if self._tokenizer.pad_token_id is not None else eos_id

        with self._torch.inference_mode():
            generated = self._model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                pad_token_id=pad_id,
            )

        completion_tokens = generated[0][input_ids.shape[-1] :]
        text = self._tokenizer.decode(completion_tokens, skip_special_tokens=True)

        payload = extract_json_from_text(text)
        if not isinstance(payload, dict):
            raise ValueError("Hugging Face local response JSON root must be an object")
        return LLMCallResult(provider=self.provider, model=self.model, raw_text=text, payload=payload)


class UnavailableJSONClient(BaseJSONLLMClient):
    provider = "unavailable"

    def __init__(self, provider_name: str, model: str) -> None:
        super().__init__(api_key=None, model=model)
        self.provider = provider_name

    def is_available(self) -> bool:
        return False

    def generate_json(self, system_prompt: str, user_prompt: str) -> LLMCallResult:
        raise RuntimeError(f"Provider '{self.provider}' is not available")


def build_llm_client(
    provider: str,
    model: str,
    openai_api_key: str | None,
    anthropic_api_key: str | None,
    role_api_key: str | None,
    role_base_url: str | None,
    role_model_dir: str | None,
    ollama_host: str | None,
) -> BaseJSONLLMClient:
    provider_key = (provider or "").strip().lower()

    if provider_key == "openai":
        return OpenAIJSONClient(
            api_key=role_api_key or openai_api_key,
            model=model,
            base_url=role_base_url,
        )

    if provider_key == "anthropic":
        return AnthropicJSONClient(
            api_key=role_api_key or anthropic_api_key,
            model=model,
        )

    if provider_key in {"openai_compatible", "openai-compatible", "compatible"}:
        return OpenAICompatibleJSONClient(
            api_key=role_api_key or openai_api_key,
            model=model,
            base_url=role_base_url,
        )

    if provider_key == "ollama":
        return OllamaJSONClient(model=model, host=ollama_host)

    if provider_key in {"hf_local", "huggingface_local", "huggingface", "hf"}:
        return HuggingFaceLocalJSONClient(
            model=model,
            model_dir=role_model_dir,
        )

    return UnavailableJSONClient(provider_name=provider or "unknown", model=model)
