"""Gera database/seeds/data/catalogo.json — catálogo 100% FICTÍCIO para demonstração.

Determinístico (SEED=2026): rodar de novo produz exatamente o mesmo arquivo.

- Marcas e modelos são INVENTADOS (qualquer semelhança com marcas reais é coincidência).
- Preços em reais seguem FAIXAS APROXIMADAS do varejo brasileiro de 2026 (referência informal,
  não é cotação de nenhuma loja) para a demonstração parecer realista.
- Contagens alinhadas ao plano de banco (DB §6): 25 categorias, 15 marcas, 300 produtos,
  >= 40 tipos de especificação, 1.500 associações produto-especificação.

Uso:  .venv\\Scripts\\python database\\seeds\\gerar_catalogo.py
"""

import json
import random
from pathlib import Path

SEED = 2026
SAIDA = Path(__file__).resolve().parent / "data" / "catalogo.json"

MARCAS = [
    "Torqmax", "Voltrix", "Ferrabraz", "Brutus Pro", "Metalix", "Prumo", "Agilis", "Rochedo",
    "Faiscar", "Nivela", "Serrano", "Hexabit", "Granitto", "Bravon", "Kalibra",
]

PAIS = [
    ("ferramentas_eletricas", "Ferramentas elétricas"),
    ("acessorios", "Acessórios"),
    ("baterias_carregadores", "Baterias e carregadores"),
    ("medicao", "Medição"),
    ("seguranca_epi", "Segurança (EPI)"),
    ("equipamentos", "Compressores e lavadoras"),
]

# (codigo, especificação, unidade, tipo)
ESPECIFICACOES = [
    ("potencia_w", "Potência", "W", "numero"),
    ("rotacao_rpm", "Rotação sem carga", "rpm", "numero"),
    ("impactos_bpm", "Impactos por minuto", "bpm", "numero"),
    ("mandril_mm", "Mandril", "mm", "numero"),
    ("torque_nm", "Torque máximo", "N·m", "numero"),
    ("tensao_bateria_v", "Tensão da bateria", "V", "numero"),
    ("capacidade_ah", "Capacidade da bateria", "Ah", "numero"),
    ("diametro_disco_mm", "Diâmetro do disco", "mm", "numero"),
    ("profundidade_corte_mm", "Profundidade de corte a 90°", "mm", "numero"),
    ("energia_impacto_j", "Energia de impacto", "J", "numero"),
    ("encaixe", "Encaixe", None, "texto"),
    ("peso_kg", "Peso", "kg", "numero"),
    ("cabo_m", "Comprimento do cabo", "m", "numero"),
    ("velocidade_variavel", "Velocidade variável", None, "booleano"),
    ("reversivel", "Reversível", None, "booleano"),
    ("inclui_maleta", "Acompanha maleta", None, "booleano"),
    ("inclui_bateria", "Acompanha bateria", None, "booleano"),
    ("qtd_baterias", "Quantidade de baterias", None, "numero"),
    ("tempo_recarga_min", "Tempo de recarga", "min", "numero"),
    ("diametro_mm", "Diâmetro", "mm", "numero"),
    ("comprimento_mm", "Comprimento", "mm", "numero"),
    ("material", "Material", None, "texto"),
    ("qtd_pecas", "Quantidade de peças", None, "numero"),
    ("aplicacao", "Aplicação", None, "texto"),
    ("espessura_disco_mm", "Espessura do disco", "mm", "numero"),
    ("furo_central_mm", "Furo central", "mm", "numero"),
    ("rotacao_maxima_rpm", "Rotação máxima permitida", "rpm", "numero"),
    ("tipo_encaixe_bit", "Encaixe da ponta", None, "texto"),
    ("dentes_por_polegada", "Dentes por polegada", "TPI", "numero"),
    ("cat_seguranca", "Categoria de segurança", None, "texto"),
    ("funcoes", "Número de funções", None, "numero"),
    ("alcance_m", "Alcance", "m", "numero"),
    ("precisao_mm", "Precisão", "± mm", "numero"),
    ("classe_laser", "Classe do laser", None, "texto"),
    ("tamanho", "Tamanho", None, "texto"),
    ("pressao_max_psi", "Pressão máxima", "psi", "numero"),
    ("vazao_l_min", "Vazão de ar", "L/min", "numero"),
    ("reservatorio_l", "Reservatório", "L", "numero"),
    ("pressao_max_bar", "Pressão máxima", "bar", "numero"),
    ("vazao_l_h", "Vazão de água", "L/h", "numero"),
    ("garantia_meses", "Garantia do fabricante", "meses", "numero"),
    ("orbita_mm", "Órbita", "mm", "numero"),
    ("golpes_min", "Golpes por minuto", "gpm", "numero"),
    ("angulo_bisel_graus", "Inclinação máxima", "°", "numero"),
    ("plataforma", "Plataforma de bateria", None, "texto"),
]
# Nomes de especificação precisam ser únicos: "Pressão máxima" aparece em psi e bar.
ESPECIFICACOES = [
    (c, f"{n} ({u})" if c in ("pressao_max_psi", "pressao_max_bar") else n, u, t) for c, n, u, t in ESPECIFICACOES
]

