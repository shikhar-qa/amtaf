# AMTAF MVP Specification

**Agentic Multi-Layer Test Automation Framework: proof-of-concept scope**

## 1. Purpose
Demonstrate that a plain-English test intent can be turned into an executed, cross-layer
test (GUI, API, hardware/CLI) with maximum reuse of existing test code and an automated
root-cause explanation on failure. This is a working vertical slice, not a production
system.

## 2. Demo target
A simulated device run with `docker compose up`: sshd, a web management console, a REST
API, `/etc/device.conf`, `/var/log/device.log`, and a fault-injection flag that makes the UI
report success while the backend fails to persist the change.

## 3. Demo scenario
"Set the syslog server to 10.0.0.5 in the management UI and verify it was applied on the
device within 10 seconds."

## 4. MVP requirements
| ID | Requirement |
|---|---|
| M-1 | **Intent to Task Graph.** English input becomes a Pydantic-validated Task Graph; each step tagged GUI, API or HARDWARE_CLI with an expected result and optional SLA. |
| M-2 | **SLA provenance.** Every SLA is `explicit` or `inferred`; inferred values require human confirmation. |
| M-3 | **LLM abstraction.** All model calls go through one interface switchable via `LLM_PROVIDER`, with schema-enforced output and a recorded-response mode. |
| M-4 | **Reuse scan.** Before generating code, index existing helpers (AST) and steps (similarity). Above-threshold matches are reused; gray-zone matches are flagged for review. |
| M-5 | **Minimal synthesis.** Only missing steps are generated (`.feature` + typed pytest-bdd steps) and must pass black, flake8 and mypy. |
| M-6 | **Reuse report.** Each run prints reused vs. generated counts. |
| M-7 | **Three drivers.** Playwright (GUI), requests (API), paramiko (SSH) with a command allowlist. |
| M-8 | **Bench lock.** Redis lock with TTL; released automatically if a run crashes. |
| M-9 | **Artifact capture on failure.** Screenshot, API dump, device log tail, tied together by a shared run id. |
| M-10 | **Triage agent.** Root-cause summary naming the failing layer, with confidence and evidence; never files defects automatically. |
| M-11 | **Reporting.** pytest-bdd results in Allure format with artifacts and RCA attached. |
| M-12 | **Git safety.** Generated tests go to a feature branch only. |

## 5. Acceptance criteria
1. The scenario produces a valid Task Graph with GUI and HARDWARE_CLI steps and a confirmed SLA.
2. The reuse report shows at least one reused and one generated step.
3. In normal mode the test passes end to end.
4. With the fault flag on, the test fails and the RCA states the UI accepted the change but the device config was not updated, citing the log line.
5. Two simultaneous runs against the same device are serialized by the lock.
6. `make demo` runs the full flow from a clean checkout.

## 6. Out of scope (roadmap)
Slack/Teams ChatOps, Streamlit/Gradio console, TestRail/Jira/Xray sync, Celery queue,
serial/IPMI drivers, gRPC/WebSocket streaming, visual regression, automated PR creation,
flaky-test quarantine, secrets management.

## 7. Known limitations
The device is simulated. Reuse matching quality depends on the embedding model. Triage
accuracy is demonstrated on injected faults only, not measured at scale.
