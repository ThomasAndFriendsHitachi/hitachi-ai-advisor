from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModelProfile:
    name: str
    role: str | None
    provider: str
    model: str
    base_url: str | None
    api_key_env: str | None
    model_dir: str | None


def load_model_profiles(path: Path) -> dict[str, ModelProfile]:
    if not path.exists():
        raise FileNotFoundError(f"Model profiles file not found: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed parsing model profiles JSON: {exc}") from exc

    rows = payload.get("profiles") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("Model profiles file must contain a 'profiles' list")

    profiles: dict[str, ModelProfile] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue

        name = str(row.get("name") or "").strip()
        provider = str(row.get("provider") or "").strip().lower()
        model = str(row.get("model") or "").strip()
        role_raw = row.get("role")
        role = str(role_raw).strip().lower() if isinstance(role_raw, str) and role_raw.strip() else None
        base_url_raw = row.get("base_url")
        api_key_env_raw = row.get("api_key_env")
        model_dir_raw = row.get("model_dir")

        if not name or not provider or not model:
            continue

        profiles[name] = ModelProfile(
            name=name,
            role=role,
            provider=provider,
            model=model,
            base_url=(str(base_url_raw).strip() if isinstance(base_url_raw, str) and base_url_raw.strip() else None),
            api_key_env=(
                str(api_key_env_raw).strip() if isinstance(api_key_env_raw, str) and api_key_env_raw.strip() else None
            ),
            model_dir=(str(model_dir_raw).strip() if isinstance(model_dir_raw, str) and model_dir_raw.strip() else None),
        )

    return profiles


def get_role_profile(profiles: dict[str, ModelProfile], profile_name: str, expected_role: str) -> ModelProfile:
    profile = profiles.get(profile_name)
    if not profile:
        available = ", ".join(sorted(profiles.keys())) or "none"
        raise ValueError(f"Unknown profile '{profile_name}'. Available profiles: {available}")

    if profile.role and profile.role != expected_role:
        raise ValueError(
            f"Profile '{profile_name}' has role '{profile.role}', expected '{expected_role}'"
        )

    return profile


def load_selected_profiles(
    profiles_path: Path,
    primary_profile_name: str | None,
    secondary_profile_name: str | None,
) -> tuple[ModelProfile | None, ModelProfile | None]:
    if not primary_profile_name and not secondary_profile_name:
        return None, None

    profiles = load_model_profiles(profiles_path)

    primary = get_role_profile(profiles, primary_profile_name, "primary") if primary_profile_name else None
    secondary = get_role_profile(profiles, secondary_profile_name, "secondary") if secondary_profile_name else None

    return primary, secondary