CORDED = ["127V", "220V"]


def preco(rng, minimo, maximo, fator=1.0):
    """Preço 'de vitrine' terminado em ,90, em centavos."""
    valor = rng.uniform(minimo, maximo) * fator
    valor = max(9.9, round(valor / 10) * 10 - 0.10)
    return int(round(valor * 100))


def b(v):
    return "sim" if v else "não"


def br(x):
    """Número com vírgula decimal para nomes de produto (1.5 -> 1,5)."""
    return f"{x:g}".replace(".", ",")


# Cada categoria: (codigo, nome, pai, qtd, montar(rng, marca) -> dict)
def furadeira(rng, marca):
    w = rng.choice([450, 550, 600, 650, 710, 750, 850])
    v = rng.choice(CORDED)
    return dict(nome=f"Furadeira {marca} F{rng.randint(100, 999)} {w}W {v}", alimentacao=v,
                preco=preco(rng, 140, 420, w / 650),
                specs=[("potencia_w", w), ("rotacao_rpm", rng.choice([2800, 3000, 3200])),
                       ("mandril_mm", rng.choice([10, 13])), ("velocidade_variavel", b(True))],
                descricao="Furadeira para perfurar madeira, metal e plástico em uso doméstico e leve.")


def impacto(rng, marca):
    w = rng.choice([550, 650, 710, 750, 850, 1000])
    v = rng.choice(CORDED)
    return dict(nome=f"Furadeira de Impacto {marca} FI{rng.randint(100, 999)} {w}W {v}", alimentacao=v,
                preco=preco(rng, 190, 620, w / 750),
                specs=[("potencia_w", w), ("impactos_bpm", rng.choice([44800, 48000, 51000])),
                       ("mandril_mm", 13), ("reversivel", b(True))],
                descricao="Furadeira com percussão para alvenaria e tijolo; para concreto intenso prefira martelete.")


def martelete(rng, marca):
    w = rng.choice([800, 850, 1000, 1200, 1500])
    v = rng.choice(CORDED)
    j = {800: 2.7, 850: 3.0, 1000: 3.5, 1200: 5.0, 1500: 8.0}[w]
    return dict(nome=f"Martelete {marca} M{rng.randint(100, 999)} {w}W {v}", alimentacao=v,
                preco=preco(rng, 450, 1650, w / 1000),
                specs=[("potencia_w", w), ("energia_impacto_j", j),
                       ("encaixe", "SDS-max" if w >= 1200 else "SDS-plus"), ("inclui_maleta", b(True))],
                descricao="Martelete rompedor para perfuração em concreto e rompimento leve, conforme o manual.")


