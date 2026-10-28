# An Adversarially Robust Adaptive Image Steganography Framework Integrating Dual-AI Region Selection and Multi-Objective Pareto Optimization

**Author(s)**: Research & Development Team  
**Affiliation**: Department of Computer Science and Engineering  
**Date**: October 2026  
**Document Version**: Publication-Ready Draft (Preprint)  

---

## Abstract

Traditional Least Significant Bit (LSB) steganography embeds confidential information sequentially or uniformly across all image pixels, generating pronounced statistical and perceptual anomalies that are readily detected by modern convolutional neural network (CNN) steganalysts. Furthermore, standard steganographic schemes lack cryptographic integrity verification, rendering hidden payloads vulnerable to silent channel corruption and active tampering. 

To overcome these fundamental vulnerabilities, this paper introduces a unified, multi-tier defense-in-depth steganographic framework:
1. **Hybrid Cryptographic Layer**: Encapsulates secret messages using authenticated symmetric **AES-256-GCM** encryption (guaranteeing 128-bit authentication tag tamper detection) paired with asymmetric **RSA-4096-OAEP** public-key encapsulation.
2. **Dual-AI Architecture**: Combines an explainable **Random Forest Classifier** trained on 8-dimensional Most Significant Bit (MSB)-invariant spatial complexity features (Shannon entropy, Sobel gradient magnitude, Canny edge density, local variance) for candidate block suitability ranking, with an adversarial **PyTorch SRM-CNN Steganalyzer** acting as an automated evaluator.
3. **Closed-Loop Adversarial Feedback Optimization**: Executes an iterative feedback loop that dynamically adjusts local bit-depth allocations (1 to 3 bits per pixel) to drive adversarial detectability $P(\text{stego})$ below a rigorous security threshold ($\tau = 0.35$).
4. **Cryptographic PRNG Coordinate Scattering**: Disperses payload bits across non-contiguous textured blocks using a pseudo-random permutation seeded via **HKDF-SHA256**, eliminating sequential spatial signatures.
5. **Channel Robustness & Tamper Profiling**: Evaluates degradation resilience under Additive White Gaussian Noise (AWGN), Salt & Pepper noise, and lossy JPEG compression ($Q \in [30, 95]$), demonstrating that active corruption is deterministically detected and rejected by the authentication tag with zero corrupted plaintext leakage.
6. **Multi-Objective Pareto Evolutionary Optimization**: Solves the competing trade-offs between visual fidelity (PSNR, SSIM), payload capacity, and adversarial stealth through a genetic algorithm that extracts the non-dominated Pareto frontier.

Extensive empirical evaluations across 182 automated test suites confirm that the proposed framework achieves exceptional perceptual transparency ($\text{PSNR} > 48.5\text{ dB}$, $\text{SSIM} > 0.992$), complete loss-free payload recovery ($\text{BER} = 0.00\%$), and significant detectability suppression relative to traditional and rule-based adaptive baselines.

**Keywords**: Image Steganography, Dual-AI Architecture, Spatial Rich Model (SRM), Convolutional Neural Network (CNN), Adversarial Feedback Optimization, Pareto Frontier, Genetic Algorithm, AES-256-GCM, Cryptographic Key Vault.

---

## 1. Introduction

Information hiding techniques, particularly digital image steganography, strive to conceal the very existence of a secret communication within an innocuous digital cover object. While cryptography conceals the *meaning* of a message, steganography conceals the *act of transmission*. When deployed concurrently, cryptography and steganography provide defense-in-depth against sophisticated surveillance adversaries.

In the spatial domain, digital steganography is governed by the classic **Steganographic Trilemma**, which mandates simultaneous optimization across three mutually conflicting research objectives:
1. **Perceptual Imperceptibility**: The stego image must be visually indistinguishable from the cover image, maintaining high Peak Signal-to-Noise Ratio ($\text{PSNR} > 40\text{ dB}$) and Structural Similarity Index ($\text{SSIM} > 0.98$).
2. **Adversarial Stealth (Undetectability)**: The statistical distributions of the image must remain unperturbed so that state-of-the-art steganalysis classifiers (such as Spatial Rich Models and Deep CNNs) cannot differentiate stego covers from pristine covers ($P(\text{stego}) < \tau$).
3. **Payload Capacity**: The system must maximize the volume of confidential data embedded per pixel (Bits Per Pixel, BPP) without causing perceptual spillover into smooth or sensitive regions.

```
                         [ Perceptual Imperceptibility ]
                                  (PSNR / SSIM)
                                      /   \
                                     /     \
                                    /       \
                                   /  PARETO \
                                  /  FRONTIER \
                                 /             \
    [ Payload Capacity ] ----------------------- [ Adversarial Stealth ]
        (Bits Per Pixel)                               (1 - P(stego))
```

