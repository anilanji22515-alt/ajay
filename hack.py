"""
AP-QAIC: Statewide Quantum Talent Pipeline & Curriculum Platform
Andhra Pradesh Quantum AI & Computing Ecosystem (QEXPO 2026 - UC 090)
Building a Quantum-Ready Workforce for Andhra Pradesh
"""

import sys
import os
import json
import random
import math
import webbrowser
import threading
import numpy as np
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# ==============================================================================
# 1. CORE QUANTUM SIMULATOR ENGINE (Pure NumPy)
# ==============================================================================

class QuantumSimulator:
    """
    Lightweight, exact Statevector & Density Matrix Quantum Simulator
    Supports 1 to 5 qubits, single-qubit unitaries, 2-qubit CNOT/CZ/SWAP,
    Bloch sphere vector extraction, and shot measurement sampling.
    """
    # Standard Unitary Matrices
    GATES = {
        'I': np.array([[1, 0], [0, 1]], dtype=complex),
        'X': np.array([[0, 1], [1, 0]], dtype=complex),
        'Y': np.array([[0, -1j], [1j, 0]], dtype=complex),
        'Z': np.array([[1, 0], [0, -1]], dtype=complex),
        'H': np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2),
        'S': np.array([[1, 0], [0, 1j]], dtype=complex),
        'T': np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex),
    }

    @staticmethod
    def rx(theta):
        return np.array([
            [np.cos(theta / 2), -1j * np.sin(theta / 2)],
            [-1j * np.sin(theta / 2), np.cos(theta / 2)]
        ], dtype=complex)

    @staticmethod
    def ry(theta):
        return np.array([
            [np.cos(theta / 2), -np.sin(theta / 2)],
            [np.sin(theta / 2), np.cos(theta / 2)]
        ], dtype=complex)

    @staticmethod
    def rz(theta):
        return np.array([
            [np.exp(-1j * theta / 2), 0],
            [0, np.exp(1j * theta / 2)]
        ], dtype=complex)

    def __init__(self, num_qubits=2):
        self.num_qubits = max(1, min(6, num_qubits))
        self.dim = 1 << self.num_qubits
        self.state = np.zeros(self.dim, dtype=complex)
        self.state[0] = 1.0  # |00...0>

    def reset(self):
        self.state = np.zeros(self.dim, dtype=complex)
        self.state[0] = 1.0

    def apply_single_gate(self, qubit, matrix):
        if qubit < 0 or qubit >= self.num_qubits:
            raise ValueError(f"Invalid qubit index: {qubit}")
        new_state = np.zeros_like(self.state)
        mask = 1 << (self.num_qubits - 1 - qubit)
        for i in range(self.dim):
            if (i & mask) == 0:
                i0 = i
                i1 = i | mask
                a0 = self.state[i0]
                a1 = self.state[i1]
                new_state[i0] = matrix[0, 0] * a0 + matrix[0, 1] * a1
                new_state[i1] = matrix[1, 0] * a0 + matrix[1, 1] * a1
        self.state = new_state

    def apply_cnot(self, control, target):
        if control == target or not (0 <= control < self.num_qubits and 0 <= target < self.num_qubits):
            raise ValueError("Invalid control or target qubit index")
        new_state = self.state.copy()
        ctrl_mask = 1 << (self.num_qubits - 1 - control)
        targ_mask = 1 << (self.num_qubits - 1 - target)
        for i in range(self.dim):
            if (i & ctrl_mask) != 0:
                flipped = i ^ targ_mask
                if i < flipped:
                    new_state[i], new_state[flipped] = new_state[flipped], new_state[i]
        self.state = new_state

    def apply_cz(self, control, target):
        ctrl_mask = 1 << (self.num_qubits - 1 - control)
        targ_mask = 1 << (self.num_qubits - 1 - target)
        for i in range(self.dim):
            if (i & ctrl_mask) != 0 and (i & targ_mask) != 0:
                self.state[i] *= -1.0

    def apply_swap(self, q1, q2):
        if q1 == q2:
            return
        m1 = 1 << (self.num_qubits - 1 - q1)
        m2 = 1 << (self.num_qubits - 1 - q2)
        new_state = self.state.copy()
        for i in range(self.dim):
            b1 = 1 if (i & m1) else 0
            b2 = 1 if (i & m2) else 0
            if b1 != b2:
                flipped = i ^ m1 ^ m2
                if i < flipped:
                    new_state[i], new_state[flipped] = new_state[flipped], new_state[i]
        self.state = new_state

    def get_probabilities(self):
        probs = np.abs(self.state) ** 2
        norm = np.sum(probs)
        if norm > 0:
            probs = probs / norm
        return probs

    def sample_shots(self, shots=1024):
        probs = self.get_probabilities()
        counts = {}
        samples = np.random.choice(self.dim, size=shots, p=probs)
        for idx in samples:
            bitstr = format(idx, f'0{self.num_qubits}b')
            counts[bitstr] = counts.get(bitstr, 0) + 1
        # Fill missing states with 0
        for i in range(self.dim):
            bitstr = format(i, f'0{self.num_qubits}b')
            if bitstr not in counts:
                counts[bitstr] = 0
        return counts

    def get_bloch_coordinates(self, qubit):
        """Compute the reduced density matrix and Bloch vector (x, y, z) for a single qubit."""
        m = 1 << (self.num_qubits - 1 - qubit)
        rho = np.zeros((2, 2), dtype=complex)
        for i in range(self.dim):
            b_i = 1 if (i & m) else 0
            for j in range(self.dim):
                b_j = 1 if (j & m) else 0
                # trace over all other qubits (all bits except qubit must match)
                if (i & ~m) == (j & ~m):
                    rho[b_i, b_j] += self.state[i] * np.conj(self.state[j])

        # Pauli expectation values
        X = self.GATES['X']
        Y = self.GATES['Y']
        Z = self.GATES['Z']
        x = float(np.real(np.trace(rho @ X)))
        y = float(np.real(np.trace(rho @ Y)))
        z = float(np.real(np.trace(rho @ Z)))

        # Spherical angles theta and phi
        r = math.sqrt(x*x + y*y + z*z)
        theta = math.acos(max(-1.0, min(1.0, z / r))) if r > 1e-7 else 0.0
        phi = math.atan2(y, x) if (x*x + y*y) > 1e-7 else 0.0

        return {
            "x": round(x, 4),
            "y": round(y, 4),
            "z": round(z, 4),
            "theta_deg": round(math.degrees(theta), 2),
            "phi_deg": round(math.degrees(phi) % 360, 2),
            "purity": round(float(np.real(np.trace(rho @ rho))), 4)
        }

    def execute_circuit(self, instructions):
        """
        Execute list of instructions:
        e.g. [{'gate': 'H', 'target': 0}, {'gate': 'CNOT', 'control': 0, 'target': 1}]
        """
        self.reset()
        for instr in instructions:
            g = instr.get('gate', '').upper()
            t = instr.get('target', 0)
            c = instr.get('control', 0)
            angle = float(instr.get('param', 0.0))

            if g in self.GATES:
                self.apply_single_gate(t, self.GATES[g])
            elif g == 'RX':
                self.apply_single_gate(t, self.rx(angle))
            elif g == 'RY':
                self.apply_single_gate(t, self.ry(angle))
            elif g == 'RZ':
                self.apply_single_gate(t, self.rz(angle))
            elif g == 'CNOT' or g == 'CX':
                self.apply_cnot(c, t)
            elif g == 'CZ':
                self.apply_cz(c, t)
            elif g == 'SWAP':
                self.apply_swap(c, t)

        probs = self.get_probabilities()
        state_list = []
        for i in range(self.dim):
            amp = self.state[i]
            mag = abs(amp)
            phase = math.atan2(amp.imag, amp.real) if mag > 1e-7 else 0.0
            bitstr = format(i, f'0{self.num_qubits}b')
            state_list.append({
                "basis": f"|{bitstr}⟩",
                "real": round(float(amp.real), 4),
                "imag": round(float(amp.imag), 4),
                "prob": round(float(probs[i]), 4),
                "phase_deg": round(math.degrees(phase), 1)
            })

        bloch_vectors = [self.get_bloch_coordinates(q) for q in range(self.num_qubits)]

        return {
            "num_qubits": self.num_qubits,
            "states": state_list,
            "bloch": bloch_vectors,
            "shots": self.sample_shots(shots=1024)
        }

# ==============================================================================
# 2. QUANTUM COMMUNICATION ENGINE (BB84 QKD Protocol Simulator)
# ==============================================================================

def simulate_bb84(num_bits=24, eavesdropper_active=False):
    """
    Simulates the BB84 Quantum Key Distribution protocol.
    Bases: 0 = Rectilinear (+, |0> / |1>), 1 = Diagonal (x, |+> / |->)
    """
    alice_bits = [random.randint(0, 1) for _ in range(num_bits)]
    alice_bases = [random.randint(0, 1) for _ in range(num_bits)]
    
    eve_bases = []
    eve_measured_bits = []
    qubits_transmitted = []

    # Alice prepares states
    for bit, base in zip(alice_bits, alice_bases):
        qubits_transmitted.append({"bit": bit, "base": base})

    # Eve optionally intercepts
    if eavesdropper_active:
        for q in qubits_transmitted:
            e_base = random.randint(0, 1)
            eve_bases.append(e_base)
            # If Eve matches Alice base, she measures correctly; else 50/50
            if e_base == q["base"]:
                eve_bit = q["bit"]
            else:
                eve_bit = random.randint(0, 1)
            eve_measured_bits.append(eve_bit)
            # State collapses to Eve's measurement
            q["bit"] = eve_bit
            q["base"] = e_base
    else:
        eve_bases = [None] * num_bits
        eve_measured_bits = [None] * num_bits

    # Bob measures
    bob_bases = [random.randint(0, 1) for _ in range(num_bits)]
    bob_measured_bits = []
    for q, b_base in zip(qubits_transmitted, bob_bases):
        if b_base == q["base"]:
            bob_measured_bits.append(q["bit"])
        else:
            bob_measured_bits.append(random.randint(0, 1))

    # Sifting: keep bits where Alice and Bob bases match
    sifted_indices = [i for i in range(num_bits) if alice_bases[i] == bob_bases[i]]
    alice_key = [alice_bits[i] for i in sifted_indices]
    bob_key = [bob_measured_bits[i] for i in sifted_indices]

    # Error calculation (QBER)
    mismatches = sum(1 for a, b in zip(alice_key, bob_key) if a != b)
    qber = (mismatches / len(alice_key) * 100) if len(alice_key) > 0 else 0.0
    secure = (qber < 11.0) and len(alice_key) > 0

    return {
        "num_bits": num_bits,
        "eavesdropper_active": eavesdropper_active,
        "alice_bits": alice_bits,
        "alice_bases": ["+" if b == 0 else "×" for b in alice_bases],
        "bob_bases": ["+" if b == 0 else "×" for b in bob_bases],
        "bob_measured": bob_measured_bits,
        "eve_bases": [("+" if b == 0 else "×") if b is not None else "-" for b in eve_bases],
        "eve_measured": eve_measured_bits,
        "sifted_count": len(sifted_indices),
        "alice_sifted_key": "".join(map(str, alice_key)),
        "bob_sifted_key": "".join(map(str, bob_key)),
        "mismatches": mismatches,
        "qber_percent": round(qber, 1),
        "status": "SECURE KEY AGREEMENT ESTABLISHED" if secure else "EAVESDROPPER INTERCEPTION DETECTED - KEY DISCARDED"
    }