def parafusadeira(rng, marca):
    tensao = rng.choice([12, 12, 20, 20, 20])
    ah = rng.choice([1.5, 2.0, 4.0])
    nb = rng.choice([1, 2])
    faixa = (190, 520) if tensao == 12 else (420, 1150)
    return dict(nome=f"Parafusadeira e Furadeira a Bateria {marca} P{rng.randint(100, 999)} {tensao}V {nb}x{br(ah)}Ah",
                alimentacao="bateria", preco=preco(rng, *faixa, 1 + 0.12 * (nb - 1)),
                specs=[("tensao_bateria_v", tensao), ("torque_nm", rng.choice([25, 30, 45, 55, 65])),
                       ("qtd_baterias", nb), ("plataforma", f"{marca} {tensao}V")],
                descricao="Parafusadeira com controle de torque para montagem de móveis e furos leves.")


def esmerilhadeira(rng, marca):
    disco = rng.choice([115, 115, 125, 180])
    w = {115: rng.choice([720, 850]), 125: rng.choice([900, 1100]), 180: 2200}[disco]
    v = rng.choice(CORDED)
    return dict(nome=f"Esmerilhadeira Angular {marca} E{rng.randint(100, 999)} {disco}mm {w}W {v}", alimentacao=v,
                preco=preco(rng, 170, 820, w / 1000),
                specs=[("potencia_w", w), ("diametro_disco_mm", disco),
                       ("rotacao_rpm", 8500 if disco == 180 else 11000), ("peso_kg", round(rng.uniform(1.6, 4.8), 1))],
                descricao="Esmerilhadeira para corte e desbaste com disco adequado; use sempre a proteção.")


def serra_circular(rng, marca):
    disco = rng.choice([165, 185, 185, 235])
    w = {165: 1200, 185: 1400, 235: 2000}[disco]
    v = rng.choice(CORDED)
    return dict(nome=f"Serra Circular {marca} SC{rng.randint(100, 999)} {disco}mm {w}W {v}", alimentacao=v,
                preco=preco(rng, 350, 1150, w / 1400),
                specs=[("potencia_w", w), ("diametro_disco_mm", disco),
                       ("profundidade_corte_mm", {165: 55, 185: 63, 235: 85}[disco]), ("angulo_bisel_graus", 45)],
                descricao="Serra circular para cortes retos em madeira e derivados.")


def tico_tico(rng, marca):
    w = rng.choice([400, 500, 600, 750])
    v = rng.choice(CORDED)
    return dict(nome=f"Serra Tico-Tico {marca} T{rng.randint(100, 999)} {w}W {v}", alimentacao=v,
                preco=preco(rng, 180, 760, w / 600),
                specs=[("potencia_w", w), ("golpes_min", rng.choice([3000, 3100, 3200])),
                       ("angulo_bisel_graus", 45), ("velocidade_variavel", b(True))],
                descricao="Serra tico-tico para cortes curvos e recortes em madeira, plástico e metal fino.")


def lixadeira(rng, marca):
    w = rng.choice([200, 240, 300, 450])
    v = rng.choice(CORDED)
    return dict(nome=f"Lixadeira Orbital {marca} L{rng.randint(100, 999)} {w}W {v}", alimentacao=v,
                preco=preco(rng, 170, 690, w / 300),
                specs=[("potencia_w", w), ("orbita_mm", rng.choice([1.6, 2.0, 2.5])),
                       ("velocidade_variavel", b(w >= 300)), ("peso_kg", round(rng.uniform(1.1, 2.4), 1))],
                descricao="Lixadeira orbital para acabamento em madeira.")


