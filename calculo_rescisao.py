import sys
import json
import argparse
import datetime
from calendar import monthrange

# ==============================================================================
#  CONSTANTES ATUALIZADAS 2025
# ==============================================================================

SALARIO_MINIMO_2025 = 1518.00
TETO_INSS_2025 = 8157.41
DEDUCAO_DEPENDENTE_2025 = 189.59

# Tabela INSS 2025 (Portaria MPS/MF 6/2025) - Progressiva
FAIXAS_INSS_2025 = [
    (1518.00, 0.075),
    (2793.88, 0.09),
    (4190.83, 0.12),
    (8157.41, 0.14)
]

# Tabelas IRRF 2025
# Janeiro a Abril/2025 (Lei 14.848/2024)
TABELA_IRRF_JAN_ABR_2025 = [
    (2259.20, 0.0, 0.0),
    (2826.65, 0.075, 169.44),
    (3751.05, 0.15, 381.44),
    (4664.68, 0.225, 662.77),
    (float('inf'), 0.275, 896.00)
]

# Maio/2025 em diante (Lei 15.191/2025)
TABELA_IRRF_MAI_2025 = [
    (2428.80, 0.0, 0.0),
    (2826.65, 0.075, 182.16),
    (3751.05, 0.15, 394.16),
    (4664.68, 0.225, 675.49),
    (float('inf'), 0.275, 908.73)
]

# ==============================================================================
#  FUNÇÕES DE CÁLCULO (Lógica Pura)
# ==============================================================================

def parse_data(data_str):
    """Converte string 'YYYY-MM-DD' para object date."""
    if not data_str:
        return None
    try:
        return datetime.datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def calcular_inss_2025(base):
    """
    Calcula INSS com alíquota progressiva (2025).
    Cada faixa aplica sua alíquota apenas sobre a parcela correspondente.
    """
    base = min(base, TETO_INSS_2025)
    desconto = 0.0
    faixa_anterior = 0
    
    for limite, aliquota in FAIXAS_INSS_2025:
        if base > faixa_anterior:
            base_faixa = min(base, limite) - faixa_anterior
            desconto += base_faixa * aliquota
            faixa_anterior = limite
        else:
            break
    
    return round(desconto, 2)


def calcular_irrf_2025(base, dependentes, pensao=0, data_rescisao=None):
    """
    Calcula IRRF considerando a tabela vigente na data da rescisão.
    - Jan-Abr/2025: tabela antiga (Lei 14.848/2024)
    - Mai/2025 em diante: tabela nova (Lei 15.191/2025)
    
    IMPORTANTE: A base deve conter APENAS verbas tributáveis.
    """
    deducao_dep = dependentes * DEDUCAO_DEPENDENTE_2025
    base_real = base - deducao_dep - pensao
    
    if base_real <= 0:
        return 0.0
    
    # Determinar qual tabela usar baseado na data da rescisão
    if data_rescisao and data_rescisao >= datetime.date(2025, 5, 1):
        tabela = TABELA_IRRF_MAI_2025
    else:
        tabela = TABELA_IRRF_JAN_ABR_2025
    
    resultado = 0.0
    for limite, aliquota, deducao in tabela:
        if base_real <= limite:
            resultado = (base_real * aliquota) - deducao
            break
    
    return round(max(0.0, resultado), 2)


def calcular_meses_trabalhados(inicio, fim):
    """
    Calcula meses para 13º Salário (baseado em mês civil: 01 a 30/31).
    Conta 1 mês se trabalhou 15 dias ou mais naquele mês.
    """
    meses = 0
    curr = inicio
    
    while curr <= fim:
        ultimo_dia = monthrange(curr.year, curr.month)[1]
        
        # Define início e fim do mês corrente para contagem de dias
        if curr.month == inicio.month and curr.year == inicio.year:
            ini_c = curr.day
        else:
            ini_c = 1
            
        if curr.month == fim.month and curr.year == fim.year:
            fim_c = fim.day
        else:
            fim_c = ultimo_dia

        dias_no_mes = fim_c - ini_c + 1
        if dias_no_mes >= 15:
            meses += 1

        # Avança para o próximo mês
        if curr.month == 12:
            curr = datetime.date(curr.year + 1, 1, 1)
        else:
            curr = datetime.date(curr.year, curr.month + 1, 1)
    
    return meses


