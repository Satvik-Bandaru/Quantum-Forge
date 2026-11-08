import math
import os
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_QUBITS = min(12, max(2, int(os.getenv('QF_MAX_QUBITS', '12'))))
MAX_SHOTS = min(65536, max(128, int(os.getenv('QF_MAX_SHOTS', '8192'))))

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)

class Gate(StrictModel):
    name: Literal['X','Y','Z','H','RX','RY','RZ','CNOT','CZ','SWAP','M','S','SDG','T','TDG','P','CP','CCX']
    target: int = Field(ge=0)
    control: int | None = Field(default=None, ge=0)
    control2: int | None = Field(default=None, ge=0)
    angle: float = Field(default=math.pi/2, ge=-100*math.pi, le=100*math.pi)

class CircuitRequest(StrictModel):
    qubits: int = Field(default=2, ge=1, le=MAX_QUBITS)
    gates: list[Gate] = Field(default_factory=list, max_length=128)
    shots: int = Field(default=1024, ge=128, le=MAX_SHOTS)
    seed: int = Field(default=42, ge=0, le=2**31-1)
    readout_error: float = Field(default=0, ge=0, le=0.3)
    gate_error: float = Field(default=0, ge=0, le=0.15)

    @model_validator(mode='after')
    def valid_gates(self):
        measured = False
        for gate in self.gates:
            if gate.target >= self.qubits:
                raise ValueError('Gate target must be inside the circuit.')
            if measured and gate.name != 'M':
                raise ValueError('Measurements must be terminal; move gates before measurement.')
            if gate.name == 'M':
                measured = True
            if gate.name in ('CNOT','CZ','SWAP','CP','CCX'):
                if gate.control is None or gate.control >= self.qubits or gate.control == gate.target:
                    raise ValueError('Two-qubit gates need distinct valid control and target qubits.')
            elif gate.control is not None:
                raise ValueError('Only controlled gates and SWAP use a second qubit.')
            if gate.name=='CCX':
                if gate.control2 is None or gate.control2>=self.qubits or gate.control2 in (gate.target,gate.control):
                    raise ValueError('CCX needs three distinct valid qubits.')
            elif gate.control2 is not None:
                raise ValueError('Only CCX uses a third qubit.')
        return self

class OptimizationRequest(StrictModel):
    problem: Literal['maxcut','knapsack'] = 'maxcut'
    nodes: int = Field(default=5, ge=2, le=MAX_QUBITS)
    edges: list[tuple[int,int,int]] = Field(default_factory=lambda:[(0,1,1),(0,2,1),(1,2,1),(1,3,1),(2,4,1),(3,4,1)], max_length=66)
    weights: list[int] = Field(default_factory=lambda:[2,3,4,5], min_length=1, max_length=8)
    values: list[int] = Field(default_factory=lambda:[3,4,5,8], min_length=1, max_length=8)
    capacity: int = Field(default=7, ge=1, le=31)
    layers: int = Field(default=2, ge=1, le=4)
    iterations: int = Field(default=40, ge=5, le=150)
    shots: int = Field(default=1024, ge=128, le=MAX_SHOTS)
    seed: int = Field(default=42, ge=0, le=2**31-1)
    repetitions: int = Field(default=1, ge=1, le=3)

    @model_validator(mode='after')
    def valid_instance(self):
        if self.iterations < 2*self.layers+2:
            raise ValueError(f'QAOA with {self.layers} layers requires at least {2*self.layers+2} objective evaluations.')
        if self.problem == 'maxcut':
            if not self.edges:
                raise ValueError('Add at least one edge.')
            seen = set()
            for i,j,w in self.edges:
                edge = tuple(sorted((i,j)))
                if i == j or min(i,j)<0 or max(i,j)>=self.nodes or not 1<=w<=100:
                    raise ValueError('Edges require distinct nodes in range and integer weights 1–100.')
                if edge in seen:
                    raise ValueError('Duplicate undirected edges are not allowed.')
                seen.add(edge)
        else:
            if len(self.weights) != len(self.values):
                raise ValueError('Each item needs one weight and one value.')
            if any(not 1<=v<=100 for v in self.weights+self.values):
                raise ValueError('Item weights and values must be integers 1–100.')
            if len(self.weights)+self.capacity.bit_length()>MAX_QUBITS:
                raise ValueError(f'Items plus slack bits exceed the {MAX_QUBITS}-qubit safety limit. Reduce items or capacity.')
        return self

class SavedCircuit(StrictModel):
    name: str = Field(min_length=1, max_length=80)
    config: CircuitRequest
