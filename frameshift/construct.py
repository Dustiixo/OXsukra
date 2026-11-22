"""Language/algebra construction workbench: deterministic tools, explicit hypotheses."""
from __future__ import annotations
import ast, re, string
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Any

WORD_RE = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?|\d+(?:\.\d+)?|[^\w\s]", re.UNICODE)

@dataclass
class Candidate:
    operation: str
    result: Any
    rationale: str
    confidence: str = "candidate—not proof"

    def as_dict(self): return asdict(self)

def words(text: str) -> list[str]:
    return [x for x in WORD_RE.findall(text) if re.fullmatch(r"[A-Za-z]+(?:['’][A-Za-z]+)?", x)]

def alpha_value(word: str) -> int:
    """A1Z26 sum, ignoring non-ASCII letters; labelled as one possible convention."""
    return sum(ord(c.lower()) - 96 for c in word if 'a' <= c.lower() <= 'z')

def caesar(text: str, shift: int) -> str:
    out=[]
    for c in text:
        if 'a' <= c <= 'z': out.append(chr((ord(c)-97+shift)%26+97))
        elif 'A' <= c <= 'Z': out.append(chr((ord(c)-65+shift)%26+65))
        else: out.append(c)
    return ''.join(out)

def analyze_text(text: str) -> dict[str, Any]:
    toks = words(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    initials = ''.join(w[0] for w in toks if w)
    line_initials = ''.join(next((c for c in line if c.isalpha()), '') for line in lines)
    candidates=[]
    if line_initials and len(lines) >= 2:
        candidates.append(Candidate('line-initials', line_initials, 'Initial letter of each non-empty line; useful only if line breaks are meaningful.'))
    if len(toks) >= 2:
        candidates.append(Candidate('word-initials', initials, 'Initial letter of each word; common acrostic/transposition probe.'))
        candidates.append(Candidate('word-lengths', [len(re.sub(r"[^A-Za-z]", "", w)) for w in toks], 'Word lengths as a numeric sequence; punctuation is ignored.'))
        candidates.append(Candidate('A1Z26-word-sums', [{'word':w,'sum':alpha_value(w)} for w in toks], 'A=1…Z=26 letter sums; one convention among many.'))
        repeated = {w.lower():n for w,n in Counter(toks).items() if n > 1}
        if repeated: candidates.append(Candidate('repetition-patterns', repeated, 'Repeated words may mark emphasis, structure, or a key; repetition alone proves nothing.'))
    candidates.append(Candidate('tokenization', toks, 'Lexical segmentation under a simple English-oriented tokenizer; not a full linguistic parse.'))
    return {'input':text,'word_count':len(toks),'unique_word_count':len(set(w.lower() for w in toks)),'line_count':len(lines),'candidates':[c.as_dict() for c in candidates], 'warning':'These are generated hypotheses, not evidence of a hidden message. Validate against context, controls, and alternatives.'}

def caesar_sweep(text: str) -> list[dict[str, Any]]:
    # Exhaustively return every shift; do not pretend to know which output is meaningful.
    return [{'shift':s,'text':caesar(text,s)} for s in range(1,26)]

class LinearExpr:
    """Represent a linear expression as coefficient*x + constant using safe AST parsing."""
    def __init__(self, variable: str): self.variable=variable
    def parse(self, text: str) -> tuple[float,float]:
        node=ast.parse(text, mode='eval').body
        return self._node(node)
    def _node(self,n):
        if isinstance(n, ast.Constant) and isinstance(n.value,(int,float)): return (0.0,float(n.value))
        if isinstance(n, ast.Name) and n.id==self.variable: return (1.0,0.0)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            a,b=self._node(n.operand); return (-a,-b)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.UAdd): return self._node(n.operand)
        if isinstance(n, ast.BinOp):
            a,b=self._node(n.left); c,d=self._node(n.right)
            if isinstance(n.op, ast.Add): return (a+c,b+d)
            if isinstance(n.op, ast.Sub): return (a-c,b-d)
            if isinstance(n.op, ast.Mult):
                if a and c: raise ValueError('Nonlinear multiplication is not supported.')
                return (a*d+c*b,b*d)
            if isinstance(n.op, ast.Div):
                if c: raise ValueError('Division by an expression containing the variable is nonlinear.')
                if d==0: raise ValueError('Division by zero.')
                return (a/d,b/d)
        raise ValueError('Only numbers, the chosen variable, parentheses, +, -, *, and / are supported.')

def solve_linear(equation: str, variable: str='x') -> dict[str, Any]:
    if equation.count('=') != 1: raise ValueError('Enter exactly one equals sign, e.g. 2*(x+3)=14.')
    left,right=equation.split('=')
    parser=LinearExpr(variable)
    a,b=parser.parse(left); c,d=parser.parse(right)
    coeff=a-c; rhs=d-b
    if abs(coeff)<1e-12:
        status='infinite_solutions' if abs(rhs)<1e-12 else 'no_solution'
        return {'equation':equation,'variable':variable,'status':status,'solution':None,'verification':'Equation reduces to a constant identity or contradiction.'}
    x=rhs/coeff
    # Direct substitution via linear forms provides a simple numeric check.
    lhs=a*x+b; rvalue=c*x+d
    return {'equation':equation,'variable':variable,'status':'solved','solution':x,'verification':{'left_value':lhs,'right_value':rvalue,'equal_within_tolerance':abs(lhs-rvalue)<1e-9},'derivation':{'left_form':f'{a}*{variable} + {b}','right_form':f'{c}*{variable} + {d}','rearranged_coefficient':coeff,'rearranged_constant':rhs}}

def solve_construct(text: str) -> dict[str, Any]:
    """Run a small transparent bank of transformations against text clues."""
    report=analyze_text(text)
    candidates=report['candidates']
    if len(text.splitlines()) > 1:
        candidates.extend({'operation':'line-caesar-shift','shift':s,'result':caesar(''.join(next((c for c in line if c.isalpha()), '') for line in text.splitlines() if line.strip()),s),'confidence':'candidate—not proof'} for s in range(1,26))
    compact=''.join(c for c in text if c.isalpha())
    if compact:
        candidates.append(Candidate('reverse-letters',compact[::-1],'Tests a simple reversal; usually needs a contextual reason.').as_dict())
    return {'task':'construct-solving','analysis':report,'transformation_candidates':candidates,'next_step':'Choose a candidate based on an explicit clue or constraint, then test it against a control text and competing transformations.'}