def calcular_avos_ferias(inicio_aquisitivo, fim_projetado):
    """
    Calcula avos de férias baseado no período aquisitivo (aniversário do contrato).
    Cada período de 30 dias a partir da admissão conta como 1 avo.
    Fração de 15 dias ou mais conta como 1 avo adicional.
    Máximo: 12 avos.
    """
    avos = 0
    curr = inicio_aquisitivo

    while True:
        # Calcula a data do próximo "mesversário"
        year = curr.year + ((curr.month + 1) // 13)
        month = (curr.month % 12) + 1

        # Tratamento para dias inexistentes (ex: 31 de fev vira 28/29)
        try:
            next_date = datetime.date(year, month, inicio_aquisitivo.day)
        except ValueError:
            last_day = monthrange(year, month)[1]
            next_date = datetime.date(year, month, last_day)

        # O período fecha um dia antes do próximo aniversário
        periodo_fim = next_date - datetime.timedelta(days=1)

        if periodo_fim <= fim_projetado:
            avos += 1
            curr = next_date
        else:
            # Fração final: Se trabalhou >= 15 dias neste ciclo incompleto
            dias_fracao = (fim_projetado - curr).days + 1
            if dias_fracao >= 15:
                avos += 1
            break

    return min(avos, 12)


def gerar_resumo_texto(tipo):
    """Gera texto explicativo sobre o tipo de rescisão."""
    resumos = {
        1: [
            "Motivo: Demissão sem Justa Causa (Iniciativa da Empresa).",
            "O trabalhador recebe todas as verbas (Aviso, 13º, Férias).",
            "Tem direito ao saque do FGTS + Multa de 40%.",
            "Tem direito ao Seguro Desemprego (se cumprir carência)."
        ],
        2: [
            "Motivo: Pedido de Demissão (Iniciativa do Funcionário).",
            "Recebe Saldo de Salário, 13º e Férias proporcionais.",
            "NÃO saca o FGTS e NÃO recebe multa.",
            "NÃO tem direito ao Seguro Desemprego."
        ],
        3: [
            "Motivo: Justa Causa (Falta Grave).",
            "Recebe apenas Saldo de Salário e Férias Vencidas (se houver).",
            "Perde Aviso Prévio, 13º e Férias Proporcionais.",
            "NÃO saca FGTS."
        ],
        4: [
            "Motivo: Acordo Comum (Art. 484-A CLT).",
            "Aviso Prévio indenizado é pago pela metade.",
            "Multa do FGTS é de 20%. Pode sacar 80% do saldo.",
            "NÃO tem direito ao Seguro Desemprego."
        ],
        5: [
            "Motivo: Término de Contrato (Prazo Determinado/Experiência).",
            "Recebe Saldo, 13º e Férias.",
            "Saca o FGTS depositado, mas NÃO tem multa de 40%."
        ],
        6: [
            "Motivo: Quebra de Contrato pelo EMPREGADOR (Art. 479).",
            "Indenização: A empresa paga metade dos dias restantes.",
            "Recebe verbas normais e FGTS + 40%."
        ],
        7: [
            "Motivo: Quebra de Contrato pelo FUNCIONÁRIO (Art. 480).",
            "O funcionário pode indenizar a empresa (limitado à metade dos dias restantes).",
            "NÃO saca FGTS."
        ]
    }
    return resumos.get(tipo, [])


# ==============================================================================
#  MOTOR PRINCIPAL (JSON INPUT)
# ==============================================================================

def processar_rescisao(data_json):
    """
    Processa rescisão trabalhista recebendo JSON e retornando JSON.
    
    Parâmetros esperados no JSON:
    - motivo: 1-7 (tipo de rescisão)
    - salario_base: valor do salário
    - adicionais: valor de adicionais (periculosidade, insalubridade, etc.)
    - media_he: média de horas extras
    - media_comissao: média de comissões
    - data_admissao: 'YYYY-MM-DD'
    - data_demissao: 'YYYY-MM-DD'
    - data_prevista_fim: 'YYYY-MM-DD' (para tipos 6 e 7)
    - ferias_vencidas_qtd: quantidade de períodos de férias vencidas
    - dependentes: número de dependentes para IRRF
    - pensao: valor de pensão alimentícia
    - adiantamento: valor de adiantamento/vale
    - saldo_fgts: saldo do FGTS para cálculo da multa
    - aviso_indenizado: true/false (para tipo 1)
    - aviso_cumprido: true/false (para tipo 2)
    """
    
    # 1. Extração e Conversão de Dados
    try:
        tipo = int(data_json.get("motivo", 1))
        salario_base = float(data_json.get("salario_base", 0))
        adicionais = float(data_json.get("adicionais", 0))
        media_he = float(data_json.get("media_he", 0))
        media_comissao = float(data_json.get("media_comissao", 0))

        dt_adm = parse_data(data_json.get("data_admissao"))
        dt_dem = parse_data(data_json.get("data_demissao"))
        dt_prev_fim = parse_data(data_json.get("data_prevista_fim"))

        ferias_vencidas_qtd = int(data_json.get("ferias_vencidas_qtd", 0))
        dependentes = int(data_json.get("dependentes", 0))
        pensao = float(data_json.get("pensao", 0))
        adiantamento = float(data_json.get("adiantamento", 0))
        saldo_fgts = float(data_json.get("saldo_fgts", 0))

        # Flags booleanas
        aviso_indenizado = bool(data_json.get("aviso_indenizado", False))
        aviso_cumprido = bool(data_json.get("aviso_cumprido", True))

    except (ValueError, TypeError) as e:
        raise ValueError(f"Erro nos dados de entrada: {e}")

    # Validações
    if not dt_adm or not dt_dem:
        raise ValueError("Datas de admissão e demissão são obrigatórias.")
    
    if dt_dem < dt_adm:
        raise ValueError("Data de demissão não pode ser anterior à data de admissão.")

    # 2. Definição da Base de Cálculo
    remuneracao_total = salario_base + adicionais + media_he + media_comissao
    val_dia = remuneracao_total / 30

    # 3. Lógica de Aviso Prévio e Datas de Projeção
    dias_aviso_pagar = 0
    aviso_descontar = False
    multa_art479_480 = 0.0
    data_projecao = dt_dem

    # Cálculo do aviso prévio proporcional (Lei 12.506/2011)
    anos_servico = (dt_dem - dt_adm).days // 365
    dias_aviso_direito = min(30 + (3 * anos_servico), 90)

    # Regras por Tipo de Rescisão
    if tipo == 1:  # Dispensa sem Justa Causa
        if aviso_indenizado:
            dias_aviso_pagar = dias_aviso_direito
            data_projecao = dt_dem + datetime.timedelta(days=dias_aviso_direito)

    elif tipo == 2:  # Pedido de Demissão
        if not aviso_cumprido:
            aviso_descontar = True

    elif tipo == 4:  # Acordo Comum (Art. 484-A CLT)
        if aviso_indenizado:
            dias_aviso_pagar = dias_aviso_direito // 2  # Metade do aviso
            data_projecao = dt_dem + datetime.timedelta(days=dias_aviso_pagar)

    elif tipo in [6, 7]:  # Quebra de contrato (Experiência/Prazo Determinado)
        if dt_prev_fim and dt_prev_fim > dt_dem:
            dias_restantes = (dt_prev_fim - dt_dem).days
            multa_art479_480 = (dias_restantes * val_dia) / 2

    # 4. Cálculos das Verbas
    prov = {}  # Proventos
    desc = {}  # Descontos
    
    # Listas para separar verbas tributáveis e isentas (para IRRF)
    verbas_tributaveis = 0.0
    verbas_isentas = 0.0

    # --- SALDO DE SALÁRIO (TRIBUTÁVEL) ---
    dias_trab = dt_dem.day
    ultimo_dia_mes = monthrange(dt_dem.year, dt_dem.month)[1]

    if dias_trab == ultimo_dia_mes or dias_trab == 31:
        dias_saldo = 30
    else:
        dias_saldo = dias_trab

    val_saldo = val_dia * dias_saldo
    prov[f"Saldo de Salário ({dias_saldo} dias)"] = round(val_saldo, 2)
    verbas_tributaveis += val_saldo

    # --- AVISO PRÉVIO INDENIZADO (ISENTO) ---
    if dias_aviso_pagar > 0:
        val_aviso = val_dia * dias_aviso_pagar
        prov[f"Aviso Prévio Indenizado ({dias_aviso_pagar} dias)"] = round(val_aviso, 2)
        verbas_isentas += val_aviso

    # --- INDENIZAÇÃO ART. 479 (ISENTO) ---
    if tipo == 6 and multa_art479_480 > 0:
        prov["Indenização Art. 479 (Quebra contrato empresa)"] = round(multa_art479_480, 2)
        verbas_isentas += multa_art479_480

    # --- DESCONTO ART. 480 ---
    if tipo == 7 and multa_art479_480 > 0:
        desc["Indenização Art. 480 (Quebra contrato funcionário)"] = round(multa_art479_480, 2)

    # --- DESCONTO AVISO NÃO CUMPRIDO ---
    if aviso_descontar:
        desc["Aviso Prévio Não Cumprido"] = round(remuneracao_total, 2)

    # --- 13º SALÁRIO PROPORCIONAL (TRIBUTÁVEL) ---
    if tipo != 3:  # Justa causa não tem direito
        inicio_ano = datetime.date(dt_dem.year, 1, 1)
        inicio_contagem = dt_adm if dt_adm > inicio_ano else inicio_ano
        meses_13 = calcular_meses_trabalhados(inicio_contagem, data_projecao)
        meses_13 = min(meses_13, 12)
        
        if meses_13 > 0:
            val_13 = (remuneracao_total / 12) * meses_13
            prov[f"13º Salário Proporcional ({meses_13}/12)"] = round(val_13, 2)
            verbas_tributaveis += val_13

    # --- FÉRIAS VENCIDAS (ISENTO) ---
    if ferias_vencidas_qtd > 0:
        val_ferias_venc = remuneracao_total * ferias_vencidas_qtd
        val_terco_venc = val_ferias_venc / 3
        prov[f"Férias Vencidas ({ferias_vencidas_qtd} período(s))"] = round(val_ferias_venc, 2)
        prov["1/3 Constitucional (Férias Vencidas)"] = round(val_terco_venc, 2)
        verbas_isentas += val_ferias_venc + val_terco_venc

    # --- FÉRIAS PROPORCIONAIS (ISENTO) ---
    if tipo != 3:  # Justa causa não tem direito a férias proporcionais
        # Determinar início do período aquisitivo atual
        anos_completos = (dt_dem.year - dt_adm.year)
        if (dt_dem.month, dt_dem.day) < (dt_adm.month, dt_adm.day):
            anos_completos -= 1
        
        try:
            inicio_periodo_aquisitivo = datetime.date(
                dt_adm.year + anos_completos, 
                dt_adm.month, 
                dt_adm.day
            )
        except ValueError:
            # Tratamento para 29 de fevereiro
            inicio_periodo_aquisitivo = datetime.date(
                dt_adm.year + anos_completos, 
                dt_adm.month, 
                28
            )
        
        avos_ferias = calcular_avos_ferias(inicio_periodo_aquisitivo, data_projecao)
        
        if avos_ferias > 0:
            val_ferias_prop = (remuneracao_total / 12) * avos_ferias
            val_terco_prop = val_ferias_prop / 3
            prov[f"Férias Proporcionais ({avos_ferias}/12)"] = round(val_ferias_prop, 2)
            prov["1/3 Constitucional (Férias Proporcionais)"] = round(val_terco_prop, 2)
            verbas_isentas += val_ferias_prop + val_terco_prop

    # --- FGTS E MULTA ---
    fgts_info = {}
    
    if tipo == 1:  # Sem justa causa
        multa_fgts = saldo_fgts * 0.40
        fgts_info["Saldo FGTS informado"] = round(saldo_fgts, 2)
        fgts_info["Multa 40% FGTS"] = round(multa_fgts, 2)
        fgts_info["Saque FGTS"] = "100% do saldo"
        
    elif tipo == 4:  # Acordo
        multa_fgts = saldo_fgts * 0.20
        fgts_info["Saldo FGTS informado"] = round(saldo_fgts, 2)
        fgts_info["Multa 20% FGTS (acordo)"] = round(multa_fgts, 2)
        fgts_info["Saque FGTS"] = "80% do saldo"
        
    elif tipo == 5:  # Término contrato
        fgts_info["Saldo FGTS informado"] = round(saldo_fgts, 2)
        fgts_info["Multa FGTS"] = 0.0
        fgts_info["Saque FGTS"] = "100% do saldo"
        
    elif tipo == 6:  # Quebra pelo empregador
        multa_fgts = saldo_fgts * 0.40
        fgts_info["Saldo FGTS informado"] = round(saldo_fgts, 2)
        fgts_info["Multa 40% FGTS"] = round(multa_fgts, 2)
        fgts_info["Saque FGTS"] = "100% do saldo"
        
    else:  # Pedido demissão, justa causa, quebra pelo funcionário
        fgts_info["Saque FGTS"] = "Não permitido"
        fgts_info["Multa FGTS"] = "Não se aplica"

    # 5. CÁLCULO DOS DESCONTOS

    # --- INSS (sobre verbas que incidem) ---
    # INSS incide sobre: saldo salário, 13º, aviso trabalhado
    # INSS NÃO incide sobre: férias indenizadas, aviso indenizado
    base_inss = val_saldo
    if tipo != 3 and meses_13 > 0:
        base_inss += val_13 if 'val_13' in dir() else 0
    
    inss_saldo = calcular_inss_2025(base_inss)
    desc["INSS"] = inss_saldo

    # --- IRRF (apenas sobre verbas tributáveis) ---
    # IRRF incide sobre: saldo salário, 13º
    # IRRF NÃO incide sobre: férias, aviso indenizado, multa FGTS
    base_irrf = verbas_tributaveis - inss_saldo
    irrf = calcular_irrf_2025(base_irrf, dependentes, pensao, dt_dem)
    if irrf > 0:
        desc["IRRF"] = irrf

    # --- Outros descontos ---
    if pensao > 0:
        desc["Pensão Alimentícia"] = round(pensao, 2)
    
    if adiantamento > 0:
        desc["Adiantamento/Vale"] = round(adiantamento, 2)

    # 6. TOTAIS
    total_proventos = sum(prov.values())
    total_descontos = sum(desc.values())
    total_liquido = total_proventos - total_descontos

    # 7. RESULTADO
    resultado = {
        "resumo": gerar_resumo_texto(tipo),
        "dados_entrada": {
            "tipo_rescisao": tipo,
            "salario_base": salario_base,
            "remuneracao_total": round(remuneracao_total, 2),
            "data_admissao": str(dt_adm),
            "data_demissao": str(dt_dem),
            "data_projecao_aviso": str(data_projecao),
            "tempo_servico_anos": anos_servico,
            "dias_aviso_direito": dias_aviso_direito
        },
        "proventos": prov,
        "descontos": desc,
        "fgts": fgts_info,
        "totais": {
            "total_proventos": round(total_proventos, 2),
            "total_descontos": round(total_descontos, 2),
            "total_liquido": round(total_liquido, 2),
            "verbas_tributaveis": round(verbas_tributaveis, 2),
            "verbas_isentas": round(verbas_isentas, 2)
        },
        "observacoes": {
            "tabela_irrf_utilizada": "Mai/2025+ (Lei 15.191/2025)" if dt_dem >= datetime.date(2025, 5, 1) else "Jan-Abr/2025 (Lei 14.848/2024)",
            "base_inss": round(base_inss, 2),
            "base_irrf": round(base_irrf, 2)
        }
    }

    return resultado


# ==============================================================================
#  EXECUÇÃO VIA LINHA DE COMANDO
# ==============================================================================

if __name__ == "_main_":
    parser = argparse.ArgumentParser(description="Calculadora de Rescisão Trabalhista")
    parser.add_argument("--input", type=str, help="JSON string com os dados")
    parser.add_argument("--file", type=str, help="Arquivo JSON com os dados")
    args = parser.parse_args()

    try:
        if args.file:
            with open(args.file, "r", encoding="utf-8") as f:
                dados = json.load(f)
        elif args.input:
            dados = json.loads(args.input)
        else:
            # Modo interativo
            print("Cole o JSON com os dados da rescisão:")
            texto = input().strip()
            dados = json.loads(texto)
        
        resultado = processar_rescisao(dados)
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(json.dumps({"erro": str(e)}, ensure_ascii=False))
        sys.exit(1)