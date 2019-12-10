from qiskit import *
from qiskit.aqua.circuits.gates import cry

from qiskit.visualization import plot_histogram

import numpy as np
import random

import sys
import matplotlib.pyplot as plt

theta = 2*np.pi/3
thetaR = np.pi/4

fileNum = 30


# Devuelve el valor esperado de un circuito con un solo bit de registro
def getExpectedValue(qc, sim = Aer.get_backend('qasm_simulator') , shots=8192):
    job = execute(qc, sim, shots=shots)

    count = job.result().get_counts()
    a,b = [count[a]/shots if a in count else 0 for a in ['0','1']]
    return a-b

def printHistogram(qc, sim =  Aer.get_backend('qasm_simulator') , shots=8192):
    job = execute(qc, sim, shots=shots)
    return plot_histogram(job.result().get_counts())

# Devuelve la Gate time_Lapse que aplica una iteracion de paso de tiempo
# 
# Changed : Float que representa el valor en radianes del gate CRY
def getDecoherence(changed):
    decoherenceG = QuantumCircuit(2,1, name='decoherence')
    decoherenceG.ry(changed,1)
    decoherenceG.cx(0,1)
    decoherenceG.ry(-changed,1)
    decoherenceG.cx(0,1)
    decoherenceG.cx(1,0)
    decoherenceG.measure([1],[0])
    decoherenceG.reset(1)
    return decoherenceG

# Crea un circuito general de una Artificial Life de poblacion 1
#
# time    : Integer representando la cantidad de iteraciones
# initial : Float que representa los radiones de la gate U3 inicial
# changed : Float que representa los radianes de la gate CRY
# pop     : Integer representando la cantidad de poblacion que tendra el algoritmo
def getCircuit(pop=1,time=3, initial=theta, changed=theta, measure = True):
    decoherenceG = getDecoherence(changed).to_instruction()
    
    qc = QuantumCircuit(3*pop,pop)
    for i in range(pop):
        qc.u3(initial,0,0,i*3)
        qc.cx(i*3,i*3+1)
    qc.barrier()
    for i in range(0,time):
        #cry
        for j in range(pop):
            qc.append(decoherenceG, [j*3+1,j*3+2],[j])
        qc.barrier()
    if(measure):
        qc.measure([3*j+1 for j in range(pop)],[j for j in range(pop)])
    return qc


# Aumenta el la cantidad de capas de tiempo del circuito.
def addTimeLapse(qc,time,measure=False, changed = theta):
    decoherenceG = getDecoherence(changed).to_instruction()
    
    qBits = int(len(qc.qubits)/3)
    for i in range(0,time):
        #cry
        for j in range(qBits):
            qc.append(decoherenceG, [j*3+1,j*3+2],[j])
        qc.barrier()
    if(measure):
        qc.measure([3*j+1 for j in range(pop)],[j for j in range(pop)])
    


# Crea un escenario general de clonacion de poblacion asexual mediante clonacion exponencial
#
# time    : Integer representando la cantidad de iteraciones 
# pop     : Integer representando la cantidad de poblacion que tendra el algoritmo
# initial : Float que representa los radiones de la gate U3 inicial
# changed : Float que representa los radianes de la gate CRY
# mutationRate : Float que representa el ratio de mutacion
def getCircuitG(time=3, pop=2, initial=theta, changed=theta, mutationRate = 0, mutation=False):
    decoherenceG = getDecoherence(changed).to_instruction()
    
    qc = QuantumCircuit(3*pop,pop)
    qc.u3(initial,0,0,0)
    qc.cx(0,1)
    
    actPop = 1
    qc.barrier()
    for i in range(0,time):
        # Adding the Time_Lapse gates
        for j in range(0,actPop):
            qc.append(decoherenceG, [3*j+1,3*j+2],[j])
        qc.barrier()
        
        # Adding the new population
        actPopi = actPop
        for z in range(0,min(actPop, pop-actPop)):      
            qc.cx(3*z, 3*actPopi)
            if mutation:
                x = np.random.normal(loc=0, scale=mutationRate)
                qc.rx(x, 3*actPopi)
                y = np.random.normal(loc=0, scale=mutationRate)
                qc.ry(y, 3*actPopi)
                
            qc.cx(3*actPopi, 3*actPopi+1)
            qc.barrier()
            actPopi+=1
        actPop = actPopi
        
    qc.measure([3*j+1 for j in range(pop)],[j for j in range(pop)])
    return qc

