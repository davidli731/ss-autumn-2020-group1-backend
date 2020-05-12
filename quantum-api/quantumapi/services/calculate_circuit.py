import numpy as np
import cmath
import json
from pyquil import Program, get_qc
from pyquil.gates import *
from pyquil.api import WavefunctionSimulator


class calculate_circuit():

    def __init__(self, data):
        self.data = data

    def calculate(self):

        p = Program()

        # get JSON, load the data from the string (convert to dictionary), assign to circuit
        try:
            circuit = json.loads(self.data["circuit_input"])
        except:
            circuit = self.data["circuit_input"]
        # length of circuit = number of columns
        col_length = len(circuit)
        num_qubits = 0
        # max length of any number of operations per column = number of qubits used
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
                if current_gate in "H": p += H(j)
                elif current_gate in "X": p += X(j)
                elif current_gate in "Y": p += Y(j)
                elif current_gate in "Z": p += Z(j)
               
                # If the gate is a quarter turn (+/- 90 deg or pi/2) for X, Y or Z, apply the respective gate
                elif current_gate in ("X^1/2", "X^½"): p += RX(np.pi/2, j)
                elif current_gate in ('X^-1/2', 'X^-½'): p += RX(-np.pi/2, j)
                elif current_gate in ("Y^1/2", "Y^½"): p += RY(np.pi/2, j)
                elif current_gate in ("Y^-1/2", "Y^-½"): p += RY(-np.pi/2, j)
                elif current_gate in ("Z^1/2", "Z^½", "S"): p += RZ(np.pi/2, j)
                elif current_gate in ("Z^-1/2", "Z^-½", "S^-1"): p += RZ(-np.pi/2, j)

                # If the gate is an eighth turn (+/- 45 deg or pi/4) for X, Y or Z, apply the respective gate
                elif current_gate in ("X^1/4", "X^¼"): p += RX(np.pi/4, j)
                elif current_gate in ("X^-1/4", "X^-¼"): p += RX(-np.pi/4, j)
                elif current_gate in ("Y^1/4", "Y^¼"): p += RY(np.pi/4, j)
                elif current_gate in ("Y^-1/4", "Y^-¼"): p += RY(-np.pi/4, j)
                elif current_gate in ("Z^1/4", "Z^¼", "T"): p += RZ(np.pi/4, j)
                elif current_gate in ("Z^-1/4", "Z^-¼", "T^-1"): p += RZ(-np.pi/4, j)
        
                # If the gate is a SWAP gate, check if another one has been found before and perform the SWAP operation
                # If not, keep track of its location until we find the other SWAP gate
                elif current_gate in "SWAP":
                    if len(special_loc) == 1:
                        p += SWAP(special_loc[0], j)
                        special_loc = []
                    else:
                        special_loc.append(j)

                # If the gate is a CNOT gate, insert its pos into the list of special components at index 0 (the front)
                # If, after inserting the pos, the length of the special list is 2 (i.e. a control has already been found, and is at index 1)
                # perform the operation, clear the special list and the special gate type, else indicate that we have a special gate that's missing parts
                elif current_gate in "CNOT":
                    special_loc.insert(0, j)
                    if len(special_loc) == 2:
                        p += CNOT(special_loc[1], special_loc[0])
                        special_loc = []
                    else:
                        special_gate_type = "CNOT"

                # If the gate is a CCNOT gate, insert its pos into the list of special components at index 0 (the front)
                # If, after inserting the pos, the length of the special list is 3 (i.e. 2 controls has already been found, at index 1 & 2)
                # perform the operation, clear the special list and the special gate type, else indicate that we have a special gate that's missing parts
                elif current_gate in "CCNOT":
                    special_loc.insert(0, j)
                    if len(special_loc) == 3:
                        p += CCNOT(special_loc[2], special_loc[1], special_loc[0])
                        special_loc = []
                    else:
                        special_gate_type = "CCNOT"

                # If the gate is a CZ gate, insert its pos into the list of special components at index 0 (the front)
                # If, after inserting the pos, the length of the special list is 2 (i.e. a control has already been found, and is at index 1)
                # perform the operation, clear the special list and the special gate type, else indicate that we have a special gate that's missing parts
                elif current_gate in "CZ":
                    special_loc.insert(0, j)
                    if len(special_loc) == 2:
                        p += CZ(special_loc[1], special_loc[0])
                        special_loc = []
                    else:
                        special_gate_type = "CZ"

                # If a control is found, add it to the list of special components
                # If we have found a special gate and the required amount of controls, perform the operation & clear the special list and the special gate type
                elif current_gate in "•": 
                    special_loc.append(j)
                    if special_gate_type not in "NULL":
                        if len(special_loc) == 2:
                            if special_gate_type in "CNOT": p += CNOT(special_loc[1], special_loc[0])
                            elif special_gate_type in "CZ": p += CZ(special_loc[1], special_loc[0])
                        elif len(special_loc) == 3: p += CCNOT(special_loc[2],special_loc[1], special_loc[0])
                        special_loc = []
                        special_gate_type = "NULL"
                    
        wf_sim = WavefunctionSimulator()
        wavefunction = wf_sim.wavefunction(p)
        amp_arr = wavefunction.amplitudes
        prob_dict = wavefunction.get_outcome_probs()

        out = {}
        i = 0
        for item in prob_dict:
            struct = {}
            # The integer value of the qubit state
            struct["int"] = "{:.0f}".format(int(item, 2))
            # The complex number representing the qubit state
            struct["val"] = "{:.5f}".format((round(amp_arr[i], 5))).strip("()")
            # The probability of obtaining the qubit state
            struct["prob"] = "{:.5f}".format(round(prob_dict[item], 5))
            # The magnitude of the qubit state
            struct["mag"] = "{:.5f}".format(round(abs(amp_arr[i]), 5))
            # The phase of the qubit state (obtained by measuring phase of the complex number and converting to)
            struct["phase"] = "{:.5f}".format(round(np.degrees(cmath.phase(amp_arr[i])), 5))
            out[item] = struct
            i = i + 1

        return out
     