# Contributing to Laufgitter

Thank you for your interest in contributing to Laufgitter. This guide outlines our design principles, development expectations, and review standards to help your pull requests move from submission to merge smoothly and efficiently.

---

## Core Philosophy

Our review decisions reflect three foundational architectural tenets:

### 1. Verify outputs; do not confine workers
Laufgitter operates on a strict verification model: an exit code of `0` from an executed check command is the primary source of truth. Correctness is proven by evaluating the concrete artifacts produced by a task, rather than by imposing speculative guardrails or artificial sandbox constraints on the worker processes. 

PRs introducing runtime restrictions, credential deny-lists, or worker-level containment are considered out of scope. Process sandboxing belongs upstream in the agent CLIs or within containerized/VM execution environments managed by the operator. We prioritize explicit, verifiable guarantees over safety theater.

### 2. Operational evaluation over synthetic benchmarking
Laufgitter tracks performance, cost, and reliability metrics as an organic byproduct of real-world task execution. The scoreboard and eval log reflect actual operational workloads rather than synthetic benchmark suites. Dedicated bakeoff frameworks and benchmark harnesses should be maintained externally; Laufgitter's role is to reliably orchestrate the runs and capture empirical telemetry.

### 3. Absolute telemetry integrity
All diagnostic, operational, and telemetry surfaces must accurately depict system state. Misrepresenting model attribution, provider routing, execution status, or test outcomes is never acceptable. Consult [`docs/TAXONOMY.md`](docs/TAXONOMY.md) for normative model identification. Sourced technical facts belong in the registry; subjective assessments and operational notes belong as dated entries in [`docs/MODEL-NOTES.md`](docs/MODEL-NOTES.md).

---

## Standards for Pull Requests

To ensure rapid review and seamless integration, pull requests should adhere to these guidelines:

1. **Focused and Scoped:** Submit one distinct bug fix, feature, or improvement per PR. Large, sprawling changes that combine unrelated refactors or multiple features will be requested to be split into separate, self-contained PRs.
2. **Current with Main:** Rebase your branch onto the latest `main` branch before opening or updating your pull request.
3. **Deterministic Automated Verification:** Every functional claim must be backed by an executed test. Checks should provide clear, descriptive diagnostic messages on failure rather than silent non-zero exits.
4. **Adherence to Architecture:**
   - Single-file, standard-library-only design for `laufgitter.py`.
   - Supported Python version: Python 3.12+.
   - Immutable data models (`@dataclass(frozen=True)`).
   - Test suites organized under `tests/` and discoverable via `python3 -m unittest discover -s tests`.
   - Explicit environment guards (e.g., `LAUFGITTER_NO_SELF_UPDATE=1`) during automated test execution.
5. **Clear Motivation:** Articulate the concrete problem or workflow failure being addressed. Evidence from real runs helps prioritize review.

---

## Contributing to Zentrale UI

We welcome modular additions and alternative interfaces for the Zentrale monitoring dashboard:

- **Consistent Data Contracts:** Consume existing `/api/runs`, `/api/library`, and `/api/models` JSON contracts. Use fixtures for offline component and rendering tests.
- **Strictly Self-Contained:** Zero dependencies on external CDNs or remote assets. Vendor all required static resources locally.
- **Defensive Rendering:** Sanitize and escape all run identifiers and captured worker output.
- **Opt-in Customization:** New dashboards or themes should arrive as configurable options rather than replacing the default interface.

---

## Review and Merge Process

- **Prompt, Transparent Feedback:** If a proposed change falls outside project scope or architectural priorities, reviewers will provide clear technical rationale explaining the decision.
- **Collaborative Refinement:** Maintainers may suggest minor mechanical adjustments to align with project conventions, keeping the review process constructive and focused on technical merit.

---

## Recommended Focus Areas

High-impact areas where community contributions are especially useful include:

- **Empirical Model Insights:** Documenting reproducible model behavior, failure modes, or strengths in `docs/MODEL-NOTES.md`.
- **Reusable Workflow Templates:** Providing structured manifests and validators in `templates/` for common swarm coordination patterns.
- **Platform Portability:** Improving cross-platform compatibility, including extending automated testing across operating systems.
- **Registry Capabilities:** Maintaining accurate, sourced specifications in `registry/model-capabilities/` (supported token limits, canonical routes, and API options).
