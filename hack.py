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

def to_qasm(num_qubits, instructions):
    """Generate standard OpenQASM 2.0 representation."""
    lines = [
        'OPENQASM 2.0;',
        'include "qelib1.inc";',
        f'qreg q[{num_qubits}];',
        f'creg c[{num_qubits}];',
        ''
    ]
    for instr in instructions:
        g = instr.get('gate', '').lower()
        t = instr.get('target', 0)
        c = instr.get('control', 0)
        c1 = instr.get('control1', c)
        c2 = instr.get('control2', 1)
        q1 = instr.get('qubit1', c)
        q2 = instr.get('qubit2', t)
        p = float(instr.get('param', 0.0))
        if g in ('h', 'x', 'y', 'z', 's', 't'):
            lines.append(f'{g} q[{t}];')
        elif g == 'sdg':
            lines.append(f'sdg q[{t}];')
        elif g == 'tdg':
            lines.append(f'tdg q[{t}];')
        elif g == 'sx':
            lines.append(f'sx q[{t}];')
        elif g in ('rx', 'ry', 'rz'):
            lines.append(f'{g}({p:.4f}) q[{t}];')
        elif g in ('cnot', 'cx'):
            lines.append(f'cx q[{c}],q[{t}];')
        elif g == 'cz':
            lines.append(f'cz q[{c}],q[{t}];')
        elif g == 'ch':
            lines.append(f'ch q[{c}],q[{t}];')
        elif g == 'swap':
            lines.append(f'swap q[{q1}],q[{q2}];')
        elif g in ('toffoli', 'ccx', 'ccnot'):
            lines.append(f'ccx q[{c1}],q[{c2}],q[{t}];')
    lines.append('measure q -> c;')
    return '\n'.join(lines)

def to_qiskit(num_qubits, instructions):
    """Generate executable Python script using IBM Qiskit SDK."""
    lines = [
        'from qiskit import QuantumCircuit, Aer, execute',
        'import numpy as np',
        '',
        f'# Initialize Quantum Register with {num_qubits} qubits',
        f'qc = QuantumCircuit({num_qubits}, {num_qubits})',
        ''
    ]
    for instr in instructions:
        g = instr.get('gate', '').upper()
        t = instr.get('target', 0)
        c = instr.get('control', 0)
        c1 = instr.get('control1', c)
        c2 = instr.get('control2', 1)
        q1 = instr.get('qubit1', c)
        q2 = instr.get('qubit2', t)
        p = float(instr.get('param', 0.0))
        if g == 'H':
            lines.append(f'qc.h({t})')
        elif g == 'X':
            lines.append(f'qc.x({t})')
        elif g == 'Y':
            lines.append(f'qc.y({t})')
        elif g == 'Z':
            lines.append(f'qc.z({t})')
        elif g == 'S':
            lines.append(f'qc.s({t})')
        elif g == 'SDG':
            lines.append(f'qc.sdg({t})')
        elif g == 'T':
            lines.append(f'qc.t({t})')
        elif g == 'TDG':
            lines.append(f'qc.tdg({t})')
        elif g == 'SX':
            lines.append(f'qc.sx({t})')
        elif g in ('RX', 'RY', 'RZ'):
            lines.append(f'qc.{g.lower()}({p:.4f}, {t})')
        elif g in ('CNOT', 'CX'):
            lines.append(f'qc.cx({c}, {t})')
        elif g == 'CZ':
            lines.append(f'qc.cz({c}, {t})')
        elif g == 'CH':
            lines.append(f'qc.ch({c}, {t})')
        elif g == 'SWAP':
            lines.append(f'qc.swap({q1}, {q2})')
        elif g in ('TOFFOLI', 'CCX', 'CCNOT'):
            lines.append(f'qc.ccx({c1}, {c2}, {t})')

    lines.append('')
    lines.append(f'qc.measure(range({num_qubits}), range({num_qubits}))')
    lines.append('print("Circuit Diagram:\\n", qc.draw(output="text"))')
    lines.append('')
    lines.append('# Execute on Local Qasm Simulator')
    lines.append('backend = Aer.get_backend("qasm_simulator")')
    lines.append('job = execute(qc, backend, shots=1024)')
    lines.append('counts = job.result().get_counts()')
    lines.append('print("Measurement Counts (1024 shots):", counts)')
    return '\n'.join(lines)

class QuantumSimulator:
    """
    High-Performance, exact Statevector & Density Matrix Quantum Simulator.
    Supports 1 to 5 qubits, single-qubit unitaries, rotations, CNOT/CZ/CH/SWAP/Toffoli,
    intermediate step execution, von Neumann entanglement entropy, and Bloch vectors.
    """
    GATES = {
        'I': np.array([[1, 0], [0, 1]], dtype=complex),
        'X': np.array([[0, 1], [1, 0]], dtype=complex),
        'Y': np.array([[0, -1j], [1j, 0]], dtype=complex),
        'Z': np.array([[1, 0], [0, -1]], dtype=complex),
        'H': np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2),
        'S': np.array([[1, 0], [0, 1j]], dtype=complex),
        'SDG': np.array([[1, 0], [0, -1j]], dtype=complex),
        'T': np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex),
        'TDG': np.array([[1, 0], [0, np.exp(-1j * np.pi / 4)]], dtype=complex),
        'SX': np.array([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]], dtype=complex) / 2.0,  # sqrt(X)
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

    @staticmethod
    def p_gate(theta):
        return np.array([
            [1, 0],
            [0, np.exp(1j * theta)]
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

    def apply_ch(self, control, target):
        if control == target or not (0 <= control < self.num_qubits and 0 <= target < self.num_qubits):
            return
        new_state = self.state.copy()
        ctrl_mask = 1 << (self.num_qubits - 1 - control)
        targ_mask = 1 << (self.num_qubits - 1 - target)
        inv_sqrt2 = 1.0 / np.sqrt(2.0)
        for i in range(self.dim):
            if (i & ctrl_mask) != 0 and (i & targ_mask) == 0:
                i0 = i
                i1 = i | targ_mask
                a0 = self.state[i0]
                a1 = self.state[i1]
                new_state[i0] = inv_sqrt2 * (a0 + a1)
                new_state[i1] = inv_sqrt2 * (a0 - a1)
        self.state = new_state

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

    def apply_toffoli(self, c1, c2, target):
        if len({c1, c2, target}) != 3 or not all(0 <= q < self.num_qubits for q in (c1, c2, target)):
            return
        c1_mask = 1 << (self.num_qubits - 1 - c1)
        c2_mask = 1 << (self.num_qubits - 1 - c2)
        targ_mask = 1 << (self.num_qubits - 1 - target)
        new_state = self.state.copy()
        for i in range(self.dim):
            if (i & c1_mask) != 0 and (i & c2_mask) != 0:
                flipped = i ^ targ_mask
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
        if shots <= 0:
            for i in range(self.dim):
                bitstr = format(i, f'0{self.num_qubits}b')
                counts[bitstr] = round(float(probs[i]) * 100, 2)
            return counts
        samples = np.random.choice(self.dim, size=shots, p=probs)
        for idx in samples:
            bitstr = format(idx, f'0{self.num_qubits}b')
            counts[bitstr] = counts.get(bitstr, 0) + 1
        for i in range(self.dim):
            bitstr = format(i, f'0{self.num_qubits}b')
            if bitstr not in counts:
                counts[bitstr] = 0
        return counts

    def get_bloch_coordinates(self, qubit):
        """Compute reduced density matrix, Bloch vector (x,y,z), purity and von Neumann entanglement entropy."""
        m = 1 << (self.num_qubits - 1 - qubit)
        rho = np.zeros((2, 2), dtype=complex)
        for i in range(self.dim):
            b_i = 1 if (i & m) else 0
            for j in range(self.dim):
                b_j = 1 if (j & m) else 0
                if (i & ~m) == (j & ~m):
                    rho[b_i, b_j] += self.state[i] * np.conj(self.state[j])

        # Pauli expectation values
        X = self.GATES['X']
        Y = self.GATES['Y']
        Z = self.GATES['Z']
        x = float(np.real(np.trace(rho @ X)))
        y = float(np.real(np.trace(rho @ Y)))
        z = float(np.real(np.trace(rho @ Z)))

        r = math.sqrt(x*x + y*y + z*z)
        theta = math.acos(max(-1.0, min(1.0, z / r))) if r > 1e-7 else 0.0
        phi = math.atan2(y, x) if (x*x + y*y) > 1e-7 else 0.0

        purity = float(np.real(np.trace(rho @ rho)))

        # von Neumann Entanglement Entropy S(rho) = -Tr(rho log2 rho)
        eigvals = np.linalg.eigvalsh(rho)
        entropy = 0.0
        for lam in eigvals:
            if lam > 1e-12:
                entropy -= float(lam * np.log2(lam))

        return {
            "x": round(x, 4),
            "y": round(y, 4),
            "z": round(z, 4),
            "theta_deg": round(math.degrees(theta), 2),
            "phi_deg": round(math.degrees(phi) % 360, 2),
            "purity": round(min(1.0, max(0.5, purity)), 4),
            "entropy": round(max(0.0, min(1.0, entropy)), 4)
        }

    def get_state_snapshot(self):
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
                "mag": round(float(mag), 4),
                "prob": round(float(probs[i]), 4),
                "phase_deg": round(math.degrees(phase) % 360, 1)
            })
        bloch_vectors = [self.get_bloch_coordinates(q) for q in range(self.num_qubits)]
        return state_list, bloch_vectors

    def execute_circuit(self, instructions, shots=1024):
        self.reset()
        steps = []
        initial_states, initial_bloch = self.get_state_snapshot()
        steps.append({
            "step": 0,
            "gate_label": "Initial |00...0⟩",
            "states": initial_states,
            "bloch": initial_bloch
        })

        for idx, instr in enumerate(instructions):
            g = instr.get('gate', '').upper()
            t = instr.get('target', 0)
            c = instr.get('control', 0)
            c1 = instr.get('control1', c)
            c2 = instr.get('control2', 1)
            q1 = instr.get('qubit1', c)
            q2 = instr.get('qubit2', t)
            angle = float(instr.get('param', 0.0))

            if g in self.GATES:
                self.apply_single_gate(t, self.GATES[g])
            elif g == 'RX':
                self.apply_single_gate(t, self.rx(angle))
            elif g == 'RY':
                self.apply_single_gate(t, self.ry(angle))
            elif g == 'RZ':
                self.apply_single_gate(t, self.rz(angle))
            elif g in ('P', 'PHASE'):
                self.apply_single_gate(t, self.p_gate(angle))
            elif g in ('CNOT', 'CX'):
                self.apply_cnot(c, t)
            elif g == 'CZ':
                self.apply_cz(c, t)
            elif g == 'CH':
                self.apply_ch(c, t)
            elif g == 'SWAP':
                self.apply_swap(q1, q2)
            elif g in ('TOFFOLI', 'CCX', 'CCNOT'):
                self.apply_toffoli(c1, c2, t)

            step_states, step_bloch = self.get_state_snapshot()
            steps.append({
                "step": idx + 1,
                "gate_label": f"{g} on q[{t}]" if g not in ('CNOT', 'CX', 'CZ', 'CH', 'SWAP', 'TOFFOLI', 'CCX', 'CCNOT') else f"{g}",
                "states": step_states,
                "bloch": step_bloch
            })

        final_states, final_bloch = self.get_state_snapshot()
        sampled_shots = self.sample_shots(shots=shots)
        qasm_code = to_qasm(self.num_qubits, instructions)
        qiskit_code = to_qiskit(self.num_qubits, instructions)

        return {
            "num_qubits": self.num_qubits,
            "states": final_states,
            "bloch": final_bloch,
            "shots": sampled_shots,
            "steps": steps,
            "qasm": qasm_code,
            "qasm_code": qasm_code,
            "qiskit": qiskit_code,
            "qiskit_code": qiskit_code
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
    {"id": "AP-NODE-002", "name": "IIT Tirupati Quantum Research Hub", "district": "Tirupati", "region": "Rayalaseema", "tier": "Level 4 (Specialist Hub)", "students": 480, "faculty": 10, "readiness": "100%", "active_lab": "NQM Superconducting & Photonic Quantum Testbed"},
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
        "aicte_nqm_alignment": "National Quantum Mission (NQM) Pillar 4: Human Resource Development (Awareness Track)",
        "visual_summary": "Transforming classical binary thinking into multi-dimensional quantum superposition on the 3D Bloch sphere.",
        "key_formula": "|ψ⟩ = α|0⟩ + β|1⟩  where  |α|² + |β|² = 1",
        "theme_color": "cyan",
        "milestones": [
            {
                "step": "01",
                "title": "Bit vs. Qubit State Space",
                "icon": "binary",
                "desc": "Classical discrete switch [0 or 1] vs continuous surface of the Bloch Sphere with infinite superposition states.",
                "highlight": "2-state Hilbert Space ℂ²"
            },
            {
                "step": "02",
                "title": "Superposition & Born Rule",
                "icon": "sparkles",
                "desc": "Spinning coin analogy: while spinning it exists in superposition; observation forces collapse into 0 or 1 with probability |α|² or |β|².",
                "highlight": "P(0) = |α|², P(1) = |β|²"
            },
            {
                "step": "03",
                "title": "Quantum Entanglement",
                "icon": "git-merge",
                "desc": "Non-local correlation: Bell state (|00⟩ + |11⟩)/√2 links twin qubits so measuring one instantly determines the other across any distance.",
                "highlight": "EPR Pair: (|00⟩ + |11⟩)/√2"
            },
            {
                "step": "04",
                "title": "Quantum Career Tracks",
                "icon": "compass",
                "desc": "Career pathways into Quantum Software Engineer, Quantum Cryptographer, Post-Quantum Analyst, and QML Research across AP tech parks.",
                "highlight": "49,850+ Enrolled Statewide"
            }
        ]
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
        "aicte_nqm_alignment": "AICTE Emerging Technology Model Curriculum: Quantum Computing Foundations (ET-QC-201)",
        "visual_summary": "Linear algebra foundations, unitary transformation matrices, and tensor-product multi-qubit entangling circuits.",
        "key_formula": "H|0⟩ = (|0⟩+|1⟩)/√2,  CNOT|10⟩ = |11⟩,  |Φ⁺⟩ = (|00⟩+|11⟩)/√2",
        "theme_color": "blue",
        "milestones": [
            {
                "step": "01",
                "title": "Dirac Bra-Ket & Hilbert Space",
                "icon": "hash",
                "desc": "Statevectors |ψ⟩, dual bras ⟨ψ|, inner product overlap ⟨ψ|φ⟩, and complex vector spaces in 2ⁿ dimensions.",
                "highlight": "Dimension = 2ⁿ States"
            },
            {
                "step": "02",
                "title": "Unitary Gate Matrices",
                "icon": "cpu",
                "desc": "Single-qubit unitaries: Pauli X (bit-flip), Pauli Z (phase-flip), Hadamard H (superposition creator), and S/T phase rotators.",
                "highlight": "U†U = I (Reversible Logic)"
            },
            {
                "step": "03",
                "title": "Tensor Products & CNOT",
                "icon": "layers",
                "desc": "Composing multi-qubit states |q0⟩ ⊗ |q1⟩ and constructing entangling gates like CNOT, CZ, and SWAP with reversible matrix logic.",
                "highlight": "CNOT Control-Target Logic"
            },
            {
                "step": "04",
                "title": "Bell State & GHZ Synthesis",
                "icon": "network",
                "desc": "Synthesizing EPR pairs and 3-qubit GHZ (|000⟩ + |111⟩)/√2 states, verifying 100% correlation on 1,024 shot measurements.",
                "highlight": "100% Correlated Measurements"
            }
        ]
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
            "Quantum Teleportation Protocol & Entanglement Swapping",
            "Parameterized Quantum Circuits (PQC) & Variational Quantum Eigensolver (VQE)",
            "Quantum Machine Learning: Quantum Support Vector Machines (QSVM) & Variational Classifiers",
            "Quantum Error Mitigation and Noise Models"
        ],
        "practical_lab": "Simulate Grover's 4-Item Search, Quantum Teleportation Protocol, and 2-Qubit Variational Classifier",
        "aicte_nqm_alignment": "AICTE Specialized Elective / APSSDC Master Trainer Certification Track",
        "visual_summary": "Quantum oracle algorithms, state teleportation protocols, and variational quantum machine learning.",
        "key_formula": "Grover Speedup: O(√N) vs Classical O(N) | Teleportation Fidelity = 1.0",
        "theme_color": "emerald",
        "milestones": [
            {
                "step": "01",
                "title": "Grover's Search Algorithm",
                "icon": "search",
                "desc": "Quadratic speedup: Oracle phase inversion combined with diffusion amplitude reflection amplifies target state to ~100%.",
                "highlight": "O(√N) Oracle Queries"
            },
            {
                "step": "02",
                "title": "Quantum Teleportation",
                "icon": "send",
                "desc": "Using shared Bell-state entanglement and classical bits to teleport an unknown quantum state |ψ⟩ with 100% fidelity.",
                "highlight": "State Teleportation via EPR Pair"
            },
            {
                "step": "03",
                "title": "Variational Circuits (VQE/VQC)",
                "icon": "workflow",
                "desc": "Hybrid quantum-classical optimization: classical optimizer tunes parameterized quantum gates U(θ) for classification and molecular energy.",
                "highlight": "min_θ ⟨ψ(θ)|H|ψ(θ)⟩"
            },
            {
                "step": "04",
                "title": "Quantum Support Vector Machines",
                "icon": "brain",
                "desc": "Mapping non-linearly separable data into exponential Hilbert space via quantum feature maps for maximum-margin classification.",
                "highlight": "Quantum Kernel Embedding"
            }
        ]
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
        "aicte_nqm_alignment": "National Quantum Mission Research Grant & APSSDC Quantum Co-op Placement",
        "visual_summary": "Solving critical Andhra Pradesh infrastructure challenges: maritime logistics, power grid dispatch, drug discovery & post-quantum security.",
        "key_formula": "QAOA: min_z ∑ C_ij z_i z_j | PQC: CRYSTALS-Kyber (ML-KEM)",
        "theme_color": "purple",
        "milestones": [
            {
                "step": "01",
                "title": "Visakhapatnam Port QAOA",
                "icon": "anchor",
                "desc": "Container berth scheduling & crane dispatch mapped to Quadratic Unconstrained Binary Optimization (QUBO) on quantum circuits.",
                "highlight": "NP-Hard Maritime Logistics"
            },
            {
                "step": "02",
                "title": "Statewide PQC Transition",
                "icon": "lock",
                "desc": "Transitioning AP state digital infrastructure to NIST-standardized lattice-based cryptography (Kyber & Dilithium) resistant to Shor's algorithm.",
                "highlight": "NIST FIPS 203 / 204 Lattice"
            },
            {
                "step": "03",
                "title": "Pharma Molecular VQE",
                "icon": "flask-conical",
                "desc": "Simulating molecular orbital ground-state energy for novel drug candidate synthesis in collaboration with AP pharma clusters.",
                "highlight": "Electronic Hamiltonian Ground State"
            },
            {
                "step": "04",
                "title": "Hardware QPU & TCS Co-Op",
                "icon": "cloud-lightning",
                "desc": "Deploying production circuits to IBM Quantum, AWS Braket, and C-DAC Param Q-Sim with paid internships at TCS, C-DAC, and APSSDC.",
                "highlight": "Real QPU Deployment + TCS Co-Op"
            }
        ]
    }
]

