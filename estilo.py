"""Paleta de cores e funções de desenho do visual moderno (cantos arredondados, sombra e ícones)."""

import json
import os

PALETA_CLARA = {
    # Base: cinza claro e branco
    "fundo": "#EEF2F8",
    "painel": "#FFFFFF",
    "painel_ativo": "#DCE8FB",
    "campo": "#F0F3F9",
    "linha": "#D3DAE6",
    "sombra": "#7F8FAE",
    # Texto
    "texto": "#1B2433",
    "muted": "#5A6578",
    # Azul
    "destaque": "#2563EB",
    "destaque_hover": "#1D4ED8",
    "destaque_texto": "#2563EB",     # azul usado em textos grandes (ex.: peso no visor)
    "destaque_claro": "#D3E2FB",     # aba ativa, cartão de resumo
    "destaque_escuro": "#1E3A8A",    # texto sobre o destaque_claro
    "total": "#1E40AF",              # valores em R$
    "botao_forte": "#1E40AF",        # botão azul-escuro (ex.: Finalizar)
    "sobre_destaque": "#FFFFFF",
    # Cabeçalho (degradê da esquerda para a direita)
    "cabecalho_ini": "#2A4DB0",
    "cabecalho_fim": "#142F85",
    "cabecalho_sub": "#C7D7F7",
    # Estados
    "desabilitado": "#CBD5E1",
    "texto_desabilitado": "#8896AB",
    "erro": "#D93636",
}

PALETA_ESCURA = {
    # Base: azul-marinho profundo e cinza-azulado
    "fundo": "#0F172A",
    "painel": "#1E293B",
    "painel_ativo": "#27447A",
    "campo": "#152033",
    "linha": "#334155",
    "sombra": "#000000",
    # Texto
    "texto": "#E6EBF4",
    "muted": "#9AA8BD",
    # Azul
    "destaque": "#3069E0",
    "destaque_hover": "#2557C4",
    "destaque_texto": "#6EA2FF",
    "destaque_claro": "#1F3A6B",
    "destaque_escuro": "#BCD3FF",
    "total": "#8DB8FF",
    "botao_forte": "#2F5FD6",
    "sobre_destaque": "#FFFFFF",
    # Cabeçalho
    "cabecalho_ini": "#2447A8",
    "cabecalho_fim": "#0F1F5E",
    "cabecalho_sub": "#C7D7F7",
    # Estados
    "desabilitado": "#334155",
    "texto_desabilitado": "#6B7A90",
    "erro": "#F87171",
}

PALETAS = {"claro": PALETA_CLARA, "escuro": PALETA_ESCURA}

# TEMA é um dicionário único, compartilhado por todos os arquivos. Ao trocar de tema o conteúdo
# dele é substituído "no lugar", então quem já importou o TEMA passa a enxergar as cores novas.
TEMA = {}
_tema_atual = "claro"
_ARQUIVO_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados", "config.json")


def tema_atual() -> str:
    return _tema_atual


def aplicar_tema(nome: str):
    global _tema_atual
    _tema_atual = nome if nome in PALETAS else "claro"
    TEMA.clear()
    TEMA.update(PALETAS[_tema_atual])


def salvar_preferencia_tema(nome: str):
    try:
        os.makedirs(os.path.dirname(_ARQUIVO_CONFIG), exist_ok=True)
        with open(_ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
            json.dump({"tema": nome}, f)
    except OSError:
        pass  # sem permissão de escrita: o tema vale só nesta sessão


def carregar_preferencia_tema() -> str:
    try:
        with open(_ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f).get("tema", "claro")
    except (OSError, json.JSONDecodeError, AttributeError):
        return "claro"


aplicar_tema(carregar_preferencia_tema())  # abre já no último modo escolhido

FONTE = "Segoe UI Semibold"
FONTE_MONO = "Consolas"


def _rgb(cor: str):
    cor = cor.lstrip("#")
    return tuple(int(cor[i:i + 2], 16) for i in (0, 2, 4))


def misturar(cor1: str, cor2: str, t: float) -> str:
    """Mistura duas cores hexadecimais. t=0 devolve cor1, t=1 devolve cor2."""
    a, b = _rgb(cor1), _rgb(cor2)
    return "#%02x%02x%02x" % tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def luminosidade(cor: str) -> float:
    r, g, b = _rgb(cor)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def _forma_arredondada(canvas, x1, y1, x2, y2, r, cor, tags):
    """Preenche um retângulo de cantos arredondados usando 4 arcos + 2 retângulos (raio exato)."""
    if r < 1:
        return canvas.create_rectangle(x1, y1, x2, y2, fill=cor, outline="", tags=tags)
    d = 2 * r
    canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=cor, outline="", tags=tags)
    canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=cor, outline="", tags=tags)
    for ax, ay, inicio in (
        (x1, y1, 90), (x2 - d, y1, 0), (x2 - d, y2 - d, 270), (x1, y2 - d, 180)
    ):
        canvas.create_arc(
            ax, ay, ax + d, ay + d, start=inicio, extent=90, style="pieslice",
            fill=cor, outline="", tags=tags
        )