def broca(rng, marca):
    aplic = rng.choice(["Madeira", "Metal", "Concreto"])
    pecas = rng.choice([5, 8, 10, 13, 15])
    material = {"Madeira": "Aço carbono", "Metal": "Aço rápido HSS", "Concreto": "Ponta de metal duro (vídea)"}[aplic]
    return dict(nome=f"Jogo de Brocas para {aplic} {marca} {pecas} peças", alimentacao="nao_eletrico",
                preco=preco(rng, 22, 210, pecas / 10),
                specs=[("aplicacao", aplic), ("qtd_pecas", pecas), ("material", material),
                       ("encaixe", "SDS-plus" if aplic == "Concreto" and rng.random() < 0.4 else "Cilíndrico")],
                descricao=f"Jogo de brocas para {aplic.lower()}; confira a compatibilidade com o mandril.")


def disco(rng, marca):
    tipo = rng.choice(["Corte", "Desbaste", "Diamantado"])
    d = rng.choice([115, 115, 180])
    nome = "Disco Diamantado" if tipo == "Diamantado" else f"Disco de {tipo}"
    faixa = (35, 120) if tipo == "Diamantado" else (6, 32)
    return dict(nome=f"{nome} {marca} {d}mm", alimentacao="nao_eletrico",
                preco=preco(rng, *faixa, d / 115),
                specs=[("diametro_disco_mm", d), ("espessura_disco_mm", {"Corte": 1.0, "Desbaste": 6.4, "Diamantado": 2.0}[tipo]),
                       ("furo_central_mm", 22.23), ("rotacao_maxima_rpm", 13300 if d == 115 else 8500)],
                descricao=f"Disco de {tipo.lower()}; use apenas em máquina com rotação até a máxima indicada.")


def bit(rng, marca):
    pecas = rng.choice([10, 20, 32, 45])
    return dict(nome=f"Jogo de Bits e Pontas {marca} {pecas} peças", alimentacao="nao_eletrico",
                preco=preco(rng, 25, 190, pecas / 25),
                specs=[("qtd_pecas", pecas), ("tipo_encaixe_bit", '1/4" sextavado'),
                       ("material", "Aço cromo-vanádio"), ("inclui_maleta", b(pecas >= 32))],
                descricao="Bits Phillips, fenda, Torx e sextavados para parafusadeira.")


def lamina(rng, marca):
    aplic = rng.choice(["Madeira", "Metal"])
    pecas = rng.choice([3, 5, 10])
    return dict(nome=f"Lâminas de Serra Tico-Tico para {aplic} {marca} {pecas} unidades", alimentacao="nao_eletrico",
                preco=preco(rng, 18, 140, pecas / 5),
                specs=[("aplicacao", aplic), ("qtd_pecas", pecas),
                       ("dentes_por_polegada", 6 if aplic == "Madeira" else 24), ("comprimento_mm", 100)],
                descricao="Lâminas com encaixe tipo T; confira a compatibilidade com a sua serra.")


def bateria(rng, marca):
    tensao = rng.choice([12, 20])
    ah = rng.choice([2.0, 4.0, 5.0])
    return dict(nome=f"Bateria {marca} {tensao}V {br(ah)}Ah", alimentacao="bateria",
                preco=preco(rng, 150, 520, (tensao / 16) * (ah / 3.5)),
                specs=[("tensao_bateria_v", tensao), ("capacidade_ah", ah),
                       ("plataforma", f"{marca} {tensao}V"), ("peso_kg", round(0.3 + ah * 0.12, 1))],
                descricao="Bateria de íon-lítio; compatível somente com ferramentas da mesma plataforma.")


def carregador(rng, marca):
    tensao = rng.choice([12, 20])
    v = "bivolt"
    return dict(nome=f"Carregador {marca} {tensao}V Bivolt", alimentacao=v,
                preco=preco(rng, 120, 480, tensao / 16),
                specs=[("tensao_bateria_v", tensao), ("tempo_recarga_min", rng.choice([30, 45, 60, 90])),
                       ("plataforma", f"{marca} {tensao}V"), ("peso_kg", 0.5)],
                descricao="Carregador para baterias da mesma plataforma; não use com outras marcas.")