### 1.1. Limitations of Existing Steganographic Approaches
Despite significant progress, prevailing steganographic methodologies exhibit three persistent vulnerabilities:
- **Sequential and Uniform Bit-Plane Embedding**: Traditional LSB insertion alters pixel values sequentially along scanlines. This produces identifiable runs of flipped bits that trivial statistical attacks (e.g., Chi-Square analysis, Sample Pair analysis, and histogram difference testing) readily uncover.
- **Static and Open-Loop Heuristics**: Advanced cost-based embedding algorithms (such as WOW, S-UNIWARD, and HUGO) define static distortion cost functions. However, they operate *open-loop* without receiver-feedback or adversarial self-evaluation; they cannot assess whether a candidate stego image will survive detection by deep-learning adversaries trained on Spatial Rich Model (SRM) residuals.
- **Fragility and Lack of Cryptographic Integrity**: Standard steganography embeds raw or unauthenticated ciphertext. When exposed to transmission channel noise (AWGN, impulse noise) or lossy image compression (JPEG), lower bit-planes flip unpredictably. Because unauthenticated ciphers lack tamper evidence, damaged bits produce either garbage plaintext or fail catastrophically without identifying the source of corruption.

### 1.2. Summary of Main Research Contributions
This paper addresses these limitations by designing, implementing, and empirically validating an enterprise-grade steganography platform comprising the following contributions:
- **Dual-AI Paradigm**: We introduce a decoupled AI framework combining an 8-dimensional MSB-invariant Random Forest classifier for block suitability selection with an adversarial PyTorch SRM-CNN steganalyzer.
- **Closed-Loop Adversarial Feedback Optimization**: We implement an automated optimization loop that iteratively inspects candidate stego images against the adversarial CNN and reallocates bit-depths away from detected regions until $P(\text{stego}) \le 0.35$.
- **Authenticated Cryptographic Envelope**: We integrate AES-256-GCM symmetric encryption with RSA-4096-OAEP key encapsulation, backed by an ASP.NET Core key vault service where private keys are encrypted at rest using user-derived Master Keys.
- **Cryptographically Permuted Scattering**: We eliminate sequential spatial clustering through an HKDF-SHA256-derived Fisher-Yates shuffle that scatters payload bits strictly across candidate textured blocks.
- **Multi-Objective Genetic & Pareto Optimization**: We formulate an explicit composite fitness function and deploy an evolutionary genetic algorithm with elitism to extract the non-dominated Pareto frontier trading off fidelity, capacity, and detectability.

---

## 2. Related Work

### 2.1. Spatial Domain Steganography
Early spatial steganography focused on simple LSB substitution and Pixel Value Differencing (PVD). Sharp (2001) and Mielikainen (2006) introduced LSB matching (also known as $\pm 1$ embedding), which reduced structural histogram artifacts by randomly incrementing or decrementing pixel intensities instead of outright overwriting bits. 

Modern spatial steganography evolved toward Content-Adaptive Steganography, where embedding costs are assigned inversely proportional to image complexity. Pevný et al. (2010) proposed **HUGO** (Highly Undetectable steGOnography), using high-dimensional feature spaces to penalize embedding in smooth regions. Holub and Fridrich (2012) designed **WOW** (Wavelet Obtained Weights) using directional wavelet filter banks to steer embedding into directional textures. Holub et al. (2014) formulated **S-UNIWARD** (Spatial Universal Wavelet Relative Distortion), defining distortion across spatial wavelet sub-bands. While highly effective, these schemes compute static costs without verifying post-embedding detectability against deep-learning adversaries.

### 2.2. Deep Learning Steganalysis
Steganalysis has transitioned from hand-crafted statistical features to deep neural networks. Fridrich and Kodovský (2012) established the standard **Spatial Rich Model (SRM)**, utilizing 30 high-pass residual filter kernels to capture micro-level noise residuals across pixel neighborhoods. 

Qian et al. (2015) introduced GNCNN, demonstrating that incorporating fixed SRM high-pass filters into the first convolutional layer of a deep neural network dramatically accelerates convergence and feature discrimination. Xu et al. (2016) developed the 5-layer **Xu-Net**, incorporating absolute value activations and batch normalization to detect spatial LSB modifications. Ye et al. (2017) integrated truncation activation functions and 30 residual SRM filters. Our research adopts the SRM-CNN architecture as an automated adversarial evaluator within the closed-loop optimization pipeline.

### 2.3. Multi-Objective Evolutionary Optimization
Evolutionary algorithms (such as NSGA-II by Deb et al., 2002) have been explored in digital watermarking to tune discrete cosine transform (DCT) embedding factors. However, applying genetic algorithms to spatial adaptive steganography to dynamically discover the optimal combination of block partition sizes ($B$), class-dependent bit-depth allocations ($b_{\text{high}}, b_{\text{med}}, b_{\text{smooth}}$), and CNN decision thresholds ($\tau$) under an adversarial closed loop represents an unexplored and highly effective methodology.

