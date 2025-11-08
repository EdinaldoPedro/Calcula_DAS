#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Versão adaptada: recebe entrada via JSON (param --input ou --file).
Mantém a lógica de fator-R (quando informada no JSON como "optante_fator_r": 1),
aplica isenção de PIS/COFINS/ISS quando exportacao_servico == 1.
Base original e dados mantidos (origem: seu arquivo anterior). :contentReference[oaicite:1]{index=1}
"""

import sys
import json
import argparse

# --- ESTRUTURA DE DADOS CENTRALIZADA (mantida) ---
DADOS_DOS_ANEXOS = {
    1: {"nome": "Anexo I (Comércio)", "aliquotas": [4.0, 7.3, 9.5, 10.7, 14.3, 19.0],
        "deducoes": [0, 5940, 13860, 22500, 87300, 378000]},
    2: {"nome": "Anexo II (Indústria)", "aliquotas": [4.5, 7.8, 10.0, 11.2, 14.7, 30.0],
        "deducoes": [0, 5940, 13860, 22500, 85500, 720000]},
    3: {"nome": "Anexo III (Serviços)", "aliquotas": [6.0, 11.2, 13.5, 16.0, 21.0, 33.0],
        "deducoes": [0, 9360, 17640, 35640, 125640, 648000]},
    4: {"nome": "Anexo IV (Serviços)", "aliquotas": [4.5, 9.0, 10.2, 14.0, 22.0, 33.0],
        "deducoes": [0, 8100, 12420, 39780, 183780, 828000]},
    5: {"nome": "Anexo V (Serviços)", "aliquotas": [15.5, 18.0, 19.5, 20.5, 23.0, 30.5],
        "deducoes": [0, 4500, 9900, 17100, 62100, 540000]}
}

LIMITES_DAS_FAIXAS = [180000, 360000, 720000, 1800000, 3600000, 4800000]

reparticao_simples_nacional = {
    "Anexo I": [
        {'faixa': 1, 'rbt12_max': 180000.00, 'IRPJ': 5.50, 'CSLL': 3.50, 'COFINS': 12.74, 'PIS/Pasep': 2.76, 'CPP': 41.50, 'ICMS': 34.00},
        {'faixa': 2, 'rbt12_max': 360000.00, 'IRPJ': 5.50, 'CSLL': 3.50, 'COFINS': 12.74, 'PIS/Pasep': 2.76, 'CPP': 41.50, 'ICMS': 34.00},
        {'faixa': 3, 'rbt12_max': 720000.00, 'IRPJ': 5.50, 'CSLL': 3.50, 'COFINS': 12.74, 'PIS/Pasep': 2.76, 'CPP': 42.00, 'ICMS': 33.50},
        {'faixa': 4, 'rbt12_max': 1800000.00, 'IRPJ': 5.50, 'CSLL': 3.50, 'COFINS': 12.74, 'PIS/Pasep': 2.76, 'CPP': 42.00, 'ICMS': 33.50},
        {'faixa': 5, 'rbt12_max': 3600000.00, 'IRPJ': 13.50, 'CSLL': 10.00, 'COFINS': 28.27, 'PIS/Pasep': 6.13, 'CPP': 42.10, 'ICMS': 0.00},
        {'faixa': 6, 'rbt12_max': 4800000.00, 'IRPJ': 13.50, 'CSLL': 10.00, 'COFINS': 28.27, 'PIS/Pasep': 6.13, 'CPP': 42.10, 'ICMS': 0.00}
    ],
    "Anexo II": [
        {'faixa': 1, 'rbt12_max': 180000.00, 'IRPJ': 5.50, 'CSLL': 3.50, 'COFINS': 12.74, 'PIS/Pasep': 2.76, 'CPP': 37.50, 'IPI': 38.00},
        {'faixa': 2, 'rbt12_max': 360000.00, 'IRPJ': 5.50, 'CSLL': 3.50, 'COFINS': 12.74, 'PIS/Pasep': 2.76, 'CPP': 37.50, 'IPI': 38.00},
        {'faixa': 3, 'rbt12_max': 720000.00, 'IRPJ': 5.50, 'CSLL': 3.50, 'COFINS': 13.57, 'PIS/Pasep': 2.93, 'CPP': 37.00, 'IPI': 37.50},
        {'faixa': 4, 'rbt12_max': 1800000.00, 'IRPJ': 5.50, 'CSLL': 3.50, 'COFINS': 13.57, 'PIS/Pasep': 2.93, 'CPP': 37.00, 'IPI': 37.50},
        {'faixa': 5, 'rbt12_max': 3600000.00, 'IRPJ': 13.50, 'CSLL': 10.00, 'COFINS': 28.27, 'PIS/Pasep': 6.13, 'CPP': 42.10, 'IPI': 0.00},
        {'faixa': 6, 'rbt12_max': 4800000.00, 'IRPJ': 13.50, 'CSLL': 10.00, 'COFINS': 28.27, 'PIS/Pasep': 6.13, 'CPP': 42.10, 'IPI': 0.00}
    ],
    "Anexo III": [
        {'faixa': 1, 'rbt12_max': 180000.00, 'IRPJ': 4.00, 'CSLL': 3.50, 'COFINS': 12.82, 'PIS/Pasep': 2.78, 'CPP': 43.40, 'ISS': 33.50},
        {'faixa': 2, 'rbt12_max': 360000.00, 'IRPJ': 4.00, 'CSLL': 3.50, 'COFINS': 14.05, 'PIS/Pasep': 3.05, 'CPP': 43.40, 'ISS': 32.00},
        {'faixa': 3, 'rbt12_max': 720000.00, 'IRPJ': 4.00, 'CSLL': 3.50, 'COFINS': 13.64, 'PIS/Pasep': 2.96, 'CPP': 43.40, 'ISS': 32.50},
        {'faixa': 4, 'rbt12_max': 1800000.00, 'IRPJ': 4.00, 'CSLL': 3.50, 'COFINS': 13.64, 'PIS/Pasep': 2.96, 'CPP': 43.40, 'ISS': 32.50},
        {'faixa': 5, 'rbt12_max': 3600000.00, 'IRPJ': 4.00, 'CSLL': 3.50, 'COFINS': 12.82, 'PIS/Pasep': 2.78, 'CPP': 43.40, 'ISS': 33.50},
        {'faixa': 6, 'rbt12_max': 4800000.00, 'IRPJ': 35.00, 'CSLL': 15.00, 'COFINS': 16.03, 'PIS/Pasep': 3.47, 'CPP': 30.50, 'ISS': 0.00}
    ],
    "Anexo IV": [
        {'faixa': 1, 'rbt12_max': 180000.00, 'IRPJ': 18.80, 'CSLL': 15.20, 'COFINS': 20.45, 'PIS/Pasep': 4.45, 'ISS': 41.10},
        {'faixa': 2, 'rbt12_max': 360000.00, 'IRPJ': 19.80, 'CSLL': 15.20, 'COFINS': 21.45, 'PIS/Pasep': 4.65, 'ISS': 38.90},
        {'faixa': 3, 'rbt12_max': 720000.00, 'IRPJ': 20.80, 'CSLL': 15.20, 'COFINS': 21.45, 'PIS/Pasep': 4.65, 'ISS': 37.90},
        {'faixa': 4, 'rbt12_max': 1800000.00, 'IRPJ': 17.80, 'CSLL': 19.20, 'COFINS': 20.45, 'PIS/Pasep': 4.45, 'ISS': 38.10},
        {'faixa': 5, 'rbt12_max': 3600000.00, 'IRPJ': 18.80, 'CSLL': 19.20, 'COFINS': 20.45, 'PIS/Pasep': 4.45, 'ISS': 37.10},
        {'faixa': 6, 'rbt12_max': 4800000.00, 'IRPJ': 23.30, 'CSLL': 11.20, 'COFINS': 25.45, 'PIS/Pasep': 5.55, 'ISS': 34.50}
    ],
    "Anexo V": [
        {'faixa': 1, 'rbt12_max': 180000.00, 'IRPJ': 25.00, 'CSLL': 15.00, 'COFINS': 14.10, 'PIS/Pasep': 3.05, 'CPP': 28.85, 'ISS': 14.00},
        {'faixa': 2, 'rbt12_max': 360000.00, 'IRPJ': 23.00, 'CSLL': 15.00, 'COFINS': 14.10, 'PIS/Pasep': 3.05, 'CPP': 27.85, 'ISS': 17.00},
        {'faixa': 3, 'rbt12_max': 720000.00, 'IRPJ': 24.00, 'CSLL': 15.00, 'COFINS': 14.92, 'PIS/Pasep': 3.23, 'CPP': 23.85, 'ISS': 19.00},
        {'faixa': 4, 'rbt12_max': 1800000.00, 'IRPJ': 21.00, 'CSLL': 15.00, 'COFINS': 15.74, 'PIS/Pasep': 3.41, 'CPP': 23.85, 'ISS': 21.00},
        {'faixa': 5, 'rbt12_max': 3600000.00, 'IRPJ': 23.00, 'CSLL': 12.50, 'COFINS': 16.56, 'PIS/Pasep': 3.59, 'CPP': 23.35, 'ISS': 21.00},
        {'faixa': 6, 'rbt12_max': 4800000.00, 'IRPJ': 30.50, 'CSLL': 13.50, 'COFINS': 14.14, 'PIS/Pasep': 3.06, 'CPP': 15.80, 'ISS': 23.00}
    ],
}


# ----------------- FUNÇÕES AUXILIARES -----------------
def determinar_faixa(rbt12):
    """Determina o índice da faixa de faturamento com base na RBT12."""
    if rbt12 > LIMITES_DAS_FAIXAS[-1]:
        return None
    for i, limite in enumerate(LIMITES_DAS_FAIXAS):
        if rbt12 <= limite:
            return i
    return len(LIMITES_DAS_FAIXAS) - 1


def exibir_rateio(rateio_calculado):
    """Exibe o rateio dos tributos formatado, ajustando percentuais e isenções."""
    print("\n--- Rateio por Tributo ---")
    tributos_com_valor = {k: v for k, v in rateio_calculado.items() if v > 0}
    total_rateio_valido = sum(tributos_com_valor.values()) if tributos_com_valor else 0.0

    for tributo, valor in rateio_calculado.items():
        if valor > 0 and total_rateio_valido > 0:
            percentual = (valor / total_rateio_valido) * 100
            print(f"{tributo:<12}: R$ {valor:,.2f} ({percentual:.2f}%)")
        elif valor > 0:
            print(f"{tributo:<12}: R$ {valor:,.2f}")
        else:
            print(f"{tributo:<12}: Isento")


# ----------------- FUNÇÃO PRINCIPAL DE CÁLCULO -----------------
def calcular_simples_nacional_from_input(data: dict):
    """
    Espera dicionário com chaves:
      - anexo: int 1..5
      - rbt: número (RBT12)
      - faturamento: número (faturamento do mês atual)
      - exportacao_servico: 0 ou 1 (ou False/True)
      - optante_fator_r: opcional 0/1 (se presente e ==1, aplica tratamento de fator-r)
    """
    # Validações básicas
    required = ["anexo", "rbt", "faturamento", "exportacao_servico"]
    for k in required:
        if k not in data:
            raise ValueError(f"Campo obrigatório '{k}' não fornecido no JSON de entrada.")

    anexo_original = int(data["anexo"])
    if anexo_original not in DADOS_DOS_ANEXOS:
        raise ValueError("Anexo inválido. Deve ser 1,2,3,4 ou 5.")

    rbt12 = float(data["rbt"])
    faturamento_mensal = float(data["faturamento"])
    is_exportacao = bool(int(data.get("exportacao_servico", 0)))
    optante_fator_r = bool(int(data.get("optante_fator_r", 0)))  # se presente, respeita; se não, assume False

    # Função interna reaproveitável (para calcular em qualquer anexo)
    def calcular_em_anexo(anexo_calculo: int):
        faixa_idx = determinar_faixa(rbt12)
        if faixa_idx is None:
            raise ValueError("A RBT12 informada ultrapassa o limite de R$ 4.800.000,00 do Simples Nacional.")

        dados_anexo_calculo = DADOS_DOS_ANEXOS[anexo_calculo]
        aliquota_nominal = dados_anexo_calculo["aliquotas"][faixa_idx]
        deducao = dados_anexo_calculo["deducoes"][faixa_idx]

        if rbt12 == 0:
            aliquota_efetiva_cheia = aliquota_nominal
        else:
            aliquota_efetiva_cheia = ((rbt12 * (aliquota_nominal / 100)) - deducao) / rbt12
            aliquota_efetiva_cheia *= 100

        valor_das_cheio = faturamento_mensal * (aliquota_efetiva_cheia / 100)

        nome_anexo_calculo_str = DADOS_DOS_ANEXOS[anexo_calculo]['nome'].split(' (')[0]
        reparticao_usada = reparticao_simples_nacional[nome_anexo_calculo_str][faixa_idx]

        rateio_final = {}
        valor_das_final = 0.0
        aliquota_efetiva_final = 0.0

        if is_exportacao and anexo_calculo in [3, 4, 5]:
            impostos_isentos = ['PIS/Pasep', 'COFINS', 'ISS']
            for imposto, perc in reparticao_usada.items():
                if imposto in ("faixa", "rbt12_max"):
                    continue
                valor_imposto = valor_das_cheio * (perc / 100)
                if imposto in impostos_isentos:
                    rateio_final[imposto] = 0.0
                else:
                    rateio_final[imposto] = valor_imposto
                    valor_das_final += valor_imposto
            aliquota_efetiva_final = (valor_das_final / faturamento_mensal) * 100 if faturamento_mensal > 0 else 0.0
        else:
            valor_das_final = valor_das_cheio
            aliquota_efetiva_final = aliquota_efetiva_cheia
            for imposto, perc in reparticao_usada.items():
                if imposto in ("faixa", "rbt12_max"):
                    continue
                rateio_final[imposto] = valor_das_cheio * (perc / 100)

        resultado = {
            "anexo_usado": anexo_calculo,
            "rbt12": rbt12,
            "faixa": faixa_idx + 1,
            "aliquota_efetiva_percent": round(aliquota_efetiva_final, 8),
            "valor_das_a_pagar": round(valor_das_final, 2),
            "rateio": {k: round(v, 2) for k, v in rateio_final.items()},
        }

        return resultado

    # ------------------- LÓGICA PRINCIPAL -------------------

    resultados = []

    # Cálculo padrão (para qualquer anexo)
    resultado_padrao = calcular_em_anexo(anexo_original)
    resultados.append(("Cálculo Padrão", resultado_padrao))

    # Caso seja anexo V, calcula também como se fosse Anexo III
    if anexo_original == 5:
        resultado_fator_r = calcular_em_anexo(3)
        resultados.append(("Cálculo Alternativo (como Anexo III / Fator-R)", resultado_fator_r))

    # Exibição formatada
    print("\n==================== RESULTADO DO CÁLCULO ====================")
    for titulo, res in resultados:
        print(f"\n--- {titulo} ---")
        print(f"Anexo Usado: {res['anexo_usado']}")
        print(f"Receita Bruta (RBT12): R$ {res['rbt12']:,.2f}")
        print(f"Faixa: {res['faixa']}")
        print(f"Alíquota Efetiva: {res['aliquota_efetiva_percent']:.8f} %")
        print(f"Valor do DAS a pagar: R$ {res['valor_das_a_pagar']:,.2f}")
        exibir_rateio(res["rateio"])

    # Exibir JSON final (com as duas saídas)
    saida_json = {titulo: res for titulo, res in resultados}
    print("\n--- JSON Consolidado ---")
    print(json.dumps(saida_json, ensure_ascii=False, indent=2))

    return saida_json


# ----------------- ENTRYPOINT -----------------
def main():
    parser = argparse.ArgumentParser(description="Calcula DAS (entrada via JSON)")
    parser.add_argument("--input", "-i", help="JSON com os dados (ex: '{\"anexo\":3,...}')")
    parser.add_argument("--file", "-f", help="Arquivo JSON contendo os dados de entrada")
    args = parser.parse_args()

    raw = None
    if args.input:
        raw = args.input
    elif args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except Exception as e:
            print(f"Erro ao ler arquivo: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("ERRO: É necessário informar um JSON de entrada via --input ou --file.", file=sys.stderr)
        print("Exemplo: python calcula_das_json.py --input '{\"anexo\":3,\"rbt\":100000,\"faturamento\":1000,\"exportacao_servico\":0}'", file=sys.stderr)
        sys.exit(2)

    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"JSON inválido: {e}", file=sys.stderr)
        sys.exit(3)

    try:
        calcular_simples_nacional_from_input(data)
    except Exception as e:
        print(f"Erro no cálculo: {e}", file=sys.stderr)
        sys.exit(4)


if __name__ == "__main__":
    main()
