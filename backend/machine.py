"""Bounded quantum assembly interpreter. Never evaluates user code."""
import ast
import math
import operator
import re
import time
from pydantic import Field,model_validator
from .models import StrictModel,CircuitRequest,Gate,MAX_QUBITS,MAX_SHOTS

MACHINE_QUBITS=min(8,MAX_QUBITS)
MAX_STEPS=96

class MachineRequest(StrictModel):
    qubits:int=Field(default=3,ge=1,le=MACHINE_QUBITS)
    program:str=Field(default='H q0\nCX q0,q1\nMEASURE ALL',min_length=1,max_length=12000)
    shots:int=Field(default=1024,ge=128,le=MAX_SHOTS)
    seed:int=Field(default=42,ge=0,le=2**31-1)
    readout_error:float=Field(default=0,ge=0,le=.3)
    gate_error:float=Field(default=0,ge=0,le=.15)

    @model_validator(mode='after')
    def validate_program(self):
        compile_program(self.program,self.qubits)
        return self


def angle_value(expression):
    if not expression or len(expression)>64: raise ValueError('Use a bounded angle expression such as pi/2.')
    tree=ast.parse(expression,mode='eval')
    if sum(1 for _ in ast.walk(tree))>24: raise ValueError('Angle expression is too complex.')
    def value(node):
        if isinstance(node,ast.Expression): return value(node.body)
        if isinstance(node,ast.Name) and node.id=='pi': return math.pi
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):
            return float(node.value)
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
            return value(node.operand)*(1 if isinstance(node.op,ast.UAdd) else -1)
        if isinstance(node,ast.BinOp) and type(node.op) in (ast.Add,ast.Sub,ast.Mult,ast.Div):
            return {ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}[type(node.op)](value(node.left),value(node.right))
        raise ValueError('Angles support numbers, pi, +, -, *, / and parentheses only.')
    try: result=value(tree)
    except (OverflowError,ZeroDivisionError) as exc: raise ValueError('Angle must be finite; division by zero is not allowed.') from exc
    if not math.isfinite(result) or abs(result)>100*math.pi: raise ValueError('Angle exceeds ±100π radians.')
    return result


