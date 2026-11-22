"""Componentes visuais próprios (cantos arredondados, sombra suave, degradê), feitos com Canvas.

O Tkinter não tem cantos arredondados nem sombra de fábrica, então aqui cada componente
desenha a própria "pele" num Canvas e se comporta como um widget normal (pack/grid/bind).
"""

import math
import tkinter as tk
import tkinter.font as tkfont

from estilo import (
    TEMA, FONTE, TAMANHO_ICONE, misturar, luminosidade, retangulo_arredondado, desenhar_icone
)


def fonte_medida(master, spec):
    """Devolve um objeto Font para medir textos. O cache fica no próprio Tk (some junto com ele)."""
    raiz = master._root()
    if not hasattr(raiz, "_cache_fontes"):
        raiz._cache_fontes = {}
    chave = tuple(spec) if isinstance(spec, (tuple, list)) else spec
    if chave not in raiz._cache_fontes:
        raiz._cache_fontes[chave] = tkfont.Font(root=raiz, font=spec)
    return raiz._cache_fontes[chave]


class BotaoArredondado(tk.Canvas):
    """Botão com cantos arredondados (pílula), ícone opcional, borda opcional e efeito ao passar o mouse.

    Aceita configure(bg=..., fg=..., text=..., state=..., borda=...) como um botão comum.
    """

    def __init__(self, master, text="", command=None, bg=None, fg=None, hover=None,
                 fundo_pai=None, borda=None, raio=14, font=(FONTE, 10), font_sec=None,
                 fg_sec=None, icone=None, alinhamento="center", padx=16, pady=9,
                 sombra=False, state="normal"):
        super().__init__(
            master, bg=fundo_pai or TEMA["fundo"], highlightthickness=0, bd=0,
            width=10, height=10, cursor="hand2" if state == "normal" else "arrow"
        )
        self._bg = bg or TEMA["painel"]
        self._fg = fg or TEMA["texto"]
        self._hover = hover
        self._borda = borda
        self._raio = raio
        self._font = font
        self._font_sec = font_sec or font
        self._fg_sec = fg_sec
        self._icone = icone
        self._alin = alinhamento
        self._padx = padx
        self._pady = pady
        self._sombra = sombra
        self._texto = text
        self._comando = command
        self._estado = state
        self._sobre = False
        self._fundo_pai = fundo_pai or TEMA["fundo"]

        self._atualizar_tamanho()
        self.bind("<Enter>", self._entrou)
        self.bind("<Leave>", self._saiu)
        self.bind("<ButtonRelease-1>", self._soltou)
        self.bind("<Configure>", lambda e: self._desenhar())
        self._desenhar()

    # ---------- tamanho ----------
    def _atualizar_tamanho(self):
        f1 = fonte_medida(self, self._font)
        f2 = fonte_medida(self, self._font_sec)
        linhas = self._texto.split("\n") if self._texto else [""]
        altura_texto = f1.metrics("linespace") + f2.metrics("linespace") * (len(linhas) - 1)
        largura_texto = max(
            (f1 if i == 0 else f2).measure(linha) for i, linha in enumerate(linhas)
        )
        largura_icone = (TAMANHO_ICONE + 8) if self._icone else 0
        self._altura = int(altura_texto + 2 * self._pady + (4 if self._sombra else 0))
        self._largura_req = int(largura_texto + largura_icone + 2 * self._padx)
        tk.Canvas.configure(self, width=self._largura_req, height=self._altura)

    # ---------- desenho ----------
    def _cor_hover(self):
        if self._hover:
            return self._hover
        if luminosidade(self._bg) > 0.6:
            return misturar(self._bg, TEMA["destaque"], 0.10)
        return misturar(self._bg, "#000000", 0.15)

    def _desenhar(self):
        self.delete("all")
        largura = self.winfo_width()
        if largura <= 2:
            largura = self._largura_req
        altura = self._altura
        margem_x = 2 if self._sombra else 1
        x1, y1 = margem_x, 1
        x2, y2 = largura - margem_x, altura - (4 if self._sombra else 1)

        ativo = self._estado == "normal"
        preenchimento = self._cor_hover() if (self._sobre and ativo) else self._bg

        if self._sombra:
            for deslocamento, forca in ((3, 0.035), (2, 0.06), (1, 0.09)):
                retangulo_arredondado(
                    self, x1, y1 + deslocamento, x2, y2 + deslocamento, self._raio,
                    fill=misturar(self._fundo_pai, TEMA["sombra"], forca), outline=""
                )
        retangulo_arredondado(
            self, x1, y1, x2, y2, self._raio, fill=preenchimento,
            outline=self._borda or preenchimento, width=1
        )

        cor_texto = self._fg if ativo else TEMA["texto_desabilitado"]
        f1 = fonte_medida(self, self._font)
        f2 = fonte_medida(self, self._font_sec)
        linhas = self._texto.split("\n") if self._texto else [""]
        alturas = [f1.metrics("linespace")] + [f2.metrics("linespace")] * (len(linhas) - 1)
        altura_texto = sum(alturas)
        y = y1 + ((y2 - y1) - altura_texto) / 2

        if self._alin == "center":
            largura_texto = f1.measure(linhas[0])
            largura_icone = (TAMANHO_ICONE + 8) if self._icone else 0
            x = (largura - (largura_texto + largura_icone)) / 2
            if self._icone:
                desenhar_icone(self, self._icone, x, y + (alturas[0] - TAMANHO_ICONE) / 2, cor_texto)
                x += largura_icone
            self.create_text(x, y, text=linhas[0], anchor="nw", font=self._font, fill=cor_texto)
        else:
            x = self._padx
            for i, linha in enumerate(linhas):
                cor = cor_texto if (i == 0 or not self._fg_sec or not ativo) else self._fg_sec
                self.create_text(
                    x, y, text=linha, anchor="nw",
                    font=self._font if i == 0 else self._font_sec, fill=cor
                )
                y += alturas[i]

    # ---------- eventos ----------
    def _entrou(self, _evento):
        self._sobre = True
        self._desenhar()

    def _saiu(self, _evento):
        self._sobre = False
        self._desenhar()

    def _soltou(self, evento):
        dentro = 0 <= evento.x <= self.winfo_width() and 0 <= evento.y <= self.winfo_height()
        if dentro:
            self.invoke()

    def invoke(self):
        if self._estado == "normal" and self._comando:
            self._comando()

    # ---------- interface parecida com a de um tk.Button ----------
    def configure(self, cnf=None, **kw):
        if isinstance(cnf, str):
            return tk.Canvas.configure(self, cnf)
        if isinstance(cnf, dict):
            kw = {**cnf, **kw}

        redesenhar = recalcular = False
        for chave in list(kw):
            if chave in ("bg", "background"):
                self._bg = kw.pop(chave)
                redesenhar = True
            elif chave in ("fg", "foreground"):
                self._fg = kw.pop(chave)
                redesenhar = True
            elif chave == "fg_sec":
                self._fg_sec = kw.pop(chave)
                redesenhar = True
            elif chave == "hover":
                self._hover = kw.pop(chave)
            elif chave == "borda":
                self._borda = kw.pop(chave)
                redesenhar = True
            elif chave == "icone":
                self._icone = kw.pop(chave)
                recalcular = True
            elif chave == "text":
                self._texto = kw.pop(chave)
                recalcular = True
            elif chave == "command":
                self._comando = kw.pop(chave)
            elif chave == "state":
                self._estado = kw.pop(chave)
                if "cursor" not in kw:
                    kw["cursor"] = "hand2" if self._estado == "normal" else "arrow"
                redesenhar = True

        if kw:
            tk.Canvas.configure(self, **kw)
        if recalcular:
            self._atualizar_tamanho()
            redesenhar = True
        if redesenhar:
            self._desenhar()

    config = configure

    def cget(self, chave):
        interno = {
            "bg": self._bg, "background": self._bg, "fg": self._fg, "foreground": self._fg,
            "text": self._texto, "state": self._estado,
        }
        if chave in interno:
            return interno[chave]
        return tk.Canvas.cget(self, chave)

    __getitem__ = cget


