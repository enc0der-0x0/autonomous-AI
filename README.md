# 🚩 CTF Autonomous Agent

An autonomous CTF (Capture The Flag) solver powered by a **local Ollama LLM**. It reasons about challenges, runs shell commands, analyses output, and iterates — just like a human hacker — until it finds the flag.

```
Challenge → LLM thinks → CMD: nmap 10.0.0.5 → output → LLM thinks → CMD: curl ... → FLAG{...}
```

> Runs entirely **offline** on your machine. No API keys. No data sent to the cloud.

---

## Features

- **Fully autonomous** — give it a challenge description and watch it work
- **Local & private** — uses [Ollama](https://ollama.com) with `qwen2.5-coder:3b` (or any model you prefer)
- **Real shell access** — runs `nmap`, `curl`, `nc`, `python3`, `strings`, `john`, `binwalk`, `gdb`, and anything else on your system
- **Adaptive reasoning** — the model analyses command output and adjusts its strategy
- **Session logging** — every step is saved to `ctf_agent.log`
- **Configurable** — tune max steps, timeout, and model at the top of the script

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.10+ |
| [Ollama](https://ollama.com) | Latest |
| `requests` Python library | Any recent |

Install the Python dependency:

```bash
pip install requests
```

Pull the model (if you haven't already):

```bash
ollama pull qwen2.5-coder:3b
```

---

## Installation

```bash
git clone https://github.com/0xEnc0der/ctf-agent
cd ctf-agent
pip install requests
```

---

## Usage

Make sure Ollama is running first:

```bash
ollama serve
```

### Pass challenge as an argument

```bash
python3 ctf_agent.py "There is a web server at 10.0.0.5:8080. Find the hidden flag."
```

### Pass a challenge file

```bash
python3 ctf_agent.py challenge.txt
```

### Interactive mode (paste & press Enter twice)

```bash
python3 ctf_agent.py
```

---

## Example Session

```
[10:42:01] ============================================================
[10:42:01]   CTF AUTONOMOUS AGENT  —  powered by Ollama
[10:42:01]   Model : qwen2.5-coder:3b
[10:42:01] ============================================================
[10:42:01] Challenge:
           Web server running at 192.168.1.50:8080. Find the flag.

[10:42:01] ──────────────────────────────────────────────────────────
[10:42:01] STEP 1/30
[10:42:01] 🤖 Thinking...
           I'll start by probing the web server to understand what's running.
           CMD: curl -s http://192.168.1.50:8080

[10:42:02] $ curl -s http://192.168.1.50:8080
           <html><body><!-- flag{h1dd3n_1n_html} --></body></html>

[10:42:03] ============================================================
[10:42:03] 🏆  FLAG CAPTURED: flag{h1dd3n_1n_html}
[10:42:03] ============================================================
```

---

## Configuration

At the top of `ctf_agent.py`:

```python
OLLAMA_URL  = "http://localhost:11434/api/chat"  # Ollama endpoint
MODEL       = "qwen2.5-coder:3b"                 # Model to use
MAX_STEPS   = 30                                 # Max reasoning cycles
CMD_TIMEOUT = 30                                 # Seconds per command
LOG_FILE    = "ctf_agent.log"                    # Session log path
```

### Using a different model

Any model available in Ollama works. Larger models generally perform better on harder challenges:

```python
MODEL = "qwen2.5-coder:7b"    # more capable, slower
MODEL = "llama3.2:3b"         # general purpose
MODEL = "deepseek-coder:6.7b" # strong at code/CTF
```

---

## How It Works

1. **System prompt** — the agent is primed with a hacker persona and told to emit commands in the format `CMD: <command>`
2. **Reasoning loop** — the LLM receives the challenge and responds with a command
3. **Execution** — the script runs the command via `subprocess` with a configurable timeout
4. **Feedback** — stdout + stderr are fed back to the LLM as the next user message
5. **Flag detection** — the script scans both LLM responses and command output for `flag{...}`, `CTF{...}`, `FLAG: ...` patterns
6. **Repeat** — continues until a flag is found or `MAX_STEPS` is reached

### Tools the agent can use

The agent has access to anything installed on your system, including:

```
nmap  curl  wget  nc  netcat  python3  ruby  perl
strings  file  xxd  base64  binwalk  exiftool
john  hashcat  openssl  gpg  steghide
gdb  ltrace  strace  objdump  radare2
sqlmap  gobuster  dirb  ffuf  hydra
```

---

## CTF Challenge Types

| Category | Example commands the agent might use |
|---|---|
| Web | `curl`, `gobuster`, `sqlmap` |
| Crypto | `python3`, `openssl`, `base64` |
| Forensics | `strings`, `binwalk`, `exiftool`, `xxd` |
| Reversing | `gdb`, `ltrace`, `objdump`, `strings` |
| Pwn | `python3`, `gdb`, `pwntools` |
| Network | `nmap`, `nc`, `wireshark` (tshark) |
| Steganography | `steghide`, `zsteg`, `exiftool` |

---

## Tips

- **Harder challenges** benefit from a larger model (7B+). `qwen2.5-coder:3b` is great for beginner/intermediate CTFs.
- **Increase `MAX_STEPS`** for complex multi-stage challenges.
- **Point the agent at real CTF targets** — HackTheBox, TryHackMe, PicoCTF, etc. Use responsibly and only on machines you are authorised to attack.
- **Check `ctf_agent.log`** after a run to review every step and learn from the agent's approach.

---

## Disclaimer

This tool is intended for **legal, authorised security research and CTF competitions only**. Do not use it against systems you do not own or have explicit permission to test. The authors are not responsible for any misuse.

---

## License

MIT