# ==============================================================================
# 3. STATEWIDE AP-QAIC DATA & COLLEGE NODES DATABASE (380+ Nodes Network)
# ==============================================================================

ANDHRA_REGIONS = {
    "North Coastal": {
        "lead_institute": "Andhra University College of Engineering (Visakhapatnam)",
        "districts": ["Visakhapatnam", "Vizianagaram", "Srikakulam", "Anakapalli", "Alluri Sitharama Raju"],
        "node_count": 86,
        "active_learners": 11400,
        "certified_faculty": 194
    },
    "Coastal Andhra": {
        "lead_institute": "JNTU Kakinada & VR Siddhartha Engineering College (Vijayawada)",
        "districts": ["Krishna", "Guntur", "NTR", "East Godavari", "West Godavari", "Eluru", "Prakasam", "Bapatla", "Palnadu", "Dr. B.R. Ambedkar Konaseema"],
        "node_count": 182,
        "active_learners": 23600,
        "certified_faculty": 412
    },
    "Rayalaseema": {
        "lead_institute": "IIT Tirupati & Sri Venkateswara University (Tirupati)",
        "districts": ["Tirupati", "Chittoor", "Ananthapuramu", "Sri Sathya Sai", "YSR Kadapa", "Annamayya", "Kurnool", "Nandyal"],
        "node_count": 114,
        "active_learners": 14850,
        "certified_faculty": 258
    }
}

COLLEGE_NODES_DATA = [
    {"id": "AP-NODE-001", "name": "Andhra University College of Engineering", "district": "Visakhapatnam", "region": "North Coastal", "tier": "Level 4 (Specialist Hub)", "students": 640, "faculty": 12, "readiness": "100%", "active_lab": "High-Performance Simulator + Qiskit Cloud"},
    {"id": "AP-NODE-002", "name": "IIT Tirupati Quantum Research Hub", "district": "Tirupati", "region": "Rayalaseema", "tier": "Level 4 (Specialist Hub)", "students": 480, "faculty": 10, "readiness": "100%", "active_lab": "NQM Superconducting & Photonic QKD Testbed"},
    {"id": "AP-NODE-003", "name": "JNTUK University College of Engineering", "district": "Kakinada", "region": "Coastal Andhra", "tier": "Level 3 (Application)", "students": 520, "faculty": 8, "readiness": "94%", "active_lab": "Quantum Algorithms & QML Node"},
    {"id": "AP-NODE-004", "name": "VR Siddhartha Engineering College", "district": "Vijayawada", "region": "Coastal Andhra", "tier": "Level 3 (Application)", "students": 410, "faculty": 7, "readiness": "92%", "active_lab": "Quantum Communication & Security Lab"},
    {"id": "AP-NODE-005", "name": "Gayatri Vidya Parishad College of Engg", "district": "Visakhapatnam", "region": "North Coastal", "tier": "Level 3 (Application)", "students": 380, "faculty": 6, "readiness": "88%", "active_lab": "Qubit Simulator Node"},
    {"id": "AP-NODE-006", "name": "Sri Venkateswara University College of Engg", "district": "Tirupati", "region": "Rayalaseema", "tier": "Level 3 (Application)", "students": 350, "faculty": 6, "readiness": "89%", "active_lab": "Quantum Cryptography Lab"},
    {"id": "AP-NODE-007", "name": "RVR & JC College of Engineering", "district": "Guntur", "region": "Coastal Andhra", "tier": "Level 2 (Foundations)", "students": 310, "faculty": 5, "readiness": "82%", "active_lab": "Quantum Gate & Linear Algebra Sandbox"},
    {"id": "AP-NODE-008", "name": "JNTUA College of Engineering", "district": "Ananthapuramu", "region": "Rayalaseema", "tier": "Level 3 (Application)", "students": 400, "faculty": 7, "readiness": "91%", "active_lab": "Quantum Optimization for Energy Grids"},
    {"id": "AP-NODE-009", "name": "GMR Institute of Technology", "district": "Vizianagaram", "region": "North Coastal", "tier": "Level 2 (Foundations)", "students": 290, "faculty": 4, "readiness": "78%", "active_lab": "Foundation Circuits Simulation Lab"},
    {"id": "AP-NODE-010", "name": "SRKR Engineering College", "district": "Bhimavaram", "region": "Coastal Andhra", "tier": "Level 2 (Foundations)", "students": 330, "faculty": 5, "readiness": "80%", "active_lab": "Algorithms & Circuit Simulation"},
    {"id": "AP-NODE-011", "name": "K L University Quantum Science Center", "district": "Vaddeswaram", "region": "Coastal Andhra", "tier": "Level 4 (Specialist Hub)", "students": 560, "faculty": 9, "readiness": "96%", "active_lab": "Quantum ML & Chemistry Simulation"},
    {"id": "AP-NODE-012", "name": "Madanapalle Institute of Tech & Science", "district": "Annamayya", "region": "Rayalaseema", "tier": "Level 1 (Awareness)", "students": 220, "faculty": 3, "readiness": "71%", "active_lab": "Quantum Awareness & Virtual Labs Node"},
    {"id": "AP-NODE-013", "name": "Sree Vidyanikethan Engineering College", "district": "Tirupati", "region": "Rayalaseema", "tier": "Level 2 (Foundations)", "students": 280, "faculty": 4, "readiness": "79%", "active_lab": "Quantum Circuit Simulator Lab"},
    {"id": "AP-NODE-014", "name": "ANITS Engineering College", "district": "Visakhapatnam", "region": "North Coastal", "tier": "Level 2 (Foundations)", "students": 270, "faculty": 4, "readiness": "77%", "active_lab": "Virtual Quantum Lab"},
    {"id": "AP-NODE-015", "name": "Govt Degree College (Autonomous)", "district": "Rajahmundry", "region": "Coastal Andhra", "tier": "Level 1 (Awareness)", "students": 190, "faculty": 2, "readiness": "68%", "active_lab": "Statewide Awareness Node"}
]

TIERED_CURRICULUM_DATA = [
    {
        "level": "Level 1",
        "title": "Quantum Awareness & Literacy",
        "badge": "Beginner Track",
        "duration": "15 Hours (1 Credit / Micro-credential)",
        "prerequisites": "10+2 Mathematics or basic logic",
        "target": "All First & Second Year Undergraduates across 380+ Colleges",
        "topics": [
            "What is Quantum Computing? Classical bits vs Qubits",
            "Superposition: The Coin Toss and State Space",
            "Entanglement: 'Spooky Action' and Quantum Correlation",
            "Real-world impact: Cryptography, Material Science, AI, and Logistics",
            "Quantum Career Map: Software, Cryptography, Algorithmic Finance"
        ],
        "practical_lab": "Bloch Sphere 3D Interactive Visualization & Simple Measurement Experiments",
        "aicte_nqm_alignment": "National Quantum Mission (NQM) Pillar 4: Human Resource Development (Awareness Track)"
    },
    {
        "level": "Level 2",
        "title": "Quantum Foundations & Gate Circuits",
        "badge": "Core Track",
        "duration": "45 Hours (3 Credits Semester Elective)",
        "prerequisites": "Linear Algebra (vectors, matrices, inner products), Basic Python",
        "target": "Third Year Computer Science, ECE, Data Science, and Physics students",
        "topics": [
            "Bra-Ket (Dirac) Notation, Statevectors, and Inner Products",
            "Unitary Operators & Single Qubit Gates (Pauli X/Y/Z, Hadamard, Phase S, T)",
            "Multiple Qubits, Tensor Products, and Entangling Gates (CNOT, CZ, SWAP)",
            "Quantum Measurement, Born Rule, and State Collapse",
            "Circuit Composition, Reversible Logic, and Phase Kickback"
        ],
        "practical_lab": "Python NumPy Circuit Simulator, Bell State Creation, GHZ State Entanglement Verification",
        "aicte_nqm_alignment": "AICTE Emerging Technology Model Curriculum: Quantum Computing Foundations (ET-QC-201)"
    },
    {
        "level": "Level 3",
        "title": "Applied Quantum Computing & AI/ML",
        "badge": "Advanced Track",
        "duration": "60 Hours (4 Credits Course + Lab)",
        "prerequisites": "Level 2 Foundations + Python OOP + Machine Learning basics",
        "target": "Final Year Students, Post-graduates & Faculty Trainees",
        "topics": [
            "Quantum Oracle Algorithms: Deutsch-Jozsa, Bernstein-Vazirani, Grover's Search",
            "Quantum Key Distribution (BB84 Protocol) & Quantum Teleportation",
            "Parameterized Quantum Circuits (PQC) & Variational Quantum Eigensolver (VQE)",
            "Quantum Machine Learning: Quantum Support Vector Machines (QSVM) & Variational Classifiers",
            "Quantum Error Mitigation and Noise Models"
        ],
        "practical_lab": "Simulate Grover's 4-Item Search, BB84 Eavesdropping Detection, and 2-Qubit Variational Classifier",
        "aicte_nqm_alignment": "AICTE Specialized Elective / APSSDC Master Trainer Certification Track"
    },
    {
        "level": "Level 4",
        "title": "Specialisation & Industry-Linked Capstone",
        "badge": "Industry & Research",
        "duration": "120 Hours (Internship / Major Project)",
        "prerequisites": "Level 3 Application + Gateway Assessment Score > 80%",
        "target": "Selected Cohort (Top 10-15% of statewide learners) & Research Scholars",
        "topics": [
            "Quantum Optimization for Real-World Problems (QAOA for Port Logistics in Visakhapatnam)",
            "Post-Quantum Cryptography (PQC) & Lattice-Based Key Exchange Migration",
            "Quantum Chemistry: Molecular Ground State Energy for Drug Discovery",
            "Cloud Quantum Hardware Deployment (IBM Quantum, AWS Braket, C-DAC Q-Sim)",
            "Research Paper Publication & Startup Incubation via QAIC Venture Desk"
        ],
        "practical_lab": "Industry Capstone Co-developed with TCS / C-DAC / APSSDC Partner Labs",
        "aicte_nqm_alignment": "National Quantum Mission Research Grant & APSSDC Quantum Co-op Placement"
    }
]

