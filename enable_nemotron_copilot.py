#!/usr/bin/env python3
"""
Registers the remote vLLM-hosted Nemotron model as a custom OpenAI-compatible
model in VS Code Copilot Chat, by merging an entry into the user's settings.json.

Run this ON THE MACHINE WHERE VS CODE RUNS (not on the Nemotron host).
"""
import json
import os
import platform
import sys

NEMOTRON_HOST = "100.116.120.61"  # this machine's Tailscale IP
NEMOTRON_PORT = 8000
MODEL_ID = "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4"
MODEL_DISPLAY_NAME = "Nemotron 3 Super 120B (local vLLM)"


def settings_path() -> str:
    system = platform.system()
    if system == "Windows":
        base = os.environ["APPDATA"]
        return os.path.join(base, "Code", "User", "settings.json")
    if system == "Darwin":
        return os.path.expanduser(
            "~/Library/Application Support/Code/User/settings.json"
        )
    # Linux
    return os.path.expanduser("~/.config/Code/User/settings.json")


def load_settings(path: str) -> dict:
    if not os.path.exists(path):
        sys.exit(f"settings.json not found at {path} -- is VS Code installed here?")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return json.loads(text) if text.strip() else {}


def main():
    path = settings_path()
    settings = load_settings(path)

    settings.setdefault("github.copilot.chat.customOAIModels", {})
    settings["github.copilot.chat.customOAIModels"][MODEL_ID] = {
        "name": MODEL_DISPLAY_NAME,
        "url": f"http://{NEMOTRON_HOST}:{NEMOTRON_PORT}/v1/chat/completions",
        "toolCalling": True,
        "vision": False,
        "maxInputTokens": 8192,
        "maxOutputTokens": 4096,
    }

    backup_path = path + ".bak"
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(load_settings(path), f, indent=2)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

    print(f"Updated {path}")
    print(f"Backup saved to {backup_path}")
    print("Restart VS Code, then enable the model in Chat > Manage Models.")


if __name__ == "__main__":
    main()