def multimetro(rng, marca):
    cat = rng.choice(["CAT II 600V", "CAT III 600V", "CAT III 1000V"])
    return dict(nome=f"Multímetro Digital {marca} MD{rng.randint(100, 999)} {cat}", alimentacao="nao_eletrico",
                preco=preco(rng, 55, 620, 1 + 0.8 * ("1000V" in cat)),
                specs=[("cat_seguranca", cat), ("funcoes", rng.choice([8, 12, 18, 24])),
                       ("cabo_m", 0.9), ("peso_kg", 0.3)],
                descricao="Multímetro para medições elétricas; siga a categoria de segurança e os procedimentos.")


def laser(rng, marca):
    tipo = rng.choice(["Trena a Laser", "Nível a Laser"])
    alcance = rng.choice([20, 30, 40, 60]) if tipo == "Trena a Laser" else rng.choice([10, 15, 20])
    return dict(nome=f"{tipo} {marca} {alcance}m", alimentacao="bateria",
                preco=preco(rng, *((120, 520) if tipo == "Trena a Laser" else (280, 1400)),
                            alcance / (40 if tipo == "Trena a Laser" else 15)),
                specs=[("alcance_m", alcance), ("precisao_mm", 2 if tipo == "Trena a Laser" else 3),
                       ("classe_laser", "Classe 2"), ("peso_kg", 0.2 if tipo == "Trena a Laser" else 0.6)],
                descricao=f"{tipo} para medições; não aponte o laser para os olhos.")


def epi(rng, marca):
    item = rng.choice(["Óculos de Proteção", "Luvas de Proteção", "Protetor Auricular Tipo Concha", "Máscara PFF2"])
    return dict(nome=f"{item} {marca}", alimentacao="nao_eletrico",
                preco=preco(rng, 9, 85),
                specs=[("tamanho", "Único" if "Luvas" not in item else rng.choice(["P", "M", "G"])),
                       ("material", rng.choice(["Policarbonato", "Nitrílico", "ABS", "Polipropileno"])),
                       ("aplicacao", "Uso com ferramentas elétricas"), ("qtd_pecas", 1)],
                descricao="Equipamento de proteção individual (dados fictícios; confira o CA do produto real).")


def compressor(rng, marca):
    litros = rng.choice([24, 50, 100])
    v = rng.choice(CORDED + ["bivolt"])
    return dict(nome=f"Compressor de Ar {marca} {litros}L {v}", alimentacao=v,
                preco=preco(rng, 650, 3400, litros / 50),
                specs=[("reservatorio_l", litros), ("pressao_max_psi", rng.choice([116, 120, 140])),
                       ("vazao_l_min", {24: 160, 50: 230, 100: 340}[litros]), ("potencia_w", {24: 1500, 50: 1800, 100: 2200}[litros])],
                descricao="Compressor para pintura e ferramentas pneumáticas; compare a vazão exigida pela pistola.")


def lavadora(rng, marca):
    bar = rng.choice([110, 130, 150])
    v = rng.choice(CORDED)
    return dict(nome=f"Lavadora de Alta Pressão {marca} {bar} bar {v}", alimentacao=v,
                preco=preco(rng, 380, 2300, bar / 130),
                specs=[("pressao_max_bar", bar), ("vazao_l_h", rng.choice([330, 390, 420, 500])),
                       ("potencia_w", {110: 1400, 130: 1700, 150: 2100}[bar]), ("cabo_m", 5)],
                descricao="Lavadora para limpeza; pressão excessiva pode danificar superfícies delicadas.")


