# AMTAF: Agentic Multi-Layer Test Automation Framework

A proof of concept showing how an LLM-driven framework can turn **plain-English test
intent** into an executed **GUI + hardware (SSH)** test, while **reusing existing test
code** instead of duplicating it, and explaining failures across layers.

> Scope: a working vertical slice, not a production system. See
> [docs/MVP_SPEC.md](docs/MVP_SPEC.md) for scope and the roadmap for what is intentionally missing.

## The idea in one scenario

> "Set the syslog server to 10.0.0.5 in the management UI and verify it was applied
> on the device within 10 seconds."

```
English intent
   -> Orchestrator      typed, validated Task Graph (Pydantic), steps tagged GUI / API / HARDWARE_CLI
   -> Codebase scanner  AST index of drivers + step library, similarity match per step
        s1 REUSE 1.00   s2 REUSE 1.00   s3 GENERATE 0.57
   -> Synthesizer       .feature file + ONLY the missing step, gated by black/flake8/mypy
   -> Runner            pytest-bdd (+ Allure), bench lock, allowlisted SSH, shared run id
   -> Triage            on failure: artifacts from every layer -> root-cause summary + confidence
```

Demo target: a simulated appliance in Docker (sshd + web console + REST API). A fault
flag makes the UI report **Saved** without persisting, so the GUI passes while the device
check fails. Cross-layer diagnosis is the point.

## Quick start

Offline, no Docker or API key (replays recorded LLM responses):

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest                      # unit tests
python -m amtaf.cli generate "Set the syslog server to 10.0.0.5 in the management UI and verify it was applied on the device within 10 seconds."
```

Full demo (needs Docker, plus Playwright for the GUI layer):

```bash
make install
make demo          # GUI change is applied on the device -> PASS
make demo-fault    # UI says Saved, device never persists -> FAIL + RCA
```

A real LLM instead of recordings: set `LLM_PROVIDER` to anything other than `recorded`,
`LLM_MODEL` to a LiteLLM model string, and the provider's API key. See `.env.example`.

## Design decisions worth reading

- **Reuse is a decision, not a hope.** Matches score against thresholds
  (`REUSE >= 0.80`, `REVIEW >= 0.60`, otherwise `GENERATE`). The gray zone stops and asks a
  human rather than silently reusing the wrong step. The scorer is a dependency-free bag of
  words behind one function; a real embedding model + vector store drops in there.
- **SLA provenance.** Every SLA is `explicit` or `inferred`. Inferred ones block generation
  until a human confirms, since a model-invented threshold can make a test meaningless.
- **Hardware safety.** The SSH driver only runs allowlisted commands. Generated tests cannot
  reboot, flash, or delete anything.
- **Bench lock with a TTL** (Redis) so two runs can't drive one device, and a crashed run
  can't hold it forever.
- **Cross-layer correlation.** One run id is sent to the GUI and API as `X-Run-Id` and
  written into the device log, so the triage step can tie a UI symptom to a device log line.
- **Generated code never goes to `main`.** `git_flow.py` creates `amtaf/<name>` branches only.
- **Tag format.** The spec's `@key=value` tags work in pytest-bdd (they become markers) but
  can't be used with `-m`; select with `-k` instead. The unknown-marker warning is silenced
  in `pyproject.toml`.

## Status: what is and isn't verified

| Area | Status |
|---|---|
| Task Graph models and validation, SLA provenance | Implemented, unit tested |
| AST + similarity reuse scan, thresholds | Implemented, unit tested |
| Synthesis + black/flake8/mypy gate | Implemented, tested end to end (offline) |
| Command allowlist | Implemented, unit tested |
| Bench lock | Implemented, unit tested against fakeredis only |
| Device simulator (console, API, fault flag, run-id logging) | Implemented, unit tested |
| Generated scenario run against the device app (pass and fault paths) | Run against the real app over HTTP with stand-in console/SSH fixtures |
| Docker image / compose, real sshd + paramiko | **Written, not yet run** |
| Playwright GUI driver | **Written, not yet run** |
| Redis against a real server, LiteLLM provider path | **Written, not yet run** |
| Allure report generation | Wired via `--alluredir`, **not yet viewed** |
| Triage agent | Recorded mode returns a **canned** answer (and says so); real-LLM triage is untested |

Roadmap (intentionally out of scope): Slack/Teams ChatOps, web console, TestRail/Jira sync,
Celery queue, serial/IPMI, gRPC/WebSocket, visual regression, automated PR creation,
flaky-test quarantine, secrets management.

## Layout

```
amtaf/         orchestrator/ scanner/ synth/ drivers/ runner/ triage/ llm/ lock.py cli.py
demo/device/   simulated appliance (FastAPI + sshd) and Dockerfile
tests/existing seed step library the scanner indexes for reuse
tests/unit     unit + offline pipeline tests
generated/     sample output of `amtaf generate` (reviewed via PR in real use)
recordings/    canned LLM responses for the offline demo
```
