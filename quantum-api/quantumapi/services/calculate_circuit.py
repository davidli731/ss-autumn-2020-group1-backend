import numpy as np
import math
import cmath
import json
import pyquil
from pyquil import Program
from pyquil.quil import DefGate
import pyquil.gates as pqg
from pyquil.api import WavefunctionSimulator


class calculate_circuit():
    
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
        self.data = data

    def calculate(self):

        p = Program()
        
        # Gets definitions for quarter & eighth turn gates
        p = self.define_extra_gates(p)

        # get JSON, load the data from the string (convert to dictionary), assign to circuit
        try:
            circuit = json.loads(self.data["circuit_input"])
        except:
            circuit = self.data["circuit_input"]

        # length of circuit = number of columns
        col_length = len(circuit)
        num_qubits = 0
        # max length of any number of operations per column = number of qubits / rows used
        for i in circuit:
            if len(i) > num_qubits: num_qubits = len(i)
        # loops over each gate in circuit and applies the gate
        for i in range(col_length):
            # stores what type of special gate it is (CNOT, CCNOT, CZ, etc)
            special_gate_type = "NULL"
            # keeps track of where special components are (i.e. controls, or SWAP)
            special_loc = []

            for j in range(len(circuit[i])):
                current_gate = str(circuit[i][j]).upper()

                # If the gate is X, Y, Z or H, apply the gate to qubit #j
                if current_gate in "H": p += pqg.H(j)
                elif current_gate in "X": p += pqg.X(j)
                elif current_gate in "Y": p += pqg.Y(j)
                elif current_gate in "Z": p += pqg.Z(j)
               
                # If the gate is a quarter turn (+/- 90 deg or pi/2) for X, Y or Z, apply the respective gate
                elif current_gate in ("X^1/2", "X^½"): p += POS_SQRT_X(j)
                elif current_gate in ('X^-1/2', 'X^-½'): p += NEG_SQRT_X(j)
                elif current_gate in ("Y^1/2", "Y^½"): p += POS_SQRT_Y(j)
                elif current_gate in ("Y^-1/2", "Y^-½"): p += NEG_SQRT_Y(j)
                elif current_gate in ("Z^1/2", "Z^½", "S"): p += POS_SQRT_Z(j)
                elif current_gate in ("Z^-1/2", "Z^-½", "S^-1"): p += NEG_SQRT_Z(j)

                # If the gate is an eighth turn (+/- 45 deg or pi/4) for X, Y or Z, apply the respective gate
                elif current_gate in ("X^1/4", "X^¼"): p += POS_FTRT_X(j)
                elif current_gate in ("X^-1/4", "X^-¼"): p += NEG_FTRT_X(j)
                elif current_gate in ("Y^1/4", "Y^¼"): p += POS_FTRT_Y(j)
                elif current_gate in ("Y^-1/4", "Y^-¼"): p += NEG_FTRT_Y(j)
                elif current_gate in ("Z^1/4", "Z^¼", "T"): p += POS_FTRT_Z(j)
                elif current_gate in ("Z^-1/4", "Z^-¼", "T^-1"): p += NEG_FTRT_Z(j)
        
                # If the gate is a SWAP gate, check if another one has been found before and perform the SWAP operation
                # If not, keep track of its location until we find the other SWAP gate
                elif current_gate in "SWAP":
                    if len(special_loc) == 1:
                        p += pqg.SWAP(special_loc[0], j)
                        special_loc = []
                    else:
                        special_loc.append(j)

                # If the gate is a CNOT gate, insert its pos into the list of special components at index 0 (the front)
                # If, after inserting the pos, the length of the special list is 2 (i.e. a control has already been found, and is at index 1)
                # perform the operation, clear the special list and the special gate type, else indicate that we have a special gate that's missing parts
                elif current_gate in "CNOT":
                    special_loc.insert(0, j)
                    if len(special_loc) == 2:
                        p += pqg.CNOT(special_loc[1], special_loc[0])
                        special_loc = []
                    else:
                        special_gate_type = "CNOT"

                # If the gate is a CCNOT gate, insert its pos into the list of special components at index 0 (the front)
                # If, after inserting the pos, the length of the special list is 3 (i.e. 2 controls has already been found, at index 1 & 2)
                # perform the operation, clear the special list and the special gate type, else indicate that we have a special gate that's missing parts
                elif current_gate in "CCNOT":
                    special_loc.insert(0, j)
                    if len(special_loc) == 3:
                        p += pqg.CCNOT(special_loc[2], special_loc[1], special_loc[0])
                        special_loc = []
                    else:
                        special_gate_type = "CCNOT"

                # If the gate is a CZ gate, insert its pos into the list of special components at index 0 (the front)
                # If, after inserting the pos, the length of the special list is 2 (i.e. a control has already been found, and is at index 1)
                # perform the operation, clear the special list and the special gate type, else indicate that we have a special gate that's missing parts
                elif current_gate in "CZ":
                    special_loc.insert(0, j)
                    if len(special_loc) == 2:
                        p += pqg.CZ(special_loc[1], special_loc[0])
                        special_loc = []
                    else:
                        special_gate_type = "CZ"

                # If a control is found, add it to the list of special components
                # If we have found a special gate and the required amount of controls, perform the operation & clear the special list and the special gate type
                elif current_gate in "•":
                    special_loc.append(j)
                    if special_gate_type not in "NULL":
                        if len(special_loc) == 2:
                            if special_gate_type in "CNOT": p += pqg.CNOT(special_loc[1], special_loc[0])
                            elif special_gate_type in "CZ": p += pqg.CZ(special_loc[1], special_loc[0])
                        elif len(special_loc) == 3: p += pqg.CCNOT(special_loc[2], special_loc[1], special_loc[0])
                        special_loc = []
                        special_gate_type = "NULL"
                    
        results = self.construct_results_dict(p)

        return results
     
    def construct_results_dict(self, qubit_program):
        wf_sim = WavefunctionSimulator()
        wavefunction = wf_sim.wavefunction(qubit_program)
        amp_arr = wavefunction.amplitudes
        prob_dict = wavefunction.get_outcome_probs()
        results_dict = {}
        i = 0
        for item in prob_dict:
            struct = {}
            # Integer value of the qubit state
            struct["int"] = "{:.0f}".format(int(item, 2))
            # Complex number representing the qubit state
            struct["val"] = "{:.5f}".format((round(amp_arr[i], 5))).strip("()")
            # Probability of obtaining the qubit state
            struct["prob"] = "{:.5f}".format(round(prob_dict[item], 5))
            # Magnitude of the qubit state
            struct["mag"] = "{:.5f}".format(round(abs(amp_arr[i]), 5))
            # Phase of the qubit state (obtained by measuring complex number phase, converting to °)
            struct["phase"] = self.format_phase(amp_arr[i])
            results_dict[item] = struct
            i = i + 1
        return results_dict

    def format_phase(self, amp):
        # If the phase is +ve, add a positive sign to string formatting
        sign = ""
        degrees = np.degrees(cmath.phase(amp))
        if degrees >= 0: sign = "+"
        return sign + "{:.2f}".format(round(degrees, 2)) + "°"

    def define_extra_gates(self, qubit_program):
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
        z_pow_gate = lambda p: np.array([[1, 0],[0, g(p)]])

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