CATEGORIAS = [
    ("furadeiras", "Furadeiras", "ferramentas_eletricas", 20, furadeira),
    ("furadeiras_impacto", "Furadeiras de impacto", "ferramentas_eletricas", 22, impacto),
    ("marteletes", "Marteletes", "ferramentas_eletricas", 16, martelete),
    ("parafusadeiras", "Parafusadeiras", "ferramentas_eletricas", 24, parafusadeira),
    ("esmerilhadeiras", "Esmerilhadeiras", "ferramentas_eletricas", 20, esmerilhadeira),
    ("serras_circulares", "Serras circulares", "ferramentas_eletricas", 16, serra_circular),
    ("serras_tico_tico", "Serras tico-tico", "ferramentas_eletricas", 14, tico_tico),
    ("lixadeiras", "Lixadeiras", "ferramentas_eletricas", 14, lixadeira),
    ("brocas", "Brocas", "acessorios", 22, broca),
    ("discos", "Discos de corte e desbaste", "acessorios", 22, disco),
    ("bits_pontas", "Bits e pontas", "acessorios", 14, bit),
    ("laminas_serra", "Lâminas de serra", "acessorios", 12, lamina),
    ("baterias", "Baterias", "baterias_carregadores", 14, bateria),
    ("carregadores", "Carregadores", "baterias_carregadores", 10, carregador),
    ("multimetros", "Multímetros", "medicao", 12, multimetro),
    ("medidores_laser", "Trenas e níveis a laser", "medicao", 10, laser),
    ("epi", "Equipamentos de proteção", "seguranca_epi", 18, epi),
    ("compressores", "Compressores de ar", "equipamentos", 10, compressor),
    ("lavadoras_alta_pressao", "Lavadoras de alta pressão", "equipamentos", 10, lavadora),
]


def gerar():
    rng = random.Random(SEED)
    produtos = []
    n = 0
    for codigo, _nome, _pai, qtd, montar in CATEGORIAS:
        for _ in range(qtd):
            n += 1
            marca = rng.choice(MARCAS)
            p = montar(rng, marca)
            garantia = rng.choice([6, 12, 12, 24]) if p["alimentacao"] != "nao_eletrico" else rng.choice([3, 6])
            specs = [[c, str(v)] for c, v in p["specs"]] + [["garantia_meses", str(garantia)]]
            assert len(specs) == 5, (codigo, specs)
            atual = p["preco"]
            anterior = int(round(atual * rng.uniform(1.0, 1.12) / 100)) * 100 - 10
            estoque = [0 if rng.random() < 0.15 else rng.randint(1, 40) for _u in range(2)]
            produtos.append({
                "sku": f"FAKE-{n:04d}",
                "nome": p["nome"],
                "descricao": p["descricao"],
                "categoria": codigo,
                "marca": marca,
                "alimentacao": p["alimentacao"],
                "especificacoes": specs,
                "precos": [
                    {"preco_centavos": max(anterior, atual), "inicio": "2026-10-01", "fim": "2026-11-01"},
                    {"preco_centavos": atual, "inicio": "2026-11-01", "fim": None},
                ],
                "estoque": {"MATRIZ": estoque[0], "NORTE": estoque[1]},
            })
    dados = {
        "aviso": "DADOS FICTÍCIOS PARA DEMONSTRAÇÃO. Marcas, modelos, preços e estoques são inventados.",
        "seed": SEED,
        "marcas": MARCAS,
        "categorias": [{"codigo": c, "nome": n, "pai": None} for c, n in PAIS]
        + [{"codigo": c, "nome": n, "pai": p} for c, n, p, _q, _f in CATEGORIAS],
        "especificacoes": [{"codigo": c, "nome": n, "unidade": u, "tipo_valor": t} for c, n, u, t in ESPECIFICACOES],
        "produtos": produtos,
    }
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return dados


if __name__ == "__main__":
    d = gerar()
    assocs = sum(len(p["especificacoes"]) for p in d["produtos"])
    print(f"categorias={len(d['categorias'])} marcas={len(d['marcas'])} produtos={len(d['produtos'])} "
          f"especificacoes={len(d['especificacoes'])} associacoes={assocs} -> {SAIDA}")