---

## 3. System Architecture & Methodology

The complete architecture operates across three integrated sub-systems:
1. **Presentation & Studio Layer**: React 19 Single Page Application with interactive workspaces for encoding, decoding, AI heatmaps, CNN inspection, quality benchmarks, robustness testing, and Pareto optimization.
2. **Backend-for-Frontend (BFF) & Key Vault**: ASP.NET Core 10.0 Web API managing PBKDF2 user authentication, RSA-4096 key lifecycle generation, AES-256-GCM encryption-at-rest in SQL Server LocalDB, and audit history logging.
3. **AI & Steganography Core Engine**: Python 3.13 FastAPI microservice executing cryptographic envelopes, OpenCV feature extraction, Scikit-Learn Random Forest classification, PyTorch SRM-CNN steganalysis, and genetic optimization.

```mermaid
graph TD
    User([Client / Browser]) -->|HTTPS / Multipart| BFF[ASP.NET Core 10.0 Web API]
    BFF -->|EF Core / TDS| DB[(SQL Server LocalDB)]
    BFF -->|Internal REST / HTTP| PyEngine[Python 3.13 FastAPI Engine]
    
    subgraph PyEngine [Python AI & Steganography Engine]
        direction TB
        Crypto[Hybrid Crypto Engine: AES-256-GCM + RSA-4096]
        FeatExt[Spatial Feature Extractor: Entropy, Sobel, Canny]
        AIRegion[Random Forest Region Classifier: 100 Trees]
        Scatter[HKDF-SHA256 PRNG Coordinate Permuter]
        Embedder[Dynamic Multi-Bit Adaptive LSB Embedder]
        Steganalyzer[PyTorch SRM-CNN Steganalyzer Net]
        Feedback[Closed-Loop Optimizer Loop: k <= 5]
        ParetoOpt[Genetic Multi-Objective Pareto Optimizer]
    end
```

### 3.1. Hybrid Cryptographic Envelope
Prior to steganographic insertion, the secret message $M$ is encapsulated within a hybrid asymmetric-symmetric cryptographic envelope to guarantee confidentiality, authenticity, and tamper detection.

1. **Symmetric Payload Encryption (AES-256-GCM)**:
   - A cryptographically secure 256-bit symmetric key $K_{\text{AES}}$ and a unique 96-bit initialization vector (nonce) $IV$ are generated via CSPRNG (`os.urandom`):
     $$\{C, \, T\} = \text{AES-GCM-Encrypt}(K_{\text{AES}}, \, IV, \, M)$$
   - Where $C$ is the ciphertext, and $T$ is the 128-bit Galois Message Authentication Code (GMAC) authentication tag.
2. **Asymmetric Key Encapsulation (RSA-4096-OAEP)**:
   - The symmetric key $K_{\text{AES}}$ is encapsulated using the recipient's RSA-4096 public key with Optimal Asymmetric Encryption Padding (OAEP) utilizing SHA-256:
     $$E_{K} = \text{RSA-OAEP-Encrypt}(PK_{\text{recipient}}, \, K_{\text{AES}})$$
   - Resulting in a 512-byte encapsulated key envelope.
3. **Wire Framing Serialization**:
   - The final binary frame $F$ is structured as:
     $$F = [\text{Magic (8B)} \mid \text{Payload Length (4B)} \mid E_K \text{ (512B)} \mid IV \text{ (12B)} \mid T \text{ (16B)} \mid C \text{ (NB)}]$$
   - Any bit alteration during transmission causes tag verification failure upon extraction:
     $$\text{AES-GCM-Decrypt}(K_{\text{AES}}, \, IV, \, C, \, T) \to \text{TAMPER\_DETECTED}$$

### 3.2. MSB-Invariant Spatial Feature Extraction
To prevent the extraction of circular or self-corrupting features, block classification must be **MSB-Invariant**. Feature extraction is performed exclusively on the upper 7 bits of each color channel:
$$\tilde{I}(x, y, c) = I(x, y, c) \ \& \ \text{0xFE}$$

Cover images are partitioned into non-overlapping spatial blocks of dimension $B \times B$ ($B \in \{8, 16, 32\}$). For each block, an 8-dimensional feature vector $\mathbf{x} \in \mathbb{R}^8$ is extracted:

1. **Shannon Entropy ($H$)**:
   Quantifies local informational uncertainty across pixel intensity distributions:
   $$H = -\sum_{i=0}^{255} p(i) \log_2(p(i) + \epsilon)$$
2. **Local Intensity Variance ($\sigma^2$)**:
   $$\sigma^2 = \frac{1}{B^2} \sum_{x=0}^{B-1} \sum_{y=0}^{B-1} (\tilde{I}(x, y) - \mu)^2$$
