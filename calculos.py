# calculos.py

def soma(a: float, b: float) -> float:
    """Retorna a soma entre dois números."""
    return a + b

def subtracao(a: float, b: float) -> float:
    """Retorna a diferença entre dois números."""
    return a - b

def multiplicacao(a: float, b: float) -> float:
    """Retorna o produto entre dois números."""
    return a * b

def divisao(a: float, b: float) -> float:
    """Retorna o quociente entre dois números."""
    if b == 0:
        return float("inf")  # evita erro de divisão por zero
    return a / b