def compile_program(program,qubits):
    gates=[];instructions=[];measured=False
    for line_number,line in enumerate(program.splitlines(),1):
        line=re.split(r'//|#',line)[0]
        for raw in line.split(';'):
            text=raw.strip()
            if not text: continue
            try:
                lower=text.lower()
                if lower=='openqasm 2.0': continue
                if lower.startswith('include'):
                    if text!='include "qelib1.inc"': raise ValueError('Only the standard qelib1.inc header is supported.')
                    continue
                register=re.fullmatch(r'(?:qreg\s+q\[(\d+)\]|QREG\s+(\d+))',text)
                if register:
                    if int(register.group(1) or register.group(2))!=qubits: raise ValueError('Program register size must match the selected qubit count.')
                    continue
                classical=re.fullmatch(r'creg\s+c\[(\d+)\]',text)
                if classical:
                    if int(classical.group(1))!=qubits: raise ValueError('Classical register must match the quantum register size.')
                    continue
                if lower in ('measure all','measure q -> c'):
                    measured=True
                    instructions.append({'line':line_number,'text':'MEASURE ALL','gate':None})
                    continue
                measurement=re.fullmatch(r'measure\s+q\[(\d+)\]\s*->\s*c\[(\d+)\]',lower)
                if measurement:
                    if measurement.group(1)!=measurement.group(2) or int(measurement.group(1))>=qubits:
                        raise ValueError('Readout maps each q[i] to c[i].')
                    measured=True
                    instructions.append({'line':line_number,'text':text,'gate':None});continue
                if lower.startswith('barrier '):
                    # Barriers are non-executable scheduling annotations; validate every operand.
                    if not re.fullmatch(r'barrier\s+q\[\d+\](?:\s*,\s*q\[\d+\])*',lower): raise ValueError('Invalid barrier annotation.')
                    if any(int(x)>=qubits for x in re.findall(r'\[(\d+)\]',lower)): raise ValueError('Barrier qubit is out of range.')
                    continue
                if measured: raise ValueError('Measurements must be terminal. Snapshot stepping only executes unitary gates.')
                match=re.fullmatch(r'([A-Za-z]+)(?:\(([^()]*)\))?\s+(.*)',text)
                if not match: raise ValueError('Use H q0, CX q0,q1 or RY pi/2 q0.')
                name=match.group(1).upper();name={'CX':'CNOT','SDG':'SDG','TDG':'TDG'}.get(name,name)
                operands=match.group(3).strip();first=re.search(r'q(?:\[\d+\]|\d+)',operands)
                if not first: raise ValueError('Each operation requires a qubit such as q0.')
                angle=match.group(2) or operands[:first.start()].strip()
                qtext=operands[first.start():]
                if not re.fullmatch(r'q(?:\[\d+\]|\d+)(?:\s*,\s*q(?:\[\d+\]|\d+))*',qtext): raise ValueError('Separate qubit operands with commas.')
                qargs=[int(a or b) for a,b in re.findall(r'q(?:\[(\d+)\]|(\d+))',qtext)]
                arity=3 if name=='CCX' else 2 if name in ('CNOT','CZ','CP','SWAP') else 1
                if len(qargs)!=arity: raise ValueError(f'{name} needs {arity} qubit operand(s).')
                needs_angle=name in ('RX','RY','RZ','P','CP')
                if bool(angle)!=needs_angle: raise ValueError(f'{name} '+('requires an angle.' if needs_angle else 'does not take an angle.'))
                gate={'name':name,'target':qargs[-1]}
                if arity>=2: gate['control']=qargs[0]
                if arity==3: gate['control2']=qargs[1]
                if needs_angle: gate['angle']=angle_value(angle)
                parsed=Gate(**gate)
                CircuitRequest(qubits=qubits,gates=[parsed])
                gates.append(parsed);instructions.append({'line':line_number,'text':text,'gate':parsed.model_dump(exclude_none=True)})
                if len(gates)>MAX_STEPS or len(instructions)>MAX_STEPS:
                    raise ValueError(f'Program exceeds the {MAX_STEPS}-instruction debugger limit.')
            except (ValueError,SyntaxError) as exc:
                raise ValueError(f'Line {line_number}: {exc}') from exc
    if not instructions: raise ValueError('Add at least one quantum operation.')
    if len(instructions)>MAX_STEPS: raise ValueError(f'Program exceeds {MAX_STEPS} instructions.')
    return CircuitRequest(qubits=qubits,gates=gates),instructions


def run_machine(config:MachineRequest):
    from qiskit.quantum_info import Statevector
    from .quantum import circuit_from_config,inspect_state,execute_circuit
    start=time.perf_counter()
    parsed,instructions=compile_program(config.program,config.qubits)
    state=Statevector.from_int(0,2**config.qubits)
    snapshots=[{'step':0,'instruction':'INITIALIZE |0…0⟩',**inspect_state(state)}]
    for i,instruction in enumerate(instructions):
        if instruction['gate']:
            step_config=CircuitRequest(qubits=config.qubits,gates=[instruction['gate']])
            state=state.evolve(circuit_from_config(step_config))
        snapshots.append({'step':i+1,'instruction':instruction['text'],**inspect_state(state)})
    result=execute_circuit(circuit_from_config(parsed),config.shots,config.seed,config.readout_error,config.gate_error)
    return {**result,'kind':'machine','snapshots':snapshots,'instructions':instructions,
            'statevector_bytes':16*2**config.qubits,'runtime_s':time.perf_counter()-start,
            'program':config.program,'compiled_config':{**parsed.model_dump(),'shots':config.shots,'seed':config.seed,
                                                       'readout_error':config.readout_error,'gate_error':config.gate_error}}