def retangulo_arredondado(canvas, x1, y1, x2, y2, raio, fill="", outline="", width=1, tags=()):
    """Desenha um retângulo de cantos arredondados (vira uma pílula se o raio for grande)."""
    r = max(0, min(raio, (x2 - x1) / 2, (y2 - y1) / 2))
    if outline and fill and outline != fill:
        _forma_arredondada(canvas, x1, y1, x2, y2, r, outline, tags)
        _forma_arredondada(
            canvas, x1 + width, y1 + width, x2 - width, y2 - width, max(r - width, 0), fill, tags
        )
    else:
        _forma_arredondada(canvas, x1, y1, x2, y2, r, fill or outline, tags)


TAMANHO_ICONE = 14


def desenhar_icone(canvas, nome, x, y, cor, tag="icone"):
    """Desenha um ícone simples (14x14 px) com o canto superior esquerdo em (x, y).

    Os ícones são desenhados com linhas, então não dependem de nenhuma fonte instalada.
    """
    def linha(*pontos, **extra):
        coords = [v + (x if i % 2 == 0 else y) for i, v in enumerate(pontos)]
        canvas.create_line(
            *coords, fill=cor, width=1.6, capstyle="round", joinstyle="round", tags=tag, **extra
        )

    if nome == "mais":
        linha(7, 2, 7, 12)
        linha(2, 7, 12, 7)
    elif nome == "lapis":
        linha(2, 12, 3, 8, 9, 2, 12, 5, 6, 11, 2, 12)
        linha(7, 4, 10, 7)
    elif nome == "lixeira":
        linha(2, 3.5, 12, 3.5)
        linha(5, 3.5, 5, 1.5, 9, 1.5, 9, 3.5)
        linha(3.5, 5, 4.3, 12.5, 9.7, 12.5, 10.5, 5)
        linha(6, 6.5, 6, 11)
        linha(8, 6.5, 8, 11)
    elif nome == "documento":
        linha(3, 1.5, 8.5, 1.5, 11.5, 4.5, 11.5, 12.5, 3, 12.5, 3, 1.5)
        linha(8.5, 1.5, 8.5, 4.5, 11.5, 4.5)
        linha(5, 8, 9.5, 8)
        linha(5, 10.5, 9.5, 10.5)
    elif nome == "check":
        linha(2, 7.5, 5.5, 11, 12, 3.5)
    elif nome == "sair":
        linha(6, 2, 2, 2, 2, 12, 6, 12)
        linha(5, 7, 12, 7)
        linha(9.5, 4, 12.5, 7, 9.5, 10)
    elif nome == "impressora":
        linha(4, 5, 4, 1.5, 10, 1.5, 10, 5)
        linha(2, 5, 12, 5, 12, 10.5, 2, 10.5, 2, 5)
        linha(4, 8.5, 10, 8.5, 10, 12.5, 4, 12.5, 4, 8.5)
    elif nome == "tema":
        canvas.create_oval(x + 1.5, y + 1.5, x + 12.5, y + 12.5, outline=cor, width=1.6, tags=tag)
        canvas.create_arc(
            x + 1.5, y + 1.5, x + 12.5, y + 12.5, start=90, extent=180, style="pieslice",
            fill=cor, outline=cor, tags=tag
        )
    elif nome == "atualizar":
        linha(11.5, 5, 10, 2.5, 7, 1.8, 3.5, 3.5, 2, 7, 3.5, 10.5, 7, 12.2, 10, 11.5, 11.8, 9)
        linha(11.8, 1.8, 11.5, 5, 8.3, 4.6)
