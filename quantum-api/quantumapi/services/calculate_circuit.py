import numpy as np
import json
from pyquil import Program, get_qc
from pyquil.gates import *
from pyquil.api import WavefunctionSimulator


class calculate_circuit():

    def __init__(self, data):
        self.data = data

    def calculate(self):

        p = Program()

        # get JSON, load the data from the string (convert to dictionary), assign to ops
        ops = json.loads(self.data["circuit_input"])
        # length of eps = number of columns
        collenth = len(ops)
        numqubits = 0
        # max length of any number of operations per column = number of qubits used
        for i in ops:
            if (len(i) > numqubits): numqubits = len(i)
        # loops over each gate in ops and applies the gate
        for i in range(collenth):
            # stores what type of special gate it is (CNOT, CCNOT, CZ, etc)
            specialgatetype = "NULL"
            # keeps track of where special components are (i.e. controls, or SWAP)
            specialloc = []

            for j in range(len(ops[i])):
                currentgate = str(ops[i][j]).upper()

                # If the gate is X, Y, Z or H, apply the gate to qubit #j
                if (currentgate=="H"): p += H(j)
                elif (currentgate=="X"): p += X(j)
                elif (currentgate=="Y"): p += Y(j)
                elif (currentgate=="Z"): p += Z(j)
               
                # If the gate is a quarter turn (+/- 90 deg or pi/2) for X, Y or Z, apply the respective gate
                elif (currentgate=="X^1/2" or currentgate=="X^½"): p += RX(np.pi/2, j)
                elif (currentgate=="X^-1/2" or currentgate=="X^-½"): p += RX(-np.pi/2, j)
                elif (currentgate=="Y^1/2" or currentgate=="Y^½"): p += RY(np.pi/2, j)
                elif (currentgate=="Y^-1/2" or currentgate=="Y^-½"): p += RY(-np.pi/2, j)
                elif (currentgate=="Z^1/2" or currentgate=="S" or currentgate=="Z^½"): p += RZ(np.pi/2, j)
                elif (currentgate=="Z^-1/2" or currentgate=="S^-1" or currentgate=="Z^-½"): p += RZ(-np.pi/2, j)

                # If the gate is an eighth turn (+/- 45 deg or pi/4) for X, Y or Z, apply the respective gate
                elif (currentgate=="X^1/4" or currentgate=="X^¼"): p += RX(np.pi/4, j)
                elif (currentgate=="X^-1/4" or currentgate=="X^-¼"): p += RX(-np.pi/4, j)
                elif (currentgate=="Y^1/4" or currentgate=="Y^¼"): p += RY(np.pi/4, j)
                elif (currentgate=="Y^-1/4" or currentgate=="Y^-¼"): p += RY(-np.pi/4, j)
                elif (currentgate=="Z^1/4" or currentgate=="T" or currentgate=="Z^¼"): p += RZ(np.pi/4, j)
                elif (currentgate=="Z^-1/4" or currentgate=="T^-1" or currentgate=="Z^-¼"): p += RZ(-np.pi/4, j)
        
                # If the gate is a SWAP gate, check if another one has been found before and perform the SWAP operation
                # If not, keep track of its location until we find the other SWAP gate
                elif (currentgate=="SWAP"):
                    if(len(specialloc)==1):
                        p += SWAP(specialloc[0],j)
                        specialloc = []
                    else:
                        specialloc.append(j)

                # If the gate is a CNOT gate, insert its pos into the list of special components at index 0 (the front)
                # If, after inserting the pos, the length of the special list is 2 (i.e. a control has already been found, and is at index 1)
                # perform the operation, clear the special list and the special gate type, else indicate that we have a special gate that's missing parts
                elif (currentgate=="CNOT"):
                    specialloc.insert(0, j)
                    if(len(specialloc)==2):
                        p += CNOT(specialloc[1], specialloc[0])
                        specialloc = []
                    else:
                        specialgatetype = "CNOT"

                # If the gate is a CCNOT gate, insert its pos into the list of special components at index 0 (the front)
                # If, after inserting the pos, the length of the special list is 3 (i.e. 2 controls has already been found, at index 1 & 2)
                # perform the operation, clear the special list and the special gate type, else indicate that we have a special gate that's missing parts
                elif (currentgate=="CCNOT"):
                    specialloc.insert(0, j)
                    if(len(specialloc)==3):
                        p += CCNOT(specialloc[2],specialloc[1], specialloc[0])
                        specialloc = []
                    else:
                        specialgatetype = "CCNOT"

                # If the gate is a CZ gate, insert its pos into the list of special components at index 0 (the front)
                # If, after inserting the pos, the length of the special list is 2 (i.e. a control has already been found, and is at index 1)
                # perform the operation, clear the special list and the special gate type, else indicate that we have a special gate that's missing parts
                elif (currentgate=="CZ"):
                    specialloc.insert(0, j)
                    if(len(specialloc)==2):
                        p += CZ(specialloc[1], specialloc[0])
                        specialloc = []
                    else:
                        specialgatetype = "CNOT"

                # If a control is found, add it to the list of special components
                # If we have found a special gate and the required amount of controls, perform the operation & clear the special list and the special gate type
                elif (currentgate=="•"): 
                    specialloc.append(j)
                    if (specialgatetype!="NULL"):
                        if (len(specialloc)==2):
                            if (specialgatetype=="CNOT"): p += CNOT(specialloc[1], specialloc[0])
                            elif (specialgatetype=="CZ"): p += CZ(specialloc[1], specialloc[0])
                        elif (len(specialloc)==3): p += CCNOT(specialloc[2],specialloc[1], specialloc[0])
                        specialloc = []
                        specialgatetype = "NULL"
                    
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
            # The phase of the qubit state
            # struct["phase"] = ...
            out[item] = struct
            i = i + 1

        return out
     