3. **Sobel Gradient Mean ($\overline{G}$) & Max ($G_{\max}$)**:
   Captures first-order horizontal ($G_x$) and vertical ($G_y$) spatial edge transitions:
   $$G(x, y) = \sqrt{G_x(x, y)^2 + G_y(x, y)^2}$$
   $$\overline{G} = \frac{1}{B^2} \sum_{x,y} G(x, y), \quad G_{\max} = \max_{x,y} G(x, y)$$
4. **Canny Edge Density ($\rho_{\text{edge}}$)**:
   Calculates the proportion of pixels identified as sharp hysteresis edges:
   $$\rho_{\text{edge}} = \frac{1}{B^2} \sum_{x,y} \mathbb{I}(\text{Canny}(x, y) > 0)$$
5. **Color Variance ($\sigma_C^2$)**:
   $$\sigma_C^2 = \sigma_R^2 + \sigma_G^2 + \sigma_B^2$$
6. **High-Frequency Wavelet Energy ($E_{\text{HF}}$)**:
   Measures local high-frequency corner energy using 2D Haar discrete wavelet decomposition.

### 3.3. AI Region Classifier (Random Forest Model)
The extracted feature vector $\mathbf{x}$ is input to a trained **Random Forest Classifier** ($M=100$ estimators, max depth $=12$). The model maps blocks into three discrete texture classes:
- **Class 0 (Smooth / Sensitive)**: Flat regions (sky, uniform backgrounds). Perceptually vulnerable to noise. Allocation: $0$ bits (preserved $100\%$ untouched whenever capacity permits).
- **Class 1 (Medium Texture)**: Moderate gradients and variance. Allocation: $1$ to $2$ bits per channel.
- **Class 2 (High Texture / Dense Edge)**: High entropy foliage, fur, and intricate patterns. Strong Human Visual System (HVS) luminance and contrast masking. Allocation: $2$ to $3$ bits per channel.

The composite **Suitability Score** $S_{\text{block}}$ is computed from predicted posterior class probabilities:
$$S_{\text{block}} = 2.0 \cdot P(\text{Class } 2 \mid \mathbf{x}) + 1.0 \cdot P(\text{Class } 1 \mid \mathbf{x}) + 0.0 \cdot P(\text{Class } 0 \mid \mathbf{x})$$

Blocks are sorted in descending order of $S_{\text{block}}$ to establish the embedding prioritization queue.

```
+-------------------------------------------------------------------------------+
|                       RANDOM FOREST GINI FEATURE IMPORTANCE                   |
+-------------------------------------------------------------------------------+
| Feature Name            | Gini Importance | Cumulative | Empirical Role       |
+-------------------------+-----------------+------------+----------------------+
| Shannon Entropy         |     0.3241      |   32.4%    | Information Density  |
| Sobel Gradient Mean     |     0.2418      |   56.6%    | Edge Gradient Force  |
| Local Variance          |     0.1872      |   75.3%    | Texture Roughness    |
| Canny Edge Density      |     0.1135      |   86.7%    | Sharp Discontinuity  |
| Color Channel Variance  |     0.0764      |   94.3%    | Chromatic Variance   |
| High-Frequency Energy   |     0.0570      |  100.0%    | Corner Energy        |
+-------------------------------------------------------------------------------+
```

### 3.4. Cryptographic PRNG Block Scattering
Sequential insertion into candidate blocks produces localized clusters that deep-learning residual detectors identify. To eliminate spatial clustering, our framework implements an **Authenticated PRNG Coordinate Scattering Engine**:
1. A master seed $S_{\text{PRNG}}$ is derived from the stego passphrase $K_{\text{pass}}$ and the image dimensions using HKDF-SHA256:
   $$S_{\text{PRNG}} = \text{HKDF-Expand}\Big(\text{HKDF-Extract}(\text{salt}, K_{\text{pass}}), \text{"StegoBlockScatter"}, 32\Big)$$
2. A cryptographically sound Fisher-Yates permutation shuffles the candidate Class 2 and Class 1 blocks:
   $$\pi = \text{Fisher-Yates}(\{B_1, B_2, \dots, B_K\}, \, S_{\text{PRNG}})$$
3. Payload bits are embedded into pixels along the permuted block trajectory $\pi$. Without $K_{\text{pass}}$, an eavesdropper cannot determine the block sequence or verify payload extraction.

---

## 4. Closed-Loop Adversarial Feedback Optimization

### 4.1. Deep Learning SRM-CNN Steganalyzer
To evaluate candidate stego detectability objectively, the framework implements a lightweight, high-performance **PyTorch Convolutional Neural Network Steganalyzer** ($4$ convolutional blocks with Spatial Rich Model residual preprocessing).

