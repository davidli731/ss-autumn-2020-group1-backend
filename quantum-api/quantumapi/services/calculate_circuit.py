'''
calculate_circuit.py
- provides object to take in quantum circuit (JSON) and return list of results
'''
import math
import cmath
import json
import numpy as np
import emoji
from pyquil import Program
from pyquil.quil import DefGate
import pyquil.gates as pqg
from pyquil.api import WavefunctionSimulator


class calculate_circuit():
    '''Intakes a quantum circuit and return results'''
    POS_SQRT_X = 0
    NEG_SQRT_X = 0
    POS_SQRT_Y = 0
    NEG_SQRT_Y = 0
    POS_SQRT_Z = 0
    NEG_SQRT_Z = 0

    POS_FTRT_X = 0
    NEG_FTRT_X = 0
    POS_FTRT_Y = 0
    NEG_FTRT_Y = 0
    POS_FTRT_Z = 0
    NEG_FTRT_Z = 0

    def __init__(self, data):
        # get JSON, load the data from the string (convert to dictionary), assign to circuit
        try:
            circuit = json.loads(data["circuit_input"])
        except:
            circuit = data["circuit_input"]
        self.circuit = circuit
        self.results = {}

    def calculate(self):
        '''Processes the quantum circuit and returns the results'''
        p = Program()

        # Gets definitions for quarter & eighth turn gates
        p = self.define_extra_gates(p)

        # length of circuit = number of columns
        col_length = len(self.circuit)
        num_qubits = 0
        # max length of any number of operations per column = number of qubits / rows used
        for i in self.circuit:
            if len(i) > num_qubits: num_qubits = len(i)

        # loops over each gate in circuit and applies the gate
        for i in range(col_length):
            # Keeps track of where special components are (i.e. SWAP)
            special_loc = []
            # Obtains any controls in the column i; if present, each gate is made into a controlled gate, else the gate is normal
            control_qubits, anticontrol_qubits = self.get_controls_in_column(i)
            # To apply anticontrols, X gate needs to be applied to the corresponding qubit wire and applied again after column is processed
            for qubit in anticontrol_qubits: p += pqg.X(qubit)

            for j in range(len(self.circuit[i])):
                current_gate = str(self.circuit[i][j]).upper()

                # If the gate is X, Y, Z or H, apply the gate to qubit #j
                if current_gate in "H": p += pqg.H(j).controlled(control_qubits)
                elif current_gate in "X": p += pqg.X(j).controlled(control_qubits)
                elif current_gate in "Y": p += pqg.Y(j).controlled(control_qubits)
                elif current_gate in "Z": p += pqg.Z(j).controlled(control_qubits)
               
                # If the gate is a quarter turn (+/- 90 deg or pi/2) for X, Y or Z, apply the respective gate
                elif current_gate in ("X^1/2", "X^½"): p += POS_SQRT_X(j).controlled(control_qubits)
                elif current_gate in ('X^-1/2', 'X^-½'): p += NEG_SQRT_X(j).controlled(control_qubits)
                elif current_gate in ("Y^1/2", "Y^½"): p += POS_SQRT_Y(j).controlled(control_qubits)
                elif current_gate in ("Y^-1/2", "Y^-½"): p += NEG_SQRT_Y(j).controlled(control_qubits)
                elif current_gate in ("Z^1/2", "Z^½", "S"): p += POS_SQRT_Z(j).controlled(control_qubits)
                elif current_gate in ("Z^-1/2", "Z^-½", "S^-1"): p += NEG_SQRT_Z(j).controlled(control_qubits)

                # If the gate is an eighth turn (+/- 45 deg or pi/4) for X, Y or Z, apply the respective gate
                elif current_gate in ("X^1/4", "X^¼"): p += POS_FTRT_X(j).controlled(control_qubits)
                elif current_gate in ("X^-1/4", "X^-¼"): p += NEG_FTRT_X(j).controlled(control_qubits)
                elif current_gate in ("Y^1/4", "Y^¼"): p += POS_FTRT_Y(j).controlled(control_qubits)
                elif current_gate in ("Y^-1/4", "Y^-¼"): p += NEG_FTRT_Y(j).controlled(control_qubits)
                elif current_gate in ("Z^1/4", "Z^¼", "T"): p += POS_FTRT_Z(j).controlled(control_qubits)
                elif current_gate in ("Z^-1/4", "Z^-¼", "T^-1"): p += NEG_FTRT_Z(j).controlled(control_qubits)
        
                # If the gate is a SWAP gate, check if another one has been found before and perform the SWAP operation
                # If not, keep track of its location until we find the other SWAP gate
                elif current_gate in "SWAP":
                    if len(special_loc) == 1:
                        p += pqg.SWAP(special_loc[0], j).controlled(control_qubits)
                        special_loc = []
                    else:
                        special_loc.append(j)

                else: p += pqg.I(j)
            
            # Reverses the process used to make anticontrols possible
            for qubit in anticontrol_qubits: p += pqg.X(qubit)

        self.construct_results_dict(p)

        return self.results

    def get_controls_in_column(self, circuit_col):
        '''Processes specific column, obtaining controls/anticontrols, and returning location'''
        control_qubits = []
        anticontrol_qubits = []
        for index, qubit in enumerate(self.circuit[circuit_col]):
            if emoji.demojize(qubit) in (":black_circle:", ":white_circle:", "◦", "•"): control_qubits.append(index)
            # List for anticontrol qubits required because of additional requirements to work
            if emoji.demojize(qubit) in (":white_circle:", "◦"): anticontrol_qubits.append(index)
        return control_qubits, anticontrol_qubits

    def construct_results_dict(self, qubit_program):
        ''' Constructs results dictionary of the evaluated quantum circuit '''
        wf_sim = WavefunctionSimulator()
        wavefunction = wf_sim.wavefunction(qubit_program)
        amp_arr = wavefunction.amplitudes
        prob_dict = wavefunction.get_outcome_probs()
        results_dict = {}
        for index, item in enumerate(prob_dict):
            struct = {}
            # Integer value of the qubit state
            struct["int"] = "{:.0f}".format(int(item, 2))
            # Complex number representing the qubit state
            struct["val"] = "{:+.5f}".format(amp_arr[index]).strip("()")
            # Probability of obtaining the qubit state
            struct["prob"] = "{:.5f}".format(prob_dict[item])
            # Magnitude of the qubit state
            struct["mag"] = "{:.5f}".format(abs(amp_arr[index]))
            # Phase of the qubit state (obtained by measuring complex number phase, converting to °)
            struct["phase"] = "{:+.2f}".format(np.degrees(cmath.phase(amp_arr[index]))) + "°"
            results_dict[item] = struct
        self.results = results_dict

    def define_extra_gates(self, qubit_program):
        ''' Defines quarter & eighth turn gates for the qubit program '''
        # Gates to be used in calculate method
        global POS_SQRT_X, NEG_SQRT_X
        global POS_SQRT_Y, NEG_SQRT_Y
        global POS_SQRT_Z, NEG_SQRT_Z
        global POS_FTRT_X, NEG_FTRT_X
        global POS_FTRT_Y, NEG_FTRT_Y
        global POS_FTRT_Z, NEG_FTRT_Z

        # Definition of the unitary matrices for x, y & z pauli gates based on powers
        g = lambda p: cmath.exp(-1j*p*np.pi/-2)
        c = lambda p: math.cos(p*np.pi/2)
        s = lambda p: math.sin(p*np.pi/2)
        x_pow_gate = lambda p: np.array([[g(p)*c(p), -1j*g(p)*s(p)], [-1j*g(p)*s(p), g(p)*c(p)]])
        y_pow_gate = lambda p: np.array([[g(p)*c(p), -g(p)*s(p)], [g(p)*s(p), g(p)*c(p)]])
        z_pow_gate = lambda p: np.array([[1, 0],[0, g(2*p)]])

        # Definition of the different dimensions and powers, all combinations
        dims = ['X', 'Y', 'Z']
        powers = {"POS-SQRT": 0.5, "NEG-SQRT": -0.5, "POS-FTRT": 0.25, "NEG-FTRT": -0.25}
        constructors = {}
        for dim in dims:
            for power in powers:
                gate_name = power + "-" + dim
                # Get the unitary matrix for that dimension to the specific power
                if dim in 'X': matrix = x_pow_gate(powers[power])
                elif dim in 'Y': matrix = y_pow_gate(powers[power])
                else: matrix = z_pow_gate(powers[power])
                # Get the Quil definition for the new gate
                gate_def = DefGate(gate_name, matrix)
                # Get the gate constructor
                constructors[gate_name] = gate_def.get_constructor()
                # Then we can use the new gate
                qubit_program += gate_def

        # Assign gate constructurs
        POS_SQRT_X, NEG_SQRT_X = constructors["POS-SQRT-X"], constructors["NEG-SQRT-X"]
        POS_SQRT_Y, NEG_SQRT_Y = constructors["POS-SQRT-Y"], constructors["NEG-SQRT-Y"]
        POS_SQRT_Z, NEG_SQRT_Z = constructors["POS-SQRT-Z"], constructors["NEG-SQRT-Z"]

        POS_FTRT_X, NEG_FTRT_X = constructors["POS-FTRT-X"], constructors["NEG-FTRT-X"]
        POS_FTRT_Y, NEG_FTRT_Y = constructors["POS-FTRT-Y"], constructors["NEG-FTRT-Y"]
        POS_FTRT_Z, NEG_FTRT_Z = constructors["POS-FTRT-Z"], constructors["NEG-FTRT-Z"]

        return qubit_program