class CartaoArredondado(tk.Canvas):
    """Cartão de cantos arredondados com sombra suave. Coloque os widgets dentro de `.interior`.

    ajustar=True  -> a altura acompanha o conteúdo (bom para cartões numa lista).
    ajustar=False -> o cartão preenche o espaço que o layout der a ele.
    """

    def __init__(self, master, bg=None, fundo_pai=None, raio=18, sombra=True, padx=16, pady=14,
                 ajustar=False, borda=None):
        super().__init__(
            master, bg=fundo_pai or TEMA["fundo"], highlightthickness=0, bd=0, width=10, height=10
        )
        self._cor = bg or TEMA["painel"]
        self._fundo_pai = fundo_pai or TEMA["fundo"]
        self._raio = raio
        self._sombra = sombra
        self._padx = padx
        self._pady = pady
        self._ajustar = ajustar
        self._borda = borda
        self._extra_base = 4 if sombra else 1
        self._margem_x = 2 if sombra else 1

        self.interior = tk.Frame(self, bg=self._cor)
        self._janela = self.create_window(
            self._margem_x + padx, 1 + pady, window=self.interior, anchor="nw"
        )
        self.bind("<Configure>", self._ao_redimensionar)
        if ajustar:
            self.interior.bind("<Configure>", lambda e: self.atualizar_altura())
            # O Tk só "mostra" o conteúdo depois que o cartão tem altura. Por isso o primeiro ajuste
            # é feito logo que quem criou o cartão terminar de colocar os widgets dentro dele.
            self.after_idle(self._primeiro_ajuste)

    def _primeiro_ajuste(self):
        try:
            self.interior.update_idletasks()
            self.atualizar_altura()
        except tk.TclError:
            pass  # o cartão já foi destruído (a lista foi refeita)

    def atualizar_altura(self):
        necessario = int(self.interior.winfo_reqheight() + 2 * self._pady + 1 + self._extra_base)
        if abs(int(float(self["height"])) - necessario) > 1:
            self.configure(height=necessario)

    def _ao_redimensionar(self, evento):
        largura, altura = evento.width, evento.height
        self.delete("fundo")
        x1, y1 = self._margem_x, 1
        x2, y2 = largura - self._margem_x, altura - self._extra_base
        if self._sombra:
            for deslocamento, forca in ((3, 0.035), (2, 0.06), (1, 0.09)):
                retangulo_arredondado(
                    self, x1, y1 + deslocamento, x2, y2 + deslocamento, self._raio,
                    fill=misturar(self._fundo_pai, TEMA["sombra"], forca), outline="", tags="fundo"
                )
        retangulo_arredondado(
            self, x1, y1, x2, y2, self._raio, fill=self._cor,
            outline=self._borda or self._cor, width=1, tags="fundo"
        )
        self.tag_lower("fundo")

        opcoes = {"width": max(largura - 2 * (self._margem_x + self._padx), 1)}
        if not self._ajustar:
            opcoes["height"] = max(altura - (1 + self._pady) - (self._pady + self._extra_base), 1)
        self.itemconfigure(self._janela, **opcoes)


