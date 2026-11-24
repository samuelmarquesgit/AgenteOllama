"""Configuração centralizada (RT-012).

Todas as variáveis de ambiente do Tork ficam registradas em VARIAVEIS (nome, padrão e descrição);
o `.env.example` na raiz é conferido contra este registro por teste. Os valores são lidos no momento
do uso, não na importação, para que testes e operadores possam alterá-los sem reiniciar o módulo.

Um arquivo `.env` na raiz (opcional, fora do git) é carregado por `carregar_env()` sem sobrescrever
variáveis já definidas no ambiente.
"""

import os
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
VERDADEIRO = ("1", "true", "sim", "yes")
FALSO = ("0", "false", "nao", "não", "no")


@dataclass(frozen=True)
class Variavel:
    nome: str
    padrao: str
    descricao: str


VARIAVEIS: dict[str, Variavel] = {v.nome: v for v in (
    Variavel("BANCO_SQLITE", "data/loja.db", "Caminho do banco SQLite (criado e migrado na primeira execução)."),
    Variavel("USAR_OLLAMA", "true", "false desliga a IA generativa: perguntas fora da base recebem resposta segura."),
    Variavel("OLLAMA_HOST", "", "Endereço do Ollama (vazio = padrão do cliente, http://localhost:11434)."),
    Variavel("OLLAMA_MODELO", "llama3.2", "Modelo usado nas respostas e na reescrita de contexto."),
    Variavel("OLLAMA_TIMEOUT", "45", "Tempo máximo (s) de uma resposta da IA; depois disso, resposta segura (RT-010)."),
    Variavel("OLLAMA_TIMEOUT_REESCRITA", "10", "Tempo máximo (s) da reescrita de contexto; depois disso, usa a pergunta original."),
    Variavel("TORK_SERVIR_SUGESTOES", "true", "false serve só conteúdo aprovado: sugestões da IA não revisadas não são reaproveitadas (RT-002)."),
)}


def texto(nome: str) -> str:
    return os.getenv(nome, VARIAVEIS[nome].padrao)


def ligado(nome: str) -> bool:
    """Liga/desliga: aceita true/false, 1/0, sim/não. Valor desconhecido usa o padrão."""
    valor = texto(nome).strip().lower()
    if valor in VERDADEIRO:
        return True
    if valor in FALSO:
        return False
    return VARIAVEIS[nome].padrao in VERDADEIRO


def segundos(nome: str, minimo: float = 1.0) -> float:
    try:
        return max(minimo, float(texto(nome)))
    except ValueError:
        return float(VARIAVEIS[nome].padrao)


def caminho(nome: str) -> Path:
    p = Path(texto(nome))
    return p if p.is_absolute() else RAIZ / p


def carregar_env(arquivo: Path = RAIZ / ".env") -> None:
    """Lê linhas NOME=valor de um .env opcional; não sobrescreve o ambiente e ignora nomes desconhecidos."""
    if not arquivo.is_file():
        return
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        nome, valor = (parte.strip() for parte in linha.split("=", 1))
        if nome in VARIAVEIS:
            os.environ.setdefault(nome, valor.strip("\"'"))