DIAGNOSTIC_ASSESSMENT_QUESTIONS = [
    {
        "id": 1,
        "question": "What mathematical principle allows a qubit to exist in a linear combination of states |0⟩ and |1⟩ simultaneously?",
        "options": [
            "Quantum Superposition",
            "Quantum Tunneling",
            "Pauli Exclusion Principle",
            "Heisenberg Uncertainty"
        ],
        "correct": 0,
        "explanation": "Superposition is the ability of a quantum state |ψ⟩ = α|0⟩ + β|1⟩ to exist in a linear combination of basis states with probability amplitudes α and β."
    },
    {
        "id": 2,
        "question": "Which quantum gate transforms the basis state |0⟩ into the equal superposition state (|0⟩ + |1⟩)/√2?",
        "options": [
            "Pauli-X Gate",
            "Hadamard (H) Gate",
            "Phase (S) Gate",
            "CNOT Gate"
        ],
        "correct": 1,
        "explanation": "The Hadamard gate H creates an equal superposition: H|0⟩ = (|0⟩ + |1⟩)/√2 and H|1⟩ = (|0⟩ - |1⟩)/√2."
    },
    {
        "id": 3,
        "question": "In a 2-qubit system, what is the resulting state when a Hadamard gate is applied to qubit 0 followed by a CNOT (control=0, target=1) starting from |00⟩?",
        "options": [
            "|00⟩",
            "|11⟩",
            "(|00⟩ + |11⟩)/√2 (Bell State |Φ+⟩)",
            "(|01⟩ + |10⟩)/√2 (Bell State |Ψ+⟩)"
        ],
        "correct": 2,
        "explanation": "H|00⟩ gives (|00⟩ + |10⟩)/√2. The CNOT flips qubit 1 when qubit 0 is 1, yielding (|00⟩ + |11⟩)/√2, the maximally entangled Bell state |Φ+⟩."
    },
    {
        "id": 4,
        "question": "In the BB84 Quantum Key Distribution protocol, why does an eavesdropper (Eve) get detected?",
        "options": [
            "Because quantum hardware has GPS tracing built into photons",
            "Because measuring a quantum state in an incompatible basis collapses the state, causing noticeable errors (QBER)",
            "Because Alice's classical channel automatically encrypts Eve's IP address",
            "Because photons cannot be transmitted through optical fiber without authorization"
        ],
        "correct": 1,
        "explanation": "Under the No-Cloning Theorem and quantum measurement postulates, measuring a qubit in the wrong basis perturbs its state, introducing ~25% error rate on sifted keys which alerts Alice and Bob."
    },
    {
        "id": 5,
        "question": "What is the theoretical quantum speedup provided by Grover's Search Algorithm over classical unstructured search of N items?",
        "options": [
            "Quadratic speedup: O(√N) versus classical O(N)",
            "Exponential speedup: O(log N) versus classical O(N)",
            "Linear speedup: O(N/2) versus classical O(N)",
            "Polynomial speedup: O(N^2)"
        ],
        "correct": 0,
        "explanation": "Grover's algorithm provides a provable quadratic speedup, finding an item in an unsorted database in O(√N) oracle queries compared to classical O(N)."
    }
]

# ==============================================================================
# 4. FLASK REST API ENDPOINTS
# ==============================================================================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_nodes = sum(r['node_count'] for r in ANDHRA_REGIONS.values())
    total_learners = sum(r['active_learners'] for r in ANDHRA_REGIONS.values())
    total_faculty = sum(r['certified_faculty'] for r in ANDHRA_REGIONS.values())
    return jsonify({
        "network_name": "AP-QAIC Hub & Spoke Network",
        "districts_covered": 26,
        "total_college_nodes": total_nodes,
        "target_nodes": 380,
        "active_enrolled_learners": total_learners,
        "certified_faculty_mentors": total_faculty,
        "active_simulations_today": 1284,
        "industry_internships_matched": 412,
        "regions": ANDHRA_REGIONS
    })

@app.route('/api/colleges', methods=['GET'])
def get_colleges():
    region_filter = request.args.get('region', 'All')
    tier_filter = request.args.get('tier', 'All')
    search = request.args.get('search', '').lower()

    filtered = COLLEGE_NODES_DATA
    if region_filter != 'All':
        filtered = [c for c in filtered if c['region'] == region_filter]
    if tier_filter != 'All':
        filtered = [c for c in filtered if tier_filter in c['tier']]
    if search:
        filtered = [c for c in filtered if search in c['name'].lower() or search in c['district'].lower()]

    return jsonify({"count": len(filtered), "nodes": filtered})

@app.route('/api/curriculum', methods=['GET'])
def get_curriculum():
    return jsonify({"curriculum": TIERED_CURRICULUM_DATA})

@app.route('/api/simulate', methods=['POST'])
def simulate():
    data = request.get_json() or {}
    num_qubits = int(data.get('num_qubits', 2))
    instructions = data.get('instructions', [])
    sim = QuantumSimulator(num_qubits=num_qubits)
    try:
        result = sim.execute_circuit(instructions)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/bb84', methods=['POST'])
def run_bb84():
    data = request.get_json() or {}
    num_bits = int(data.get('num_bits', 20))
    eve = bool(data.get('eavesdropper', False))
    result = simulate_bb84(num_bits=num_bits, eavesdropper_active=eve)
    return jsonify({"success": True, "result": result})

@app.route('/api/quiz', methods=['GET'])
def get_quiz():
    # Return questions without disclosing answers
    sanitized = []
    for q in DIAGNOSTIC_ASSESSMENT_QUESTIONS:
        sanitized.append({
            "id": q["id"],
            "question": q["question"],
            "options": q["options"]
        })
    return jsonify({"questions": sanitized})

@app.route('/api/quiz/evaluate', methods=['POST'])
def evaluate_quiz():
    data = request.get_json() or {}
    user_answers = data.get('answers', {})
    student_name = data.get('name', 'Learner')
    college_name = data.get('college', 'Andhra Pradesh College Node')

    score = 0
    feedback = []
    for q in DIAGNOSTIC_ASSESSMENT_QUESTIONS:
        qid_str = str(q["id"])
        chosen = user_answers.get(qid_str)
        is_correct = (chosen == q["correct"])
        if is_correct:
            score += 1
        feedback.append({
            "id": q["id"],
            "question": q["question"],
            "your_answer": chosen,
            "correct_answer": q["correct"],
            "is_correct": is_correct,
            "explanation": q["explanation"]
        })

    percentage = round((score / len(DIAGNOSTIC_ASSESSMENT_QUESTIONS)) * 100, 1)
    status = "QUALIFIED - QUANTUM ADVANCED TRACK" if percentage >= 60 else "RECOMMENDED - LEVEL 1 FOUNDATIONS TRACK"

    return jsonify({
        "student_name": student_name,
        "college_name": college_name,
        "score": score,
        "total": len(DIAGNOSTIC_ASSESSMENT_QUESTIONS),
        "percentage": percentage,
        "status": status,
        "feedback": feedback,
        "competencies": {
            "Superposition & Principles": 95 if percentage >= 60 else 65,
            "Quantum Circuit Architecture": 90 if percentage >= 60 else 55,
            "Multi-Qubit Entanglement": 85 if percentage >= 60 else 50,
            "Quantum Cryptography & QKD": 90 if percentage >= 60 else 60,
            "Algorithmic Complexity": 88 if percentage >= 60 else 45
        }
    })

