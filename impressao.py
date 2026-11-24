"""Comprovante de pesagem (a "notinha"): monta o texto e imprime em impressora térmica de cupom.

As impressoras de cupom (Elgin, Epson, Bematech, Daruma, Tanca, Xprinter e as genéricas) quase
todas entendem o mesmo "idioma" de comandos, o ESC/POS. O programa manda esses comandos
para a impressora que estiver instalada no Windows, então funciona com qualquer modelo.
Sem impressora configurada, a nota é salva em arquivo de texto.
"""

import json
import os
import subprocess
import textwrap
import unicodedata
from datetime import datetime

PASTA_DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")
ARQUIVO_CONFIG = os.path.join(PASTA_DADOS, "impressao.json")
PASTA_NOTAS = os.path.join(PASTA_DADOS, "notas")

# largura do papel (mm) -> quantidade de caracteres por linha
LARGURAS = {58: 32, 80: 48}

# chave -> (nome mostrado, número da tabela de caracteres ESC/POS, codificação do Python)
ACENTOS = {
    "cp850": ("Padrão (CP850)", 2, "cp850"),
    "cp860": ("Português (CP860)", 3, "cp860"),
    "cp1252": ("Windows (CP1252)", 16, "cp1252"),
    "ascii": ("Sem acentos", None, "ascii"),
}

CONFIG_PADRAO = {"impressora": "", "largura_mm": 58, "acentos": "cp850", "cortar": False}


class ErroImpressao(Exception):
    """Falha ao entregar a nota (mensagem já pensada para ser mostrada ao usuário)."""


# ---------- Configuração ----------
def carregar_config() -> dict:
    config = dict(CONFIG_PADRAO)
    try:
        with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
            salvo = json.load(f)
        if isinstance(salvo, dict):
            config.update({k: v for k, v in salvo.items() if k in CONFIG_PADRAO})
    except (OSError, json.JSONDecodeError):
        pass
    if config["largura_mm"] not in LARGURAS:
        config["largura_mm"] = CONFIG_PADRAO["largura_mm"]
    if config["acentos"] not in ACENTOS:
        config["acentos"] = CONFIG_PADRAO["acentos"]
    return config


def salvar_config(config: dict):
    os.makedirs(PASTA_DADOS, exist_ok=True)
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
        json.dump({k: config[k] for k in CONFIG_PADRAO}, f, ensure_ascii=False, indent=2)


# ---------- Texto da nota ----------
def _numero(valor: float) -> str:
    """Formato brasileiro: 1.234,56"""
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def montar_linhas(registro: dict, empresa: str, largura: int) -> list:
    """Devolve a nota como lista de (texto, negrito), cada texto com no máximo `largura` caracteres."""
    L = largura
    dupla, simples = "=" * L, "-" * L
    linhas = [(dupla, False)]
    for trecho in textwrap.wrap((empresa or "").upper(), L):
        linhas.append((trecho.center(L).rstrip(), True))
    linhas.append(("COMPROVANTE DE PESAGEM".center(L).rstrip(), True))
    linhas.append((dupla, False))

    linhas.append((f"Data/hora: {registro['data']}", False))
    if registro.get("cliente"):
        for trecho in textwrap.wrap(f"Cliente: {registro['cliente']}", L):
            linhas.append((trecho, False))
    linhas.append((simples, False))

    for item in registro["itens"]:
        linhas.append((item["nome"][:L], True))
        esquerda = f"  {_numero(item['peso'])} kg x {_numero(item['preco'])}"
        direita = _numero(item["valor"])
        if len(esquerda) + len(direita) + 1 <= L:
            linhas.append((esquerda + " " * (L - len(esquerda) - len(direita)) + direita, False))
        else:  # números muito grandes: divide em duas linhas
            linhas.append((esquerda[:L], False))
            linhas.append((direita.rjust(L), False))

    linhas.append((simples, False))
    total = f"R$ {_numero(registro['total'])}"
    linhas.append(("TOTAL".ljust(L - len(total)) + total, True))
    linhas.append((dupla, False))
    linhas.append(("Obrigado!".center(L).rstrip(), False))
    return linhas


def registro_de_teste() -> dict:
    itens = [("Alumínio", 1.5, 4.0), ("Plástico", 2.0, 1.0), ("Papelão", 10.0, 0.2)]
    return {
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "cliente": "Teste de Impressão",
        "itens": [{"nome": n, "peso": p, "preco": pr, "valor": p * pr} for n, p, pr in itens],
        "total": sum(p * pr for _, p, pr in itens),
    }


# ---------- Comandos ESC/POS ----------
def _codificar(texto: str, codec: str) -> bytes:
    if codec == "ascii":  # tira os acentos: serve em qualquer impressora
        texto = unicodedata.normalize("NFKD", texto)
        return texto.encode("ascii", "ignore")
    return texto.encode(codec, errors="replace")


