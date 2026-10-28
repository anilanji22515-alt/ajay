# AP-QAIC: Statewide Quantum Talent Pipeline & Curriculum Platform
## QEXPO 2026 | USE CASE UC 090
**Building a Quantum-Ready Workforce for Andhra Pradesh**  
*Domains: Quantum Computing • Quantum AI/ML • Quantum Communication*

---

## Live Published URL
> 🚀 **Public Live Link:** [**https://2c83f7ac3951f4.lhr.life**](https://2c83f7ac3951f4.lhr.life)  
> *Active, secured over TLS/HTTPS, and accessible globally from any browser or mobile device.*

---

## 1. Executive Summary & Problem Context

The adoption of quantum technologies across India is constrained by a severe talent bottleneck: the lack of practical, job-relevant quantum software engineering and algorithmic skills. While top-tier specialist institutions (like IITs and IISc) possess research equipment, **380+ engineering and degree colleges across Andhra Pradesh remain excluded** due to:
1. **Skills Gap:** Few graduates possess hands-on quantum circuit design, QML, or quantum cryptographic expertise.
2. **Access Gap:** High-end quantum hardware and specialized curricula are concentrated in a few institutions.
3. **Coordination Gap:** Training efforts are fragmented without a synchronized statewide curriculum or standardized faculty enablement.

### The Big Idea
**Make quantum skills accessible statewide—not limited to a few specialist institutions.**  
Deploy a **QAIC Hub-and-Spoke Network** connecting 1 Central Coordinating Hub, 3 Regional Lead Hubs, and 380+ College Nodes across Andhra Pradesh to deliver a tiered curriculum from foundational awareness to industry-ready specialization.

---

## 2. Hub-and-Spoke Architecture

```
                       ┌──────────────────────────────────────────────┐
                       │          QAIC COORDINATING HUB               │
                       │   (State Command, APSSDC, AICTE, NQM)        │
                       └──────────────────────┬───────────────────────┘
                                              │
           ┌──────────────────────────────────┼──────────────────────────────────┐
           │                                  │                                  │
           ▼                                  ▼                                  ▼
┌───────────────────────┐          ┌───────────────────────┐          ┌───────────────────────┐
│  NORTH COASTAL HUB    │          │   COASTAL ANDHRA HUB  │          │    RAYALASEEMA HUB    │
│  Lead: AUCE Vizag     │          │  Lead: JNTUK / VRSEC  │          │  Lead: IIT Tirupati   │
│  Districts: 5         │          │  Districts: 10        │          │  Districts: 8         │
│  Nodes: 86 Colleges   │          │  Nodes: 182 Colleges  │          │  Nodes: 114 Colleges  │
└──────────┬────────────┘          └──────────┬────────────┘          └──────────┬────────────┘
           │                                  │                                  │
    [College Nodes 1..86]             [College Nodes 1..182]             [College Nodes 1..114]
           │                                  │                                  │
           └──────────────────────────────────┴──────────────────────────────────┘
                                              │
                                              ▼
                         [Industry & Research Partners]
                   (TCS, C-DAC, IBM Quantum, DRDO, ISRO Labs)
```

---

## 3. Tiered 4-Level Curriculum Pathway

| Level | Target Audience | Focus Area | Hands-on Labs & Tools | AICTE / NQM Alignment |
|---|---|---|---|---|
| **Level 1: Awareness** | 1st & 2nd Year Undergrads (Statewide) | Qubits, Superposition, Entanglement intuition, Quantum Career Tracks | 3D Bloch Sphere visualization, Interactive coin-toss analogy | NQM Pillar 4: Human Resource Development (Awareness Track) |
| **Level 2: Foundations** | 3rd Year CS, ECE, Data Science | Bra-Ket notation, Unitary Gates (H, X, Y, Z, S, T, CNOT), Matrix tensors | Pure Python / NumPy Circuit Simulator, Bell State & GHZ creation | AICTE Model Curriculum: Quantum Computing Foundations (ET-QC-201) |
| **Level 3: Application** | Final Year Students & Faculty Trainees | Quantum Algorithms (Deutsch-Jozsa, Grover's), Quantum Teleportation, QML (VQC) | Grover's 4-item search, Quantum Teleportation circuit simulation | AICTE Specialized Elective / APSSDC Master Trainer Certification |
| **Level 4: Specialisation**| Top 10-15% cohort & Post-graduates | Port logistics optimization (QAOA), Post-Quantum Cryptography, Drug Discovery | Capstone projects with TCS / C-DAC, hardware cloud execution | National Quantum Mission Co-Op Grant & Industry Placements |

---

## 4. Key Prototype Features Built in `hack.py`

### A. Statewide Hub-and-Spoke Governance Dashboard
- Real-time monitoring of **382 connected college nodes** across 26 Andhra Pradesh districts.
- Regional breakdown (North Coastal, Coastal Andhra, Rayalaseema).
- Searchable and filterable institutional node registry with readiness metrics and active lab environments.

### B. Upgraded Multi-Qubit Quantum Lab Simulation Studio (1–4 Qubits)
- **Configurable Qubit Registers & Sampling:** 1 to 4 configurable qubit registers with 100 to 4,096 measurement shots, plus an exact analytical probability mode.
- **Universal Unitary Gate Library:**
  - *Superposition & Pauli Unitaries:* $H, X, \sqrt{X}, Y, Z, S, S^\dagger, T, T^\dagger$.
  - *Continuous Parameterized Rotations:* $RX(\theta), RY(\theta), RZ(\theta)$ with configurable rotation angles ($\pi/4, \pi/2, \pi, 3\pi/2, 2\pi$).
  - *Multi-Qubit Entanglers:* $CNOT, CZ, CH, SWAP$, and 3-qubit $CCNOT$ (Toffoli).
- **Interactive Step-by-Step Circuit Stepper:** Step forward and backward through each gate operation, visualizing intermediate statevector evolutions and Bloch vector rotations before wavefunction collapse.
- **Multimodal State Inspector:**
  - *Complex Amplitudes & Dynamic Phase Wheels:* Statevector kets with real/imaginary parts, probabilities, and SVG phase wheels color-coded by quantum phase angle $\phi$.
  - *3D SVG Bloch Spheres & von Neumann Entanglement Entropy:* Calculates single-qubit reduced density matrices $\rho$, density purity $\text{Tr}(\rho^2)$, and exact bipartite von Neumann entanglement entropy $S(\rho) = -\text{Tr}(\rho \log_2 \rho)$ to rigorously distinguish separable states from maximally entangled Bell and GHZ states.
  - *Probabilistic Measurement Histogram:* Live Chart.js shot distribution for arbitrary circuits.
  - *OpenQASM 2.0 & Qiskit Python Exporters:* Real-time automated code synthesis and 1-click clipboard export for execution on IBM Quantum or C-DAC Param Q-Sim cloud backends.
- **8 Built-in Algorithmic Presets:**
  1. **Bell State $|\Phi^+\rangle$:** $(|00\rangle + |11\rangle)/\sqrt{2}$
  2. **Bell Singlet $|\Psi^-\rangle$:** $(|01\rangle - |10\rangle)/\sqrt{2}$
  3. **GHZ State (3Q):** $(|000\rangle + |111\rangle)/\sqrt{2}$
  4. **W-State (3Q):** $(|001\rangle + |010\rangle + |100\rangle)/\sqrt{3}$
  5. **Quantum Teleportation (3Q):** Full pipeline with unknown state preparation, EPR distribution, Bell state measurement, and feedforward recovery.
  6. **Grover's Search (2Q):** Oracle inversion and diffusion operator with 100% amplification of target $|11\rangle$.
  7. **Deutsch-Jozsa Algorithm (2Q):** Deterministic single-query evaluation of balanced vs. constant functions.
  8. **Quantum Fourier Transform (3Q QFT):** Modular frequency-domain phase transformation.

### C. Statewide Diagnostic Assessment & APSSDC Credential Engine
- **Expanded 12-Question Diagnostic Assessment:** Rigorous evaluation covering 6 core quantum domains:
  1. *Superposition & Principles* (Born rule, probability amplitudes, No-Cloning Theorem).
  2. *Unitary Gates & Matrices* (Reversibility, Hadamard, Pauli, S & T phase relationships).
  3. *Multi-Qubit Entanglement* (Tensor product Hilbert spaces $2^n$, Bell state synthesis via $H + CNOT$).
  4. *Measurement & Entropy* (Subsystem density matrices, purity $\text{Tr}(\rho^2)$, von Neumann entropy $S(\rho)$).
  5. *Quantum Algorithms* (Quantum Teleportation protocol, Grover diffusion operator, Deutsch-Jozsa query complexity).
  6. *Complexity & Hardware* (BQP complexity boundary, classical vs quantum polynomial time).
- **Personalized Weak-Topic Recommendations & Remediation:**
  - Evaluates granular percentage mastery per competency category.
  - Automatically identifies sub-mastery areas ($< 75\%$) and categorizes severity (*Critical Review Required* vs. *Targeted Practice Recommended*).
  - Delivers specific diagnostic guidance, recommended curriculum level links (opening the pop-out visualizer modal), and 1-click lab practice presets directly in the quantum circuit simulator.
  - Provides a question-by-question post-assessment review with theoretical explanations and formula derivations.
- **Verifiable APSSDC Quantum Skill Credential:**
  - Real-time generation of verifiable digital certificate badges with unique credential ID (`AP-QAIC-XXXXXX`), candidate name, academic institution, and verified score tier.
  - Dynamic radar chart mapping individual demonstrated skills across all evaluated competency dimensions.

---

## 5. How to Run the Prototype

### Option 1: Launch Interactive Web Application (Default)
```bash
python hack.py
```
*Automatically launches a local web server at `http://127.0.0.1:5000/` and opens your default browser.*

### Option 2: Run CLI Diagnostic Verification
```bash
python hack.py --cli
```
*Runs programmatic verification of the statevector engine, Bell state maximal entanglement, 3-qubit GHZ state von Neumann entropy, Grover's search 100% probability amplification, and prints the statewide AP college node distribution.*

---

## 6. Project Files
- `hack.py`: Complete self-contained Python application containing the upgraded quantum simulation studio, Flask REST API backend, and interactive Tailwind CSS frontend.
- `README.md`: Architectural documentation, problem statement alignment, and operational guide.