class EntradaArredondada(tk.Canvas):
    """Campo de texto com fundo arredondado. O campo de verdade fica em `.entry`."""

    def __init__(self, master, fundo_pai=None, bg=None, fg=None, font=(FONTE, 11),
                 justify="left", show="", largura_chars=None, raio=12, padx=14, pady=9):
        f = fonte_medida(master, font)
        altura = f.metrics("linespace") + 2 * pady
        largura = (f.measure("0") * largura_chars + 2 * padx) if largura_chars else 200
        super().__init__(
            master, bg=fundo_pai or TEMA["painel"], highlightthickness=0, bd=0,
            width=int(largura), height=int(altura)
        )
        self._campo = bg or TEMA["campo"]
        self._raio = raio
        self._padx = padx
        self._foco = False

        self.entry = tk.Entry(
            self, bd=0, relief="flat", highlightthickness=0, bg=self._campo,
            fg=fg or TEMA["texto"], insertbackground=fg or TEMA["texto"], font=font,
            justify=justify, show=show
        )
        self._janela = self.create_window(
            padx, altura / 2, window=self.entry, anchor="w", width=int(largura - 2 * padx)
        )
        self.bind("<Configure>", self._ao_redimensionar)
        self.bind("<Button-1>", lambda e: self.entry.focus_set())
        self.entry.bind("<FocusIn>", lambda e: self._mudar_foco(True), add="+")
        self.entry.bind("<FocusOut>", lambda e: self._mudar_foco(False), add="+")

    def _mudar_foco(self, ligado):
        self._foco = ligado
        self._ao_redimensionar()

    def _ao_redimensionar(self, evento=None):
        largura = evento.width if evento else self.winfo_width()
        altura = evento.height if evento else self.winfo_height()
        if largura <= 2:
            return
        self.delete("fundo")
        retangulo_arredondado(
            self, 1, 1, largura - 1, altura - 1, self._raio, fill=self._campo,
            outline=TEMA["destaque"] if self._foco else self._campo, width=2 if self._foco else 1,
            tags="fundo"
        )
        self.tag_lower("fundo")
        self.coords(self._janela, self._padx, altura / 2)
        self.itemconfigure(self._janela, width=max(largura - 2 * self._padx, 1))