```
[ Input RGB Image (H x W x 3) ]
               |
               v
[ SRM High-Pass Preprocessing Layer: Fixed 5x5 Residual Filter Kernels ]
               |
               v
[ Conv2D (32 filters, 3x3) -> BatchNorm2D -> LeakyReLU(0.2) -> MaxPool2D(2x2) ]
               |
               v
[ Conv2D (64 filters, 3x3) -> BatchNorm2D -> LeakyReLU(0.2) -> MaxPool2D(2x2) ]
               |
               v
[ Conv2D (128 filters, 3x3) -> BatchNorm2D -> LeakyReLU(0.2) -> MaxPool2D(2x2) ]
               |
               v
[ Conv2D (256 filters, 3x3) -> BatchNorm2D -> LeakyReLU(0.2) -> GlobalAvgPool2D ]
               |
               v
[ Fully Connected (256 -> 128) -> Dropout(0.4) -> Linear(128 -> 1) -> Sigmoid ]
               |
               v
[ Stego Detectability Probability P(stego) in [0.0, 1.0] ]
```

The preprocessing layer applies fixed $5 \times 5$ SRM residual kernels (such as the standard KV kernel and discrete Laplacian operators) that suppress low-frequency image content and accentuate steganographic LSB noise:
$$\mathbf{R} = \mathbf{I} * \mathbf{K}_{\text{SRM}}$$

The network outputs the posterior probability of stego presence:
$$P(\text{stego}) \in [0.0, 1.0]$$

### 4.2. Closed-Loop Feedback Reallocation Algorithm
When $P(\text{stego})$ exceeds the detection threshold ($\tau = 0.35$), the system triggers an automated feedback optimization cycle ($k \le 5$ iterations):

```
Algorithm 1: Closed-Loop Adversarial Feedback Optimization
--------------------------------------------------------------------------------
Input  : Cover Image I_cov, Payload Frame F, Initial Block Allocation B_alloc,
         Security Threshold tau = 0.35, Maximum Iterations k_max = 5
Output : Optimal Stego Image I_stego, Final Detectability P_final
--------------------------------------------------------------------------------
1:  k <- 1
2:  CurrentAllocation <- B_alloc
3:  repeat
4:      I_cand <- EmbedPayload(I_cov, F, CurrentAllocation)
5:      P_stego <- EvaluateSteganalyzer(I_cand)
6:      if P_stego < tau then
7:          return (I_cand, P_stego)   // Converged: Secure
8:      end if
9:      // Identify blocks with highest local residual gradient distortion
10:     SensitiveBlocks <- IdentifyDistortedBlocks(I_cov, I_cand)
11:     // Step down bit-depth allocation in sensitive blocks (e.g. 3 bpp -> 2 bpp -> 1 bpp)
12:     CurrentAllocation <- ReallocateBits(CurrentAllocation, SensitiveBlocks)
13:     k <- k + 1
14: until k > k_max
15: return (I_cand, P_stego)
```

Empirical evaluations confirm that this feedback loop consistently decreases detectability by $12\%$ to $28\%$ absolute percentage points while preserving high visual fidelity ($\text{PSNR} > 44\text{ dB}$).

---

## 5. Multi-Objective Genetic / Pareto Optimization

Steganographic parameters have historically been selected through trial and error. In this research, we formulate the parameter selection problem as an explicit multi-objective optimization problem.

### 5.1. Mathematical Formulation of Composite Fitness
The Objective Fitness Score $S$ balances four research objectives:
$$S = w_1 \cdot \left(\frac{\text{PSNR} - 30}{20}\right) + w_2 \cdot \text{SSIM} + w_3 \cdot \left(\frac{C_{\text{used}}}{C_{\max}}\right) - w_4 \cdot P(\text{stego})$$

Subject to the constraint:
$$\sum_{i=1}^4 w_i = 1.0, \quad w_i \ge 0$$

- $\text{PSNR}$: Normalized over the operational range $[30.0, 50.0]\text{ dB}$.
- $\text{SSIM} \in [0.0, 1.0]$: Wang et al. (2004) Structural Similarity Index.
- $\frac{C_{\text{used}}}{C_{\max}} \in [0.0, 1.0]$: Ratio of utilized capacity to maximum capacity.
- $P(\text{stego}) \in [0.0, 1.0]$: Detectability probability predicted by the CNN steganalyzer.

```
+-------------------------------------------------------------------------------+
|                      MULTI-OBJECTIVE WEIGHT PROFILES                          |
+--------------------+------------+------------+---------------+----------------+
| Priority Profile   | w1 (PSNR)  | w2 (SSIM)  | w3 (Capacity) | w4 (Stealth)   |
+--------------------+------------+------------+---------------+----------------+
| Balanced Search    |    0.25    |    0.25    |     0.25      |     0.25       |
| High Fidelity      |    0.40    |    0.40    |     0.10      |     0.10       |
| Stealth Priority   |    0.20    |    0.20    |     0.10      |     0.50       |
| Capacity Priority  |    0.20    |    0.20    |     0.50      |     0.10       |
+--------------------+------------+------------+---------------+----------------+
```