DIAGNOSTIC_ASSESSMENT_QUESTIONS = [
    {
        "id": 1,
        "category": "Superposition & Principles",
        "difficulty": "Foundational",
        "question": "A single qubit is prepared in the state |ψ⟩ = (√3/2)|0⟩ - (1/2)|1⟩. According to the Born Rule, what is the probability of measuring the outcome |1⟩?",
        "options": [
            "25% (Probability = |-1/2|² = 1/4)",
            "75% (Probability = |√3/2|² = 3/4)",
            "50% (Equal probability)",
            "100% (Deterministic measurement)"
        ],
        "correct": 0,
        "explanation": "According to the Born rule, the probability of measuring basis state |1⟩ is the squared magnitude of its complex amplitude: P(|1⟩) = |-1/2|² = 1/4 = 25%.",
        "topic": "Level 1: Qubit Superposition & Born Rule Probability",
        "recommended_level_idx": 0,
        "recommended_preset": "bell_phi_plus",
        "action_label": "Explore Superposition in Level 1 Visualizer"
    },
    {
        "id": 2,
        "category": "Unitary Gates & Matrices",
        "difficulty": "Foundational",
        "question": "Why must all closed quantum circuit operations be represented by Unitary matrices U satisfying U†U = I?",
        "options": [
            "To preserve the total probability norm (⟨ψ|ψ⟩ = 1) and guarantee reversible computation",
            "To eliminate physical thermal decoherence in quantum registers",
            "Because non-unitary matrices cannot be diagonalized classically",
            "To force instantaneous wavefunction collapse after each gate execution"
        ],
        "correct": 0,
        "explanation": "Unitary operators preserve the L2-norm of statevectors (preserving total probability = 1). Since U† = U⁻¹, all quantum gates are inherently reversible without information loss.",
        "topic": "Level 2: Unitary Gate Matrices & Reversible Logic",
        "recommended_level_idx": 1,
        "recommended_preset": "bell_phi_plus",
        "action_label": "Review Unitary Matrices in Level 2 Visualizer"
    },
    {
        "id": 3,
        "category": "Unitary Gates & Matrices",
        "difficulty": "Foundational",
        "question": "Applying a Hadamard gate (H) to the basis state |1⟩ produces which quantum state?",
        "options": [
            "|-⟩ = (|0⟩ - |1⟩)/√2 (Equal superposition with π relative phase)",
            "|+⟩ = (|0⟩ + |1⟩)/√2 (Equal superposition with 0 relative phase)",
            "|0⟩ (Deterministic quantum NOT bit-flip)",
            "i|1⟩ (Pure imaginary phase shift)"
        ],
        "correct": 0,
        "explanation": "The Hadamard gate creates an equal superposition: H|0⟩ = (|0⟩ + |1⟩)/√2 = |+⟩, and H|1⟩ = (|0⟩ - |1⟩)/√2 = |-⟩.",
        "topic": "Level 2: Hadamard Gate & Superposition States",
        "recommended_level_idx": 1,
        "recommended_preset": "bell_phi_plus",
        "action_label": "Inspect Gate H in Quantum Lab Simulator"
    },
    {
        "id": 4,
        "category": "Unitary Gates & Matrices",
        "difficulty": "Intermediate",
        "question": "What is the exact algebraic relationship between the Phase gate S, the T gate, and the Pauli-Z gate?",
        "options": [
            "S = T² and Z = S² = T⁴, where T adds π/4 phase and S adds π/2 phase",
            "S = Z² and T = S² (Inverse phase scaling)",
            "T is the Hermitian conjugate of Pauli-X bit flip",
            "S and T gates are non-unitary approximations of Pauli-Y"
        ],
        "correct": 0,
        "explanation": "T = diag(1, e^(iπ/4)). Squaring T yields S = diag(1, e^(iπ/2)) = diag(1, i). Squaring S yields Pauli-Z = diag(1, -1). Hence S = T² and Z = S² = T⁴.",
        "topic": "Level 2: S, T, and Continuous Rotation Gates (RX, RY, RZ)",
        "recommended_level_idx": 1,
        "recommended_preset": "bell_psi_minus",
        "action_label": "Test S & T Gates in Quantum Lab Simulator"
    },
    {
        "id": 5,
        "category": "Multi-Qubit Entanglement",
        "difficulty": "Foundational",
        "question": "How many complex probability amplitudes are required to represent the pure statevector of an n-qubit quantum register?",
        "options": [
            "2^n amplitudes, illustrating the exponential dimension of composite Hilbert space",
            "2n amplitudes, scaling linearly with register qubit count",
            "n² amplitudes, scaling quadratically with register qubit count",
            "n! amplitudes, scaling factorially with qubit interactions"
        ],
        "correct": 0,
        "explanation": "The state space of n qubits is the tensor product of n two-dimensional Hilbert spaces: (C²)⊗ⁿ = C^(2ⁿ), requiring 2ⁿ complex amplitudes.",
        "topic": "Level 2: Tensor Products & Multi-Qubit Hilbert Space",
        "recommended_level_idx": 1,
        "recommended_preset": "ghz",
        "action_label": "Explore Multi-Qubit Registers in Simulator"
    },
    {
        "id": 6,
        "category": "Multi-Qubit Entanglement",
        "difficulty": "Intermediate",
        "question": "Which two-gate circuit sequence transforms two unentangled qubits |00⟩ into the maximally entangled Bell pair |Φ+⟩ = (|00⟩ + |11⟩)/√2?",
        "options": [
            "Hadamard on q[0], followed by CNOT with control q[0] and target q[1]",
            "Pauli-X on q[0], followed by Hadamard on q[1]",
            "CNOT with control q[0] and target q[1], followed by Hadamard on q[0]",
            "Hadamard on both q[0] and q[1] simultaneously"
        ],
        "correct": 0,
        "explanation": "Starting at |00⟩: H on q[0] yields (|00⟩ + |10⟩)/√2. Then CNOT(0,1) flips q[1] when q[0] is 1, yielding (|00⟩ + |11⟩)/√2, the canonical Bell state |Φ+⟩.",
        "topic": "Level 2: Bell State Synthesis & CNOT Entanglement",
        "recommended_level_idx": 1,
        "recommended_preset": "bell_phi_plus",
        "action_label": "Load Bell State Preset in Lab Simulator"
    },
    {
        "id": 7,
        "category": "Measurement & Entropy",
        "difficulty": "Advanced",
        "question": "For a bipartite maximally entangled Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2, what are the density matrix purity Tr(ρ_A²) and von Neumann entropy S(ρ_A) of the single-qubit subsystem A?",
        "options": [
            "Purity = 0.5 (completely mixed subsystem) and S(ρ_A) = 1.0 bit (maximum entanglement)",
            "Purity = 1.0 (pure state) and S(ρ_A) = 0.0 bits (separable subsystem)",
            "Purity = 0.0 and S(ρ_A) = undefined (divergent entropy)",
            "Purity = 0.25 and S(ρ_A) = 2.0 bits (quad-state mixture)"
        ],
        "correct": 0,
        "explanation": "Tracing out qubit B yields reduced density matrix ρ_A = I/2 = [[0.5, 0], [0, 0.5]]. Its purity is Tr(ρ_A²) = 0.25 + 0.25 = 0.5. Its von Neumann entropy is S(ρ_A) = -Tr(ρ log2 ρ) = 1.0 bit, proving maximal bipartite entanglement.",
        "topic": "Level 2 & 3: Reduced Density Matrices & von Neumann Entropy",
        "recommended_level_idx": 1,
        "recommended_preset": "bell_phi_plus",
        "action_label": "Inspect 3D Bloch & S(ρ) in Simulator"
    },
    {
        "id": 8,
        "category": "Superposition & Principles",
        "difficulty": "Intermediate",
        "question": "What fundamental principle of quantum mechanics states that an arbitrary unknown quantum state |ψ⟩ cannot be cloned into two identical copies?",
        "options": [
            "The No-Cloning Theorem (Wootters, Zurek & Dieks, 1982)",
            "Bell's Non-Locality Theorem",
            "Heisenberg's Uncertainty Principle",
            "The Quantum Adiabatic Theorem"
        ],
        "correct": 0,
        "explanation": "The linearity of quantum mechanics forbids any unitary operator U from satisfying U(|ψ⟩|0⟩) = |ψ⟩|ψ⟩ for all arbitrary states |ψ⟩. This protects quantum information from eavesdropping.",
        "topic": "Level 1 & 2: Quantum Principles & No-Cloning Theorem",
        "recommended_level_idx": 0,
        "recommended_preset": "teleportation",
        "action_label": "Review Quantum Principles in Level 1"
    },
    {
        "id": 9,
        "category": "Quantum Algorithms",
        "difficulty": "Intermediate",
        "question": "In the Quantum Teleportation protocol, what quantum and classical resources are required to transmit one unknown qubit state |ψ⟩ from Alice to Bob?",
        "options": [
            "1 pre-shared entangled Bell pair (EPR pair) and 2 classical bits transmitted via classical channel",
            "2 entangled Bell pairs and zero classical communication",
            "Instantaneous superluminal transmission without classical communication",
            "1 quantum repeater and 1 classical quantum state clone"
        ],
        "correct": 0,
        "explanation": "Quantum Teleportation requires 1 pre-shared Bell pair and 2 classical bits sent from Alice to Bob so Bob can apply the conditional Pauli recovery Z^(m0) X^(m1). No information travels faster than light.",
        "topic": "Level 3: Quantum Teleportation Protocol & Entanglement Channel",
        "recommended_level_idx": 2,
        "recommended_preset": "teleportation",
        "action_label": "Simulate Teleportation Protocol in Lab Sim"
    },
    {
        "id": 10,
        "category": "Quantum Algorithms",
        "difficulty": "Intermediate",
        "question": "What is the primary role of the Grover Diffusion Operator (2|s⟩⟨s| - I) in Grover's unstructured database search?",
        "options": [
            "Inversion about the mean amplitude, constructively amplifying the marked target state probability",
            "Measuring the qubits to collapse the wavefunction into the target state",
            "Adding constructive decoherence to suppress non-target states",
            "Inverting only the phase of the marked target state |11⟩"
        ],
        "correct": 0,
        "explanation": "The Oracle first flips the sign of the target state (phase inversion). The Grover Diffusion Operator then performs reflection about the mean amplitude, amplifying the target amplitude while suppressing non-target states.",
        "topic": "Level 3: Grover Search Algorithm & Amplitude Amplification",
        "recommended_level_idx": 2,
        "recommended_preset": "grover",
        "action_label": "Run Grover Search in Lab Sim"
    },
    {
        "id": 11,
        "category": "Quantum Algorithms",
        "difficulty": "Advanced",
        "question": "How many oracle queries does the Deutsch-Jozsa algorithm require to deterministically classify whether an n-bit Boolean function f(x) is constant or balanced?",
        "options": [
            "Exactly 1 quantum query, compared to 2^(n-1) + 1 classical queries in the worst case",
            "n quantum queries (linear in bit length)",
            "2^n quantum queries (exponential in bit length)",
            "√N quantum queries (quadratic speedup)"
        ],
        "correct": 0,
        "explanation": "Deutsch-Jozsa provides an exact, deterministic exponential speedup: a single quantum query evaluates if f(x) is constant or balanced using quantum interference, whereas a classical deterministic algorithm requires 2^(n-1) + 1 evaluations.",
        "topic": "Level 3: Deutsch-Jozsa & Quantum Oracle Complexity",
        "recommended_level_idx": 2,
        "recommended_preset": "deutsch",
        "action_label": "Run Deutsch-Jozsa Preset in Lab Sim"
    },
    {
        "id": 12,
        "category": "Complexity & Hardware",
        "difficulty": "Advanced",
        "question": "Which computational complexity class characterizes the set of decision problems solvable by a quantum computer in polynomial time with bounded error probability (≤ 1/3)?",
        "options": [
            "BQP (Bounded-error Quantum Polynomial-time)",
            "NP-Complete (Nondeterministic Polynomial Complete)",
            "PSPACE (Polynomial Space)",
            "BPP (Bounded-error Probabilistic Polynomial-time)"
        ],
        "correct": 0,
        "explanation": "BQP is the class of decision problems solvable by a polynomial-time quantum algorithm with bounded error probability. It contains P and BPP, and is widely believed to contain problems outside BPP (such as integer factorization via Shor's algorithm).",
        "topic": "Level 4: Quantum Complexity (BQP) & Real-World Algorithms",
        "recommended_level_idx": 3,
        "recommended_preset": "qft",
        "action_label": "Explore Level 4 Industry Applications"
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
    shots = int(data.get('shots', 1024))
    instructions = data.get('instructions', [])
    sim = QuantumSimulator(num_qubits=num_qubits)
    try:
        result = sim.execute_circuit(instructions, shots=shots)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/quiz', methods=['GET'])
def get_quiz():
    # Return questions with category & difficulty without disclosing answers
    sanitized = []
    for q in DIAGNOSTIC_ASSESSMENT_QUESTIONS:
        sanitized.append({
            "id": q["id"],
            "category": q["category"],
            "difficulty": q["difficulty"],
            "question": q["question"],
            "options": q["options"]
        })
    return jsonify({"questions": sanitized})

@app.route('/api/quiz/evaluate', methods=['POST'])
def evaluate_quiz():
    data = request.get_json() or {}
    user_answers = data.get('answers', {})
    student_name = data.get('name', 'Learner').strip() or 'Ajay Kumar'
    college_name = data.get('college', 'Andhra Pradesh College Node').strip() or 'AUCE Visakhapatnam'

    score = 0
    feedback = []
    category_stats = {}

    for q in DIAGNOSTIC_ASSESSMENT_QUESTIONS:
        cat = q["category"]
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "correct": 0, "missed": []}
        category_stats[cat]["total"] += 1

        qid_str = str(q["id"])
        chosen = user_answers.get(qid_str)
        is_correct = (chosen == q["correct"])
        if is_correct:
            score += 1
            category_stats[cat]["correct"] += 1
        else:
            category_stats[cat]["missed"].append(q)

        feedback.append({
            "id": q["id"],
            "category": q["category"],
            "difficulty": q["difficulty"],
            "question": q["question"],
            "your_answer": chosen,
            "your_answer_text": q["options"][chosen] if chosen is not None and 0 <= chosen < len(q["options"]) else "Not Answered",
            "correct_answer": q["correct"],
            "correct_answer_text": q["options"][q["correct"]],
            "is_correct": is_correct,
            "explanation": q["explanation"],
            "topic": q["topic"],
            "recommended_level_idx": q["recommended_level_idx"],
            "recommended_preset": q["recommended_preset"],
            "action_label": q["action_label"]
        })

    total_questions = len(DIAGNOSTIC_ASSESSMENT_QUESTIONS)
    percentage = round((score / total_questions) * 100, 1)

    if percentage >= 80.0:
        status = "QUALIFIED - LEVEL 4 SPECIALIST & INDUSTRY CAPSTONE"
    elif percentage >= 60.0:
        status = "QUALIFIED - LEVEL 3 ADVANCED QUANTUM TRACK"
    else:
        status = "ENABLING RECOMMENDED - LEVEL 1 & 2 FOUNDATIONS TRACK"

    # Compute granular competency percentages for radar chart and diagnostic review
    DIAGNOSTIC_CATEGORIES = [
        "Superposition & Principles",
        "Unitary Gates & Matrices",
        "Multi-Qubit Entanglement",
        "Measurement & Entropy",
        "Quantum Algorithms",
        "Complexity & Hardware"
    ]

    competencies = {}
    weak_topics = []

    diagnosis_notes = {
        "Superposition & Principles": "Reinforce the Born Rule (probabilities equal squared magnitudes of complex amplitudes) and the No-Cloning Theorem preventing arbitrary state duplication.",
        "Unitary Gates & Matrices": "Review linear algebraic representations of single-qubit unitaries (Hadamard H, Pauli-X/Z, and relative phase gates S and T).",
        "Multi-Qubit Entanglement": "Practice composite Hilbert space dimensions (2^n) and Bell state synthesis using the Hadamard + CNOT entangling gate sequence.",
        "Measurement & Entropy": "Deepen intuition on wavefunction collapse, subsystem mixed density matrices, and bipartite von Neumann entanglement entropy S(ρ).",
        "Quantum Algorithms": "Study constructive vs destructive interference in Grover's diffusion operator and single-query oracle evaluations in Deutsch-Jozsa.",
        "Complexity & Hardware": "Understand the BQP complexity boundary and how quantum computing differs fundamentally from classical probabilistic BPP."
    }

    for cat in DIAGNOSTIC_CATEGORIES:
        stats = category_stats.get(cat, {"total": 1, "correct": 0, "missed": []})
        pct = round((stats["correct"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0.0
        competencies[cat] = pct

        if pct < 75.0 or len(stats["missed"]) > 0:
            sample_missed = stats["missed"][0] if stats["missed"] else None
            severity = "Critical Review Required" if pct < 50.0 else "Targeted Practice Recommended"

            weak_topics.append({
                "category": cat,
                "score_percent": pct,
                "missed_count": len(stats["missed"]),
                "total_in_cat": stats["total"],
                "severity": severity,
                "diagnosis": diagnosis_notes.get(cat, "Review fundamental mathematical principles and circuit implementations."),
                "topic": sample_missed["topic"] if sample_missed else cat,
                "recommended_level_idx": sample_missed["recommended_level_idx"] if sample_missed else 1,
                "recommended_preset": sample_missed["recommended_preset"] if sample_missed else "bell_phi_plus",
                "action_label": sample_missed["action_label"] if sample_missed else "Launch Simulator Practice"
            })

    return jsonify({
        "student_name": student_name,
        "college_name": college_name,
        "score": score,
        "total": total_questions,
        "percentage": percentage,
        "status": status,
        "feedback": feedback,
        "competencies": competencies,
        "weak_topics": weak_topics
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
        <!-- TAB 3: UPGRADED QUANTUM LAB SIMULATION & CIRCUIT STUDIO -->
        <!-- =================================================================== -->
        <div id="tab-simulator" class="tab-content hidden space-y-6">
            <!-- Studio Header & Config -->
            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-xl flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                <div>
                    <div class="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-cyan-400">
                        <i data-lucide="cpu" class="w-4 h-4"></i>
                        <span>High-Performance Quantum Statevector & Circuit Studio</span>
                    </div>
                    <h2 class="text-2xl font-extrabold text-white mt-1">Interactive Quantum Lab Simulator</h2>
                    <p class="text-xs text-slate-400 mt-0.5">Multi-qubit circuit design, step-by-step statevector stepper, 3D Bloch sphere projections, and Qiskit code export.</p>
                </div>

                <!-- Configurations: Qubits & Shots -->
                <div class="flex flex-wrap items-center gap-3 text-xs">
                    <!-- Qubit Register Count -->
                    <div class="bg-slate-950 border border-slate-800 rounded-xl p-1.5 flex items-center space-x-1">
                        <span class="text-slate-400 font-medium px-2">Register:</span>
                        <button onclick="setNumQubits(1)" id="btn-qubit-1" class="px-2.5 py-1 rounded-lg text-xs font-bold text-slate-400 hover:text-white transition">1 Qubit</button>
                        <button onclick="setNumQubits(2)" id="btn-qubit-2" class="px-2.5 py-1 rounded-lg text-xs font-bold bg-cyan-500 text-slate-950 shadow transition">2 Qubits</button>
                        <button onclick="setNumQubits(3)" id="btn-qubit-3" class="px-2.5 py-1 rounded-lg text-xs font-bold text-slate-400 hover:text-white transition">3 Qubits</button>
                        <button onclick="setNumQubits(4)" id="btn-qubit-4" class="px-2.5 py-1 rounded-lg text-xs font-bold text-slate-400 hover:text-white transition">4 Qubits</button>
                    </div>

                    <!-- Shots Sampling -->
                    <div class="bg-slate-950 border border-slate-800 rounded-xl p-1.5 flex items-center space-x-1.5">
                        <span class="text-slate-400 font-medium px-1">Shots:</span>
                        <select id="sim-shots-select" onchange="updateSimShots()" class="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-2 py-1 focus:outline-none">
                            <option value="100">100 Shots</option>
                            <option value="512">512 Shots</option>
                            <option value="1024" selected>1,024 Shots</option>
                            <option value="4096">4,096 Shots</option>
                            <option value="0">Analytical (Exact Probs)</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- Presets Toolbar -->
            <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-3 flex flex-wrap items-center justify-between gap-2 text-xs">
                <div class="flex items-center space-x-2">
                    <span class="text-slate-400 font-bold uppercase tracking-wider text-[11px] flex items-center space-x-1">
                        <i data-lucide="bookmark" class="w-3.5 h-3.5 text-cyan-400"></i>
                        <span>Circuit Presets:</span>
                    </span>
                </div>
                <div class="flex flex-wrap items-center gap-1.5">
                    <button onclick="loadPreset('bell_phi_plus')" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 font-medium transition">Bell |Φ+⟩</button>
                    <button onclick="loadPreset('bell_psi_minus')" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-blue-300 border border-slate-700 font-medium transition">Singlet |Ψ-⟩</button>
                    <button onclick="loadPreset('ghz')" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-purple-300 border border-slate-700 font-medium transition">GHZ (3Q)</button>
                    <button onclick="loadPreset('w_state')" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-pink-300 border border-slate-700 font-medium transition">W-State (3Q)</button>
                    <button onclick="loadPreset('teleportation')" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-300 border border-slate-700 font-medium transition">Teleportation (3Q)</button>
                    <button onclick="loadPreset('grover')" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-300 border border-slate-700 font-medium transition">Grover (2Q)</button>
                    <button onclick="loadPreset('deutsch')" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-teal-300 border border-slate-700 font-medium transition">Deutsch-Jozsa (2Q)</button>
                    <button onclick="loadPreset('qft')" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-slate-700 font-medium transition">QFT (3Q)</button>
                    <button onclick="clearCircuit()" class="px-2.5 py-1 rounded-lg bg-rose-950/60 hover:bg-rose-900 text-rose-300 border border-rose-800 font-medium transition">Clear</button>
                </div>
            </div>

            <!-- Main Grid: Circuit Builder on Left (7 cols) + State Inspector on Right (5 cols) -->
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <!-- Left: Gate Toolbox & Circuit Schematic (7 cols) -->
                <div class="lg:col-span-7 space-y-5">
                    <!-- Gate Toolbox Box -->
                    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                            <span class="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-1.5">
                                <i data-lucide="wrench" class="w-4 h-4 text-cyan-400"></i>
                                <span>1. Gate Toolbox (Click Gate to Insert)</span>
                            </span>
                            <div class="flex items-center space-x-2 text-xs">
                                <span class="text-slate-400">Target Qubit:</span>
                                <select id="active-qubit-select" class="bg-slate-800 border border-slate-700 text-slate-100 text-xs rounded-lg px-2.5 py-1 focus:border-cyan-500">
                                    <option value="0">q[0]</option>
                                    <option value="1">q[1]</option>
                                </select>
                            </div>
                        </div>

                        <!-- Gate Groups Grid -->
                        <div class="space-y-3">
                            <!-- 1-Qubit Basic Gates -->
                            <div>
                                <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1.5">Superposition & Pauli Unitaries</span>
                                <div class="flex flex-wrap gap-2">
                                    <button onclick="addGate('H')" class="w-10 h-9 rounded-lg bg-blue-600 hover:bg-blue-500 font-bold text-xs text-white border border-blue-400 transition" title="Hadamard (Superposition)">H</button>
                                    <button onclick="addGate('X')" class="w-10 h-9 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-bold text-xs text-white border border-emerald-400 transition" title="Pauli-X (NOT)">X</button>
                                    <button onclick="addGate('SX')" class="w-10 h-9 rounded-lg bg-teal-600 hover:bg-teal-500 font-bold text-xs text-white border border-teal-400 transition" title="Sqrt(X)">√X</button>
                                    <button onclick="addGate('Y')" class="w-10 h-9 rounded-lg bg-amber-600 hover:bg-amber-500 font-bold text-xs text-white border border-amber-400 transition" title="Pauli-Y">Y</button>
                                    <button onclick="addGate('Z')" class="w-10 h-9 rounded-lg bg-rose-600 hover:bg-rose-500 font-bold text-xs text-white border border-rose-400 transition" title="Pauli-Z (Phase Flip)">Z</button>
                                    <button onclick="addGate('S')" class="w-10 h-9 rounded-lg bg-indigo-600 hover:bg-indigo-500 font-bold text-xs text-white border border-indigo-400 transition" title="Phase S (pi/2)">S</button>
                                    <button onclick="addGate('SDG')" class="w-10 h-9 rounded-lg bg-indigo-800 hover:bg-indigo-700 font-bold text-xs text-white border border-indigo-500 transition" title="S-Dagger (-pi/2)">S†</button>
                                    <button onclick="addGate('T')" class="w-10 h-9 rounded-lg bg-violet-600 hover:bg-violet-500 font-bold text-xs text-white border border-violet-400 transition" title="Phase T (pi/4)">T</button>
                                    <button onclick="addGate('TDG')" class="w-10 h-9 rounded-lg bg-violet-800 hover:bg-violet-700 font-bold text-xs text-white border border-violet-500 transition" title="T-Dagger (-pi/4)">T†</button>
                                </div>
                            </div>

                            <!-- Parameterized Continuous Rotations -->
                            <div>
                                <div class="flex items-center justify-between mb-1.5">
                                    <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Continuous Parameterized Rotations (Angle θ):</span>
                                    <div class="flex items-center space-x-1.5 text-xs">
                                        <span class="text-[10px] text-slate-400 font-mono">Angle:</span>
                                        <select id="param-rotation-angle" class="bg-slate-800 border border-slate-700 text-slate-200 text-[11px] rounded px-2 py-0.5">
                                            <option value="1.5707963">π/2 (90°)</option>
                                            <option value="3.14159265">π (180°)</option>
                                            <option value="0.785398">π/4 (45°)</option>
                                            <option value="4.712389">3π/2 (270°)</option>
                                            <option value="6.283185">2π (360°)</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="flex flex-wrap gap-2">
                                    <button onclick="addRotationGate('RX')" class="px-3 h-9 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 font-bold text-xs border border-cyan-500/40 transition">RX(θ)</button>
                                    <button onclick="addRotationGate('RY')" class="px-3 h-9 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-300 font-bold text-xs border border-emerald-500/40 transition">RY(θ)</button>
                                    <button onclick="addRotationGate('RZ')" class="px-3 h-9 rounded-lg bg-slate-800 hover:bg-slate-700 text-purple-300 font-bold text-xs border border-purple-500/40 transition">RZ(θ)</button>
                                </div>
                            </div>

                            <!-- Multi-Qubit Entangling Gates -->
                            <div>
                                <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1.5">Multi-Qubit Entangling Gates</span>
                                <div class="flex flex-wrap gap-2">
                                    <button onclick="promptCnot()" class="px-3 h-9 rounded-lg bg-cyan-700 hover:bg-cyan-600 font-bold text-xs text-white shadow border border-cyan-400 transition">+ CNOT (CX)</button>
                                    <button onclick="promptCz()" class="px-3 h-9 rounded-lg bg-teal-700 hover:bg-teal-600 font-bold text-xs text-white shadow border border-teal-400 transition">+ CZ</button>
                                    <button onclick="promptCh()" class="px-3 h-9 rounded-lg bg-blue-700 hover:bg-blue-600 font-bold text-xs text-white shadow border border-blue-400 transition">+ CH</button>
                                    <button onclick="promptSwap()" class="px-3 h-9 rounded-lg bg-amber-700 hover:bg-amber-600 font-bold text-xs text-white shadow border border-amber-400 transition">+ SWAP</button>
                                    <button onclick="promptToffoli()" class="px-3 h-9 rounded-lg bg-purple-700 hover:bg-purple-600 font-bold text-xs text-white shadow border border-purple-400 transition">+ Toffoli (CCNOT)</button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Visual Circuit Schematic Board -->
                    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                            <div>
                                <span class="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-1.5">
                                    <i data-lucide="layers" class="w-4 h-4 text-cyan-400"></i>
                                    <span>2. Circuit Wire Schematic (Click gate or [×] to remove)</span>
                                </span>
                                <p class="text-[11px] text-slate-400 mt-0.5">Interactive multi-wire timeline. Click wire headers to switch target; hover gates for instant deletion.</p>
                            </div>
                            <div class="flex items-center space-x-2 text-xs">
                                <span id="circuit-step-count" class="font-mono text-cyan-400 font-bold bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">0 Gates</span>
                                <button onclick="undoLastGate()" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 flex items-center space-x-1 transition">
                                    <i data-lucide="undo" class="w-3 h-3"></i><span>Undo</span>
                                </button>
                                <button onclick="clearCircuit()" class="px-2.5 py-1 rounded-lg bg-rose-950/60 hover:bg-rose-900 text-rose-300 text-xs border border-rose-800 flex items-center space-x-1 transition">
                                    <i data-lucide="trash-2" class="w-3 h-3"></i><span>Clear</span>
                                </button>
                            </div>
                        </div>

                        <!-- Direct 1Q & 2Q Quick Operations Bar (Zero Dialog Prompts) -->
                        <div class="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-2">
                            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-900 pb-2">
                                <div class="flex items-center space-x-1.5 text-xs">
                                    <i data-lucide="zap" class="w-3.5 h-3.5 text-amber-400"></i>
                                    <span class="font-bold text-white uppercase tracking-wider text-[11px]">Instant 1Q & 2Q Shortcuts (1-Click Placement)</span>
                                </div>
                                <div class="flex items-center space-x-2 text-xs">
                                    <span class="text-slate-400 text-[11px]">Selected Wire:</span>
                                    <span id="quick-target-badge" class="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 font-mono font-bold text-xs">q[0]</span>
                                    <span id="circuit-telemetry-badge" class="text-[10px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">Depth: 0</span>
                                </div>
                            </div>

                            <div class="flex flex-wrap items-center gap-2 text-xs">
                                <!-- 1-Qubit Quick Gates for active wire -->
                                <div class="flex items-center space-x-1">
                                    <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wider mr-1">1Q Gates:</span>
                                    <button onclick="addGateToActive('H')" class="px-2.5 py-1 rounded-lg bg-blue-600/30 hover:bg-blue-600 text-blue-200 border border-blue-500/50 font-bold transition" title="Add Hadamard H to active wire">+ H</button>
                                    <button onclick="addGateToActive('X')" class="px-2.5 py-1 rounded-lg bg-emerald-600/30 hover:bg-emerald-600 text-emerald-200 border border-emerald-500/50 font-bold transition" title="Add Pauli-X NOT to active wire">+ X</button>
                                    <button onclick="addGateToActive('Z')" class="px-2.5 py-1 rounded-lg bg-rose-600/30 hover:bg-rose-600 text-rose-200 border border-rose-500/50 font-bold transition" title="Add Pauli-Z Phase Flip to active wire">+ Z</button>
                                    <button onclick="addGateToActive('S')" class="px-2.5 py-1 rounded-lg bg-indigo-600/30 hover:bg-indigo-600 text-indigo-200 border border-indigo-500/50 font-bold transition" title="Add S Gate (pi/2) to active wire">+ S</button>
                                    <button onclick="addGateToActive('T')" class="px-2.5 py-1 rounded-lg bg-violet-600/30 hover:bg-violet-600 text-violet-200 border border-violet-500/50 font-bold transition" title="Add T Gate (pi/4) to active wire">+ T</button>
                                    <button onclick="addGateToActive('SX')" class="px-2.5 py-1 rounded-lg bg-teal-600/30 hover:bg-teal-600 text-teal-200 border border-teal-500/50 font-bold transition" title="Add Sqrt(X) to active wire">+ √X</button>
                                </div>

                                <span class="hidden sm:inline-block text-slate-700">|</span>

                                <!-- 2-Qubit Instant Entangling Gates -->
                                <div class="flex items-center space-x-1">
                                    <span class="text-[10px] text-cyan-400 font-bold uppercase tracking-wider mr-1">2Q Entanglers:</span>
                                    <button onclick="addQuick2QGate('CNOT', 0, 1)" class="px-2.5 py-1 rounded-lg bg-cyan-600/30 hover:bg-cyan-600 text-cyan-200 border border-cyan-500/50 font-bold transition" title="Instant CNOT: q[0] control -> q[1] target">+ CX(0→1)</button>
                                    <button onclick="addQuick2QGate('CNOT', 1, 0)" class="px-2.5 py-1 rounded-lg bg-blue-600/30 hover:bg-blue-600 text-blue-200 border border-blue-500/50 font-bold transition" title="Instant CNOT: q[1] control -> q[0] target">+ CX(1→0)</button>
                                    <button onclick="addQuick2QGate('CZ', 0, 1)" class="px-2.5 py-1 rounded-lg bg-teal-600/30 hover:bg-teal-600 text-teal-200 border border-teal-500/50 font-bold transition" title="Instant Controlled-Z between q[0] and q[1]">+ CZ(0,1)</button>
                                    <button onclick="addQuick2QGate('SWAP', 0, 1)" class="px-2.5 py-1 rounded-lg bg-amber-600/30 hover:bg-amber-600 text-amber-200 border border-amber-500/50 font-bold transition" title="Instant SWAP between q[0] and q[1]">+ SWAP(0,1)</button>
                                    <button onclick="quickAddBellPair()" class="px-2.5 py-1 rounded-lg bg-purple-600/40 hover:bg-purple-600 text-purple-200 border border-purple-500/50 font-bold transition" title="1-Click Bell State Synthesis: H(0) + CX(0->1)">+ Bell Pair</button>
                                </div>
                            </div>
                        </div>

                        <!-- Circuit Canvas & Interactive Wire Schematic -->
                        <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs overflow-x-auto min-h-[170px]" id="circuit-board">
                            <!-- Dynamically rendered timeline grid & clickable gate blocks -->
                        </div>

                        <!-- Execution & Stepper Bar -->
                        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
                            <div class="flex items-center space-x-2">
                                <button onclick="runSimulation()" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-extrabold text-sm flex items-center space-x-2 shadow-lg shadow-cyan-500/20 transition">
                                    <i data-lucide="play" class="w-4 h-4 fill-slate-950"></i>
                                    <span>Execute Circuit</span>
                                </button>

                                <!-- Step-by-Step Stepper -->
                                <button onclick="stepCircuit(-1)" class="px-3 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 flex items-center space-x-1 transition" title="Step Back">
                                    <i data-lucide="skip-back" class="w-3.5 h-3.5"></i>
                                    <span>Step Back</span>
                                </button>
                                <button onclick="stepCircuit(1)" class="px-3 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 flex items-center space-x-1 transition" title="Step Forward">
                                    <span>Step Forward</span>
                                    <i data-lucide="skip-forward" class="w-3.5 h-3.5"></i>
                                </button>
                            </div>

                            <div id="stepper-indicator" class="text-xs font-mono text-slate-400">
                                Current Step: <strong id="current-step-display" class="text-cyan-400">Full Execution</strong>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Right: Multimodal State Inspector, 3D Bloch Spheres, Histogram & QASM/Qiskit (5 cols) -->
                <div class="lg:col-span-5 space-y-5">
                    <!-- Inspection Tabs Navigation -->
                    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-4">
                        <div class="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
                            <button onclick="switchInspectorTab('states')" id="ins-tab-states" class="flex-1 py-1.5 rounded-lg font-bold text-cyan-400 bg-slate-800 transition">Amplitudes</button>
                            <button onclick="switchInspectorTab('bloch')" id="ins-tab-bloch" class="flex-1 py-1.5 rounded-lg font-bold text-slate-400 hover:text-slate-200 transition">3D Bloch & S(ρ)</button>
                            <button onclick="switchInspectorTab('histogram')" id="ins-tab-histogram" class="flex-1 py-1.5 rounded-lg font-bold text-slate-400 hover:text-slate-200 transition">Shots</button>
                            <button onclick="switchInspectorTab('code')" id="ins-tab-code" class="flex-1 py-1.5 rounded-lg font-bold text-slate-400 hover:text-slate-200 transition">Qiskit/QASM</button>
                        </div>

                        <!-- Tab 1: Statevector & Phase Wheels View -->
                        <div id="inspector-panel-states" class="space-y-3">
                            <div class="flex items-center justify-between text-xs font-mono text-slate-400 pb-1 border-b border-slate-800">
                                <span>Basis Ket</span>
                                <span>Amplitude (a + bi)</span>
                                <span>Prob & Phase</span>
                            </div>
                            <div id="statevector-list" class="space-y-1.5 text-xs font-mono max-h-[380px] overflow-y-auto pr-1">
                                <!-- Rendered with phase wheels -->
                            </div>
                        </div>

                        <!-- Tab 2: Visual 3D Bloch Spheres & Entanglement Metrics View -->
                        <div id="inspector-panel-bloch" class="hidden space-y-4">
                            <div class="flex items-center justify-between text-xs text-slate-400 pb-1 border-b border-slate-800">
                                <span class="font-bold text-slate-200">Single Qubit Bloch Projections:</span>
                                <span class="font-mono text-purple-400 text-[11px]">|ψ⟩ = cos(θ/2)|0⟩ + e^(iφ)sin(θ/2)|1⟩</span>
                            </div>
                            <div id="bloch-spheres-container" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                <!-- Visual SVG rendered Bloch spheres -->
                            </div>
                        </div>

                        <!-- Tab 3: Measurement Histogram View -->
                        <div id="inspector-panel-histogram" class="hidden space-y-3">
                            <div class="flex items-center justify-between text-xs text-slate-400 pb-1 border-b border-slate-800">
                                <span>Measurement Distribution</span>
                                <span id="hist-shot-count-label" class="font-mono text-cyan-400">1024 Shots</span>
                            </div>
                            <div class="h-64">
                                <canvas id="histogramChart"></canvas>
                            </div>
                        </div>

                        <!-- Tab 4: Qiskit & OpenQASM 2.0 Real-time Code Exporters -->
                        <div id="inspector-panel-code" class="hidden space-y-3 text-xs">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center space-x-2">
                                    <button onclick="switchCodeLang('qiskit')" id="btn-lang-qiskit" class="px-2.5 py-1 rounded bg-blue-950 text-blue-300 font-bold border border-blue-800">Qiskit Python</button>
                                    <button onclick="switchCodeLang('qasm')" id="btn-lang-qasm" class="px-2.5 py-1 rounded bg-slate-800 text-slate-400 font-bold border border-slate-700">OpenQASM 2.0</button>
                                </div>
                                <button onclick="copyCurrentCode()" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center space-x-1 transition">
                                    <i data-lucide="copy" class="w-3 h-3"></i><span>Copy</span>
                                </button>
                            </div>
                            <textarea id="code-export-box" readonly class="w-full h-72 bg-slate-950 border border-slate-800 rounded-xl p-3 font-mono text-[11px] text-cyan-300 focus:outline-none resize-none leading-relaxed"></textarea>
                        </div>
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

            <!-- Personalized Diagnostic & Weak Topics Remediation Hub -->
            <div id="assessment-results-panel" class="hidden bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 shadow-2xl">
                <!-- Dynamically populated upon evaluation with score breakdown, weak topic diagnosis, and question-by-question review -->
            </div>
        </div>

        <!-- Curriculum Visualizer Modal (Pop-out Immersive View) -->
        <div id="curriculum-visualizer-modal" class="fixed inset-0 z-50 hidden bg-slate-950/85 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
            <div class="relative w-full max-w-5xl bg-slate-900 border border-cyan-500/50 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6 max-h-[92vh] overflow-y-auto">
                <div class="flex items-center justify-between border-b border-slate-800 pb-4">
                    <div id="modal-visualizer-header">
                        <!-- Populated dynamically -->
                    </div>
                    <button onclick="closeVisualizerModal()" class="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition">
                        <i data-lucide="x" class="w-5 h-5"></i>
                    </button>
                </div>
                <div id="modal-visualizer-body" class="space-y-6">
                    <!-- Populated dynamically -->
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
        let currentStep = 0;
        let simResultCache = null;
        let currentShots = 1024;
        let activeCodeLang = 'qiskit';
        let histogramChartInstance = null;
        let radarChartInstance = null;

        // Initialize App
        document.addEventListener('DOMContentLoaded', () => {
            lucide.createIcons();
            loadCollegesTable();
            loadCurriculum();
            loadQuiz();
            initCharts();
            loadPreset('bell_phi_plus');
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

        // 2. Curriculum & Interactive Syllabus Visualizer
        let curriculumDataCache = [];

        async function loadCurriculum() {
            try {
                const res = await fetch('/api/curriculum');
                const data = await res.json();
                curriculumDataCache = data.curriculum;
                const container = document.getElementById('curriculum-container');
                container.innerHTML = '';

                data.curriculum.forEach((lvl, idx) => {
                    const card = document.createElement('div');
                    card.className = "p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition space-y-5 shadow-lg";
                    card.id = `curriculum-level-card-${idx}`;
                    
                    const themeColor = lvl.theme_color || 'cyan';

                    card.innerHTML = `
                        <!-- Level Header -->
                        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3.5">
                            <div class="flex items-center space-x-3">
                                <span class="w-9 h-9 rounded-xl bg-${themeColor}-950 text-${themeColor}-300 border border-${themeColor}-800/80 flex items-center justify-center font-extrabold text-sm font-mono shadow-inner">
                                    0${idx + 1}
                                </span>
                                <div>
                                    <div class="flex items-center space-x-2">
                                        <span class="text-xs font-bold uppercase text-${themeColor}-400 tracking-wider">${lvl.level} • ${lvl.badge}</span>
                                        <span class="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">${lvl.duration}</span>
                                    </div>
                                    <h3 class="text-lg font-extrabold text-white mt-0.5">${lvl.title}</h3>
                                </div>
                            </div>

                            <!-- Action Button to Trigger Visualizer -->
                            <div class="flex items-center space-x-2">
                                <button onclick="toggleSyllabusVisualizer(${idx})" class="px-3.5 py-1.5 rounded-xl bg-${themeColor}-500/10 hover:bg-${themeColor}-500/20 text-${themeColor}-300 border border-${themeColor}-500/40 text-xs font-bold flex items-center space-x-2 transition shadow-sm hover:scale-[1.02]">
                                    <i data-lucide="eye" class="w-4 h-4 text-${themeColor}-400"></i>
                                    <span id="vis-btn-text-${idx}">Tap to Visualize Syllabus Roadmap</span>
                                </button>
                            </div>
                        </div>

                        <!-- 2-Column Overview (Clickable Syllabus Box on Left) -->
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                            <!-- Left: Interactive Syllabus Box -->
                            <div onclick="toggleSyllabusVisualizer(${idx})" class="cursor-pointer group bg-slate-950/60 hover:bg-slate-950 p-4 rounded-xl border border-slate-800 hover:border-${themeColor}-500/50 transition-all duration-200 relative flex flex-col justify-between">
                                <div>
                                    <div class="flex items-center justify-between mb-2.5 pb-2 border-b border-slate-800/70">
                                        <span class="font-bold text-slate-200 uppercase tracking-wider text-xs flex items-center space-x-2">
                                            <i data-lucide="book-open" class="w-4 h-4 text-${themeColor}-400"></i>
                                            <span>Syllabus & Core Modules</span>
                                        </span>
                                        <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-${themeColor}-950 text-${themeColor}-300 border border-${themeColor}-800/80 flex items-center space-x-1 group-hover:bg-${themeColor}-900/60 transition">
                                            <i data-lucide="sparkles" class="w-3 h-3 text-${themeColor}-400"></i>
                                            <span>Tap to Visualize</span>
                                        </span>
                                    </div>
                                    <ul class="space-y-2 text-slate-300">
                                        ${lvl.topics.map((t, tIdx) => `
                                            <li class="flex items-center justify-between p-1.5 rounded-lg group-hover:bg-slate-900/80 hover:text-white transition">
                                                <div class="flex items-start space-x-2.5">
                                                    <span class="w-4 h-4 rounded-full bg-slate-800 text-[10px] font-mono flex items-center justify-center text-${themeColor}-400 mt-0.5 font-bold">${tIdx + 1}</span>
                                                    <span class="font-medium">${t}</span>
                                                </div>
                                                <i data-lucide="chevron-right" class="w-3.5 h-3.5 text-slate-600 group-hover:text-${themeColor}-400 transition ml-2"></i>
                                            </li>
                                        `).join('')}
                                    </ul>
                                </div>
                                <div class="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-${themeColor}-400/90 font-medium">
                                    <span class="flex items-center space-x-1.5">
                                        <i data-lucide="mouse-pointer-click" class="w-3.5 h-3.5 animate-bounce"></i>
                                        <span>Click anywhere on this syllabus to expand Visualizer Card</span>
                                    </span>
                                    <span class="font-mono text-[10px] text-slate-400">4 Stages • Concepts & Labs</span>
                                </div>
                            </div>

                            <!-- Right: Target, Practical Lab & Accreditation -->
                            <div class="space-y-3 bg-slate-950/40 p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
                                <div class="space-y-3">
                                    <div>
                                        <span class="font-bold text-blue-300 uppercase tracking-wider block mb-1">Practical Activity / Lab:</span>
                                        <p class="text-slate-300 leading-relaxed">${lvl.practical_lab}</p>
                                    </div>
                                    <div>
                                        <span class="font-bold text-purple-300 uppercase tracking-wider block mb-1">Target Learner Cohort:</span>
                                        <p class="text-slate-400 leading-relaxed">${lvl.target}</p>
                                    </div>
                                </div>
                                <div class="pt-2 border-t border-slate-800/80 text-[11px] text-emerald-400 flex items-center space-x-1.5">
                                    <i data-lucide="shield-check" class="w-4 h-4 text-emerald-400"></i>
                                    <span>${lvl.aicte_nqm_alignment}</span>
                                </div>
                            </div>
                        </div>

                        <!-- Expandable Visualize Card Container -->
                        <div id="syllabus-visualizer-${idx}" class="hidden mt-4 pt-4 border-t border-slate-800 transition-all duration-300">
                            ${renderVisualizerCardContent(lvl, idx, false)}
                        </div>
                    `;
                    container.appendChild(card);
                });
                lucide.createIcons();
            } catch (err) {
                console.error(err);
            }
        }

        function renderVisualizerCardContent(lvl, idx, isModal) {
            const themeColor = lvl.theme_color || 'cyan';
            const milestones = lvl.milestones || [];

            let interactiveDemoHTML = '';
            if (idx === 0) {
                // Level 1: Interactive Superposition & Born Rule Simulator
                interactiveDemoHTML = `
                    <div class="bg-slate-950/80 border border-cyan-900/60 rounded-xl p-4 space-y-3">
                        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-2">
                            <div class="flex items-center space-x-2">
                                <i data-lucide="play-circle" class="w-4 h-4 text-cyan-400"></i>
                                <span class="font-bold text-sm text-white">Interactive Concept Demo: Superposition & Wavefunction Collapse</span>
                            </div>
                            <span class="text-[11px] font-mono text-cyan-300 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800">Born's Rule Simulator</span>
                        </div>
                        
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 items-center">
                            <div class="md:col-span-2 space-y-2">
                                <div class="flex justify-between text-xs font-mono">
                                    <span class="text-cyan-400">State |0⟩ Probability: <strong id="demo-p0">50.0%</strong></span>
                                    <span class="text-purple-400">State |1⟩ Probability: <strong id="demo-p1">50.0%</strong></span>
                                </div>
                                <div class="w-full bg-slate-900 h-3 rounded-full overflow-hidden flex border border-slate-800">
                                    <div id="demo-bar-0" class="bg-gradient-to-r from-cyan-500 to-blue-500 h-full w-[50%] transition-all duration-500"></div>
                                    <div id="demo-bar-1" class="bg-gradient-to-r from-purple-500 to-pink-500 h-full w-[50%] transition-all duration-500"></div>
                                </div>
                                <div id="demo-status-text" class="text-xs text-slate-300 bg-slate-900/90 p-2.5 rounded-lg border border-slate-800 font-mono">
                                    State: |ψ⟩ = (|0⟩ + |1⟩)/√2 (Equal Superposition). Qubit exists as both simultaneously.
                                </div>
                            </div>
                            <div class="flex flex-col gap-2">
                                <button onclick="measureSuperpositionDemo()" class="px-3 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-extrabold text-xs flex items-center justify-center space-x-1.5 shadow transition">
                                    <i data-lucide="dices" class="w-3.5 h-3.5"></i>
                                    <span>Measure / Collapse Qubit</span>
                                </button>
                                <button onclick="resetSuperpositionDemo()" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs flex items-center justify-center space-x-1 border border-slate-700 transition">
                                    <i data-lucide="rotate-ccw" class="w-3 h-3"></i>
                                    <span>Restore Superposition</span>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            } else if (idx === 1) {
                // Level 2: Visual Quantum Circuit Schematic & Interactive Matrix Inspector
                interactiveDemoHTML = `
                    <div class="bg-slate-950/80 border border-blue-900/60 rounded-xl p-4 space-y-3">
                        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-2">
                            <div class="flex items-center space-x-2">
                                <i data-lucide="cpu" class="w-4 h-4 text-blue-400"></i>
                                <span class="font-bold text-sm text-white">Visual Circuit Schematic: Bell State EPR Pair Synthesis</span>
                            </div>
                            <span class="text-[11px] font-mono text-blue-300 bg-blue-950/80 px-2 py-0.5 rounded border border-blue-800">Hadamard + CNOT Circuit</span>
                        </div>

                        <!-- Circuit Wire Schematic -->
                        <div class="p-3 bg-slate-900/90 rounded-lg border border-slate-800 space-y-2 font-mono text-xs">
                            <div class="flex items-center space-x-2">
                                <span class="text-cyan-400 font-bold w-14">q[0] |0⟩ ─</span>
                                <span class="px-2 py-1 bg-blue-600 text-white rounded font-bold">H</span>
                                <span class="text-slate-500">───────</span>
                                <span class="px-2 py-1 bg-cyan-700 text-cyan-200 rounded font-bold">● (Control)</span>
                                <span class="text-slate-500">───────</span>
                                <span class="text-emerald-400 font-bold">|Φ⁺⟩ = (|00⟩ + |11⟩)/√2</span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <span class="text-purple-400 font-bold w-14">q[1] |0⟩ ─</span>
                                <span class="text-slate-500">───────────</span>
                                <span class="px-2 py-1 bg-blue-800 text-blue-200 rounded font-bold">⊕ (Target)</span>
                                <span class="text-slate-500">───────</span>
                                <span class="text-slate-400">100% Entangled Measurement</span>
                            </div>
                        </div>

                        <!-- Interactive Unitary Gate Matrix Inspector -->
                        <div>
                            <span class="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">Tap a Gate to Inspect Unitary Matrix:</span>
                            <div class="flex flex-wrap gap-2 items-center">
                                <button onclick="inspectGateMatrix('H')" class="px-2.5 py-1 text-xs font-bold rounded bg-blue-600/30 hover:bg-blue-600/60 border border-blue-500/50 text-blue-200 transition">Gate H (Hadamard)</button>
                                <button onclick="inspectGateMatrix('X')" class="px-2.5 py-1 text-xs font-bold rounded bg-emerald-600/30 hover:bg-emerald-600/60 border border-emerald-500/50 text-emerald-200 transition">Gate X (Pauli-X NOT)</button>
                                <button onclick="inspectGateMatrix('Z')" class="px-2.5 py-1 text-xs font-bold rounded bg-rose-600/30 hover:bg-rose-600/60 border border-rose-500/50 text-rose-200 transition">Gate Z (Phase-Flip)</button>
                                <button onclick="inspectGateMatrix('S')" class="px-2.5 py-1 text-xs font-bold rounded bg-indigo-600/30 hover:bg-indigo-600/60 border border-indigo-500/50 text-indigo-200 transition">Gate S (π/2 Phase)</button>
                                <button onclick="inspectGateMatrix('CNOT')" class="px-2.5 py-1 text-xs font-bold rounded bg-cyan-600/30 hover:bg-cyan-600/60 border border-cyan-500/50 text-cyan-200 transition">CNOT (CX 2-Qubit)</button>
                            </div>
                            <div id="gate-inspector-box" class="mt-2 p-2.5 rounded bg-slate-900 border border-slate-800 text-xs font-mono text-cyan-300">
                                <strong>Hadamard (H):</strong> 1/√2 [[1, 1], [1, -1]] • Creates equal superposition: H|0⟩ = (|0⟩+|1⟩)/√2, H|1⟩ = (|0⟩-|1⟩)/√2.
                            </div>
                        </div>
                    </div>
                `;
            } else if (idx === 2) {
                // Level 3: Grover Search & Quantum Teleportation Protocol
                interactiveDemoHTML = `
                    <div class="bg-slate-950/80 border border-emerald-900/60 rounded-xl p-4 space-y-3">
                        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-2">
                            <div class="flex items-center space-x-2">
                                <i data-lucide="zap" class="w-4 h-4 text-emerald-400"></i>
                                <span class="font-bold text-sm text-white">Algorithms & Protocols: Grover Search & Quantum Teleportation</span>
                            </div>
                            <span class="text-[11px] font-mono text-emerald-300 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800">O(√N) Speedup & Entanglement Channel</span>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                            <!-- Grover Flow -->
                            <div class="p-3 bg-slate-900/90 rounded-lg border border-slate-800 space-y-2">
                                <div class="font-bold text-cyan-300 flex items-center space-x-1.5">
                                    <i data-lucide="search" class="w-3.5 h-3.5"></i>
                                    <span>Grover's 2-Qubit Database Search Pipeline</span>
                                </div>
                                <div class="space-y-1 text-slate-300 font-mono text-[11px]">
                                    <div class="p-1 rounded bg-slate-800/60">1. Equal Superposition: |s⟩ = 1/2(|00⟩+|01⟩+|10⟩+|11⟩)</div>
                                    <div class="p-1 rounded bg-slate-800/60 text-amber-300">2. Oracle Inversion: Target |11⟩ phase flipped (-|11⟩)</div>
                                    <div class="p-1 rounded bg-slate-800/60 text-emerald-300">3. Diffusion Operator: Inversion about the mean 2|s⟩⟨s| - I</div>
                                    <div class="p-1 rounded bg-emerald-950/80 text-emerald-200 font-bold border border-emerald-800">Outcome: Probability of |11⟩ amplified to 100%!</div>
                                </div>
                            </div>

                            <!-- Quantum Teleportation Pipeline -->
                            <div class="p-3 bg-slate-900/90 rounded-lg border border-slate-800 space-y-2">
                                <div class="font-bold text-emerald-300 flex items-center space-x-1.5">
                                    <i data-lucide="radio" class="w-3.5 h-3.5"></i>
                                    <span>Quantum Teleportation & Entanglement Channel</span>
                                </div>
                                <div class="space-y-1 text-slate-300 font-mono text-[11px]">
                                    <div class="p-1 rounded bg-slate-800/60 text-blue-300">1. Unknown State: Prepare |ψ⟩ = α|0⟩ + β|1⟩ on Alice's q[0]</div>
                                    <div class="p-1 rounded bg-slate-800/60 text-indigo-300">2. Bell Pair Distribution: Entangle EPR pair on q[1] & Bob's q[2]</div>
                                    <div class="p-1 rounded bg-slate-800/60 text-purple-300">3. Bell State Measurement (BSM): CNOT(0,1) + H(0) on Alice's qubits</div>
                                    <div class="p-1 rounded bg-emerald-950/80 text-emerald-200 font-bold border border-emerald-800">4. Bob Recovery: Classical feedforward Z^(m0) X^(m1) restores |ψ⟩!</div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            } else if (idx === 3) {
                // Level 4: Andhra Pradesh Industrial Deployment Blueprint
                interactiveDemoHTML = `
                    <div class="bg-slate-950/80 border border-purple-900/60 rounded-xl p-4 space-y-3">
                        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-2">
                            <div class="flex items-center space-x-2">
                                <i data-lucide="briefcase" class="w-4 h-4 text-purple-400"></i>
                                <span class="font-bold text-sm text-white">Andhra Pradesh Real-World Capstone Deployment Matrix</span>
                            </div>
                            <span class="text-[11px] font-mono text-purple-300 bg-purple-950/80 px-2 py-0.5 rounded border border-purple-800">State Mission Use Cases</span>
                        </div>

                        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 text-xs">
                            <div class="p-2.5 rounded-lg bg-slate-900/90 border border-cyan-800/50 space-y-1">
                                <div class="font-bold text-cyan-300 flex items-center space-x-1">
                                    <i data-lucide="anchor" class="w-3.5 h-3.5"></i>
                                    <span>Vizag Port Logistics</span>
                                </div>
                                <p class="text-[11px] text-slate-400 leading-tight">QAOA optimization for berth scheduling, crane allocation, and container dispatch.</p>
                                <span class="text-[10px] text-cyan-400 font-mono block">Ising / QUBO Mapping</span>
                            </div>

                            <div class="p-2.5 rounded-lg bg-slate-900/90 border border-purple-800/50 space-y-1">
                                <div class="font-bold text-purple-300 flex items-center space-x-1">
                                    <i data-lucide="lock" class="w-3.5 h-3.5"></i>
                                    <span>AP PQC Migration</span>
                                </div>
                                <p class="text-[11px] text-slate-400 leading-tight">Replacing RSA/ECC with NIST ML-KEM Kyber lattice cryptography across state portals.</p>
                                <span class="text-[10px] text-purple-400 font-mono block">Shor-Safe Security</span>
                            </div>

                            <div class="p-2.5 rounded-lg bg-slate-900/90 border border-emerald-800/50 space-y-1">
                                <div class="font-bold text-emerald-300 flex items-center space-x-1">
                                    <i data-lucide="flask-conical" class="w-3.5 h-3.5"></i>
                                    <span>Tirupati Pharma VQE</span>
                                </div>
                                <p class="text-[11px] text-slate-400 leading-tight">Molecular Hamiltonian simulation for drug candidate ground state energy calculations.</p>
                                <span class="text-[10px] text-emerald-400 font-mono block">Quantum Chemistry</span>
                            </div>

                            <div class="p-2.5 rounded-lg bg-slate-900/90 border border-blue-800/50 space-y-1">
                                <div class="font-bold text-blue-300 flex items-center space-x-1">
                                    <i data-lucide="cloud-lightning" class="w-3.5 h-3.5"></i>
                                    <span>Cloud Hardware & Co-Op</span>
                                </div>
                                <p class="text-[11px] text-slate-400 leading-tight">Execution on C-DAC Param Q-Sim & IBM Quantum with TCS Quantum Lab placements.</p>
                                <span class="text-[10px] text-blue-400 font-mono block">Paid Stipends & Co-Ops</span>
                            </div>
                        </div>
                    </div>
                `;
            }

            // Quick Action Buttons at the bottom of the visualizer
            let actionButtonsHTML = '';
            if (idx === 0) {
                actionButtonsHTML = `
                    <button onclick="launchSimulatorWithPreset(null)" class="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs flex items-center space-x-1.5 shadow transition">
                        <i data-lucide="play" class="w-3.5 h-3.5 fill-slate-950"></i>
                        <span>Launch 3D Bloch Sphere in Quantum Lab Sim</span>
                    </button>
                    <button onclick="switchTab('curriculum')" class="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition">
                        <span>Compare with Level 2 Foundations</span>
                    </button>
                `;
            } else if (idx === 1) {
                actionButtonsHTML = `
                    <button onclick="launchSimulatorWithPreset('bell_phi_plus')" class="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center space-x-1.5 shadow transition">
                        <i data-lucide="play" class="w-3.5 h-3.5 fill-white"></i>
                        <span>Load Bell State Preset in Lab Simulator</span>
                    </button>
                    <button onclick="launchSimulatorWithPreset('ghz')" class="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center space-x-1.5 shadow transition">
                        <i data-lucide="play" class="w-3.5 h-3.5 fill-white"></i>
                        <span>Load GHZ (3-Qubit) Preset in Lab Simulator</span>
                    </button>
                `;
            } else if (idx === 2) {
                actionButtonsHTML = `
                    <button onclick="launchSimulatorWithPreset('grover')" class="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs flex items-center space-x-1.5 shadow transition">
                        <i data-lucide="play" class="w-3.5 h-3.5 fill-slate-950"></i>
                        <span>Run Grover 2-Qubit Search in Lab Sim</span>
                    </button>
                    <button onclick="launchSimulatorWithPreset('teleportation')" class="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-bold text-xs flex items-center space-x-1.5 shadow transition">
                        <i data-lucide="cpu" class="w-3.5 h-3.5"></i>
                        <span>Simulate Quantum Teleportation in Lab Sim</span>
                    </button>
                    <button onclick="launchSimulatorWithPreset('deutsch')" class="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition">
                        <span>Deutsch-Jozsa Preset</span>
                    </button>
                `;
            } else if (idx === 3) {
                actionButtonsHTML = `
                    <button onclick="launchAssessmentTab()" class="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center space-x-1.5 shadow transition">
                        <i data-lucide="award" class="w-3.5 h-3.5"></i>
                        <span>Take Gateway Assessment for Level 4 Eligibility</span>
                    </button>
                    <button onclick="launchDashboardTab()" class="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition">
                        <span>View 380+ Connected College Nodes</span>
                    </button>
                `;
            }

            return `
                <div class="bg-gradient-to-br from-slate-900/95 via-slate-900/90 to-slate-950 border border-${themeColor}-500/40 rounded-2xl p-5 sm:p-6 space-y-5 shadow-2xl relative">
                    <!-- Top Bar of Visualizer -->
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3.5">
                        <div>
                            <div class="flex items-center space-x-2">
                                <span class="px-2.5 py-0.5 rounded-full bg-${themeColor}-950 text-${themeColor}-300 border border-${themeColor}-800 text-[10px] font-mono font-bold uppercase tracking-wider">
                                    Visual Concept Roadmap • ${lvl.level}
                                </span>
                                <span class="text-xs text-slate-400 font-mono">${lvl.badge}</span>
                            </div>
                            <h4 class="text-base sm:text-lg font-extrabold text-white mt-1">${lvl.title}</h4>
                            <p class="text-xs text-slate-300 mt-0.5">${lvl.visual_summary}</p>
                            <div class="mt-2 inline-block px-3 py-1 rounded bg-slate-950 border border-slate-800 font-mono text-xs text-${themeColor}-300">
                                <strong>Core Principle:</strong> ${lvl.key_formula}
                            </div>
                        </div>

                        <div class="flex items-center space-x-2 self-start sm:self-center">
                            ${!isModal ? `
                                <button onclick="openVisualizerModal(${idx})" class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs flex items-center space-x-1.5 transition" title="Open full screen modal view">
                                    <i data-lucide="maximize" class="w-3.5 h-3.5"></i>
                                    <span>Pop Out</span>
                                </button>
                                <button onclick="toggleSyllabusVisualizer(${idx})" class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-rose-950/60 text-slate-300 hover:text-rose-300 border border-slate-700 hover:border-rose-800 text-xs flex items-center space-x-1 transition">
                                    <i data-lucide="x" class="w-3.5 h-3.5"></i>
                                    <span>Collapse</span>
                                </button>
                            ` : ''}
                        </div>
                    </div>

                    <!-- 4-Stage Learning Journey Roadmap -->
                    <div>
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
                                <i data-lucide="git-commit" class="w-3.5 h-3.5 text-${themeColor}-400"></i>
                                <span>4-Stage Syllabus Progression Pathway</span>
                            </span>
                            <span class="text-[11px] font-mono text-slate-400">Step-by-step Mastery</span>
                        </div>

                        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                            ${milestones.map((m, mIdx) => `
                                <div class="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-${themeColor}-500/60 transition space-y-2 relative group flex flex-col justify-between">
                                    <div>
                                        <div class="flex justify-between items-center">
                                            <span class="w-6 h-6 rounded-lg bg-${themeColor}-950 text-${themeColor}-300 border border-${themeColor}-800/80 flex items-center justify-center font-mono text-[10px] font-extrabold">
                                                ${m.step}
                                            </span>
                                            <i data-lucide="${m.icon}" class="w-4 h-4 text-${themeColor}-400"></i>
                                        </div>
                                        <h5 class="font-bold text-white text-xs mt-2 group-hover:text-${themeColor}-300 transition">${m.title}</h5>
                                        <p class="text-[11px] text-slate-400 mt-1 leading-relaxed">${m.desc}</p>
                                    </div>
                                    <div class="mt-2 pt-2 border-t border-slate-900">
                                        <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-${themeColor}-300 border border-slate-800 block truncate">
                                            ${m.highlight}
                                        </span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Interactive Demo / Schematic Component -->
                    ${interactiveDemoHTML}

                    <!-- Action Bar -->
                    <div class="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
                        <div class="flex flex-wrap items-center gap-2">
                            ${actionButtonsHTML}
                        </div>
                        <div class="text-[11px] text-slate-400 font-mono">
                            Aligned with AICTE & National Quantum Mission
                        </div>
                    </div>
                </div>
            `;
        }

        function toggleSyllabusVisualizer(levelIdx) {
            const el = document.getElementById(`syllabus-visualizer-${levelIdx}`);
            const btnText = document.getElementById(`vis-btn-text-${levelIdx}`);
            if (!el) return;

            const isCurrentlyHidden = el.classList.contains('hidden');
            if (isCurrentlyHidden) {
                el.classList.remove('hidden');
                if (btnText) btnText.innerText = "Hide Visualizer";
                el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else {
                el.classList.add('hidden');
                if (btnText) btnText.innerText = "Tap to Visualize Syllabus Roadmap";
            }
            lucide.createIcons();
        }

        function openVisualizerModal(levelIdx) {
            if (!curriculumDataCache || !curriculumDataCache[levelIdx]) return;
            const lvl = curriculumDataCache[levelIdx];
            const modal = document.getElementById('curriculum-visualizer-modal');
            const header = document.getElementById('modal-visualizer-header');
            const body = document.getElementById('modal-visualizer-body');

            header.innerHTML = `
                <div class="flex items-center space-x-2">
                    <span class="px-2.5 py-0.5 rounded-full bg-${lvl.theme_color}-950 text-${lvl.theme_color}-300 border border-${lvl.theme_color}-800 text-xs font-mono font-bold">
                        ${lvl.level} IMMERSIVE VISUALIZER
                    </span>
                    <span class="text-slate-400 text-xs font-mono">${lvl.badge}</span>
                </div>
                <h3 class="text-xl font-extrabold text-white mt-1">${lvl.title}</h3>
            `;

            body.innerHTML = renderVisualizerCardContent(lvl, levelIdx, true);
            modal.classList.remove('hidden');
            lucide.createIcons();
        }

        function closeVisualizerModal() {
            const modal = document.getElementById('curriculum-visualizer-modal');
            if (modal) modal.classList.add('hidden');
        }

        // Level 1 Demo Logic
        let superpositionState = { p0: 0.5, p1: 0.5, collapsed: false };

        function measureSuperpositionDemo() {
            const outcome = Math.random() < 0.5 ? 0 : 1;
            superpositionState = {
                p0: outcome === 0 ? 1.0 : 0.0,
                p1: outcome === 1 ? 1.0 : 0.0,
                collapsed: true
            };
            const p0El = document.getElementById('demo-p0');
            const p1El = document.getElementById('demo-p1');
            const bar0El = document.getElementById('demo-bar-0');
            const bar1El = document.getElementById('demo-bar-1');
            if (p0El) p0El.innerText = `${(superpositionState.p0 * 100).toFixed(1)}%`;
            if (p1El) p1El.innerText = `${(superpositionState.p1 * 100).toFixed(1)}%`;
            if (bar0El) bar0El.style.width = `${superpositionState.p0 * 100}%`;
            if (bar1El) bar1El.style.width = `${superpositionState.p1 * 100}%`;

            const status = document.getElementById('demo-status-text');
            if (status) {
                status.innerHTML = `
                    <span class="text-emerald-400 font-bold">WAVEFUNCTION COLLAPSED!</span> Observation forced state into <strong>|${outcome}⟩</strong>.
                    Born Rule probability was 50%. Superposition destroyed upon measurement.
                `;
                status.className = "text-xs text-emerald-300 bg-emerald-950/60 p-2.5 rounded-lg border border-emerald-800 font-mono animate-pulse";
            }
        }

        function resetSuperpositionDemo() {
            superpositionState = { p0: 0.5, p1: 0.5, collapsed: false };
            const p0El = document.getElementById('demo-p0');
            const p1El = document.getElementById('demo-p1');
            const bar0El = document.getElementById('demo-bar-0');
            const bar1El = document.getElementById('demo-bar-1');
            if (p0El) p0El.innerText = "50.0%";
            if (p1El) p1El.innerText = "50.0%";
            if (bar0El) bar0El.style.width = "50%";
            if (bar1El) bar1El.style.width = "50%";

            const status = document.getElementById('demo-status-text');
            if (status) {
                status.innerHTML = "State: |ψ⟩ = (|0⟩ + |1⟩)/√2 (Equal Superposition). Qubit exists as both simultaneously.";
                status.className = "text-xs text-slate-300 bg-slate-900/90 p-2.5 rounded-lg border border-slate-800 font-mono";
            }
        }

        // Level 2 Gate Matrix Inspector
        function inspectGateMatrix(gate) {
            const box = document.getElementById('gate-inspector-box');
            if (!box) return;
            const matrices = {
                'H': "<strong>Hadamard (H):</strong> 1/√2 [[1, 1], [1, -1]] • Creates equal superposition: H|0⟩ = (|0⟩+|1⟩)/√2, H|1⟩ = (|0⟩-|1⟩)/√2.",
                'X': "<strong>Pauli-X:</strong> [[0, 1], [1, 0]] • Quantum NOT bit-flip: X|0⟩ = |1⟩, X|1⟩ = |0⟩.",
                'Z': "<strong>Pauli-Z:</strong> [[1, 0], [0, -1]] • Quantum phase-flip: Z|0⟩ = |0⟩, Z|1⟩ = -|1⟩.",
                'S': "<strong>Phase S:</strong> [[1, 0], [0, i]] • Adds π/2 (90°) phase: S|1⟩ = i|1⟩. Notice S² = Z.",
                'CNOT': "<strong>CNOT (Controlled-NOT):</strong> 4x4 unitary matrix • Flips target qubit if and only if control qubit is |1⟩. Fundamental 2-qubit entangler!"
            };
            box.innerHTML = matrices[gate] || matrices['H'];
        }

        // Quick Launchers
        function launchSimulatorWithPreset(preset) {
            switchTab('simulator');
            if (preset) {
                loadPreset(preset);
            }
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function launchAssessmentTab() {
            switchTab('assessment');
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function launchDashboardTab() {
            switchTab('dashboard');
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        // =====================================================================
        // 3. UPGRADED QUANTUM LAB SIMULATION STUDIO LOGIC
        // =====================================================================

        function setNumQubits(n) {
            numQubits = n;
            [1, 2, 3, 4].forEach(q => {
                const btn = document.getElementById('btn-qubit-' + q);
                if (!btn) return;
                if (q === n) {
                    btn.className = "px-2.5 py-1 rounded-lg text-xs font-bold bg-cyan-500 text-slate-950 shadow transition";
                } else {
                    btn.className = "px-2.5 py-1 rounded-lg text-xs font-bold text-slate-400 hover:text-white transition";
                }
            });

            // Update active qubit dropdown
            const select = document.getElementById('active-qubit-select');
            if (select) {
                select.innerHTML = '';
                for (let i = 0; i < n; i++) {
                    const opt = document.createElement('option');
                    opt.value = i;
                    opt.innerText = `q[${i}]`;
                    select.appendChild(opt);
                }
            }

            // Filter out gates exceeding qubit count
            circuitInstructions = circuitInstructions.filter(instr => {
                if (instr.target !== undefined && instr.target >= n) return false;
                if (instr.control !== undefined && instr.control >= n) return false;
                if (instr.control1 !== undefined && instr.control1 >= n) return false;
                if (instr.control2 !== undefined && instr.control2 >= n) return false;
                if (instr.qubit1 !== undefined && instr.qubit1 >= n) return false;
                if (instr.qubit2 !== undefined && instr.qubit2 >= n) return false;
                return true;
            });

            renderCircuitBoard();
            runSimulation();
        }

        function updateSimShots() {
            const select = document.getElementById('sim-shots-select');
            if (select) {
                currentShots = parseInt(select.value);
            }
            runSimulation();
        }

        function addGate(gate) {
            const select = document.getElementById('active-qubit-select');
            const target = select ? parseInt(select.value) : 0;
            circuitInstructions.push({ gate: gate, target: target });
            renderCircuitBoard();
            runSimulation();
        }

        function addRotationGate(gate) {
            const select = document.getElementById('active-qubit-select');
            const target = select ? parseInt(select.value) : 0;
            const angleSelect = document.getElementById('param-rotation-angle');
            const angle = angleSelect ? parseFloat(angleSelect.value) : Math.PI / 2;
            circuitInstructions.push({ gate: gate, target: target, param: angle });
            renderCircuitBoard();
            runSimulation();
        }

        function promptCnot() {
            if (numQubits < 2) {
                alert("CNOT requires at least 2 qubits. Switching register to 2 Qubits.");
                setNumQubits(2);
            }
            const cStr = prompt(`Enter Control Qubit index (0 to ${numQubits - 1}):`, "0");
            if (cStr === null) return;
            const tStr = prompt(`Enter Target Qubit index (0 to ${numQubits - 1}):`, "1");
            if (tStr === null) return;
            const c = parseInt(cStr);
            const t = parseInt(tStr);
            if (!isNaN(c) && !isNaN(t) && c >= 0 && c < numQubits && t >= 0 && t < numQubits && c !== t) {
                circuitInstructions.push({ gate: 'CNOT', control: c, target: t });
                renderCircuitBoard();
                runSimulation();
            } else {
                alert("Invalid Control or Target Qubit! They must be distinct indices within the register.");
            }
        }

        function promptCz() {
            if (numQubits < 2) {
                alert("CZ requires at least 2 qubits. Switching register to 2 Qubits.");
                setNumQubits(2);
            }
            const cStr = prompt(`Enter Control Qubit index (0 to ${numQubits - 1}):`, "0");
            if (cStr === null) return;
            const tStr = prompt(`Enter Target Qubit index (0 to ${numQubits - 1}):`, "1");
            if (tStr === null) return;
            const c = parseInt(cStr);
            const t = parseInt(tStr);
            if (!isNaN(c) && !isNaN(t) && c >= 0 && c < numQubits && t >= 0 && t < numQubits && c !== t) {
                circuitInstructions.push({ gate: 'CZ', control: c, target: t });
                renderCircuitBoard();
                runSimulation();
            } else {
                alert("Invalid Control or Target Qubit! They must be distinct indices within the register.");
            }
        }

        function promptCh() {
            if (numQubits < 2) {
                alert("CH requires at least 2 qubits. Switching register to 2 Qubits.");
                setNumQubits(2);
            }
            const cStr = prompt(`Enter Control Qubit index (0 to ${numQubits - 1}):`, "0");
            if (cStr === null) return;
            const tStr = prompt(`Enter Target Qubit index (0 to ${numQubits - 1}):`, "1");
            if (tStr === null) return;
            const c = parseInt(cStr);
            const t = parseInt(tStr);
            if (!isNaN(c) && !isNaN(t) && c >= 0 && c < numQubits && t >= 0 && t < numQubits && c !== t) {
                circuitInstructions.push({ gate: 'CH', control: c, target: t });
                renderCircuitBoard();
                runSimulation();
            } else {
                alert("Invalid Control or Target Qubit! They must be distinct indices within the register.");
            }
        }

        function promptSwap() {
            if (numQubits < 2) {
                alert("SWAP requires at least 2 qubits. Switching register to 2 Qubits.");
                setNumQubits(2);
            }
            const q1Str = prompt(`Enter First Qubit index (0 to ${numQubits - 1}):`, "0");
            if (q1Str === null) return;
            const q2Str = prompt(`Enter Second Qubit index (0 to ${numQubits - 1}):`, "1");
            if (q2Str === null) return;
            const q1 = parseInt(q1Str);
            const q2 = parseInt(q2Str);
            if (!isNaN(q1) && !isNaN(q2) && q1 >= 0 && q1 < numQubits && q2 >= 0 && q2 < numQubits && q1 !== q2) {
                circuitInstructions.push({ gate: 'SWAP', qubit1: q1, qubit2: q2 });
                renderCircuitBoard();
                runSimulation();
            } else {
                alert("Invalid Qubit indices for SWAP! They must be distinct indices within the register.");
            }
        }

        function promptToffoli() {
            if (numQubits < 3) {
                alert("Toffoli (CCNOT) requires at least 3 qubits. Switching register to 3 Qubits.");
                setNumQubits(3);
            }
            const c1Str = prompt(`Enter Control Qubit 1 index (0 to ${numQubits - 1}):`, "0");
            if (c1Str === null) return;
            const c2Str = prompt(`Enter Control Qubit 2 index (0 to ${numQubits - 1}):`, "1");
            if (c2Str === null) return;
            const tStr = prompt(`Enter Target Qubit index (0 to ${numQubits - 1}):`, "2");
            if (tStr === null) return;
            const c1 = parseInt(c1Str);
            const c2 = parseInt(c2Str);
            const t = parseInt(tStr);
            if (!isNaN(c1) && !isNaN(c2) && !isNaN(t) &&
                c1 >= 0 && c1 < numQubits && c2 >= 0 && c2 < numQubits && t >= 0 && t < numQubits &&
                c1 !== c2 && c1 !== t && c2 !== t) {
                circuitInstructions.push({ gate: 'CCNOT', control1: c1, control2: c2, target: t });
                renderCircuitBoard();
                runSimulation();
            } else {
                alert("Invalid Qubit indices for Toffoli! Control 1, Control 2, and Target must all be distinct.");
            }
        }

        function undoLastGate() {
            if (circuitInstructions.length > 0) {
                circuitInstructions.pop();
                renderCircuitBoard();
                runSimulation();
            }
        }

        function removeGate(index) {
            if (index >= 0 && index < circuitInstructions.length) {
                circuitInstructions.splice(index, 1);
                renderCircuitBoard();
                runSimulation();
            }
        }

        function clearCircuit() {
            circuitInstructions = [];
            currentStep = 0;
            renderCircuitBoard();
            runSimulation();
        }

        function loadPreset(name) {
            circuitInstructions = [];
            if (name === 'bell' || name === 'bell_phi_plus') {
                numQubits = 2;
                circuitInstructions = [
                    { gate: 'H', target: 0 },
                    { gate: 'CNOT', control: 0, target: 1 }
                ];
            } else if (name === 'bell_psi_minus') {
                numQubits = 2;
                circuitInstructions = [
                    { gate: 'X', target: 0 },
                    { gate: 'X', target: 1 },
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
            } else if (name === 'w_state') {
                numQubits = 3;
                circuitInstructions = [
                    { gate: 'RY', target: 0, param: 1.910633 },
                    { gate: 'CH', control: 0, target: 1 },
                    { gate: 'CNOT', control: 1, target: 2 },
                    { gate: 'CNOT', control: 0, target: 1 },
                    { gate: 'X', target: 0 }
                ];
            } else if (name === 'teleportation') {
                numQubits = 3;
                circuitInstructions = [
                    { gate: 'RY', target: 0, param: 1.047197 }, // Prepare arbitrary state on Alice's q[0]
                    { gate: 'H', target: 1 },                  // Entangle EPR pair (q[1], q[2])
                    { gate: 'CNOT', control: 1, target: 2 },
                    { gate: 'CNOT', control: 0, target: 1 },   // Bell state measurement
                    { gate: 'H', target: 0 },
                    { gate: 'CZ', control: 0, target: 2 },     // Bob conditional recovery
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
                    { gate: 'CZ', control: 0, target: 1 }, // Diffusion operator
                    { gate: 'X', target: 0 },
                    { gate: 'X', target: 1 },
                    { gate: 'H', target: 0 },
                    { gate: 'H', target: 1 }
                ];
            } else if (name === 'deutsch') {
                numQubits = 2;
                circuitInstructions = [
                    { gate: 'X', target: 1 },
                    { gate: 'H', target: 0 },
                    { gate: 'H', target: 1 },
                    { gate: 'CNOT', control: 0, target: 1 }, // Balanced oracle f(x) = x
                    { gate: 'H', target: 0 }
                ];
            } else if (name === 'qft') {
                numQubits = 3;
                circuitInstructions = [
                    { gate: 'H', target: 0 },
                    { gate: 'S', target: 1 },
                    { gate: 'H', target: 1 },
                    { gate: 'T', target: 2 },
                    { gate: 'H', target: 2 },
                    { gate: 'SWAP', qubit1: 0, qubit2: 2 }
                ];
            }

            setNumQubits(numQubits);
        }

        function renderCircuitBoard() {
            const board = document.getElementById('circuit-board');
            if (!board) return;
            board.innerHTML = '';
            const stepCountEl = document.getElementById('circuit-step-count');
            if (stepCountEl) {
                stepCountEl.innerText = `${circuitInstructions.length} Gate${circuitInstructions.length === 1 ? '' : 's'}`;
            }

            for (let q = 0; q < numQubits; q++) {
                const wire = document.createElement('div');
                wire.className = 'flex items-center space-x-2 py-2 border-b border-slate-800/80';
                
                const qLabel = document.createElement('span');
                qLabel.className = 'w-16 font-bold text-cyan-400 shrink-0';
                qLabel.innerText = `q[${q}] |0⟩ ──`;
                wire.appendChild(qLabel);

                const track = document.createElement('div');
                track.className = 'flex items-center space-x-2 flex-grow overflow-x-auto py-1';

                if (circuitInstructions.length === 0) {
                    const emptySpan = document.createElement('span');
                    emptySpan.className = 'text-slate-600 font-mono text-xs';
                    emptySpan.innerText = '──────────────────────────────────────── (Circuit empty: tap a gate above to insert)';
                    track.appendChild(emptySpan);
                } else {
                    circuitInstructions.forEach((instr, idx) => {
                        const block = document.createElement('div');
                        const isCurrentActiveStep = (currentStep > 0 && idx === currentStep - 1);
                        const activeRing = isCurrentActiveStep ? 'ring-2 ring-yellow-400 shadow-md shadow-yellow-500/20' : '';

                        if (instr.gate === 'CNOT') {
                            if (instr.control === q) {
                                block.className = `px-2 py-1 rounded bg-cyan-950 border border-cyan-400 text-cyan-300 font-bold cursor-pointer hover:bg-rose-900/60 transition ${activeRing}`;
                                block.title = `CNOT Control (q[${instr.control}] → q[${instr.target}]). Click to remove gate.`;
                                block.innerHTML = `● <span class="text-[9px] text-cyan-300">CX→q${instr.target}</span>`;
                            } else if (instr.target === q) {
                                block.className = `px-2 py-1 rounded bg-blue-950 border border-blue-400 text-blue-300 font-bold cursor-pointer hover:bg-rose-900/60 transition ${activeRing}`;
                                block.title = `CNOT Target (from q[${instr.control}]). Click to remove gate.`;
                                block.innerHTML = `⊕ <span class="text-[9px] text-blue-300">from q${instr.control}</span>`;
                            } else {
                                block.className = 'px-2 py-1 text-slate-600 font-bold select-none';
                                block.innerText = '──────';
                            }
                        } else if (instr.gate === 'CZ') {
                            if (instr.control === q) {
                                block.className = `px-2 py-1 rounded bg-teal-950 border border-teal-400 text-teal-300 font-bold cursor-pointer hover:bg-rose-900/60 transition ${activeRing}`;
                                block.title = `CZ Control (q[${instr.control}] → q[${instr.target}]). Click to remove gate.`;
                                block.innerHTML = `● <span class="text-[9px] text-teal-300">CZ→q${instr.target}</span>`;
                            } else if (instr.target === q) {
                                block.className = `px-2 py-1 rounded bg-teal-900 border border-teal-400 text-teal-200 font-bold cursor-pointer hover:bg-rose-900/60 transition ${activeRing}`;
                                block.title = `CZ Target (from q[${instr.control}]). Click to remove gate.`;
                                block.innerHTML = `Z <span class="text-[9px] text-teal-300">from q${instr.control}</span>`;
                            } else {
                                block.className = 'px-2 py-1 text-slate-600 font-bold select-none';
                                block.innerText = '──────';
                            }
                        } else if (instr.gate === 'CH') {
                            if (instr.control === q) {
                                block.className = `px-2 py-1 rounded bg-blue-950 border border-blue-400 text-blue-300 font-bold cursor-pointer hover:bg-rose-900/60 transition ${activeRing}`;
                                block.title = `CH Control (q[${instr.control}] → q[${instr.target}]). Click to remove gate.`;
                                block.innerHTML = `● <span class="text-[9px] text-blue-300">CH→q${instr.target}</span>`;
                            } else if (instr.target === q) {
                                block.className = `px-2 py-1 rounded bg-blue-900 border border-blue-400 text-blue-200 font-bold cursor-pointer hover:bg-rose-900/60 transition ${activeRing}`;
                                block.title = `CH Target (from q[${instr.control}]). Click to remove gate.`;
                                block.innerHTML = `H <span class="text-[9px] text-blue-300">from q${instr.control}</span>`;
                            } else {
                                block.className = 'px-2 py-1 text-slate-600 font-bold select-none';
                                block.innerText = '──────';
                            }
                        } else if (instr.gate === 'SWAP') {
                            if (instr.qubit1 === q || instr.qubit2 === q) {
                                const partner = instr.qubit1 === q ? instr.qubit2 : instr.qubit1;
                                block.className = `px-2 py-1 rounded bg-amber-950 border border-amber-400 text-amber-300 font-bold cursor-pointer hover:bg-rose-900/60 transition ${activeRing}`;
                                block.title = `SWAP with q[${partner}]. Click to remove gate.`;
                                block.innerHTML = `✕ <span class="text-[9px] text-amber-300">q${partner}</span>`;
                            } else {
                                block.className = 'px-2 py-1 text-slate-600 font-bold select-none';
                                block.innerText = '──────';
                            }
                        } else if (instr.gate === 'CCNOT') {
                            if (instr.control1 === q || instr.control2 === q) {
                                block.className = `px-2 py-1 rounded bg-purple-950 border border-purple-400 text-purple-300 font-bold cursor-pointer hover:bg-rose-900/60 transition ${activeRing}`;
                                block.title = `Toffoli Control. Click to remove gate.`;
                                block.innerHTML = `● <span class="text-[9px] text-purple-300">CCNOT→q${instr.target}</span>`;
                            } else if (instr.target === q) {
                                block.className = `px-2 py-1 rounded bg-purple-900 border border-purple-400 text-purple-200 font-bold cursor-pointer hover:bg-rose-900/60 transition ${activeRing}`;
                                block.title = `Toffoli Target. Click to remove gate.`;
                                block.innerHTML = `⊕ <span class="text-[9px] text-purple-300">q${instr.control1},q${instr.control2}</span>`;
                            } else {
                                block.className = 'px-2 py-1 text-slate-600 font-bold select-none';
                                block.innerText = '──────';
                            }
                        } else if (instr.target === q) {
                            let label = instr.gate;
                            let colorClasses = 'bg-slate-800 border-cyan-500/50 text-cyan-300';
                            if (instr.gate === 'H') colorClasses = 'bg-blue-900/70 border-blue-400 text-blue-200';
                            else if (instr.gate === 'X') colorClasses = 'bg-emerald-900/70 border-emerald-400 text-emerald-200';
                            else if (instr.gate === 'SX') { label = '√X'; colorClasses = 'bg-teal-900/70 border-teal-400 text-teal-200'; }
                            else if (instr.gate === 'Y') colorClasses = 'bg-amber-900/70 border-amber-400 text-amber-200';
                            else if (instr.gate === 'Z') colorClasses = 'bg-rose-900/70 border-rose-400 text-rose-200';
                            else if (instr.gate === 'S') colorClasses = 'bg-indigo-900/70 border-indigo-400 text-indigo-200';
                            else if (instr.gate === 'SDG') { label = 'S†'; colorClasses = 'bg-indigo-950 border-indigo-500 text-indigo-300'; }
                            else if (instr.gate === 'T') colorClasses = 'bg-violet-900/70 border-violet-400 text-violet-200';
                            else if (instr.gate === 'TDG') { label = 'T†'; colorClasses = 'bg-violet-950 border-violet-500 text-violet-300'; }
                            else if (instr.param !== undefined) {
                                const deg = Math.round((instr.param * 180) / Math.PI);
                                label = `${instr.gate}(${deg}°)`;
                                colorClasses = 'bg-cyan-950 border-cyan-400 text-cyan-200';
                            }
                            block.className = `px-2.5 py-1 rounded border font-bold cursor-pointer hover:bg-rose-900/60 transition ${colorClasses} ${activeRing}`;
                            block.title = `${instr.gate} on q[${q}]. Click to remove gate.`;
                            block.innerText = label;
                        } else {
                            block.className = 'px-2 py-1 text-slate-600 font-bold select-none';
                            block.innerText = '──────';
                        }

                        block.onclick = () => removeGate(idx);
                        track.appendChild(block);
                    });
                }

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
                        instructions: circuitInstructions,
                        shots: currentShots
                    })
                });
                const data = await res.json();
                if (data.success) {
                    simResultCache = data.result;
                    currentStep = circuitInstructions.length;
                    const stepDisplay = document.getElementById('current-step-display');
                    if (stepDisplay) {
                        stepDisplay.innerText = `Full Execution (${circuitInstructions.length}/${circuitInstructions.length} Gates)`;
                    }
                    renderSimulationResults(data.result);
                } else {
                    alert('Simulation error: ' + data.error);
                }
            } catch (err) {
                console.error("Simulation error:", err);
            }
        }

        function stepCircuit(delta) {
            if (!simResultCache || !simResultCache.steps || simResultCache.steps.length === 0) return;
            const totalSteps = circuitInstructions.length;
            currentStep = Math.max(0, Math.min(totalSteps, currentStep + delta));

            const stepDisplay = document.getElementById('current-step-display');
            if (stepDisplay) {
                if (currentStep === 0) {
                    stepDisplay.innerText = "Step 0: Initial State (|0...0⟩)";
                } else if (currentStep === totalSteps) {
                    stepDisplay.innerText = `Full Execution (${totalSteps}/${totalSteps} Gates)`;
                } else {
                    const gateName = circuitInstructions[currentStep - 1].gate;
                    stepDisplay.innerText = `Step ${currentStep}/${totalSteps}: After Gate ${gateName}`;
                }
            }

            const stepData = simResultCache.steps[currentStep];
            if (stepData) {
                renderStepResults(stepData);
            }
            renderCircuitBoard();
        }

        function switchInspectorTab(tabId) {
            const tabs = ['states', 'bloch', 'histogram', 'code'];
            tabs.forEach(t => {
                const btn = document.getElementById('ins-tab-' + t);
                const panel = document.getElementById('inspector-panel-' + t);
                if (btn) {
                    if (t === tabId) {
                        btn.className = "flex-1 py-1.5 rounded-lg font-bold text-cyan-400 bg-slate-800 transition";
                    } else {
                        btn.className = "flex-1 py-1.5 rounded-lg font-bold text-slate-400 hover:text-slate-200 transition";
                    }
                }
                if (panel) {
                    if (t === tabId) {
                        panel.classList.remove('hidden');
                    } else {
                        panel.classList.add('hidden');
                    }
                }
            });

            if (tabId === 'histogram' && histogramChartInstance) {
                histogramChartInstance.resize();
            }
        }

        function switchCodeLang(lang) {
            activeCodeLang = lang;
            const btnQiskit = document.getElementById('btn-lang-qiskit');
            const btnQasm = document.getElementById('btn-lang-qasm');
            if (btnQiskit && btnQasm) {
                if (lang === 'qiskit') {
                    btnQiskit.className = "px-2.5 py-1 rounded bg-blue-950 text-blue-300 font-bold border border-blue-800";
                    btnQasm.className = "px-2.5 py-1 rounded bg-slate-800 text-slate-400 font-bold border border-slate-700";
                } else {
                    btnQasm.className = "px-2.5 py-1 rounded bg-cyan-950 text-cyan-300 font-bold border border-cyan-800";
                    btnQiskit.className = "px-2.5 py-1 rounded bg-slate-800 text-slate-400 font-bold border border-slate-700";
                }
            }
            updateCodeExportBox();
        }

        function updateCodeExportBox() {
            const box = document.getElementById('code-export-box');
            if (!box || !simResultCache) return;
            if (activeCodeLang === 'qiskit') {
                box.value = simResultCache.qiskit_code || "# No circuit defined";
            } else {
                box.value = simResultCache.qasm_code || "// No circuit defined";
            }
        }

        function copyCurrentCode() {
            const box = document.getElementById('code-export-box');
            if (!box) return;
            navigator.clipboard.writeText(box.value).then(() => {
                alert("Quantum circuit code copied to clipboard!");
            }).catch(err => {
                console.error("Copy failed", err);
            });
        }

        function renderPhaseStateList(states) {
            const list = document.getElementById('statevector-list');
            if (!list) return;
            list.innerHTML = '';

            states.forEach(s => {
                const phaseDeg = s.phase_deg !== undefined ? s.phase_deg : 0;
                const normalizedPhase = phaseDeg < 0 ? (phaseDeg + 360) : phaseDeg;
                const phaseColor = `hsl(${normalizedPhase}, 85%, 60%)`;
                const rad = (normalizedPhase * Math.PI) / 180;
                const ex = 9 + 6.5 * Math.cos(rad);
                const ey = 9 - 6.5 * Math.sin(rad);

                const item = document.createElement('div');
                item.className = 'p-2 rounded bg-slate-800/80 border border-slate-700/60 flex items-center justify-between hover:bg-slate-800 transition';
                item.innerHTML = `
                    <div class="flex items-center space-x-2">
                        <span class="font-bold text-cyan-300 text-xs w-12">${s.basis}</span>
                        <div class="w-16 bg-slate-900 rounded-full h-1.5 overflow-hidden">
                            <div class="bg-gradient-to-r from-cyan-400 to-emerald-400 h-full rounded-full" style="width: ${(s.prob * 100).toFixed(1)}%"></div>
                        </div>
                    </div>
                    <div class="font-mono text-[11px] text-slate-300">
                        ${s.real >= 0 ? '+' : ''}${s.real} ${s.imag >= 0 ? '+' : ''}${s.imag}i
                    </div>
                    <div class="flex items-center space-x-2">
                        <span class="text-emerald-400 font-bold text-xs">${(s.prob * 100).toFixed(1)}%</span>
                        <div class="flex items-center space-x-1" title="Phase: ${normalizedPhase}°">
                            <svg width="18" height="18" viewBox="0 0 18 18" class="shrink-0">
                                <circle cx="9" cy="9" r="8" fill="#090d16" stroke="#334155" stroke-width="1.2" />
                                <line x1="9" y1="9" x2="${ex.toFixed(1)}" y2="${ey.toFixed(1)}" stroke="${phaseColor}" stroke-width="2" stroke-linecap="round" />
                                <circle cx="9" cy="9" r="1.5" fill="${phaseColor}" />
                            </svg>
                            <span class="text-[10px] font-mono text-slate-400 w-7">${normalizedPhase}°</span>
                        </div>
                    </div>
                `;
                list.appendChild(item);
            });
        }

        function renderBlochSpheres(blochArray) {
            const container = document.getElementById('bloch-spheres-container');
            if (!container) return;
            container.innerHTML = '';

            blochArray.forEach(b => {
                const card = document.createElement('div');
                card.className = "p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 space-y-2.5 shadow";

                // Project 3D (x, y, z) into 2D SVG
                const R = 44;
                const cx = 60;
                const cy = 60;
                const xVal = b.x;
                const yVal = b.y;
                const zVal = b.z;

                // Projection
                const px = cx + R * (0.85 * yVal - 0.45 * xVal);
                const py = cy - R * (0.85 * zVal - 0.35 * xVal);

                // Entanglement classification
                const S = b.entropy !== undefined ? b.entropy : 0.0;
                let entropyBadge = 'bg-emerald-950 text-emerald-300 border-emerald-800';
                let entropyLabel = 'Separable (Pure)';
                if (S >= 0.8) {
                    entropyBadge = 'bg-purple-950 text-purple-300 border-purple-800';
                    entropyLabel = 'Maximally Entangled';
                } else if (S > 0.05) {
                    entropyBadge = 'bg-amber-950 text-amber-300 border-amber-800';
                    entropyLabel = 'Partially Entangled';
                }

                card.innerHTML = `
                    <div class="flex items-center justify-between pb-1.5 border-b border-slate-800">
                        <span class="font-bold text-xs text-cyan-400">Qubit q[${b.qubit}]</span>
                        <span class="text-[10px] font-mono px-2 py-0.5 rounded border ${entropyBadge} font-bold">
                            S(ρ) = ${S.toFixed(3)} • ${entropyLabel}
                        </span>
                    </div>

                    <div class="flex items-center justify-center py-1">
                        <svg width="120" height="120" viewBox="0 0 120 120" class="overflow-visible select-none">
                            <!-- Outer sphere boundary -->
                            <circle cx="${cx}" cy="${cy}" r="${R}" fill="rgba(15, 23, 42, 0.6)" stroke="#334155" stroke-width="1.5" />
                            <!-- Equator ellipse -->
                            <ellipse cx="${cx}" cy="${cy}" rx="${R}" ry="13" fill="none" stroke="#475569" stroke-width="1" stroke-dasharray="3,3" />
                            <!-- Prime meridian ellipse -->
                            <ellipse cx="${cx}" cy="${cy}" rx="13" ry="${R}" fill="none" stroke="#475569" stroke-width="1" stroke-dasharray="3,3" />
                            <!-- Vertical Z Axis -->
                            <line x1="${cx}" y1="12" x2="${cx}" y2="108" stroke="#64748b" stroke-width="1" />
                            <!-- Horizontal axis -->
                            <line x1="16" y1="${cy}" x2="104" y2="${cy}" stroke="#475569" stroke-width="0.8" stroke-dasharray="2,2" />
                            <!-- Poles -->
                            <text x="${cx}" y="9" text-anchor="middle" font-size="9" font-family="monospace" fill="#38bdf8" font-weight="bold">|0⟩</text>
                            <text x="${cx}" y="117" text-anchor="middle" font-size="9" font-family="monospace" fill="#38bdf8" font-weight="bold">|1⟩</text>
                            
                            <!-- 3D Vector Arrow -->
                            <line x1="${cx}" y1="${cy}" x2="${px.toFixed(1)}" y2="${py.toFixed(1)}" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round" />
                            <circle cx="${px.toFixed(1)}" cy="${py.toFixed(1)}" r="3.5" fill="#38bdf8" stroke="#0284c7" stroke-width="1" />
                            <circle cx="${cx}" cy="${cy}" r="2" fill="#64748b" />
                        </svg>
                    </div>

                    <div class="space-y-1 text-[11px] font-mono text-slate-300 pt-1 border-t border-slate-800">
                        <div class="flex justify-between">
                            <span class="text-slate-400">Bloch Vector:</span>
                            <span class="text-cyan-300">⟨${xVal.toFixed(2)}, ${yVal.toFixed(2)}, ${zVal.toFixed(2)}⟩</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-slate-400">Spherical:</span>
                            <span class="text-purple-300">θ = ${b.theta_deg}°, φ = ${b.phi_deg}°</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-slate-400">Density Purity Tr(ρ²):</span>
                            <span class="text-emerald-300 font-bold">${b.purity.toFixed(3)}</span>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        function renderSimulationResults(result) {
            renderPhaseStateList(result.states);
            renderBlochSpheres(result.bloch);
            updateCodeExportBox();

            // Histogram Chart
            const labels = Object.keys(result.shots);
            const counts = Object.values(result.shots);
            updateHistogramChart(labels, counts);
            const shotLabel = document.getElementById('hist-shot-count-label');
            if (shotLabel) {
                shotLabel.innerText = currentShots === 0 ? "Analytical Probs (0 Shots)" : `${currentShots} Shots`;
            }
        }

        function renderStepResults(stepData) {
            renderPhaseStateList(stepData.states);
            renderBlochSpheres(stepData.bloch);
        }

        // =====================================================================
        // 4. DIAGNOSTIC ASSESSMENT & APSSDC CREDENTIAL LOGIC
        // =====================================================================
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
            renderAssessmentResults(data);
        }

        function renderAssessmentResults(data) {
            const panel = document.getElementById('assessment-results-panel');
            if (!panel) return;

            let weakTopicsHtml = '';
            if (data.weak_topics && data.weak_topics.length > 0) {
                weakTopicsHtml = `
                    <div class="bg-slate-950/70 border border-amber-500/30 rounded-xl p-5 space-y-4">
                        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                            <div class="flex items-center space-x-2.5">
                                <span class="p-1.5 rounded-lg bg-amber-500/20 text-amber-400">
                                    <i data-lucide="compass" class="w-5 h-5"></i>
                                </span>
                                <div>
                                    <h4 class="font-bold text-white text-base">Identified Weak Areas & Remediation Topics</h4>
                                    <p class="text-xs text-slate-400">Targeted topic suggestions based on your diagnostic responses (&lt; 75% accuracy)</p>
                                </div>
                            </div>
                            <span class="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-950 text-amber-300 border border-amber-800">
                                ${data.weak_topics.length} Areas to Strengthen
                            </span>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            ${data.weak_topics.map(item => `
                                <div class="bg-slate-900 border ${item.severity.includes('Critical') ? 'border-rose-900/60 bg-gradient-to-br from-slate-900 to-rose-950/20' : 'border-amber-900/60 bg-gradient-to-br from-slate-900 to-amber-950/20'} rounded-xl p-4 space-y-3">
                                    <div class="flex items-center justify-between">
                                        <span class="text-xs font-bold text-white">${item.category}</span>
                                        <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${item.severity.includes('Critical') ? 'bg-rose-900/60 text-rose-300 border border-rose-700' : 'bg-amber-900/60 text-amber-300 border border-amber-700'}">
                                            ${item.severity}
                                        </span>
                                    </div>
                                    <div class="flex items-center space-x-2 text-xs">
                                        <div class="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                                            <div class="h-2 rounded-full ${item.score_percent < 50 ? 'bg-rose-500' : 'bg-amber-500'}" style="width: ${item.score_percent}%"></div>
                                        </div>
                                        <span class="font-mono text-xs font-bold ${item.score_percent < 50 ? 'text-rose-400' : 'text-amber-400'} whitespace-nowrap">${item.score_percent}%</span>
                                    </div>
                                    <p class="text-xs text-slate-300 leading-relaxed font-sans">${item.diagnosis}</p>
                                    <div class="pt-2 border-t border-slate-800/80 flex flex-col gap-2">
                                        <div class="text-[11px] text-cyan-300 font-mono flex items-center space-x-1">
                                            <i data-lucide="book-open" class="w-3.5 h-3.5 flex-shrink-0"></i>
                                            <span><strong>Recommended:</strong> ${item.topic}</span>
                                        </div>
                                        <div class="flex items-center space-x-2 pt-1">
                                            <button onclick="openVisualizerModal(${item.recommended_level_idx})" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 hover:text-white border border-slate-700 text-[11px] font-semibold flex items-center space-x-1 transition">
                                                <i data-lucide="layers" class="w-3 h-3"></i>
                                                <span>Level Visualizer</span>
                                            </button>
                                            <button onclick="launchSimulatorWithPreset('${item.recommended_preset}')" class="px-2.5 py-1 rounded-lg bg-indigo-900/60 hover:bg-indigo-800 text-indigo-200 hover:text-white border border-indigo-700 text-[11px] font-semibold flex items-center space-x-1 transition">
                                                <i data-lucide="play" class="w-3 h-3"></i>
                                                <span>Lab Practice Preset</span>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            } else {
                weakTopicsHtml = `
                    <div class="bg-gradient-to-r from-emerald-950/40 via-slate-900 to-cyan-950/40 border border-emerald-500/40 rounded-xl p-5 flex items-center space-x-4">
                        <div class="p-3 rounded-xl bg-emerald-500/20 text-emerald-400">
                            <i data-lucide="award" class="w-8 h-8"></i>
                        </div>
                        <div>
                            <h4 class="font-bold text-white text-base">Exceptional Diagnostic Mastery!</h4>
                            <p class="text-xs text-slate-300 mt-1">You demonstrated &gt;= 75% accuracy across all core quantum domains. You are cleared for direct entry into Level 4 Specialisation & Industry Capstone deployment.</p>
                        </div>
                    </div>
                `;
            }

            const feedbackListHtml = data.feedback.map((item, idx) => `
                <div class="p-4 rounded-xl border ${item.is_correct ? 'border-emerald-900/50 bg-slate-950/50' : 'border-rose-900/50 bg-slate-950/50'} space-y-2">
                    <div class="flex items-start justify-between gap-2">
                        <div class="flex items-center space-x-2">
                            <span class="p-1 rounded ${item.is_correct ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}">
                                <i data-lucide="${item.is_correct ? 'check-circle' : 'x-circle'}" class="w-4 h-4"></i>
                            </span>
                            <span class="text-xs font-mono font-semibold text-slate-400">Q${idx + 1} • ${item.category} (${item.difficulty})</span>
                        </div>
                        <span class="text-[11px] px-2 py-0.5 rounded font-mono ${item.is_correct ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-rose-950 text-rose-300 border border-rose-800'}">
                            ${item.is_correct ? 'Correct' : 'Needs Review'}
                        </span>
                    </div>
                    <p class="text-sm font-medium text-white">${item.question}</p>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs pt-1">
                        <div class="p-2 rounded bg-slate-900 border border-slate-800">
                            <span class="text-slate-400 block text-[10px] uppercase font-bold">Your Response:</span>
                            <span class="${item.is_correct ? 'text-emerald-300' : 'text-rose-300'} font-medium">${item.your_answer_text}</span>
                        </div>
                        <div class="p-2 rounded bg-slate-900 border border-slate-800">
                            <span class="text-slate-400 block text-[10px] uppercase font-bold">Correct Formulation:</span>
                            <span class="text-cyan-300 font-medium">${item.correct_answer_text}</span>
                        </div>
                    </div>
                    <div class="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800/80 text-xs text-slate-300 font-sans leading-relaxed">
                        <strong class="text-slate-200">Theoretical Explanation:</strong> ${item.explanation}
                    </div>
                    ${item.recommended_preset ? `
                        <div class="flex justify-end pt-1">
                            <button onclick="launchSimulatorWithPreset('${item.recommended_preset}')" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-indigo-300 hover:text-white border border-slate-700 text-xs flex items-center space-x-1 transition">
                                <i data-lucide="play" class="w-3 h-3"></i>
                                <span>${item.action_label || 'Practice Circuit in Lab Sim'}</span>
                            </button>
                        </div>
                    ` : ''}
                </div>
            `).join('');

            panel.innerHTML = `
                <div class="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-4 gap-4">
                    <div>
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping"></span>
                            <h3 class="font-bold text-white text-lg">Diagnostic Skill Assessment Evaluation</h3>
                        </div>
                        <p class="text-xs text-slate-400 mt-1">Evaluated for <strong class="text-white">${data.student_name}</strong> (${data.college_name})</p>
                    </div>
                    <div class="flex items-center space-x-3">
                        <div class="text-right">
                            <span class="text-xs text-slate-400 block">Overall Score</span>
                            <span class="text-xl font-mono font-bold ${data.percentage >= 75 ? 'text-emerald-400' : data.percentage >= 50 ? 'text-amber-400' : 'text-rose-400'}">${data.percentage}%</span>
                            <span class="text-[11px] text-slate-500 block">(${data.score} of ${data.total} correct)</span>
                        </div>
                        <span class="px-3 py-1.5 rounded-xl text-xs font-bold border ${data.percentage >= 80 ? 'bg-purple-950/80 text-purple-300 border-purple-700' : data.percentage >= 60 ? 'bg-indigo-950/80 text-indigo-300 border-indigo-700' : 'bg-slate-800 text-slate-300 border-slate-700'}">
                            ${data.status}
                        </span>
                    </div>
                </div>

                ${weakTopicsHtml}

                <div class="space-y-4">
                    <div class="flex items-center justify-between">
                        <h4 class="font-bold text-white text-sm flex items-center space-x-2">
                            <i data-lucide="list-checks" class="w-4 h-4 text-cyan-400"></i>
                            <span>Detailed Diagnostic Breakdown (${data.total} Questions)</span>
                        </h4>
                    </div>
                    <div class="space-y-3">
                        ${feedbackListHtml}
                    </div>
                </div>
            `;

            panel.classList.remove('hidden');
            if (window.lucide) {
                lucide.createIcons();
            }
            panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
    print(f"  Qubit 0 von Neumann Entropy S(ρ): {res['bloch'][0]['entropy']} (Purity: {res['bloch'][0]['purity']})")

    # Test 2: GHZ 3-Qubit Entanglement & von Neumann Entropy Verification
    print("\n[TEST 2] Running 3-Qubit GHZ State Entanglement Verification...")
    sim_ghz = QuantumSimulator(3)
    res_ghz = sim_ghz.execute_circuit([
        {'gate': 'H', 'target': 0},
        {'gate': 'CNOT', 'control': 0, 'target': 1},
        {'gate': 'CNOT', 'control': 1, 'target': 2}
    ])
    for s in res_ghz['states']:
        if s['prob'] > 0.01:
            print(f"  Basis {s['basis']}: Amplitude = {s['real']} + {s['imag']}i | Probability = {s['prob']*100:.1f}%")
    print(f"  Qubit 0 Entropy S(ρ): {res_ghz['bloch'][0]['entropy']} | Purity: {res_ghz['bloch'][0]['purity']}")
    print(f"  Generated Qiskit Code:\n{res_ghz['qiskit_code']}")

    # Test 3: Grover's 2-Qubit Search Algorithm Simulation
    print("\n[TEST 3] Running Grover's 2-Qubit Search Algorithm (Target |11>)...")
    sim_grover = QuantumSimulator(2)
    res_grover = sim_grover.execute_circuit([
        {'gate': 'H', 'target': 0}, {'gate': 'H', 'target': 1},
        {'gate': 'CZ', 'control': 0, 'target': 1},
        {'gate': 'H', 'target': 0}, {'gate': 'H', 'target': 1},
        {'gate': 'X', 'target': 0}, {'gate': 'X', 'target': 1},
        {'gate': 'CZ', 'control': 0, 'target': 1},
        {'gate': 'X', 'target': 0}, {'gate': 'X', 'target': 1},
        {'gate': 'H', 'target': 0}, {'gate': 'H', 'target': 1}
    ], shots=1000)
    for s in res_grover['states']:
        print(f"  Basis {s['basis']}: Probability = {s['prob']*100:.1f}%")
    print(f"  Shots Measured (1000 shots): {res_grover['shots']}")
    assert res_grover['shots'].get('11', 0) == 1000 or res_grover['shots'].get('|11>', 0) == 1000, "Grover search failed to amplify |11> to 100%!"
    print("  Outcome: |11> successfully amplified to 100% with quadratic speedup!")

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
* Built-in: Upgraded Multi-Qubit Quantum Simulation Studio (1-4Q, Toffoli, Entropy, Qiskit)
------------------------------------------------------------------------
Starting Web Server on http://127.0.0.1:{port}/ ...
Press Ctrl+C to stop.
========================================================================
""")
        threading.Timer(1.2, lambda: open_browser(port)).start()
        app.run(host='0.0.0.0', port=port, debug=False)