def montar_escpos(linhas: list, config: dict) -> bytes:
    _, tabela, codec = ACENTOS.get(config.get("acentos"), ACENTOS["cp850"])
    dados = bytearray(b"\x1b@")                     # reinicia a impressora
    if tabela is not None:
        dados += bytes([0x1B, 0x74, tabela])        # escolhe a tabela de caracteres (acentos)
    for texto, negrito in linhas:
        if negrito:
            dados += b"\x1bE\x01"                   # negrito ligado
        dados += _codificar(texto, codec) + b"\n"
        if negrito:
            dados += b"\x1bE\x00"                   # negrito desligado
    dados += b"\x1bd\x04"                           # avança 4 linhas (para a nota sair da máquina)
    if config.get("cortar"):
        dados += b"\x1dVB\x00"                      # corta o papel (só impressoras com guilhotina)
    return bytes(dados)


# ---------- Windows: impressoras e envio direto ----------
def listar_impressoras() -> list:
    """Nomes das impressoras instaladas no Windows (lista vazia em outros sistemas)."""
    if os.name != "nt":
        return []
    comando = (
        "[Console]::OutputEncoding=[Text.Encoding]::UTF8; "
        "Get-Printer | Select-Object -ExpandProperty Name"
    )
    try:
        resultado = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", comando],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        return []
    return [linha.strip() for linha in resultado.stdout.splitlines() if linha.strip()]


def enviar_bytes_para_impressora(nome: str, dados: bytes):
    """Envia os bytes "crus" (RAW) para a impressora instalada no Windows."""
    if os.name != "nt":
        raise ErroImpressao("A impressão direta só funciona no Windows.")

    import ctypes
    from ctypes import wintypes

    class DOC_INFO_1W(ctypes.Structure):
        _fields_ = [
            ("pDocName", wintypes.LPWSTR),
            ("pOutputFile", wintypes.LPWSTR),
            ("pDatatype", wintypes.LPWSTR),
        ]

    spool = ctypes.WinDLL("winspool.drv", use_last_error=True)
    spool.OpenPrinterW.argtypes = [wintypes.LPWSTR, ctypes.POINTER(wintypes.HANDLE), ctypes.c_void_p]
    spool.OpenPrinterW.restype = wintypes.BOOL
    spool.StartDocPrinterW.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(DOC_INFO_1W)]
    spool.StartDocPrinterW.restype = wintypes.DWORD
    spool.StartPagePrinter.argtypes = [wintypes.HANDLE]
    spool.StartPagePrinter.restype = wintypes.BOOL
    spool.WritePrinter.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)
    ]
    spool.WritePrinter.restype = wintypes.BOOL
    spool.EndPagePrinter.argtypes = [wintypes.HANDLE]
    spool.EndDocPrinter.argtypes = [wintypes.HANDLE]
    spool.ClosePrinter.argtypes = [wintypes.HANDLE]

    manipulador = wintypes.HANDLE()
    if not spool.OpenPrinterW(nome, ctypes.byref(manipulador), None):
        raise ErroImpressao(
            f"Não consegui abrir a impressora \"{nome}\". Confira se ela está ligada, "
            "instalada no Windows e se o nome está certo."
        )
    try:
        documento = DOC_INFO_1W("Nota de pesagem", None, "RAW")
        if not spool.StartDocPrinterW(manipulador, 1, ctypes.byref(documento)):
            raise ErroImpressao(f"A impressora \"{nome}\" não aceitou o trabalho de impressão.")
        try:
            spool.StartPagePrinter(manipulador)
            escritos = wintypes.DWORD(0)
            buffer = ctypes.create_string_buffer(dados, len(dados))
            if not spool.WritePrinter(manipulador, buffer, len(dados), ctypes.byref(escritos)):
                raise ErroImpressao(f"Falha ao enviar a nota para a impressora \"{nome}\".")
            spool.EndPagePrinter(manipulador)
        finally:
            spool.EndDocPrinter(manipulador)
    finally:
        spool.ClosePrinter(manipulador)


# ---------- Entrega da nota ----------
def salvar_em_arquivo(linhas: list) -> str:
    os.makedirs(PASTA_NOTAS, exist_ok=True)
    nome = f"nota_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.txt"
    caminho = os.path.join(PASTA_NOTAS, nome)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(texto for texto, _ in linhas))
    return caminho


def _entregar(linhas: list, config: dict) -> str:
    impressora = (config.get("impressora") or "").strip()
    if impressora:
        enviar_bytes_para_impressora(impressora, montar_escpos(linhas, config))
        return f"Nota enviada para a impressora \"{impressora}\"."
    caminho = salvar_em_arquivo(linhas)
    return f"Nenhuma impressora configurada, então a nota foi salva em:\n{caminho}"


def emitir_nota(registro: dict, empresa: str, config: dict = None) -> str:
    config = config or carregar_config()
    linhas = montar_linhas(registro, empresa, LARGURAS[config["largura_mm"]])
    return _entregar(linhas, config)


def emitir_teste(empresa: str, config: dict) -> str:
    linhas = montar_linhas(registro_de_teste(), empresa or "Teste", LARGURAS[config["largura_mm"]])
    largura = LARGURAS[config["largura_mm"]]
    # linha extra para conferir os acentos no papel
    linhas.insert(-2, ("Acentos: ç ã é í ó ú ü".ljust(largura)[:largura], False))
    return _entregar(linhas, config)