# Crea un circuito general de una Artificial Life de poblacion 1 con un background customizado
#
# time    : Integer representando la cantidad de iteraciones
# initial : Float que representa los radiones de la gate U3 inicial
# changed : Float que representa los radianes de la gate CRY
# pop     : Integer representando la cantidad de poblacion que tendra el algoritmo
def getCircuitCB(pop=1,time=3, initial=theta, changed=theta, measure = True,
                 background_change=[np.pi/4,np.pi/8,np.pi/4], background_sign = [0,1,0]):
    
    
    qc = QuantumCircuit(3*pop,pop)
    for i in range(pop):
        qc.u3(initial,0,0,i*3)
        qc.cx(i*3,i*3+1)
    qc.barrier()

    for i in range(0,time):
        #cry
        for j in range(pop):
            decoherenceG = getDecoherence(background_change[i]).to_instruction()
            if(background_sign[i]==1):
                qc.x(j*3+1)
            qc.append(decoherenceG, [j*3+1,j*3+2],[j])
            if(background_sign[i]==1):
                qc.x(j*3+1)
        qc.barrier()
    if(measure):
        qc.measure([3*j+1 for j in range(pop)],[j for j in range(pop)])
    return qc


# Devuelve un circuito de un conjunto de individuos con reproduccion sexual
def getSexualCircuit():
    
    q=QuantumRegister(10)
    c=ClassicalRegister(2)
    qc=QuantumCircuit(q,c)

    qc.h(q[0])
    qc.cx(q[0],q[2])
    qc.h(q[3])
    qc.cx(q[3],q[5])
    qc.barrier()
    qc.cx(q[2],q[6])
    qc.cx(q[5],q[6])
    qc.barrier()
    qc.u3(np.pi/4,0,0,q[0])
    qc.cx(q[0],q[1])
    qc.u3(3*np.pi/4,0,0,q[3])
    qc.cx(q[3],q[4])
    qc.barrier()
    qc.h(q[8])
    qc.cu3(5*np.pi/2,0,0,q[0],q[8])
    qc.cu3(5*np.pi/2,0,0,q[3],q[8])
    qc.cx(q[8],q[7])
    qc.barrier()
    qc.x(q[6])
    qc.ccx(q[6],q[7],q[8])
    qc.x(q[6])
    qc.barrier()
    qc.cx(q[8],q[9])


    qc.measure(q[6],c[0])
    qc.measure(q[8],c[1])
    return qc

# Crea un circuito general de una Artificial Life de poblacion 1 con un background customizado
#
# time    : Integer representando la cantidad de iteraciones
# initial : Float que representa los radiones de la gate U3 inicial
# changed : Float que representa los radianes de la gate CRY
# pop     : Integer representando la cantidad de poblacion que tendra el algoritmo
def getCircuitCB(pop=1,time=3, initial=theta, changed=theta, measure = True,
                 background_change=[np.pi/4,np.pi/8,np.pi/4], background_sign = [0,1,0]):
    
    
    qc = QuantumCircuit(3*pop,pop)
    for i in range(pop):
        qc.u3(initial,0,0,i*3)
        qc.cx(i*3,i*3+1)
    qc.barrier()

    for i in range(0,time):
        #cry
        for j in range(pop):
            decoherenceG = getDecoherence(background_change[i]).to_instruction()
            if(background_sign[i]==1):
                qc.x(j*3+1)
            qc.append(decoherenceG, [j*3+1,j*3+2],[j])
            if(background_sign[i]==1):
                qc.x(j*3+1)
        qc.barrier()
    if(measure):
        qc.measure([3*j+1 for j in range(pop)],[j for j in range(pop)])
    return qc