# valor_bruto.py

def calcular_valor_bruto(valor_liquido, imposto_principal, lista_custos):
    soma_fixos_R = 0.0
    soma_perc = 0.0

    for c in lista_custos:
        valor = float(c["valor"])
        if c["tipo"] == "R$":
            soma_fixos_R += valor
        else:
            soma_perc += valor

    total_perc = float(imposto_principal) + soma_perc

    if total_perc >= 100:
        raise ValueError("A soma dos percentuais é >= 100%. Cálculo impossível.")

    bruto = (valor_liquido + soma_fixos_R) / (1 - total_perc / 100)

    detalhes = []

    # imposto principal
    detalhes.append({
        "descricao": f"Imposto Principal ({imposto_principal}%)",
        "valor": round(bruto * (imposto_principal / 100), 2),
        "tipo": "%"
    })

    # demais custos
    for c in lista_custos:
        if c["tipo"] == "%":
            v = bruto * (c["valor"] / 100)
        else:
            v = c["valor"]

        detalhes.append({
            "descricao": c["descricao"],
            "valor": round(v, 2),
            "tipo": c["tipo"]
        })

    liquido_final = bruto - sum([d["valor"] for d in detalhes])

    return {
        "valor_bruto": round(bruto, 2),
        "liquido_final": round(liquido_final, 2),
        "detalhes": detalhes
    }


def calcular_valor_bruto_from_input(data):
    valor_liquido = float(str(data.get("valor_liquido", "0")).replace(",", "."))
    imposto_principal = float(str(data.get("imposto_principal", "0")).replace(",", "."))

    custos_raw = data.get("custos", [])
    custos = []

    for c in custos_raw:
        custos.append({
            "descricao": c["descricao"],
            "tipo": c["tipo"],
            "valor": float(str(c["valor"]).replace(",", "."))
        })

    return calcular_valor_bruto(valor_liquido, imposto_principal, custos)
