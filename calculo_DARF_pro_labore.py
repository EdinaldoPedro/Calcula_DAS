# Tabela do Imposto de Renda (baseada na sua imagem)
# Cada tupla contém: (limite_superior, aliquota, parcela_a_deduzir)
TABELA_IRPF = [
    (2428.80, 0.0, 0.0),
    (2826.65, 0.075, 182.16),
    (3751.05, 0.15, 394.16),
    (4664.68, 0.225, 675.49),
    # Para valores acima do último limite
    (float('inf'), 0.275, 908.73)
]

# Dados de referência (usando valores de 2024/2025 como base)
PISO_PRO_LABORE = 1510.00
PERCENTUAL_FATOR_R = 0.28
ALIQUOTA_INSS = 0.11
TETO_INSS = 7786.02  # Teto de contribuição do INSS em 2024
INSS_MAXIMO = TETO_INSS * ALIQUOTA_INSS # Valor máximo da contribuição INSS


def calcular_darf_pro_labore(faturamento_mensal: float):
    """
    Calcula o Pró-labore, INSS e o DARF de IRPF com base no faturamento mensal.
    
    Args:
        faturamento_mensal: O valor do faturamento bruto da empresa no mês.
        
    Returns:
        Um dicionário com todos os valores calculados.
    """
    
    # --- Passo 1: Calcular o Pró-labore ---
    pro_labore_calculado = faturamento_mensal * PERCENTUAL_FATOR_R
    pro_labore = max(pro_labore_calculado, PISO_PRO_LABORE)
    
    # --- Passo 2: Calcular o INSS sobre o Pró-labore ---
    inss_descontado = pro_labore * ALIQUOTA_INSS
    inss_descontado = min(inss_descontado, INSS_MAXIMO)
    
    # --- Passo 3: Calcular a base para o Imposto de Renda ---
    base_calculo_irpf = pro_labore - inss_descontado
    
    # --- Passo 4: Calcular o DARF de IRPF usando a tabela ---
    darf_irpf = 0.0
    for limite, aliquota, deducao in TABELA_IRPF:
        if base_calculo_irpf <= limite:
            darf_irpf = (base_calculo_irpf * aliquota) - deducao
            break
            
    darf_irpf = max(0.0, darf_irpf)

    # --- Passo 5: Somar os tributos (INSS + IR) ---
    total_a_recolher = inss_descontado + darf_irpf

    return {
        "Faturamento Mensal": faturamento_mensal,
        "Pró-labore (Base de Cálculo)": pro_labore,
        "Contribuição INSS (11%)": inss_descontado,
        "Base para Cálculo do IRPF": base_calculo_irpf,
        "Imposto de Renda (DARF)": darf_irpf,
        "Total a Recolher (INSS + IR)": total_a_recolher
    }

# --- Execução do Programa ---
if __name__ == "__main__":
    try:
        faturamento_input = float(input("Digite o seu faturamento mensal: R$ "))
        
        resultado = calcular_darf_pro_labore(faturamento_input)
        
        print("\n--- Resultado do Cálculo ---")
        # Imprime todos os itens, exceto o último (o total)
        itens_resultado = list(resultado.items())
        for chave, valor in itens_resultado[:-1]:
            print(f"{chave}: R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        print("--------------------------")
        # Imprime o último item (o total) em destaque
        chave_total, valor_total = itens_resultado[-1]
        print(f"✅ {chave_total}: R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    except ValueError:
        print("Erro: Por favor, insira um número válido para o faturamento.")