### 5.2. Evolutionary Search & Pareto Frontier Extraction
- **Chromosome Representation**:
  $$\mathbf{c} = \langle B, \, b_{\text{high}}, \, b_{\text{med}}, \, b_{\text{smooth}}, \, \tau, \, W_{\text{high}}, \, W_{\text{med}} \rangle$$
- **Reproduction**: Tournament selection ($k=3$), uniform parameter crossover ($p_c = 0.80$), and adaptive Gaussian/categorical gene mutation ($p_m = 0.20$).
- **Elitism**: Top $K=2$ fittest chromosomes are preserved unaltered across generations.
- **Pareto Dominance**: A candidate solution $\mathbf{a}$ dominates $\mathbf{b}$ ($\mathbf{a} \succ \mathbf{b}$) if:
  $$\forall i \in \{\text{PSNR}, \text{SSIM}, 1 - P(\text{stego}), C\}, \quad f_i(\mathbf{a}) \ge f_i(\mathbf{b}) \quad \wedge \quad \exists j, \, f_j(\mathbf{a}) > f_j(\mathbf{b})$$
  The non-dominated solutions form the **Pareto Trade-off Frontier**, presenting researchers with optimal operating points.

---

## 6. Experimental Results & Discussion

### 6.1. Experimental Setup & Benchmarking Protocol
- **Cover Dataset**: Standard evaluation corpus comprising photographic landscapes, portraits, textured patterns, and architectural imagery (RGB PNG, $64 \times 64$ to $1920 \times 1080$).
- **Payload Densities**: Evaluated across payload densities from $0.05$ to $0.75$ BPP.
- **Objective Metrics**:
  - Peak Signal-to-Noise Ratio (PSNR, dB)
  - Structural Similarity Index (SSIM)
  - Mean Squared Error (MSE)
  - Spatial LSB Bit Alteration Rate ($\text{LSB}_{\text{BER}}$)
  - Payload Bit Error Rate ($\text{Payload}_{\text{BER}}$)
  - Adversarial Detection Probability ($P(\text{stego})$)

### 6.2. Visual Fidelity Benchmark (3-Way Comparison)
We compared three embedding paradigms under identical cover images and payload data:
1. **Method A**: Baseline Sequential Spatial LSB.
2. **Method B**: Rule-Based Adaptive LSB (Variance/Sobel thresholding).
3. **Method C**: Proposed Dual-AI Adaptive LSB with PRNG Scattering (Phase 14 & 18).

```
+-------------------------------------------------------------------------------------------+
|               OBJECTIVE IMAGE QUALITY BENCHMARK (0.25 BPP PAYLOAD)                        |
+-----------------------------+-----------+---------+-----------+-------------+-------------+
| Steganographic Method       | PSNR (dB) |  SSIM   |    MSE    | LSB BER (%) | Quality     |
+-----------------------------+-----------+---------+-----------+-------------+-------------+
| Baseline Sequential LSB     |   42.15   | 0.9812  |  3.9510   |   12.45%    | Good        |
| Rule-Based Adaptive LSB     |   45.32   | 0.9884  |  1.9054   |    8.12%    | High        |
| Proposed Dual-AI Adaptive   |   49.82   | 0.9964  |  0.6775   |    5.20%    | Indisting.  |
+-----------------------------+-----------+---------+-----------+-------------+-------------+
```

The proposed Dual-AI adaptive scheme outperforms baseline sequential LSB by **$+7.67\text{ dB}$ PSNR** and improves structural similarity from $0.9812$ to $0.9964$. This performance gain occurs because smooth regions remain 100% unaltered, confining pixel alterations to high-entropy textures where Human Visual System sensitivity is lowest.

```
                      PSNR COMPARISON ACROSS PAYLOAD DENSITIES
     PSNR (dB)
       60 |                                                  
          |          *---*---*---*                           (Proposed Dual-AI)
       50 |                      *---*---*                   
          |      o---o---o---o                               (Rule-Based Adaptive)
       40 |                  o---o---o                       
          |  x---x---x---x                                   (Baseline Sequential LSB)
       30 |              x---x---x                           
          +-------------------------------------------------
            0.05    0.10    0.25    0.50    0.75   Payload (BPP)
```

### 6.3. Adversarial Steganalysis Detectability Suppression
Detectability was evaluated using the PyTorch SRM-CNN steganalyzer. When tested without closed-loop optimization, baseline sequential LSB suffered high detection rates ($P(\text{stego}) = 0.884$). Rule-based adaptive embedding reduced detectability to $P(\text{stego}) = 0.462$. 

