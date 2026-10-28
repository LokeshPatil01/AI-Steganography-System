# AI-Based Adaptive Steganography System with Automated Key Generation

## Project Overview
This repository contains the complete implementation of the final-year B.Tech project:
**"AI-Based Adaptive Steganography System with Automated Key Generation"**.

A hybrid, research-oriented steganographic framework combining:
1. **Authenticated Hybrid Cryptography**: AES-256-GCM message encryption paired with RSA-4096-OAEP key encapsulation.
2. **Automated Key Lifecycle & Vaulting**: Automatic generation, encryption-at-rest, and delivery of cryptographic keys via ASP.NET Core and SQL Server.
3. **Feature-Driven & AI Region Suitability Prediction**: Feature extraction (Sobel gradients, Canny edge density, Shannon entropy, local variance) evaluated by a Scikit-Learn Random Forest model.
4. **Dynamic Embedding Strength & Randomized Distribution**: Key-derived PRNG coordinate mapping with variable bit allocations (1–3 bits/pixel).
5. **Deep Learning Steganalysis & Feedback Loop**: A lightweight PyTorch convolutional neural network (CNN) evaluating detectability and triggering iterative embedding adjustments.
6. **Empirical Quality & Robustness Evaluation**: PSNR, SSIM, MSE, BER, and noise/compression resilience profiling.

See [PROJECT_ARCHITECTURE.md](file:///C:/Users/Om%20Pol/.gemini/antigravity-ide/scratch/AI-Steganography-System/PROJECT_ARCHITECTURE.md) for the complete design specification.

---

## Phase Implementation Status

| Phase | Description | Status | Verification |
|---|---|---|---|
| **Phase 0** | Project Planning & Architecture Specification | ✅ Complete | [PROJECT_ARCHITECTURE.md](file:///C:/Users/Om%20Pol/.gemini/antigravity-ide/scratch/AI-Steganography-System/PROJECT_ARCHITECTURE.md) |
| **Phase 1** | Project Structure & Multi-Service Initialization | ✅ Complete | React, ASP.NET Core & FastAPI verified |
| **Phase 2** | SQL Server Database Design & Migrations | ✅ Complete | EF Core `StegoDb` created & migrated |
| **Phase 3** | User Authentication & JWT Security | ✅ Complete | PBKDF2 + JWT + 11 Automated Tests Passed |
| **Phase 4** | Automated RSA Key Generation & Protected Storage | ✅ Complete | RSA-4096 + AES-GCM Vaulting + 17 Tests Passed |
| **Phase 5** | AES-256-GCM Authenticated Encryption Module | ✅ Complete | AES-GCM + 15 Python Tests Passed |
| **Phase 6** | RSA + AES Hybrid Envelope Encryption | ✅ Complete | RSA-OAEP + AES-GCM Envelope + 26 Tests Passed |
| **Phase 7** | Basic Spatial LSB Steganography Engine | ✅ Complete | Baseline LSB + FastAPI Endpoints + 37 Tests Passed |
| **Phase 8** | Image Analysis & Spatial Feature Extraction | ✅ Complete | OpenCV Features (Entropy, Sobel, Canny) + 44 Tests Passed |
| **Phase 9** | Image Quality Metrics (PSNR, SSIM, MSE, BER) | ✅ Complete | Full-Reference Metrics + CSV Audit + 62 Tests Passed |
| **Phase 10** | Adaptive Steganography Without AI (Rule-Based) | ✅ Complete | MSB-Invariance + Block Ranking + 73 Tests Passed |
| **Phase 11** | Dataset Creation for AI Region Model | ✅ Complete | 3,000 Balanced Samples + 8 Features + 82 Tests Passed |
| **Phase 12** | Train AI Region Model (Random Forest) | ✅ Complete | 100 Trees + 100% Test Acc + ROC-AUC 1.000 + 89 Tests Passed |
| **Phase 13** | Integrate Region AI Model into FastAPI | ✅ Complete | Endpoints (/analyze, /heatmap) + React Inspector + 98 Tests Passed |
| **Phase 14** | AI-Selected Dynamic LSB Embedding | ✅ Complete | Random Forest Block Ranking + MSB Invariance + 3-Way Benchmark + 113 Tests Passed |
| **Phase 15** | PRNG Key-Based Random Block Scatter | ✅ Complete | HKDF-SHA256 + Fisher-Yates Permuter + 130 Tests Passed |
| **Phase 16** | Deep Learning Steganalyzer CNN Training | ✅ Complete | PyTorch SRM CNN + 91.67% Acc + ROC-AUC 0.9630 + 142 Tests Passed |
| **Phase 17** | Feedback Optimization Loop | ✅ Complete | Closed-Loop Adversarial CNN + Reallocation + 149 Tests Passed |
| **Phase 18** | One-Click End-to-End Orchestration Pipeline | ✅ Complete | Unified Multi-Tier Pipeline + SQL Server Audit + 154 Tests Passed |
| **Phase 19** | Robustness & Noise Perturbation Profiling | ✅ Complete | Gaussian, Salt & Pepper, and JPEG Compression Resilience Suite + 171 Tests Passed |
| **Phase 20** | Multi-Objective Genetic / Pareto Optimization | ✅ Complete | Evolutionary Parameter Search + Non-Dominated Pareto Frontier + 182 Tests Passed |

---

## System Verification Summary
* **Python Engine**: `pytest tests/` $\to$ **182/182 passed** (16.17s, Genetic Optimizer, Pareto Frontier, Robustness Profiler, Perturbation Engine, Pipeline Orchestrator, Feedback Loop, CNN Steganalyzer, PRNG Scatter, AI Stego, Heatmap, Random Forest, Dataset Gen, Adaptive Rules, Metrics, Features, LSB, Hybrid, AES-GCM)
* **ASP.NET Core Backend**: `dotnet test` $\to$ **18/18 passed** (4.0s, Operations Audit, Keys, Auth, DB Integration tests)
* **SQL Server LocalDB**: `(localdb)\mssqllocaldb` $\to$ Database `StegoDb` active and migrated
* **React Frontend**: `npm run build` $\to$ **Vite build clean** (0 errors, 3.40s)