class CabecalhoDegrade(tk.Canvas):
    """Faixa de topo com degradê azul, cantos arredondados, título, subtítulo e botão "Sair"."""

    def __init__(self, master, titulo, subtitulo="", ao_sair=None, fundo_pai=None,
                 altura=80, raio=22):
        super().__init__(
            master, bg=fundo_pai or TEMA["fundo"], highlightthickness=0, bd=0, height=altura
        )
        self._titulo = titulo
        self._subtitulo = subtitulo
        self._altura = altura
        self._raio = raio
        self._pendente = None
        self._botao = None
        self._janela_botao = None

        if ao_sair:
            cor_local = TEMA["cabecalho_fim"]
            self._botao = BotaoArredondado(
                self, text="Sair", command=ao_sair, bg=cor_local, fg="#FFFFFF",
                fundo_pai=cor_local, borda=misturar(cor_local, "#FFFFFF", 0.75), raio=999,
                font=(FONTE, 9, "bold"), icone="sair", padx=16, pady=7,
                hover=misturar(cor_local, "#FFFFFF", 0.18)
            )
            self._janela_botao = self.create_window(0, 0, window=self._botao, anchor="e")
        self.bind("<Configure>", self._agendar)

    def _agendar(self, _evento=None):
        if self._pendente is None:
            self._pendente = self.after(10, self._desenhar)

    def _desenhar(self):
        self._pendente = None
        largura, altura = self.winfo_width(), self.winfo_height()
        if largura <= 2:
            return
        self.delete("degrade")
        self.delete("texto")
        r = min(self._raio, altura / 2)
        x = 0
        while x < largura:
            distancia = min(x, largura - 1 - x)
            passo = 1 if distancia < r else 3  # passo fino nos cantos deixa a curva mais lisa
            cor = misturar(TEMA["cabecalho_ini"], TEMA["cabecalho_fim"], x / max(largura - 1, 1))
            deslocamento = 0 if distancia >= r else r - math.sqrt(max(r * r - (r - distancia) ** 2, 0))
            self.create_line(
                x + passo / 2, deslocamento, x + passo / 2, altura - deslocamento,
                fill=cor, width=passo, tags="degrade"
            )
            x += passo
        self.tag_lower("degrade")

        meio = altura / 2
        self.create_text(
            28, meio - (11 if self._subtitulo else 0), text=self._titulo, anchor="w",
            font=(FONTE, 17, "bold"), fill="#FFFFFF", tags="texto"
        )
        if self._subtitulo:
            self.create_text(
                28, meio + 14, text=self._subtitulo, anchor="w",
                font=(FONTE, 9), fill=TEMA["cabecalho_sub"], tags="texto"
            )
        if self._janela_botao is not None:
            self.coords(self._janela_botao, largura - 24, meio)