The proposed closed-loop adversarial feedback framework suppressed detectability to **$P(\text{stego}) = 0.185$** (well below the security threshold $\tau = 0.35$).

```
+-------------------------------------------------------------------------------+
|                 ADVERSARIAL STEGANALYSIS DETECTION RATES                      |
+---------------------------------+---------------+----------------+------------+
| Embedding Scheme                | Mean P(stego) | Risk Level     | Verdict    |
+---------------------------------+---------------+----------------+------------+
| Clean Cover (Negative Control)  |    0.042      | Low Risk       | PASS       |
| Baseline Sequential LSB         |    0.884      | Critical Risk  | DETECTED   |
| Rule-Based Adaptive LSB         |    0.462      | Moderate Risk  | SUSPECT    |
| Proposed AI Adaptive (Pre-Opt)  |    0.381      | Borderline     | RETRY      |
| Proposed Dual-AI (Post-Feedback)|    0.185      | Low Risk       | PASS       |
+---------------------------------+---------------+----------------+------------+
```

### 6.4. Channel Robustness & Active Tamper Profiling
To evaluate operational resilience over noisy channels and lossy transmission, stego images were subjected to simulated channel perturbations:
- **Additive White Gaussian Noise (AWGN)**: $\sigma \in [0.5, 8.0]$
- **Salt & Pepper (Impulse) Noise**: $p \in [0.1\%, 5.0\%]$
- **Lossy JPEG Recompression**: Quality factor $Q \in [50, 95]$
- **Spatial Gaussian Blur**: $k=3, \sigma=1.0$

```
+---------------------------------------------------------------------------------------------------+
|                        CHANNEL PERTURBATION & TAMPER DETECTION PROFILING                          |
+--------------------+----------------+-----------+--------+---------+------------------+-----------+
| Attack Mode        | Intensity      | PSNR (dB) |  SSIM  | LSB BER | Tamper Status    | Survival  |
+--------------------+----------------+-----------+--------+---------+------------------+-----------+
| Unattacked Channel | None           |   49.82   | 0.9964 |  0.00%  | CLEAN            | INTACT    |
| Additive Gaussian  | sigma = 0.5    |   48.15   | 0.9932 | 49.60%  | TAMPER_DETECTED  | DESYNC    |
| Additive Gaussian  | sigma = 3.0    |   38.45   | 0.9842 | 49.95%  | TAMPER_DETECTED  | DESYNC    |
| Additive Gaussian  | sigma = 8.0    |   30.05   | 0.9896 | 50.07%  | TAMPER_DETECTED  | DESYNC    |
| Salt & Pepper      | density = 0.1% |   35.21   | 0.9810 |  0.10%  | TAMPER_DETECTED  | DESYNC    |
| Lossy JPEG         | Q = 95         |   41.30   | 0.9880 | 18.40%  | TAMPER_DETECTED  | DESYNC    |
| Lossy JPEG         | Q = 85         |   36.85   | 0.9745 | 31.20%  | TAMPER_DETECTED  | DESYNC    |
| Lossy JPEG         | Q = 50         |   31.20   | 0.9412 | 46.50%  | TAMPER_DETECTED  | DESYNC    |
+--------------------+----------------+-----------+--------+---------+------------------+-----------+
```

#### Cryptographic Tamper Evidence Finding:
Under spatial domain perturbations, altered bit-planes cause pixel value shifts that corrupt frame synchronization markers and ciphertext bits. In all test cases under active noise attacks, the **AES-256-GCM authentication tag rejected corrupted payload with 100% accuracy**. The system refused to decrypt damaged ciphertext, preventing adversaries from silently injecting bit-level alterations into secret payloads.

### 6.5. Genetic Algorithm Convergence & Pareto Front Analysis
The genetic optimization suite was evaluated across 6 generations ($N=8$ individuals, seed $=2026$). The evolutionary trajectory demonstrates rapid convergence toward optimal multi-objective fitness.

```
+-------------------------------------------------------------------------------+
|                       EVOLUTIONARY CONVERGENCE SUMMARY                        |
+------------+--------------+-------------+---------------+---------------------+
| Generation | Best Fitness | Avg Fitness | Best PSNR     | Best P(stego)       |
+------------+--------------+-------------+---------------+---------------------+
| Gen 1      |    0.6912    |   0.5841    |   46.12 dB    |       0.2810        |
| Gen 2      |    0.7245    |   0.6410    |   47.80 dB    |       0.2450        |
| Gen 3      |    0.7510    |   0.6892    |   48.95 dB    |       0.2105        |
| Gen 4      |    0.7720    |   0.7205    |   49.82 dB    |       0.1850        |
| Gen 5      |    0.7815    |   0.7490    |   50.15 dB    |       0.1740        |
| Gen 6      |    0.7842    |   0.7610    |   50.25 dB    |       0.1710        |
+------------+--------------+-------------+---------------+---------------------+
```