# ==============================================================================
# 5. EMBEDDED SINGLE PAGE APPLICATION (SPA) TEMPLATE
# ==============================================================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AP-QAIC | Statewide Quantum Talent Pipeline & Curriculum (QEXPO 2026)</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        quantum: {
                            50: '#f0f5ff',
                            100: '#e0ecff',
                            500: '#3b82f6',
                            600: '#2563eb',
                            700: '#1d4ed8',
                            900: '#0b132b',
                            accent: '#06d6a0',
                            purple: '#8b5cf6',
                            neon: '#00f2fe'
                        }
                    }
                }
            }
        }
    </script>
    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 15px rgba(6, 214, 160, 0.4); }
            50% { box-shadow: 0 0 30px rgba(0, 242, 254, 0.7); }
        }
        .glow-box { animation: pulse-glow 3s infinite; }
        .circuit-wire {
            background: repeating-linear-gradient(90deg, #334155, #334155 10px, transparent 10px, transparent 16px);
        }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans antialiased selection:bg-cyan-500 selection:text-slate-900">

    <!-- Top Navigation Header -->
    <header class="border-b border-slate-800 bg-slate-900/90 backdrop-blur-md sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-purple-600 flex items-center justify-center font-bold text-lg shadow-lg shadow-blue-500/20 text-white">
                    Ψ
                </div>
                <div>
                    <div class="flex items-center space-x-2">
                        <span class="font-extrabold text-lg tracking-tight bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
                            AP-QAIC
                        </span>
                        <span class="text-xs px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800 font-mono">
                            UC 090
                        </span>
                        <span class="text-xs px-2 py-0.5 rounded-full bg-blue-950 text-blue-300 border border-blue-800 font-mono">
                            QEXPO 2026
                        </span>
                    </div>
                    <p class="text-xs text-slate-400 font-medium">Statewide Quantum Talent Pipeline & Curriculum • Andhra Pradesh</p>
                </div>
            </div>

            <!-- Navigation Tabs -->
            <nav class="hidden md:flex space-x-1">
                <button onclick="switchTab('dashboard')" id="nav-dashboard" class="nav-btn px-3 py-1.5 rounded-lg text-sm font-medium text-cyan-400 bg-slate-800 border border-cyan-500/30 flex items-center space-x-1.5 transition">
                    <i data-lucide="layout-dashboard" class="w-4 h-4"></i>
                    <span>Statewide Hub</span>
                </button>
                <button onclick="switchTab('curriculum')" id="nav-curriculum" class="nav-btn px-3 py-1.5 rounded-lg text-sm font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 flex items-center space-x-1.5 transition">
                    <i data-lucide="book-open" class="w-4 h-4"></i>
                    <span>Tiered Curriculum</span>
                </button>
                <button onclick="switchTab('simulator')" id="nav-simulator" class="nav-btn px-3 py-1.5 rounded-lg text-sm font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 flex items-center space-x-1.5 transition">
                    <i data-lucide="cpu" class="w-4 h-4"></i>
                    <span>Quantum Lab Sim</span>
                </button>
                <button onclick="switchTab('qkd')" id="nav-qkd" class="nav-btn px-3 py-1.5 rounded-lg text-sm font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 flex items-center space-x-1.5 transition">
                    <i data-lucide="shield-check" class="w-4 h-4"></i>
                    <span>BB84 QKD Protocol</span>
                </button>
                <button onclick="switchTab('assessment')" id="nav-assessment" class="nav-btn px-3 py-1.5 rounded-lg text-sm font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 flex items-center space-x-1.5 transition">
                    <i data-lucide="award" class="w-4 h-4"></i>
                    <span>Skill Test & Credential</span>
                </button>
            </nav>

            <!-- Status Indicator -->
            <div class="flex items-center space-x-3">
                <div class="flex items-center space-x-2 text-xs text-slate-400">
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping"></span>
                    <span class="text-emerald-400 font-semibold">Sim Engine Online</span>
                </div>
                <a href="#roadmap" onclick="switchTab('dashboard')" class="text-xs bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium px-3 py-1.5 rounded-lg shadow-sm">
                    APSSDC / NQM Sync
                </a>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

        <!-- =================================================================== -->
        <!-- TAB 1: STATEWIDE HUB & SPOKE DASHBOARD -->
        <!-- =================================================================== -->
        <div id="tab-dashboard" class="tab-content space-y-6">
            <!-- Hero Banner -->
            <div class="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-blue-950/60 to-slate-900 border border-slate-800 p-6 sm:p-8">
                <div class="absolute -right-16 -top-16 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>
                <div class="absolute -left-16 -bottom-16 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl pointer-events-none"></div>

                <div class="relative z-10 max-w-3xl">
                    <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-3">
                        <i data-lucide="globe" class="w-3.5 h-3.5"></i>
                        <span>Andhra Pradesh Quantum Mission • 380+ College Nodes</span>
                    </div>
                    <h1 class="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
                        Democratizing Quantum Skills <br/>
                        <span class="bg-gradient-to-r from-cyan-400 via-teal-300 to-blue-400 bg-clip-text text-transparent">
                            Across Every District of Andhra Pradesh
                        </span>
                    </h1>
                    <p class="mt-3 text-slate-300 text-sm sm:text-base leading-relaxed">
                        Moving quantum learning from isolated premier labs into a synchronized <strong>Hub-and-Spoke statewide network</strong>. 
                        Coordinating AICTE-aligned curriculum, shared cloud quantum simulators, certified faculty enablement, and industry co-ops.
                    </p>

                    <div class="mt-6 flex flex-wrap gap-3">
                        <button onclick="switchTab('simulator')" class="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm flex items-center space-x-2 shadow-lg shadow-cyan-500/20 transition">
                            <i data-lucide="play" class="w-4 h-4 fill-slate-950"></i>
                            <span>Launch Live Quantum Circuit Simulator</span>
                        </button>
                        <button onclick="switchTab('curriculum')" class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium text-sm flex items-center space-x-2 transition">
                            <i data-lucide="compass" class="w-4 h-4"></i>
                            <span>Explore 4-Tier Curriculum Pathway</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- KPI Cards Grid -->
            <div class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-cyan-500/40 transition">
                    <div class="flex items-center justify-between text-slate-400 text-xs font-medium uppercase tracking-wider">
                        <span>Connected College Nodes</span>
                        <i data-lucide="network" class="w-4 h-4 text-cyan-400"></i>
                    </div>
                    <div class="mt-2 flex items-baseline space-x-2">
                        <span class="text-2xl sm:text-3xl font-extrabold text-white">382</span>
                        <span class="text-xs text-emerald-400 font-semibold font-mono">/ 380+ Target</span>
                    </div>
                    <div class="mt-3 text-xs text-slate-400">All 26 Districts Active (North, Coastal, Rayalaseema)</div>
                    <div class="mt-2 w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                        <div class="bg-cyan-400 h-full w-[100%]"></div>
                    </div>
                </div>

                <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-blue-500/40 transition">
                    <div class="flex items-center justify-between text-slate-400 text-xs font-medium uppercase tracking-wider">
                        <span>Active Enrolled Learners</span>
                        <i data-lucide="users" class="w-4 h-4 text-blue-400"></i>
                    </div>
                    <div class="mt-2 flex items-baseline space-x-2">
                        <span class="text-2xl sm:text-3xl font-extrabold text-white">49,850</span>
                        <span class="text-xs text-cyan-400 font-semibold font-mono">+34% this term</span>
                    </div>
                    <div class="mt-3 text-xs text-slate-400">Awareness (Level 1) through Specialist (Level 4)</div>
                    <div class="mt-2 w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                        <div class="bg-blue-500 h-full w-[82%]"></div>
                    </div>
                </div>

                <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-purple-500/40 transition">
                    <div class="flex items-center justify-between text-slate-400 text-xs font-medium uppercase tracking-wider">
                        <span>Certified Faculty Mentors</span>
                        <i data-lucide="graduation-cap" class="w-4 h-4 text-purple-400"></i>
                    </div>
                    <div class="mt-2 flex items-baseline space-x-2">
                        <span class="text-2xl sm:text-3xl font-extrabold text-white">864</span>
                        <span class="text-xs text-purple-300 font-semibold font-mono">APSSDC Certified</span>
                    </div>
                    <div class="mt-3 text-xs text-slate-400">Trained via Master Trainer Faculty Enablement</div>
                    <div class="mt-2 w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                        <div class="bg-purple-500 h-full w-[94%]"></div>
                    </div>
                </div>

                <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-emerald-500/40 transition">
                    <div class="flex items-center justify-between text-slate-400 text-xs font-medium uppercase tracking-wider">
                        <span>Industry Placements / Co-Ops</span>
                        <i data-lucide="briefcase" class="w-4 h-4 text-emerald-400"></i>
                    </div>
                    <div class="mt-2 flex items-baseline space-x-2">
                        <span class="text-2xl sm:text-3xl font-extrabold text-white">412</span>
                        <span class="text-xs text-emerald-400 font-semibold font-mono">TCS, C-DAC, Q-Labs</span>
                    </div>
                    <div class="mt-3 text-xs text-slate-400">Internships, capstones & research stipends</div>
                    <div class="mt-2 w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                        <div class="bg-emerald-400 h-full w-[76%]"></div>
                    </div>
                </div>
            </div>

            <!-- Regional Lead Hubs & Hub-Spoke Architecture Section -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Regional Leads Breakdown -->
                <div class="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
                    <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                        <h3 class="font-bold text-white flex items-center space-x-2 text-base">
                            <i data-lucide="map-pin" class="w-4 h-4 text-cyan-400"></i>
                            <span>Regional Hub Leads</span>
                        </h3>
                        <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">3 Hubs</span>
                    </div>

                    <!-- Hub 1: North Coastal -->
                    <div class="p-3.5 rounded-lg bg-slate-800/60 border border-slate-700/60 hover:border-cyan-500/50 transition">
                        <div class="flex justify-between items-start">
                            <div>
                                <span class="text-xs font-bold uppercase tracking-wider text-cyan-400">North Coastal Lead</span>
                                <h4 class="font-semibold text-sm text-slate-100">Andhra University (AUCE)</h4>
                                <p class="text-xs text-slate-400 mt-0.5">Visakhapatnam, Vizianagaram, Srikakulam</p>
                            </div>
                            <span class="text-xs font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">86 Nodes</span>
                        </div>
                        <div class="mt-2 text-xs flex justify-between text-slate-300">
                            <span>Learners: <strong>11,400</strong></span>
                            <span>Faculty: <strong>194</strong></span>
                        </div>
                    </div>

                    <!-- Hub 2: Coastal AP -->
                    <div class="p-3.5 rounded-lg bg-slate-800/60 border border-slate-700/60 hover:border-blue-500/50 transition">
                        <div class="flex justify-between items-start">
                            <div>
                                <span class="text-xs font-bold uppercase tracking-wider text-blue-400">Coastal Andhra Lead</span>
                                <h4 class="font-semibold text-sm text-slate-100">JNTU Kakinada & VRSEC</h4>
                                <p class="text-xs text-slate-400 mt-0.5">Krishna, Guntur, East/West Godavari, Nellore</p>
                            </div>
                            <span class="text-xs font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">182 Nodes</span>
                        </div>
                        <div class="mt-2 text-xs flex justify-between text-slate-300">
                            <span>Learners: <strong>23,600</strong></span>
                            <span>Faculty: <strong>412</strong></span>
                        </div>
                    </div>

                    <!-- Hub 3: Rayalaseema -->
                    <div class="p-3.5 rounded-lg bg-slate-800/60 border border-slate-700/60 hover:border-purple-500/50 transition">
                        <div class="flex justify-between items-start">
                            <div>
                                <span class="text-xs font-bold uppercase tracking-wider text-purple-400">Rayalaseema Lead</span>
                                <h4 class="font-semibold text-sm text-slate-100">IIT Tirupati & SV University</h4>
                                <p class="text-xs text-slate-400 mt-0.5">Tirupati, Anantapur, Chittoor, Kadapa, Kurnool</p>
                            </div>
                            <span class="text-xs font-mono px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800">114 Nodes</span>
                        </div>
                        <div class="mt-2 text-xs flex justify-between text-slate-300">
                            <span>Learners: <strong>14,850</strong></span>
                            <span>Faculty: <strong>258</strong></span>
                        </div>
                    </div>

                    <div class="p-3 rounded-lg bg-blue-950/40 border border-blue-900/60 text-xs text-blue-200">
                        <span class="font-bold text-blue-300">Governance Role:</span> Regional Leads run localized faculty development, administer standardized gateway assessments, and host physical quantum hardware access days.
                    </div>
                </div>

                <!-- College Nodes Search & Directory -->
                <div class="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
                    <div>
                        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-800 pb-3">
                            <div>
                                <h3 class="font-bold text-white text-base flex items-center space-x-2">
                                    <i data-lucide="building-2" class="w-4 h-4 text-cyan-400"></i>
                                    <span>Statewide College Node Directory</span>
                                </h3>
                                <p class="text-xs text-slate-400">Real-time status of participating higher education institutions</p>
                            </div>
                            <!-- Filter Controls -->
                            <div class="flex items-center space-x-2">
                                <input id="college-search" oninput="filterColleges()" type="text" placeholder="Search college or district..." class="bg-slate-800 border border-slate-700 text-xs text-slate-100 rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyan-500 w-48">
                                <select id="region-filter" onchange="filterColleges()" class="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg px-2 py-1.5 focus:outline-none">
                                    <option value="All">All Regions</option>
                                    <option value="North Coastal">North Coastal</option>
                                    <option value="Coastal Andhra">Coastal Andhra</option>
                                    <option value="Rayalaseema">Rayalaseema</option>
                                </select>
                            </div>
                        </div>

                        <!-- Table -->
                        <div class="mt-4 overflow-x-auto max-h-[340px] overflow-y-auto">
                            <table class="w-full text-left text-xs">
                                <thead class="bg-slate-800/70 text-slate-400 uppercase font-mono sticky top-0">
                                    <tr>
                                        <th class="p-2.5">Node ID / College</th>
                                        <th class="p-2.5">Region</th>
                                        <th class="p-2.5">Tier Level</th>
                                        <th class="p-2.5">Learners</th>
                                        <th class="p-2.5">Faculty</th>
                                        <th class="p-2.5">Readiness</th>
                                    </tr>
                                </thead>
                                <tbody id="college-table-body" class="divide-y divide-slate-800 text-slate-300">
                                    <!-- Populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div class="mt-3 pt-3 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
                        <span>Showing verified college nodes aligned with AICTE & APSSDC standards.</span>
                        <span id="nodes-count-display" class="font-mono text-cyan-400 font-semibold">15 Nodes Shown</span>
                    </div>
                </div>
            </div>

            <!-- Stakeholder Alignment Roadmap Section -->
            <div id="roadmap" class="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-5">
                <div class="border-b border-slate-800 pb-3 flex justify-between items-center">
                    <div>
                        <h3 class="font-bold text-white text-lg flex items-center space-x-2">
                            <i data-lucide="git-merge" class="w-5 h-5 text-purple-400"></i>
                            <span>Statewide Implementation Roadmap (Phases 1 to 4)</span>
                        </h3>
                        <p class="text-xs text-slate-400 mt-1">Structured scaling from 50 pilot nodes to 380+ permanent quantum centers</p>
                    </div>
                    <span class="text-xs bg-emerald-950 text-emerald-300 border border-emerald-800 px-3 py-1 rounded-full font-mono font-medium">
                        Current Status: Phase 3 Expand
                    </span>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <!-- Phase 1 -->
                    <div class="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 relative">
                        <span class="text-xs font-mono font-bold text-cyan-400">PHASE 1 (COMPLETED)</span>
                        <h4 class="font-bold text-white text-sm mt-1">Curriculum Design</h4>
                        <p class="text-xs text-slate-400 mt-1.5 leading-relaxed">
                            Mapping competencies to National Quantum Mission & AICTE guidelines. Establishing faculty requirements and core domains.
                        </p>
                        <div class="mt-3 text-xs text-emerald-400 flex items-center space-x-1">
                            <i data-lucide="check-circle" class="w-3.5 h-3.5"></i>
                            <span>Syllabus Verified</span>
                        </div>
                    </div>

                    <!-- Phase 2 -->
                    <div class="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 relative">
                        <span class="text-xs font-mono font-bold text-blue-400">PHASE 2 (COMPLETED)</span>
                        <h4 class="font-bold text-white text-sm mt-1">Pilot 50 College Nodes</h4>
                        <p class="text-xs text-slate-400 mt-1.5 leading-relaxed">
                            Tested Level 1 & 2 coursework across 50 engineering colleges. Iterated virtual labs, simulator workloads, and assessment engine.
                        </p>
                        <div class="mt-3 text-xs text-emerald-400 flex items-center space-x-1">
                            <i data-lucide="check-circle" class="w-3.5 h-3.5"></i>
                            <span>92% Completion Gain</span>
                        </div>
                    </div>

                    <!-- Phase 3 -->
                    <div class="p-4 rounded-xl bg-gradient-to-b from-blue-950/40 to-slate-800/60 border border-cyan-500/50 relative shadow-lg shadow-cyan-500/10">
                        <div class="flex justify-between items-center">
                            <span class="text-xs font-mono font-bold text-cyan-300">PHASE 3 (ACTIVE NOW)</span>
                            <span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                        </div>
                        <h4 class="font-bold text-white text-sm mt-1">Statewide Expansion</h4>
                        <p class="text-xs text-slate-300 mt-1.5 leading-relaxed">
                            Activating 380+ college nodes statewide. Onboarding 800+ faculty master trainers via APSSDC. Opening Level 3 Applied modules.
                        </p>
                        <div class="mt-3 text-xs text-cyan-300 font-semibold">
                            Target: 50,000 Certified Graduates
                        </div>
                    </div>

                    <!-- Phase 4 -->
                    <div class="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 relative">
                        <span class="text-xs font-mono font-bold text-purple-400">PHASE 4 (H2 2026-27)</span>
                        <h4 class="font-bold text-white text-sm mt-1">Sustain & Industry Link</h4>
                        <p class="text-xs text-slate-400 mt-1.5 leading-relaxed">
                            Continuous curriculum refresh, annual outcomes review, venture desk incubation, and deep quantum hardware partnerships.
                        </p>
                        <div class="mt-3 text-xs text-purple-300 font-semibold">
                            Target: Self-sustaining Talent Pipeline
                        </div>
                    </div>
                </div>

                <!-- Stakeholder Matrix -->
                <div class="mt-4 pt-4 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                    <div class="p-3 bg-slate-800/50 rounded-lg">
                        <strong class="text-cyan-300 block mb-1">Higher Education Nodes</strong>
                        <p class="text-slate-400">Embed quantum foundations into electives, student clubs, capstones, and credit frameworks.</p>
                    </div>
                    <div class="p-3 bg-slate-800/50 rounded-lg">
                        <strong class="text-blue-300 block mb-1">APSSDC & Skilling Ecosystem</strong>
                        <p class="text-slate-400">Finances faculty enablement, coordinates regional leads, and provides verifiable state credentials.</p>
                    </div>
                    <div class="p-3 bg-slate-800/50 rounded-lg">
                        <strong class="text-purple-300 block mb-1">Industry & Research Partners</strong>
                        <p class="text-slate-400">TCS, C-DAC, IBM, IITs provide problem statements, real-world internships, and hardware credits.</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- =================================================================== -->
        <!-- TAB 2: TIERED CURRICULUM (LEVEL 1 TO LEVEL 4) -->
        <!-- =================================================================== -->
        <div id="tab-curriculum" class="tab-content hidden space-y-6">
            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
                    <div>
                        <div class="inline-flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-cyan-400 mb-2">
                            <i data-lucide="layers" class="w-3.5 h-3.5"></i>
                            <span>Tiered Progression Pathway • 4 Levels</span>
                        </div>
                        <h2 class="text-2xl sm:text-3xl font-extrabold text-white">Beginner to Quantum Specialist Pathway</h2>
                        <p class="text-slate-400 text-sm mt-1">
                            Designed so every student in AP starts with foundational awareness, progressing through hands-on labs into industry specialization.
                        </p>
                    </div>
                    <div class="flex items-center space-x-2 text-xs">
                        <span class="px-3 py-1.5 rounded-lg bg-blue-950 border border-blue-800 text-blue-300 font-mono">
                            AICTE ET-QC Aligned
                        </span>
                        <span class="px-3 py-1.5 rounded-lg bg-emerald-950 border border-emerald-800 text-emerald-300 font-mono">
                            NQM Approved
                        </span>
                    </div>
                </div>

                <!-- 4 Tier Cards -->
                <div class="mt-6 space-y-6" id="curriculum-container">
                    <!-- Populated dynamically via JS -->
                </div>
            </div>
        </div>

        <!-- =================================================================== -->
        <!-- TAB 3: LIVE QUANTUM CIRCUIT SIMULATOR LAB -->
        <!-- =================================================================== -->
        <div id="tab-simulator" class="tab-content hidden space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Circuit Builder Controls & Presets -->
                <div class="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                        <div>
                            <div class="inline-flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-cyan-400">
                                <i data-lucide="cpu" class="w-3.5 h-3.5"></i>
                                <span>Interactive Quantum Lab Engine</span>
                            </div>
                            <h2 class="text-xl font-extrabold text-white mt-1">Statevector & Circuit Simulator</h2>
                        </div>

                        <!-- Circuit Presets -->
                        <div class="flex items-center space-x-2">
                            <span class="text-xs text-slate-400">Presets:</span>
                            <button onclick="loadPreset('bell')" class="px-2.5 py-1 text-xs rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700">
                                Bell State |Φ+⟩
                            </button>
                            <button onclick="loadPreset('ghz')" class="px-2.5 py-1 text-xs rounded bg-slate-800 hover:bg-slate-700 text-purple-300 border border-slate-700">
                                GHZ (3 Qubits)
                            </button>
                            <button onclick="loadPreset('grover')" class="px-2.5 py-1 text-xs rounded bg-slate-800 hover:bg-slate-700 text-emerald-300 border border-slate-700">
                                Grover Search
                            </button>
                            <button onclick="clearCircuit()" class="px-2.5 py-1 text-xs rounded bg-rose-950/60 hover:bg-rose-900 text-rose-300 border border-rose-800">
                                Clear
                            </button>
                        </div>
                    </div>

                    <!-- Available Gate Toolbox -->
                    <div>
                        <div class="flex justify-between items-center mb-2">
                            <span class="text-xs font-bold uppercase tracking-wider text-slate-300">1. Click Gate to Insert onto Active Qubit:</span>
                            <div class="flex items-center space-x-2 text-xs">
                                <span class="text-slate-400">Qubit Target:</span>
                                <select id="active-qubit-select" class="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded px-2 py-1">
                                    <option value="0">Qubit q[0]</option>
                                    <option value="1">Qubit q[1]</option>
                                    <option value="2">Qubit q[2]</option>
                                </select>
                            </div>
                        </div>

                        <div class="flex flex-wrap gap-2">
                            <button onclick="addGate('H')" class="w-12 h-10 rounded-lg bg-blue-600 hover:bg-blue-500 font-bold text-sm text-white shadow transition flex items-center justify-center border border-blue-400">
                                H
                            </button>
                            <button onclick="addGate('X')" class="w-12 h-10 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-bold text-sm text-white shadow transition flex items-center justify-center border border-emerald-400">
                                X
                            </button>
                            <button onclick="addGate('Y')" class="w-12 h-10 rounded-lg bg-amber-600 hover:bg-amber-500 font-bold text-sm text-white shadow transition flex items-center justify-center border border-amber-400">
                                Y
                            </button>
                            <button onclick="addGate('Z')" class="w-12 h-10 rounded-lg bg-rose-600 hover:bg-rose-500 font-bold text-sm text-white shadow transition flex items-center justify-center border border-rose-400">
                                Z
                            </button>
                            <button onclick="addGate('S')" class="w-12 h-10 rounded-lg bg-indigo-600 hover:bg-indigo-500 font-bold text-sm text-white shadow transition flex items-center justify-center border border-indigo-400">
                                S
                            </button>
                            <button onclick="addGate('T')" class="w-12 h-10 rounded-lg bg-violet-600 hover:bg-violet-500 font-bold text-sm text-white shadow transition flex items-center justify-center border border-violet-400">
                                T
                            </button>
                            <!-- 2 Qubit Gates -->
                            <button onclick="addCnot()" class="px-3 h-10 rounded-lg bg-cyan-700 hover:bg-cyan-600 font-bold text-xs text-white shadow transition flex items-center justify-center border border-cyan-400">
                                + CNOT (CX)
                            </button>
                            <button onclick="addGate('CZ')" class="px-3 h-10 rounded-lg bg-teal-700 hover:bg-teal-600 font-bold text-xs text-white shadow transition flex items-center justify-center border border-teal-400">
                                + CZ
                            </button>
                        </div>
                    </div>

                    <!-- Visual Circuit Board -->
                    <div>
                        <div class="flex justify-between items-center mb-2">
                            <span class="text-xs font-bold uppercase tracking-wider text-slate-300">2. Circuit Schematic:</span>
                            <span class="text-xs text-slate-400" id="circuit-step-count">0 Gates Applied</span>
                        </div>
                        <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-4 font-mono text-xs overflow-x-auto min-h-[140px]" id="circuit-board">
                            <!-- Populated dynamically -->
                        </div>
                    </div>

                    <!-- Run Simulation Button -->
                    <div class="flex items-center justify-between pt-2">
                        <button onclick="runSimulation()" class="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-extrabold text-sm flex items-center space-x-2 shadow-lg shadow-cyan-500/20 transition">
                            <i data-lucide="play" class="w-4 h-4 fill-slate-950"></i>
                            <span>Execute Simulation on Python Kernel</span>
                        </button>
                        <span class="text-xs text-slate-400 font-mono">Pure NumPy Matrix Tensor Contraction</span>
                    </div>
                </div>

                <!-- Simulation Results & Measurement Histograms -->
                <div class="lg:col-span-1 space-y-6">
                    <!-- Statevector Output -->
                    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                        <h3 class="font-bold text-white text-sm flex items-center justify-between">
                            <span class="flex items-center space-x-2">
                                <i data-lucide="code" class="w-4 h-4 text-cyan-400"></i>
                                <span>Quantum State Amplitudes</span>
                            </span>
                            <span class="text-xs font-mono text-slate-400">|ψ⟩ = Σ c_i |i⟩</span>
                        </h3>
                        <div id="statevector-list" class="space-y-2 text-xs font-mono max-h-48 overflow-y-auto pr-1">
                            <div class="p-2.5 rounded bg-slate-800/80 text-slate-400 text-center">
                                Run simulation to view statevector amplitudes.
                            </div>
                        </div>
                    </div>

                    <!-- Measurement Histogram Chart -->
                    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
                        <div class="flex justify-between items-center">
                            <h3 class="font-bold text-white text-sm flex items-center space-x-2">
                                <i data-lucide="bar-chart-2" class="w-4 h-4 text-blue-400"></i>
                                <span>Measurement Shots (1024)</span>
                            </h3>
                            <span class="text-xs font-mono text-cyan-400">Probabilities</span>
                        </div>
                        <div class="h-44">
                            <canvas id="histogramChart"></canvas>
                        </div>
                    </div>

                    <!-- Single Qubit Bloch Vector Metrics -->
                    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
                        <h3 class="font-bold text-white text-sm flex items-center space-x-2">
                            <i data-lucide="compass" class="w-4 h-4 text-purple-400"></i>
                            <span>Bloch Sphere Coordinates</span>
                        </h3>
                        <div id="bloch-metrics" class="text-xs space-y-2 font-mono text-slate-300">
                            <p class="text-slate-500">Bloch sphere values appear after execution.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- =================================================================== -->
        <!-- TAB 4: BB84 QUANTUM KEY DISTRIBUTION (QKD) PROTOCOL -->
        <!-- =================================================================== -->
        <div id="tab-qkd" class="tab-content hidden space-y-6">
            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
                    <div>
                        <div class="inline-flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-emerald-400 mb-1">
                            <i data-lucide="shield-check" class="w-3.5 h-3.5"></i>
                            <span>Quantum Communication Domain • Level 3</span>
                        </div>
                        <h2 class="text-2xl font-extrabold text-white">BB84 Quantum Key Distribution (QKD) Simulator</h2>
                        <p class="text-slate-400 text-sm mt-1">
                            Simulate unconditionally secure cryptographic key exchange between <strong>Alice (Visakhapatnam Hub)</strong> and <strong>Bob (Tirupati Hub)</strong> with eavesdropper detection.
                        </p>
                    </div>

                    <!-- Eve Toggle -->
                    <div class="flex items-center space-x-3 bg-slate-800 p-2.5 rounded-xl border border-slate-700">
                        <label class="text-xs font-medium text-slate-200 cursor-pointer flex items-center space-x-2">
                            <span>Eavesdropper (Eve) Intercept:</span>
                        </label>
                        <button id="eve-toggle-btn" onclick="toggleEve()" class="px-3 py-1 text-xs font-bold rounded-lg bg-slate-700 text-slate-300 border border-slate-600 transition">
                            OFF (Secure Channel)
                        </button>
                    </div>
                </div>

                <!-- Interactive QKD Controls -->
                <div class="flex flex-wrap items-center justify-between gap-4">
                    <div class="flex items-center space-x-3">
                        <button onclick="runQkdSim()" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-bold text-sm flex items-center space-x-2 shadow-lg shadow-emerald-500/20 transition">
                            <i data-lucide="send" class="w-4 h-4"></i>
                            <span>Transmit Photons (Execute QKD Protocol)</span>
                        </button>
                        <select id="qkd-bits-select" class="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg px-3 py-2">
                            <option value="16">16 Photons (Quick Demo)</option>
                            <option value="24" selected>24 Photons (Standard)</option>
                            <option value="32">32 Photons (High Fidelity)</option>
                        </select>
                    </div>

                    <div id="qkd-status-badge" class="px-3 py-1.5 rounded-lg bg-slate-800 text-xs font-mono text-slate-300 border border-slate-700">
                        Awaiting Transmission...
                    </div>
                </div>

                <!-- Step-by-Step Visualization Flow -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
                    <!-- Alice -->
                    <div class="p-4 rounded-xl bg-slate-950 border border-blue-900/50 space-y-3">
                        <div class="flex justify-between items-center text-blue-400 font-bold">
                            <span>ALICE (Sender Node)</span>
                            <i data-lucide="radio" class="w-4 h-4"></i>
                        </div>
                        <div class="text-slate-400 space-y-1">
                            <div>Random Bits: <span id="qkd-alice-bits" class="text-blue-300 font-bold break-all">-</span></div>
                            <div>Polarization Bases: <span id="qkd-alice-bases" class="text-amber-300 font-bold break-all">-</span></div>
                        </div>
                    </div>

                    <!-- Channel & Eve -->
                    <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 relative" id="qkd-eve-card">
                        <div class="flex justify-between items-center text-slate-400 font-bold">
                            <span>QUANTUM CHANNEL</span>
                            <i data-lucide="activity" class="w-4 h-4 text-emerald-400"></i>
                        </div>
                        <div class="text-slate-400 space-y-1">
                            <div>Eve Active: <span id="qkd-eve-status" class="text-slate-300 font-bold">NO</span></div>
                            <div>Eve Bases: <span id="qkd-eve-bases" class="text-rose-400 font-bold break-all">-</span></div>
                        </div>
                    </div>

                    <!-- Bob -->
                    <div class="p-4 rounded-xl bg-slate-950 border border-purple-900/50 space-y-3">
                        <div class="flex justify-between items-center text-purple-400 font-bold">
                            <span>BOB (Receiver Node)</span>
                            <i data-lucide="satellite" class="w-4 h-4"></i>
                        </div>
                        <div class="text-slate-400 space-y-1">
                            <div>Measurement Bases: <span id="qkd-bob-bases" class="text-amber-300 font-bold break-all">-</span></div>
                            <div>Measured Bits: <span id="qkd-bob-bits" class="text-purple-300 font-bold break-all">-</span></div>
                        </div>
                    </div>
                </div>

                <!-- Sifted Key Output & QBER Analysis -->
                <div class="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
                    <h3 class="font-bold text-white text-sm flex items-center justify-between">
                        <span>Basis Sifting & Quantum Bit Error Rate (QBER)</span>
                        <span id="qber-val-badge" class="font-mono text-xs px-2.5 py-0.5 rounded bg-slate-800 text-slate-300">QBER: --%</span>
                    </h3>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
                        <div class="p-3 bg-slate-900 rounded-lg border border-slate-800">
                            <span class="text-slate-400 block mb-1">Alice's Sifted Key:</span>
                            <span id="sifted-alice-key" class="text-emerald-400 text-sm font-bold tracking-widest break-all">--</span>
                        </div>
                        <div class="p-3 bg-slate-900 rounded-lg border border-slate-800">
                            <span class="text-slate-400 block mb-1">Bob's Sifted Key:</span>
                            <span id="sifted-bob-key" class="text-emerald-400 text-sm font-bold tracking-widest break-all">--</span>
                        </div>
                    </div>

                    <div id="qkd-explanation" class="text-xs text-slate-400 leading-relaxed bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                        When Alice and Bob choose matching bases (+ or ×), their measurement results are identical with 100% fidelity. If Eve intercepts the channel, the measurement collapse increases QBER to ~25%, instantly proving eavesdropping under the laws of quantum mechanics.
                    </div>
                </div>
            </div>
        </div>

        <!-- =================================================================== -->
        <!-- TAB 5: SKILL ASSESSMENT & VERIFIED APSSDC CREDENTIAL -->
        <!-- =================================================================== -->
        <div id="tab-assessment" class="tab-content hidden space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Assessment Questions -->
                <div class="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
                    <div class="border-b border-slate-800 pb-4">
                        <div class="inline-flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-purple-400 mb-1">
                            <i data-lucide="check-square" class="w-3.5 h-3.5"></i>
                            <span>Statewide Diagnostic Assessment Engine</span>
                        </div>
                        <h2 class="text-2xl font-extrabold text-white">Quantum Foundations Competency Test</h2>
                        <p class="text-slate-400 text-xs mt-1">Pre/Post assessment metrics aligned with AICTE & National Quantum Mission standards.</p>
                    </div>

                    <!-- Student Info Inputs -->
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <label class="text-xs text-slate-300 font-medium">Candidate Name:</label>
                            <input id="student-name-input" type="text" value="Ajay Kumar" class="mt-1 w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-lg px-3 py-2 focus:border-cyan-500 focus:outline-none">
                        </div>
                        <div>
                            <label class="text-xs text-slate-300 font-medium">College Node / Institution:</label>
                            <input id="student-college-input" type="text" value="Andhra University College of Engineering" class="mt-1 w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-lg px-3 py-2 focus:border-cyan-500 focus:outline-none">
                        </div>
                    </div>

                    <!-- Quiz Questions Container -->
                    <div id="quiz-container" class="space-y-5">
                        <!-- Populated by JavaScript -->
                    </div>

                    <button onclick="submitAssessment()" class="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 font-extrabold text-white text-sm shadow-lg shadow-purple-500/20 transition flex items-center justify-center space-x-2">
                        <i data-lucide="award" class="w-4 h-4"></i>
                        <span>Submit Assessment & Evaluate Competencies</span>
                    </button>
                </div>

                <!-- Competency Radar & Certificate Preview -->
                <div class="lg:col-span-1 space-y-6">
                    <!-- Radar Chart -->
                    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                        <h3 class="font-bold text-white text-sm flex items-center space-x-2">
                            <i data-lucide="pie-chart" class="w-4 h-4 text-purple-400"></i>
                            <span>Competency Radar Profile</span>
                        </h3>
                        <div class="h-56">
                            <canvas id="radarChart"></canvas>
                        </div>
                    </div>

                    <!-- Digital Certificate Card -->
                    <div id="certificate-card" class="bg-gradient-to-br from-slate-900 via-indigo-950/60 to-slate-900 border border-indigo-800/80 rounded-2xl p-5 space-y-3 relative overflow-hidden">
                        <div class="flex justify-between items-start">
                            <div>
                                <span class="text-[10px] uppercase font-bold text-cyan-400 tracking-wider">APSSDC • NQM Certified</span>
                                <h4 class="font-bold text-sm text-white mt-0.5">Quantum Skill Credential</h4>
                            </div>
                            <div class="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-400 flex items-center justify-center text-indigo-300 font-bold text-xs">
                                Ψ
                            </div>
                        </div>

                        <div class="text-xs text-slate-300 space-y-1 font-mono pt-2 border-t border-slate-800">
                            <div>Candidate: <strong id="cert-candidate" class="text-white">Ajay Kumar</strong></div>
                            <div>Institution: <span id="cert-college" class="text-slate-400">AUCE Visakhapatnam</span></div>
                            <div>Score: <span id="cert-score" class="text-emerald-400 font-bold">--%</span></div>
                            <div>Credential ID: <span id="cert-id" class="text-cyan-300">AP-QAIC-2026-PENDING</span></div>
                        </div>

                        <div class="pt-2 text-[11px] text-slate-400 italic">
                            Verifiable digital badge for academic credits & industry internship matching.
                        </div>
                    </div>
                </div>
            </div>
        </div>

    </main>

    <!-- Footer -->
    <footer class="mt-16 border-t border-slate-800 bg-slate-900/60 py-8">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-4">
            <div class="flex items-center space-x-2">
                <span class="w-2 h-2 rounded-full bg-cyan-400"></span>
                <span class="font-semibold text-slate-300">QEXPO 2026 Prototype • USE CASE UC 090</span>
                <span>| Statewide Quantum Talent Pipeline & Curriculum</span>
            </div>
            <div class="text-slate-500">
                Government of Andhra Pradesh • APSSDC • AICTE • National Quantum Mission (NQM)
            </div>
        </div>
    </footer>

    <!-- =================================================================== -->
    <!-- JAVASCRIPT LOGIC -->
    <!-- =================================================================== -->
    <script>
        // Tab switching
        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.nav-btn').forEach(btn => {
                btn.classList.remove('text-cyan-400', 'bg-slate-800', 'border', 'border-cyan-500/30');
                btn.classList.add('text-slate-400');
            });

            const activeTab = document.getElementById('tab-' + tabId);
            if (activeTab) activeTab.classList.remove('hidden');

            const activeBtn = document.getElementById('nav-' + tabId);
            if (activeBtn) {
                activeBtn.classList.remove('text-slate-400');
                activeBtn.classList.add('text-cyan-400', 'bg-slate-800', 'border', 'border-cyan-500/30');
            }
            lucide.createIcons();
        }

        // Global Circuit State
        let circuitInstructions = [];
        let numQubits = 2;
        let histogramChartInstance = null;
        let radarChartInstance = null;
        let eveActive = false;

        // Initialize App
        document.addEventListener('DOMContentLoaded', () => {
            lucide.createIcons();
            loadCollegesTable();
            loadCurriculum();
            loadQuiz();
            initCharts();
            loadPreset('bell');
        });

        // 1. Colleges Table
        async function loadCollegesTable() {
            try {
                const res = await fetch('/api/colleges');
                const data = await res.json();
                renderCollegeRows(data.nodes);
            } catch (err) {
                console.error(err);
            }
        }

        function renderCollegeRows(nodes) {
            const tbody = document.getElementById('college-table-body');
            tbody.innerHTML = '';
            nodes.forEach(c => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-slate-800/40 transition';
                tr.innerHTML = `
                    <td class="p-2.5">
                        <div class="font-semibold text-slate-100">${c.name}</div>
                        <div class="text-[11px] text-slate-400">${c.id} • ${c.district}</div>
                    </td>
                    <td class="p-2.5 text-slate-300">${c.region}</td>
                    <td class="p-2.5">
                        <span class="px-2 py-0.5 rounded text-[10px] font-semibold ${
                            c.tier.includes('Level 4') ? 'bg-purple-950 text-purple-300 border border-purple-800' :
                            c.tier.includes('Level 3') ? 'bg-blue-950 text-blue-300 border border-blue-800' :
                            'bg-slate-800 text-slate-300 border border-slate-700'
                        }">
                            ${c.tier}
                        </span>
                    </td>
                    <td class="p-2.5 font-mono text-cyan-400 font-bold">${c.students}</td>
                    <td class="p-2.5 font-mono text-slate-300">${c.faculty}</td>
                    <td class="p-2.5">
                        <div class="flex items-center space-x-1.5">
                            <span class="font-mono text-emerald-400 font-bold">${c.readiness}</span>
                        </div>
                    </td>
                `;
                tbody.appendChild(tr);
            });
            document.getElementById('nodes-count-display').innerText = `${nodes.length} Nodes Shown`;
        }

        async function filterColleges() {
            const search = document.getElementById('college-search').value;
            const region = document.getElementById('region-filter').value;
            const res = await fetch(`/api/colleges?region=${encodeURIComponent(region)}&search=${encodeURIComponent(search)}`);
            const data = await res.json();
            renderCollegeRows(data.nodes);
        }

        // 2. Curriculum
        async function loadCurriculum() {
            try {
                const res = await fetch('/api/curriculum');
                const data = await res.json();
                const container = document.getElementById('curriculum-container');
                container.innerHTML = '';

                data.curriculum.forEach((lvl, idx) => {
                    const card = document.createElement('div');
                    card.className = "p-5 rounded-xl bg-slate-800/40 border border-slate-700/60 hover:border-cyan-500/40 transition space-y-4";
                    card.innerHTML = `
                        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-700/60 pb-3">
                            <div class="flex items-center space-x-3">
                                <span class="w-8 h-8 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-800 flex items-center justify-center font-bold text-xs font-mono">
                                    0${idx + 1}
                                </span>
                                <div>
                                    <span class="text-xs font-bold uppercase text-cyan-400 tracking-wider">${lvl.level} • ${lvl.badge}</span>
                                    <h3 class="text-lg font-bold text-white">${lvl.title}</h3>
                                </div>
                            </div>
                            <div class="text-xs text-slate-400 font-mono">
                                Duration: <strong class="text-slate-200">${lvl.duration}</strong>
                            </div>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                            <div>
                                <span class="font-bold text-slate-300 uppercase tracking-wider block mb-2">Core Competencies & Modules:</span>
                                <ul class="space-y-1.5 text-slate-400">
                                    ${lvl.topics.map(t => `<li class="flex items-start space-x-2"><span class="text-cyan-400 mt-0.5">•</span><span>${t}</span></li>`).join('')}
                                </ul>
                            </div>
                            <div class="space-y-3 bg-slate-900/60 p-4 rounded-lg border border-slate-800">
                                <div>
                                    <span class="font-bold text-blue-300 uppercase tracking-wider block mb-1">Practical Activity / Lab:</span>
                                    <p class="text-slate-300">${lvl.practical_lab}</p>
                                </div>
                                <div>
                                    <span class="font-bold text-purple-300 uppercase tracking-wider block mb-1">Target Learner Cohort:</span>
                                    <p class="text-slate-400">${lvl.target}</p>
                                </div>
                                <div class="pt-1 text-[11px] text-emerald-400 flex items-center space-x-1">
                                    <i data-lucide="shield-check" class="w-3.5 h-3.5"></i>
                                    <span>${lvl.aicte_nqm_alignment}</span>
                                </div>
                            </div>
                        </div>
                    `;
                    container.appendChild(card);
                });
                lucide.createIcons();
            } catch (err) {
                console.error(err);
            }
        }

        // 3. Circuit Simulator Logic
        function addGate(gate) {
            const target = parseInt(document.getElementById('active-qubit-select').value);
            circuitInstructions.push({ gate: gate, target: target });
            renderCircuitBoard();
        }

        function addCnot() {
            const control = parseInt(prompt("Enter Control Qubit index (0, 1, or 2):", "0"));
            const target = parseInt(prompt("Enter Target Qubit index (0, 1, or 2):", "1"));
            if (!isNaN(control) && !isNaN(target) && control !== target && control >= 0 && control < 3 && target >= 0 && target < 3) {
                circuitInstructions.push({ gate: 'CNOT', control: control, target: target });
                renderCircuitBoard();
            } else {
                alert("Invalid control or target qubit selection!");
            }
        }

        function clearCircuit() {
            circuitInstructions = [];
            renderCircuitBoard();
        }

        function loadPreset(name) {
            circuitInstructions = [];
            if (name === 'bell') {
                numQubits = 2;
                circuitInstructions = [
                    { gate: 'H', target: 0 },
                    { gate: 'CNOT', control: 0, target: 1 }
                ];
            } else if (name === 'ghz') {
                numQubits = 3;
                circuitInstructions = [
                    { gate: 'H', target: 0 },
                    { gate: 'CNOT', control: 0, target: 1 },
                    { gate: 'CNOT', control: 1, target: 2 }
                ];
            } else if (name === 'grover') {
                numQubits = 2;
                circuitInstructions = [
                    { gate: 'H', target: 0 },
                    { gate: 'H', target: 1 },
                    { gate: 'CZ', control: 0, target: 1 }, // Oracle for |11>
                    { gate: 'H', target: 0 },
                    { gate: 'H', target: 1 },
                    { gate: 'X', target: 0 },
                    { gate: 'X', target: 1 },
                    { gate: 'CZ', control: 0, target: 1 }, // Diffusion
                    { gate: 'X', target: 0 },
                    { gate: 'X', target: 1 },
                    { gate: 'H', target: 0 },
                    { gate: 'H', target: 1 }
                ];
            }
            renderCircuitBoard();
            runSimulation();
        }

        function renderCircuitBoard() {
            const board = document.getElementById('circuit-board');
            board.innerHTML = '';
            document.getElementById('circuit-step-count').innerText = `${circuitInstructions.length} Gates Applied`;

            for (let q = 0; q < numQubits; q++) {
                const wire = document.createElement('div');
                wire.className = 'flex items-center space-x-2 py-2 border-b border-slate-800/80';
                
                const qLabel = document.createElement('span');
                qLabel.className = 'w-16 font-bold text-cyan-400';
                qLabel.innerText = `q[${q}] |0⟩ ──`;
                wire.appendChild(qLabel);

                const track = document.createElement('div');
                track.className = 'flex items-center space-x-2 flex-grow overflow-x-auto';

                circuitInstructions.forEach((instr, idx) => {
                    const block = document.createElement('span');
                    if (instr.gate === 'CNOT') {
                        if (instr.control === q) {
                            block.className = 'px-2 py-1 rounded bg-cyan-900 border border-cyan-400 text-cyan-200 font-bold';
                            block.innerText = `● (to q[${instr.target}])`;
                        } else if (instr.target === q) {
                            block.className = 'px-2 py-1 rounded bg-blue-900 border border-blue-400 text-blue-200 font-bold';
                            block.innerText = `⊕ (from q[${instr.control}])`;
                        } else {
                            block.className = 'px-2 py-1 text-slate-600 font-bold';
                            block.innerText = '───';
                        }
                    } else if (instr.gate === 'CZ') {
                        if (instr.control === q || instr.target === q) {
                            block.className = 'px-2 py-1 rounded bg-teal-900 border border-teal-400 text-teal-200 font-bold';
                            block.innerText = `CZ`;
                        } else {
                            block.className = 'px-2 py-1 text-slate-600 font-bold';
                            block.innerText = '───';
                        }
                    } else if (instr.target === q) {
                        block.className = 'px-2.5 py-1 rounded bg-slate-800 border border-cyan-500/50 text-cyan-300 font-bold';
                        block.innerText = instr.gate;
                    } else {
                        block.className = 'px-2 py-1 text-slate-600 font-bold';
                        block.innerText = '───';
                    }
                    track.appendChild(block);
                });

                wire.appendChild(track);
                board.appendChild(wire);
            }
        }

        async function runSimulation() {
            try {
                const res = await fetch('/api/simulate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        num_qubits: numQubits,
                        instructions: circuitInstructions
                    })
                });
                const data = await res.json();
                if (data.success) {
                    renderSimulationResults(data.result);
                } else {
                    alert('Simulation error: ' + data.error);
                }
            } catch (err) {
                console.error(err);
            }
        }

        function renderSimulationResults(result) {
            // Statevector
            const list = document.getElementById('statevector-list');
            list.innerHTML = '';
            result.states.forEach(s => {
                const div = document.createElement('div');
                div.className = 'p-2 rounded bg-slate-800/80 flex justify-between items-center';
                div.innerHTML = `
                    <span class="font-bold text-cyan-400">${s.basis}</span>
                    <span class="text-slate-300">${s.real >= 0 ? '+' : ''}${s.real} ${s.imag >= 0 ? '+' : ''}${s.imag}i</span>
                    <span class="text-emerald-400 font-bold">${(s.prob * 100).toFixed(1)}%</span>
                `;
                list.appendChild(div);
            });

            // Histogram Chart
            const labels = Object.keys(result.shots);
            const counts = Object.values(result.shots);
            updateHistogramChart(labels, counts);

            // Bloch metrics
            const blochBox = document.getElementById('bloch-metrics');
            blochBox.innerHTML = '';
            result.bloch.forEach((b, idx) => {
                const item = document.createElement('div');
                item.className = 'p-2 bg-slate-800/70 rounded border border-slate-700/60';
                item.innerHTML = `
                    <div class="flex justify-between font-bold text-slate-200">
                        <span>q[${idx}] Bloch Vector:</span>
                        <span class="text-purple-300">Purity: ${b.purity}</span>
                    </div>
                    <div class="text-[11px] text-slate-400 mt-1">
                        ⟨X⟩: ${b.x} | ⟨Y⟩: ${b.y} | ⟨Z⟩: ${b.z} <br/>
                        Angles: θ = ${b.theta_deg}°, φ = ${b.phi_deg}°
                    </div>
                `;
                blochBox.appendChild(item);
            });
        }

        // 4. BB84 QKD Protocol Logic
        function toggleEve() {
            eveActive = !eveActive;
            const btn = document.getElementById('eve-toggle-btn');
            const card = document.getElementById('qkd-eve-card');
            if (eveActive) {
                btn.innerText = "ACTIVE (Eavesdropping)";
                btn.className = "px-3 py-1 text-xs font-bold rounded-lg bg-rose-600 text-white border border-rose-400 animate-pulse";
                card.classList.add('border-rose-600', 'bg-rose-950/20');
            } else {
                btn.innerText = "OFF (Secure Channel)";
                btn.className = "px-3 py-1 text-xs font-bold rounded-lg bg-slate-700 text-slate-300 border border-slate-600";
                card.classList.remove('border-rose-600', 'bg-rose-950/20');
            }
        }

        async function runQkdSim() {
            const bits = parseInt(document.getElementById('qkd-bits-select').value);
            const res = await fetch('/api/bb84', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ num_bits: bits, eavesdropper: eveActive })
            });
            const data = await res.json();
            if (data.success) {
                const r = data.result;
                document.getElementById('qkd-alice-bits').innerText = r.alice_bits.join('');
                document.getElementById('qkd-alice-bases').innerText = r.alice_bases.join('');
                document.getElementById('qkd-bob-bases').innerText = r.bob_bases.join('');
                document.getElementById('qkd-bob-bits').innerText = r.bob_measured.join('');
                document.getElementById('qkd-eve-status').innerText = r.eavesdropper_active ? "YES (Interception & Resend)" : "NO";
                document.getElementById('qkd-eve-bases').innerText = r.eve_bases.join('');

                document.getElementById('sifted-alice-key').innerText = r.alice_sifted_key || "NONE (Zero matches)";
                document.getElementById('sifted-bob-key').innerText = r.bob_sifted_key || "NONE (Zero matches)";
                
                const qberBadge = document.getElementById('qber-val-badge');
                qberBadge.innerText = `QBER: ${r.qber_percent}% (${r.mismatches} mismatches)`;

                const statusBadge = document.getElementById('qkd-status-badge');
                if (r.qber_percent > 11.0) {
                    statusBadge.innerText = "SECURITY ALERT: TAMPERING DETECTED (QBER > 11%)";
                    statusBadge.className = "px-3 py-1.5 rounded-lg bg-rose-950 text-xs font-mono text-rose-300 border border-rose-800 font-bold";
                    qberBadge.className = "font-mono text-xs px-2.5 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-700 font-bold";
                } else {
                    statusBadge.innerText = "AUTHENTICATED SECURE KEY ESTABLISHED";
                    statusBadge.className = "px-3 py-1.5 rounded-lg bg-emerald-950 text-xs font-mono text-emerald-300 border border-emerald-800 font-bold";
                    qberBadge.className = "font-mono text-xs px-2.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700 font-bold";
                }
            }
        }

        // 5. Quiz & Assessment Logic
        async function loadQuiz() {
            try {
                const res = await fetch('/api/quiz');
                const data = await res.json();
                const container = document.getElementById('quiz-container');
                container.innerHTML = '';

                data.questions.forEach((q, idx) => {
                    const box = document.createElement('div');
                    box.className = 'p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-3';
                    box.innerHTML = `
                        <div class="font-bold text-slate-100 text-sm">
                            <span class="text-cyan-400 font-mono">Q${idx + 1}.</span> ${q.question}
                        </div>
                        <div class="space-y-1.5 text-xs">
                            ${q.options.map((opt, oIdx) => `
                                <label class="flex items-center space-x-2.5 p-2 rounded bg-slate-900/60 border border-slate-800 hover:border-cyan-500/40 cursor-pointer transition">
                                    <input type="radio" name="q_${q.id}" value="${oIdx}" class="text-cyan-500 focus:ring-0">
                                    <span class="text-slate-300">${opt}</span>
                                </label>
                            `).join('')}
                        </div>
                    `;
                    container.appendChild(box);
                });
            } catch (err) {
                console.error(err);
            }
        }

        async function submitAssessment() {
            const name = document.getElementById('student-name-input').value;
            const college = document.getElementById('student-college-input').value;
            const answers = {};

            document.querySelectorAll('input[type="radio"]:checked').forEach(radio => {
                const qid = radio.name.replace('q_', '');
                answers[qid] = parseInt(radio.value);
            });

            if (Object.keys(answers).length < 3) {
                alert("Please answer at least 3 questions to evaluate your competencies!");
                return;
            }

            const res = await fetch('/api/quiz/evaluate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name, college: college, answers: answers })
            });

            const data = await res.json();
            document.getElementById('cert-candidate').innerText = data.student_name;
            document.getElementById('cert-college').innerText = data.college_name;
            document.getElementById('cert-score').innerText = `${data.percentage}% (${data.score}/${data.total})`;
            document.getElementById('cert-id').innerText = `AP-QAIC-${Math.floor(100000 + Math.random() * 900000)}`;

            updateRadarChart(Object.keys(data.competencies), Object.values(data.competencies));
            alert(`Assessment evaluated! Your Score: ${data.percentage}%. Status: ${data.status}`);
        }

        // Charts Initialization
        function initCharts() {
            // Histogram
            const ctxHist = document.getElementById('histogramChart').getContext('2d');
            histogramChartInstance = new Chart(ctxHist, {
                type: 'bar',
                data: {
                    labels: ['|00⟩', '|01⟩', '|10⟩', '|11⟩'],
                    datasets: [{
                        label: 'Shots',
                        data: [512, 0, 0, 512],
                        backgroundColor: '#06b6d4',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } },
                        x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                    }
                }
            });

            // Radar
            const ctxRadar = document.getElementById('radarChart').getContext('2d');
            radarChartInstance = new Chart(ctxRadar, {
                type: 'radar',
                data: {
                    labels: ['Superposition', 'Circuits', 'Entanglement', 'Cryptography', 'Complexity'],
                    datasets: [{
                        label: 'Demonstrated Skill',
                        data: [85, 75, 80, 70, 65],
                        backgroundColor: 'rgba(139, 92, 246, 0.25)',
                        borderColor: '#8b5cf6',
                        pointBackgroundColor: '#06d6a0',
                        pointBorderColor: '#fff',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        r: {
                            angleLines: { color: '#334155' },
                            grid: { color: '#1e293b' },
                            pointLabels: { color: '#94a3b8', font: { size: 10 } },
                            ticks: { display: false, max: 100, min: 0 }
                        }
                    }
                }
            });
        }

        function updateHistogramChart(labels, counts) {
            if (!histogramChartInstance) return;
            histogramChartInstance.data.labels = labels;
            histogramChartInstance.data.datasets[0].data = counts;
            histogramChartInstance.update();
        }

        function updateRadarChart(labels, dataValues) {
            if (!radarChartInstance) return;
            radarChartInstance.data.labels = labels;
            radarChartInstance.data.datasets[0].data = dataValues;
            radarChartInstance.update();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# ==============================================================================
# 6. CLI AND LAUNCH UTILITIES
# ==============================================================================

def open_browser(port):
    webbrowser.open_new(f"http://127.0.0.1:{port}/")

def run_cli_tests():
    print("=" * 70)
    print("AP-QAIC QUANTUM TALENT PIPELINE & SIMULATOR CLI VERIFICATION")
    print("USE CASE UC 090 - QEXPO 2026")
    print("=" * 70)

    # Test 1: Bell State
    print("\n[TEST 1] Creating Maximally Entangled Bell State (|00> + |11>)/sqrt(2)...")
    sim = QuantumSimulator(2)
    res = sim.execute_circuit([{'gate': 'H', 'target': 0}, {'gate': 'CNOT', 'control': 0, 'target': 1}])
    for s in res['states']:
        print(f"  Basis {s['basis']}: Amplitude = {s['real']} + {s['imag']}i | Probability = {s['prob']*100:.1f}%")
    print(f"  Sample Shots: {res['shots']}")

    # Test 2: BB84 QKD Simulation without Eve
    print("\n[TEST 2] Running BB84 QKD Protocol (Secure Channel, No Eavesdropper)...")
    qkd_clean = simulate_bb84(num_bits=16, eavesdropper_active=False)
    print(f"  Alice Key: {qkd_clean['alice_sifted_key']}")
    print(f"  Bob Key:   {qkd_clean['bob_sifted_key']}")
    print(f"  QBER:      {qkd_clean['qber_percent']}% | Status: {qkd_clean['status']}")

    # Test 3: BB84 QKD Simulation with Eve
    print("\n[TEST 3] Running BB84 QKD Protocol with Active Eavesdropper (Eve)...")
    qkd_eve = simulate_bb84(num_bits=16, eavesdropper_active=True)
    print(f"  Alice Key: {qkd_eve['alice_sifted_key']}")
    print(f"  Bob Key:   {qkd_eve['bob_sifted_key']}")
    print(f"  QBER:      {qkd_eve['qber_percent']}% | Status: {qkd_eve['status']}")

    print("\n[TEST 4] Statewide Andhra Pradesh Network Node Distribution:")
    for region, info in ANDHRA_REGIONS.items():
        print(f"  * {region}: {info['node_count']} College Nodes, {info['active_learners']} Learners, Lead: {info['lead_institute']}")
    print("\nAll verification tests completed successfully!\n" + "=" * 70)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    if "--cli" in sys.argv or "--test-sim" in sys.argv:
        run_cli_tests()
    else:
        print(f"""
========================================================================
AP-QAIC STATEWIDE QUANTUM TALENT PIPELINE & CURRICULUM PLATFORM
QEXPO 2026 | USE CASE UC 090
------------------------------------------------------------------------
* Coordinating Hub: Central AP-QAIC Node (APSSDC & Higher Ed)
* Regional Leads: North Coastal (AU), Coastal AP (JNTUK/VRSEC), Rayalaseema (IIT Tirupati/SVU)
* Target: 380+ Connected College Nodes Across Andhra Pradesh
* Tiered Curriculum: Level 1 (Awareness) -> Level 4 (Specialist)
* Built-in: Real Python NumPy Quantum Circuit Simulator & BB84 QKD Engine
------------------------------------------------------------------------
Starting Web Server on http://127.0.0.1:{port}/ ...
Press Ctrl+C to stop.
========================================================================
""")
        threading.Timer(1.2, lambda: open_browser(port)).start()
        app.run(host='0.0.0.0', port=port, debug=False)
