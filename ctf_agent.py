#!/usr/bin/env python3
"""
CTF Autonomous Agent powered by Ollama (qwen2.5-coder:3b)
Solves CTF challenges by autonomously running commands like a human hacker.
"""

import subprocess
import requests
import json
import re
import sys
import os
import time
from datetime import datetime

# ─── CONFIG ──────────────────────────────────────────────────────────────────
OLLAMA_URL   = "http://localhost:11434/api/chat"
MODEL        = "qwen2.5-coder:3b"
MAX_STEPS    = 30          # max reasoning + command cycles
CMD_TIMEOUT  = 30          # seconds per shell command
LOG_FILE     = "ctf_agent.log"

# ─── SYSTEM PROMPT ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert CTF (Capture The Flag) hacker agent.
Your goal is to autonomously solve the given CTF challenge by reasoning and running shell commands.

RULES:
1. Think step-by-step about what to do next.
2. To run a command, output it in this EXACT format on its own line:
   CMD: <your shell command here>
3. Only ONE CMD per response.
4. After seeing the command output, analyse it and decide the next step.
5. When you find the flag (format: flag{...} or CTF{...} or similar), output:
   FLAG: <the flag value>
6. Be creative: use nmap, curl, wget, strings, file, base64, python3, xxd, nc, openssl, john, hashcat, binwalk, gdb, ltrace, strace, etc.
7. Never give up — try different approaches if one fails.
8. Keep responses concise; focus on reasoning and the next command.
"""

# ─── LOGGING ─────────────────────────────────────────────────────────────────
def log(msg: str, color: str = ""):
    colors = {"red": "\033[91m", "green": "\033[92m", "yellow": "\033[93m",
              "cyan": "\033[96m", "bold": "\033[1m", "": ""}
    reset = "\033[0m" if color else ""
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(f"{colors.get(color,'')}{line}{reset}")
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ─── OLLAMA CHAT ──────────────────────────────────────────────────────────────
def chat(messages: list[dict]) -> str:
    payload = {"model": MODEL, "messages": messages, "stream": False}
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["message"]["content"]
    except requests.exceptions.ConnectionError:
        log("ERROR: Cannot connect to Ollama. Is it running? (ollama serve)", "red")
        sys.exit(1)
    except Exception as e:
        log(f"Ollama error: {e}", "red")
        return ""

# ─── SHELL COMMAND RUNNER ─────────────────────────────────────────────────────
def run_command(cmd: str) -> str:
    log(f"$ {cmd}", "cyan")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=CMD_TIMEOUT, cwd=os.getcwd()
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += result.stderr
        output = output.strip()
        if not output:
            output = "(no output)"
        # Truncate very long outputs
        if len(output) > 3000:
            output = output[:3000] + "\n... [output truncated]"
        log(output, "")
        return output
    except subprocess.TimeoutExpired:
        msg = f"(command timed out after {CMD_TIMEOUT}s)"
        log(msg, "yellow")
        return msg
    except Exception as e:
        msg = f"(error running command: {e})"
        log(msg, "red")
        return msg

# ─── PARSE MODEL RESPONSE ─────────────────────────────────────────────────────
def extract_cmd(text: str) -> str | None:
    """Extract CMD: ... from model response."""
    match = re.search(r"CMD:\s*(.+)", text)
    if match:
        return match.group(1).strip()
    return None

def extract_flag(text: str) -> str | None:
    """Extract FLAG: ... or flag{...} patterns."""
    # Explicit FLAG: marker
    match = re.search(r"FLAG:\s*(.+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Common flag patterns
    for pattern in [r"flag\{[^}]+\}", r"CTF\{[^}]+\}", r"picoCTF\{[^}]+\}"]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None

# ─── MAIN AGENT LOOP ─────────────────────────────────────────────────────────
def run_agent(challenge_description: str):
    log("=" * 60, "bold")
    log("  CTF AUTONOMOUS AGENT  —  powered by Ollama", "bold")
    log(f"  Model : {MODEL}", "bold")
    log("=" * 60, "bold")
    log(f"Challenge:\n{challenge_description}\n", "yellow")

    # Initialise conversation
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content":
            f"Here is the CTF challenge to solve:\n\n{challenge_description}\n\n"
            "Start by analysing the challenge and running your first command."}
    ]

    flag_found = None

    for step in range(1, MAX_STEPS + 1):
        log(f"\n{'─'*50}", "bold")
        log(f"STEP {step}/{MAX_STEPS}", "bold")

        # Ask the model
        log("🤖 Thinking...", "cyan")
        response = chat(messages)
        if not response:
            log("Empty response from model. Retrying...", "yellow")
            continue

        log(f"\n{response}\n", "")

        # Append assistant turn
        messages.append({"role": "assistant", "content": response})

        # Check for flag
        flag = extract_flag(response)
        if flag:
            flag_found = flag
            break

        # Check for command
        cmd = extract_cmd(response)
        if cmd:
            output = run_command(cmd)
            # Feed output back as user message
            messages.append({
                "role": "user",
                "content": f"Command output:\n```\n{output}\n```\n\nAnalyse the output and continue."
            })
            # Check if flag appeared in command output
            flag = extract_flag(output)
            if flag:
                flag_found = flag
                log(f"\n🚩 Flag found in command output!", "green")
                break
        else:
            # No command — ask model to produce one
            messages.append({
                "role": "user",
                "content": "Please provide the next command using the format: CMD: <command>"
            })

    log("\n" + "=" * 60, "bold")
    if flag_found:
        log(f"🏆  FLAG CAPTURED: {flag_found}", "green")
    else:
        log("❌  Max steps reached without finding the flag.", "red")
        log("   Check ctf_agent.log for full session details.", "yellow")
    log("=" * 60, "bold")

# ─── ENTRY POINT ─────────────────────────────────────────────────────────────
def main():
    # Clear log
    open(LOG_FILE, "w").close()

    if len(sys.argv) > 1:
        # Challenge passed as CLI argument or file
        arg = sys.argv[1]
        if os.path.isfile(arg):
            with open(arg) as f:
                challenge = f.read()
        else:
            challenge = arg
    else:
        # Interactive prompt
        print("\n" + "="*60)
        print("  CTF AUTONOMOUS AGENT")
        print("="*60)
        print("Paste your CTF challenge description below.")
        print("Press ENTER twice when done.\n")
        lines = []
        try:
            while True:
                line = input()
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
        except EOFError:
            pass
        challenge = "\n".join(lines).strip()

    if not challenge:
        print("No challenge provided. Exiting.")
        sys.exit(1)

    run_agent(challenge)

if __name__ == "__main__":
    main()