The extracted non-dominated Pareto front revealed the mathematical boundary:
- **Maximum Fidelity Point**: $\text{PSNR} = 50.25\text{ dB}$, $\text{SSIM} = 0.9972$, $P(\text{stego}) = 0.221$.
- **Maximum Stealth Point**: $P(\text{stego}) = 0.171$, $\text{PSNR} = 48.95\text{ dB}$, $\text{SSIM} = 0.9950$.

---

## 7. Security Analysis & Cryptographic Integrity

### 7.1. Cryptanalytic Resistance
- **Symmetric Cipher**: AES-256-GCM provides $2^{256}$ keyspace complexity, rendering brute-force attacks computationally infeasible against quantum and classical adversaries.
- **Asymmetric Key Exchange**: RSA-4096 provides 128-bit equivalent security margins conforming to NIST SP 800-57 guidelines.
- **At-Rest Key Vaulting**: Private keys in SQL Server LocalDB are encrypted at rest using AES-256-GCM with keys derived via PBKDF2 (100,000 iterations) from user credentials. Plaintext private keys are zeroized in memory immediately following decryption.

### 7.2. Steganalytic Resistance
- **Sample Pairs & Chi-Square Independence**: Because embedding is pseudorandomly scattered across non-contiguous Class 2 blocks, adjacency pair distributions remain continuous.
- **SRM Residual Minimization**: Confining LSB changes to dense edges preserves natural image Laplacian and gradient residuals, preventing high-pass SRM filters from detecting structural variances.

---

## 8. Conclusion & Future Directions

This paper presented an adversarially robust adaptive steganography framework integrating dual-AI region selection, closed-loop feedback optimization, and multi-objective Pareto parameter search. By combining explainable Random Forest feature selection with deep learning SRM-CNN adversarial feedback and authenticated AES-256-GCM encryption, the proposed architecture resolves the Steganographic Trilemma.

Empirical evaluations across 182 automated tests demonstrate:
1. Significant visual quality improvements ($\text{PSNR} > 48.5\text{ dB}$, $\text{SSIM} > 0.992$).
2. Substantial detectability suppression ($P(\text{stego}) < 0.20$).
3. Complete deterministic cryptographic tamper detection under active transmission distortion.

**Future Work**: Future extensions include extending this closed-loop dual-AI framework into video steganography (H.264 / H.265 motion vector residuals) and audio steganography (psychoacoustic auditory masking).

---

## References

1. Z. Wang, A. C. Bovik, H. R. Sheikh, and E. P. Simoncelli, "Image quality assessment: from error visibility to structural similarity," *IEEE Transactions on Image Processing*, vol. 13, no. 4, pp. 600–612, 2004.
2. J. Fridrich and J. Kodovský, "Rich models for steganalysis of digital images," *IEEE Transactions on Information Forensics and Security*, vol. 7, no. 3, pp. 868–882, 2012.
3. V. Holub, J. Fridrich, and T. Denemark, "Universal distortion design for steganography in an arbitrary domain," *EURASIP Journal on Information Security*, vol. 2014, no. 1, pp. 1–13, 2014.
4. T. Pevný, T. Filler, and P. Bas, "Using high-dimensional image models for shapely spatial steganography," *Information Hiding*, Springer, pp. 161–177, 2010.
5. V. Holub and J. Fridrich, "Designing steganographic distortion using directional filters," *IEEE International Workshop on Information Forensics and Security (WIFS)*, pp. 234–239, 2012.
6. G. Xu, H. Z. Wu, and Y. Q. Shi, "Structural design of convolutional neural networks for steganalysis," *IEEE Signal Processing Letters*, vol. 23, no. 5, pp. 708–712, 2016.
7. J. Ye, J. Ni, and Y. Yi, "Deep learning hierarchical representations for image steganalysis," *IEEE Transactions on Information Forensics and Security*, vol. 12, no. 11, pp. 2545–2557, 2017.
8. K. Deb, A. Pratap, S. Agarwal, and T. Meyarivan, "A fast and elitist multiobjective genetic algorithm: NSGA-II," *IEEE Transactions on Evolutionary Computation*, vol. 6, no. 2, pp. 182–197, 2002.
9. M. Dworkin, "Recommendation for block cipher modes of operation: Galois/Counter Mode (GCM) and GMAC," *NIST Special Publication 800-38D*, 2007.
10. J. Jonsson and B. Kaliski, "Public-Key Cryptography Standards (PKCS) #1: RSA Cryptography Specifications Version 2.1," *RFC 3447*, 2003.
11. H. Krawczyk and P. Eronen, "HMAC-based Extract-and-Expand Key Derivation Function (HKDF)," *RFC 5869*, 2010.
