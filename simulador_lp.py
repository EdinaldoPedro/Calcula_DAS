# simulador_lp.py
# Simulador de Lucro Presumido - Cálculo de Impostos proporcionais à NFS-e
def calcula_imposto(valor_nfse, faturamento_mensal, natureza_exportacao, aliquota_iss_percentual):
    """
    valor_nfse: valor da nota emitida
    faturamento_mensal: faturamento total mensal
    natureza_exportacao: 1 = operação normal | 2 = exportação de serviços
    aliquota_iss_percentual: valor entre 2 e 5 (%)
    """

    # Aliquotas fixas do Lucro Presumido (PIS e COFINS)
    aliquota_pis = 0.0065
    aliquota_cofins = 0.03
    aliquota_iss = aliquota_iss_percentual / 100

    # Isenções em caso de exportação
    if natureza_exportacao == 2:
        pis_valor = 0.0
        cofins_valor = 0.0
        iss_valor = 0.0
    else:
        pis_valor = valor_nfse * aliquota_pis
        cofins_valor = valor_nfse * aliquota_cofins
        iss_valor = valor_nfse * aliquota_iss

    # Base de cálculo presumida IRPJ/CSLL (32% do faturamento)
    base_irpj_csll = faturamento_mensal * 0.32

    # Totais mensais sobre a base presumida
    csll_mensal_total = base_irpj_csll * 0.09
    irpj_mensal_total = base_irpj_csll * 0.15

    # IRPJ adicional (10% sobre o que exceder R$ 20.000/mês)
    deducao_irpj_adicional = 20000
    if base_irpj_csll > deducao_irpj_adicional:
        base_irpj_adicional = base_irpj_csll - deducao_irpj_adicional
        irpj_adicional_mensal_total = base_irpj_adicional * 0.10
    else:
        irpj_adicional_mensal_total = 0.0

    # Proporção da nota sobre o faturamento
    proporcao_nfse = valor_nfse / faturamento_mensal if faturamento_mensal > 0 else 0.0

    # Impostos proporcionais à nota (valores)
    csll_valor = csll_mensal_total * proporcao_nfse
    irpj_valor = irpj_mensal_total * proporcao_nfse
    irpj_adicional_valor = irpj_adicional_mensal_total * proporcao_nfse

    # Calcular alíquotas efetivas sobre a NFS-e (em %)
    def pct_eff(valor_imposto):
        return (valor_imposto / valor_nfse * 100) if valor_nfse > 0 else 0.0

    pis_pct = pct_eff(pis_valor)
    cofins_pct = pct_eff(cofins_valor)
    iss_pct = pct_eff(iss_valor)
    csll_pct = pct_eff(csll_valor)
    irpj_pct = pct_eff(irpj_valor)
    irpj_ad_pct = pct_eff(irpj_adicional_valor)

        # Soma total das alíquotas efetivas
        # Soma total das alíquotas efetivas
    aliquota_total = pis_pct + cofins_pct + iss_pct + csll_pct + irpj_pct + irpj_ad_pct

    # Total de tributos em reais
    total_tributos = pis_valor + cofins_valor + iss_valor + csll_valor + irpj_valor + irpj_adicional_valor

    # Resultado formatado (sem linha separada de alíquota total)
    resultado = {
        f"COFINS ({cofins_pct:.2f}%)": cofins_valor,
        f"CSLL ({csll_pct:.2f}%)": csll_valor,
        f"IRPJ ({irpj_pct:.2f}%)": irpj_valor,
        f"IRPJ Adicional ({irpj_ad_pct:.2f}%)": irpj_adicional_valor,
        f"ISS ({iss_pct:.2f}%)": iss_valor,
        f"PIS ({pis_pct:.2f}%)": pis_valor,
        f"Total Tributos da Nota ({aliquota_total:.2f}%)": total_tributos
    }

    return resultado


# ==============================
# Execução direta via terminal
# ==============================
if __name__ == "__main__":
    print("=== Simulador Lucro Presumido ===")

    faturamento_mensal = float(input("Informe o faturamento mensal total (R$): ").replace(",", "."))
    valor_nfse = float(input("Informe o valor da NFS-e (R$): ").replace(",", "."))
    natureza_exportacao = int(input("Natureza da operação (1 = normal, 2 = exportação): "))

    if natureza_exportacao == 1:
        aliquota_iss_percentual = float(input("Informe a alíquota do ISS (% de 2 a 5): ").replace(",", "."))
    else:
        aliquota_iss_percentual = 0.0

    resultado = calcula_imposto(valor_nfse, faturamento_mensal, natureza_exportacao, aliquota_iss_percentual)

    print("\n--- Resultado do Cálculo ---")
    for chave, valor in resultado.items():
        # formata valores em padrão BR (vírgula como decimal)
        print(f"{chave}: R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
