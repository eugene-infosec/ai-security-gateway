# Documentation Index

> **Truth scope:** accurate as of **v1.0.0**.

This folder is the documentation hub for the repository. If you only have a few minutes, use one of the guided paths below.

---

## 🏁 Start Here

- **Fast orientation:** Read **[Architecture](./architecture.md)**, then skim **[Controls Catalog](./controls.md)**.
- **Proof-first:** Jump to **[Operations](./operations.md)** and run `make verify`.

---

## 🕵️ If you’re an Auditor / Security Reviewer

1.  **Controls + Evidence Mapping (Authoritative):** **[Controls Catalog](./controls.md)**
2.  **Threat Model:** **[Threat Model](./threat_model.md)**
3.  **System Trust Boundary + Data Flow:** **[Architecture](./architecture.md)**
4.  **Evidence Index (Screenshots + Artifacts):** **[Evidence Index](../evidence/INDEX.md)**
5.  **How to Reproduce Proofs:** **[Operations](./operations.md)**

> **Suggested review order:** Controls → Threat Model → Architecture → Evidence → Operations.

---

## 👷 If you’re an Engineer / Maintainer

1.  **How to Run / Verify / Demo / Tear Down:** **[Operations](./operations.md)**
2.  **System Map:** **[Architecture](./architecture.md)**
3.  **Controls to Preserve:** **[Controls Catalog](./controls.md)**
4.  **Attacker Model:** **[Threat Model](./threat_model.md)**
5.  **Design Decisions (ADRs):** **[Decisions](./decisions/)**

---

## 📂 Key Documents

| File | Purpose |
| :--- | :--- |
| **[Architecture](./architecture.md)** | High-level data flow, trust boundary, and identity modes. |
| **[Controls Catalog](./controls.md)** | **Canonical source** for controls, implementation logic, and evidence links. |
| **[Operations](./operations.md)** | The unified guide for Demos, Runbooks, Costs, and Teardown. |
| **[Threat Model](./threat_model.md)** | Asset definitions, risks, and mitigations (STRIDE-aligned). |
| **[Public Sector Notes](./public_sector_notes.md)** | Context for FOIPPA/PIPA alignment and data residency. |
| **[Azure Mapping](./azure_mapping.md)** | Translation of AWS patterns to the Azure Enterprise Stack. |

---

## ⚡ Quick Picks

* **“Show me it works” (2 min):** **[Operations](./operations.md)** → run `make verify`
* **“Prove it’s safe”:** **[Controls Catalog](./controls.md)** → **[Evidence Index](../evidence/INDEX.md)**
* **“Understand the system”:** **[Architecture](./architecture.md)**
