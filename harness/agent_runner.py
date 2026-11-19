"""Agent-under-test runner. Copied into the container's /opt/harness (root, 0700) right before the run and
removed afterwards; runs as root and starts the Claude Code CLI as the unprivileged `agent` user, so the
agent can read neither this file nor the condition file.

Reads /opt/harness/condition.json, writes /opt/harness/out/transcript.jsonl (scorer format, one SDK
message per line) and /opt/harness/out/run_meta.json.
"""
import asyncio
import dataclasses
import json
import os
import time

from claude_agent_sdk import ClaudeAgentOptions, query

H = "/opt/harness"


def block_dict(b):
    d = dataclasses.asdict(b) if dataclasses.is_dataclass(b) else {"raw": repr(b)}
    d["type"] = {"TextBlock": "text", "ToolUseBlock": "tool_use", "ToolResultBlock": "tool_result",
                 "ThinkingBlock": "thinking"}.get(type(b).__name__, type(b).__name__)
    return d


def msg_dict(m):
    name = type(m).__name__
    if name in ("AssistantMessage", "UserMessage"):
        d = {k: v for k, v in dataclasses.asdict(m).items() if k != "content"}
        d["type"] = "assistant" if name == "AssistantMessage" else "user"
        d["content"] = ([{"type": "text", "text": m.content}] if isinstance(m.content, str)
                        else [block_dict(b) for b in m.content])
        return d
    d = dataclasses.asdict(m) if dataclasses.is_dataclass(m) else {"raw": repr(m)}
    d["type"] = {"ResultMessage": "result", "SystemMessage": "system"}.get(name, name)
    return d


async def main():
    cond = json.load(open(f"{H}/condition.json"))
    os.makedirs(f"{H}/out", exist_ok=True)
    opts = ClaudeAgentOptions(
        model=cond["model"],
        system_prompt=cond["system_prompt"],          # None -> SDK minimal default (empty --system-prompt)
        setting_sources=["project"],                  # same in every cell; only mem cells have a CLAUDE.md
        tools=["Read", "Edit", "Write", "Bash", "Glob", "Grep"],
        permission_mode="bypassPermissions",          # inside the container only, as non-root `agent`
        max_turns=cond["max_turns"],
        max_budget_usd=cond["max_budget_usd"],
        cwd="/work",
        user="agent",
        env={"HOME": "/home/agent", "USER": "agent", "LOGNAME": "agent"},
    )
    t0, max_prompt, n = time.time(), 0, 0
    with open(f"{H}/out/transcript.jsonl", "w") as f:
        async for m in query(prompt=cond["prompt"], options=opts):
            d = msg_dict(m)
            f.write(json.dumps(d, default=repr) + "\n")
            f.flush()
            u = d.get("usage") if d["type"] == "assistant" else None
            if u:
                n += 1
                max_prompt = max(max_prompt, u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                                 + u.get("cache_creation_input_tokens", 0))
    json.dump({"wall_s": round(time.time() - t0, 1), "max_prompt_tokens": max_prompt,
               "over_100k": max_prompt > 100_000, "assistant_messages_with_usage": n},
              open(f"{H}/out/run_meta.json", "w"))


asyncio.run(main())
