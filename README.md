# AP-QAIC: Statewide Quantum Talent Pipeline & Curriculum Platform
## QEXPO 2026 | USE CASE UC 090
**Building a Quantum-Ready Workforce for Andhra Pradesh**  
*Domains: Quantum Computing • Quantum AI/ML • Quantum Communication*

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
| **Level 3: Application** | Final Year Students & Faculty Trainees | Quantum Algorithms (Deutsch-Jozsa, Grover's), BB84 QKD, QML (VQC) | Grover's 4-item search, BB84 protocol simulation with Eve detection | AICTE Specialized Elective / APSSDC Master Trainer Certification |
| **Level 4: Specialisation**| Top 10-15% cohort & Post-graduates | Port logistics optimization (QAOA), Post-Quantum Cryptography, Drug Discovery | Capstone projects with TCS / C-DAC, hardware cloud execution | National Quantum Mission Co-Op Grant & Industry Placements |

---

## 4. Key Prototype Features Built in `hack.py`

### A. Statewide Hub-and-Spoke Governance Dashboard
- Real-time monitoring of **382 connected college nodes** across 26 Andhra Pradesh districts.
- Regional breakdown (North Coastal, Coastal Andhra, Rayalaseema).
- Searchable and filterable institutional node registry with readiness metrics and active lab environments.

### B. High-Performance Quantum Circuit Simulator (Pure Python & NumPy)
- Exact statevector calculation for multi-qubit systems without heavy external C-dependencies.
- Unitary gate implementation ($H, X, Y, Z, S, T, CNOT, CZ, SWAP$).
- Computes single-qubit reduced density matrices, Bloch vector coordinates $(\langle X \rangle, \langle Y \rangle, \langle Z \rangle)$, spherical angles $(\theta, \phi)$, and purity.
- Generates 1,024-shot probabilistic measurement histograms.
- Built-in circuit presets:
  - **Bell State $|\Phi^+\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$**
  - **GHZ 3-Qubit Entanglement $|\text{GHZ}\rangle = \frac{1}{\sqrt{2}}(|000\rangle + |111\rangle)$**
  - **Grover's 2-Qubit Database Search** with Oracle and Diffusion operator.

### C. BB84 Quantum Key Distribution (QKD) Simulator
- Interactive sender (Alice) and receiver (Bob) with random photon polarization bases ($+$ rectilinear, $\times$ diagonal).
- **Interactive Eavesdropper (Eve) Intercept Toggle**:
  - Without Eve: Error rate (QBER) = 0.0% $\rightarrow$ Secure authenticated key generated.
  - With Eve: Wavefunction collapse causes QBER $\approx 25-30\%$ $\rightarrow$ Tampering immediately detected, compromised key discarded!

### D. Statewide Diagnostic Assessment & APSSDC Credential Engine
- Standardized multiple-choice competency exam covering Levels 1 to 3.
- Automatic scoring, granular competency radar profiling (Superposition, Circuits, Entanglement, Cryptography, Algorithmic Complexity).
- Instant verifiable digital credential badge generator with unique ID.

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
*Runs verification of the quantum statevector engine, Bell state creation, BB84 QKD protocol under eavesdropping conditions, and prints the statewide AP college node distribution.*

---

## 6. Project Files
- `hack.py`: Complete Python application containing the quantum simulator, QKD engine, Flask API backend, and the interactive Tailwind CSS frontend.
- `README.md`: Architectural documentation, problem statement alignment, and operational guide.

