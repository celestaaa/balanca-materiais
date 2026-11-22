"""Interface Tkinter da Balança de Materiais: visual moderno, organizada em abas."""

import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

from materiais import MATERIAIS
from estilo import TEMA, FONTE, FONTE_MONO
from widgets import BotaoArredondado, CartaoArredondado, EntradaArredondada, CabecalhoDegrade
from modelo import Ticket
from armazenamento import GerenciadorHistorico, gerar_relatorio
from precos import GerenciadorPrecos
from clientes import GerenciadorClientes, formatar_documento, formatar_telefone


# ---------- Botões prontos (para manter o mesmo visual em todas as telas) ----------
def botao_contorno(pai, texto, comando, icone=None, fundo_pai=None, pady=8, padx=14):
    """Pílula branca com borda cinza (ação secundária)."""
    return BotaoArredondado(
        pai, text=texto, command=comando, icone=icone, bg=TEMA["painel"], fg=TEMA["texto"],
        borda=TEMA["linha"], fundo_pai=fundo_pai or TEMA["fundo"], raio=999,
        font=(FONTE, 9), padx=padx, pady=pady
    )


def botao_cheio(pai, texto, comando, icone=None, fundo_pai=None, pady=8, padx=14, cor=None,
                fonte=(FONTE, 9, "bold")):
    """Pílula azul preenchida (ação principal)."""
    return BotaoArredondado(
        pai, text=texto, command=comando, icone=icone, bg=cor or TEMA["destaque"],
        fg=TEMA["sobre_destaque"], hover=TEMA["destaque_hover"], fundo_pai=fundo_pai or TEMA["fundo"],
        raio=999, font=fonte, padx=padx, pady=pady
    )


class BalancaApp:
    def __init__(self, root: tk.Tk, empresa: str = "", ao_sair=None):
        self.root = root
        self.empresa = empresa
        self.ao_sair = ao_sair
        self.root.title(f"Balança de Materiais — {empresa}" if empresa else "Balança de Materiais")
        self.root.configure(bg=TEMA["fundo"])
        self.root.geometry("980x680")
        self.root.minsize(900, 640)

        self.ticket = Ticket()
        self.historico = GerenciadorHistorico()
        self.precos = GerenciadorPrecos(MATERIAIS)
        self.clientes = GerenciadorClientes()
        self._cliente_sel_id = None
        self._ids_combo = [None]
        self._botoes_cliente = {}
        self.material_selecionado = None

        self._montar_estilo()
        self._montar_abas()

    # ---------- Estilo ----------
    def _montar_estilo(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=TEMA["fundo"])
        style.configure("Painel.TFrame", background=TEMA["painel"])
        style.configure("TLabel", background=TEMA["fundo"], foreground=TEMA["texto"], font=(FONTE, 10))
        style.configure("Painel.TLabel", background=TEMA["painel"], foreground=TEMA["texto"], font=(FONTE, 10))
        style.configure("Muted.TLabel", background=TEMA["fundo"], foreground=TEMA["muted"], font=(FONTE, 9))
        style.configure("Titulo.TLabel", background=TEMA["fundo"], foreground=TEMA["texto"], font=(FONTE, 16, "bold"))

        # Lista de seleção sem borda (ela fica dentro de um cartão arredondado)
        style.configure(
            "TCombobox", fieldbackground=TEMA["painel"], background=TEMA["painel"],
            foreground=TEMA["texto"], arrowcolor=TEMA["muted"], bordercolor=TEMA["painel"],
            lightcolor=TEMA["painel"], darkcolor=TEMA["painel"], borderwidth=0, padding=4
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", TEMA["painel"])],
            background=[("readonly", TEMA["painel"]), ("active", TEMA["painel"])],
            foreground=[("readonly", TEMA["texto"])],
            selectbackground=[("readonly", TEMA["painel"])],
            selectforeground=[("readonly", TEMA["texto"])],
            arrowcolor=[("active", TEMA["destaque"])],
        )

        # Barra de rolagem fina, sem setas
        style.layout("Vertical.TScrollbar", [
            ("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
                ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})
            ]})
        ])
        style.configure(
            "Vertical.TScrollbar", troughcolor=TEMA["fundo"], background=TEMA["linha"],
            bordercolor=TEMA["fundo"], lightcolor=TEMA["linha"], darkcolor=TEMA["linha"],
            gripcount=0, width=9
        )
        style.map("Vertical.TScrollbar", background=[("active", TEMA["muted"])])

        self.root.option_add("*TCombobox*Listbox.background", TEMA["painel"])
        self.root.option_add("*TCombobox*Listbox.foreground", TEMA["texto"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", TEMA["destaque"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", TEMA["sobre_destaque"])
        self.root.option_add("*TCombobox*Listbox.font", "{Segoe UI Semibold} 10")

    # ---------- Estrutura em abas ----------
    def _montar_abas(self):
        subtitulo = f"Empresa: {self.empresa}" if self.empresa else "Pese, calcule e acompanhe suas pesagens."
        CabecalhoDegrade(
            self.root, "Balança de Materiais", subtitulo,
            ao_sair=self._sair if self.ao_sair else None, fundo_pai=TEMA["fundo"]
        ).pack(fill="x", padx=14, pady=(14, 0))

        self.abas_nomes = ["Pesagem", "Histórico", "Clientes"]
        self.aba_atual = 0
        self.animando = False

        barra_abas = tk.Frame(self.root, bg=TEMA["fundo"])
        barra_abas.pack(fill="x", padx=18, pady=(14, 4))

        self.botoes_aba = []
        for i, nome in enumerate(self.abas_nomes):
            btn = BotaoArredondado(
                barra_abas, text=nome, command=lambda idx=i: self._trocar_aba(idx),
                raio=999, padx=20, pady=7, font=(FONTE, 10), fundo_pai=TEMA["fundo"]
            )
            btn.pack(side="left", padx=(0, 8))
            self.botoes_aba.append(btn)
        self._pintar_abas()

        # Área de conteúdo: painéis sobrepostos que deslizam ao trocar de aba
        self.area_conteudo = tk.Frame(self.root, bg=TEMA["fundo"])
        self.area_conteudo.pack(fill="both", expand=True, padx=18, pady=(4, 14))

        aba_pesagem = ttk.Frame(self.area_conteudo, style="TFrame")
        aba_historico = ttk.Frame(self.area_conteudo, style="TFrame")
        aba_clientes = ttk.Frame(self.area_conteudo, style="TFrame")
        self.paineis_aba = [aba_pesagem, aba_historico, aba_clientes]
        aba_pesagem.place(relx=0, rely=0, relwidth=1, relheight=1)
        aba_historico.place(relx=1, rely=0, relwidth=1, relheight=1)
        aba_clientes.place(relx=1, rely=0, relwidth=1, relheight=1)

        self._montar_aba_pesagem(aba_pesagem)
        self._montar_aba_historico(aba_historico)
        self._montar_aba_clientes(aba_clientes)

    def _pintar_abas(self):
        for i, btn in enumerate(self.botoes_aba):
            if i == self.aba_atual:
                btn.configure(
                    bg=TEMA["destaque_claro"], fg=TEMA["destaque_escuro"],
                    borda=TEMA["destaque_claro"], hover=TEMA["destaque_claro"]
                )
            else:
                btn.configure(bg=TEMA["fundo"], fg=TEMA["muted"], borda=TEMA["linha"], hover=None)

    def _trocar_aba(self, indice):
        if indice == self.aba_atual or self.animando:
            return

        direcao = 1 if indice > self.aba_atual else -1
        origem = self.paineis_aba[self.aba_atual]
        destino = self.paineis_aba[indice]

        destino.place(relx=direcao, rely=0, relwidth=1, relheight=1)
        destino.lift()

        self.aba_atual = indice
        self._pintar_abas()
        self.animando = True
        self._animar_transicao(origem, destino, direcao, passo=0, total_passos=14)

    def _animar_transicao(self, origem, destino, direcao, passo, total_passos):
        t = passo / total_passos
        t_suave = 1 - (1 - t) ** 3  # ease-out: começa rápido, termina suave

        origem.place(relx=-direcao * t_suave, rely=0, relwidth=1, relheight=1)
        destino.place(relx=direcao * (1 - t_suave), rely=0, relwidth=1, relheight=1)

        if passo >= total_passos:
            self.animando = False
            return
        self.root.after(
            12, lambda: self._animar_transicao(origem, destino, direcao, passo + 1, total_passos)
        )

    # ---------- Aba Pesagem ----------
    def _montar_aba_pesagem(self, pai):
        pai.columnconfigure(0, weight=4, uniform="pesagem")
        pai.columnconfigure(1, weight=3, uniform="pesagem")
        pai.columnconfigure(2, weight=3, uniform="pesagem")
        pai.rowconfigure(0, weight=1)

        self._montar_lista_materiais(pai)
        self._montar_painel_visor(pai)
        self._montar_ticket(pai)

    def _montar_lista_materiais(self, pai):
        frame = tk.Frame(pai, bg=TEMA["fundo"])
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=6)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        topo = tk.Frame(frame, bg=TEMA["fundo"])
        topo.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        tk.Label(topo, text="Materiais", bg=TEMA["fundo"], fg=TEMA["texto"], font=(FONTE, 11)).pack(side="left")
        botao_contorno(
            topo, "Editar preços", self.abrir_edicao_precos, icone="lapis", pady=5, padx=12
        ).pack(side="right")

        area, rolar = self._criar_area_rolavel(frame, coluna=0)
        self.botoes_material = {}
        for m in self.precos.listar():
            btn = BotaoArredondado(
                area, text=f"{m['nome']}\nR$ {m['preco']:.2f}/kg", alinhamento="w", sombra=True,
                raio=16, font=(FONTE, 10), font_sec=(FONTE, 9), fg_sec=TEMA["muted"],
                padx=18, pady=10, command=lambda mat=m: self.selecionar_material(mat)
            )
            btn.pack(fill="x", pady=(2, 3), padx=(0, 4))
            for evento in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                btn.bind(evento, rolar)
            self.botoes_material[m["nome"]] = btn

    def _montar_painel_visor(self, pai):
        cartao = CartaoArredondado(pai, raio=24, padx=22, pady=18)
        cartao.grid(row=0, column=1, sticky="nsew", padx=5, pady=6)
        frame = cartao.interior

        self.lbl_material = tk.Label(
            frame, text="Selecione um material", bg=TEMA["painel"], fg=TEMA["muted"], font=(FONTE, 10)
        )
        self.lbl_material.pack(pady=(10, 6))

        self.lbl_peso_visor = tk.Label(
            frame, text="0.00 kg", bg=TEMA["painel"], fg=TEMA["destaque"], font=(FONTE_MONO, 32, "bold")
        )
        self.lbl_peso_visor.pack(pady=(0, 16))

        campo = EntradaArredondada(
            frame, fundo_pai=TEMA["painel"], justify="center", font=(FONTE_MONO, 14), raio=999
        )
        campo.pack(fill="x", pady=(0, 6))
        self.entry_peso = campo.entry
        self.entry_peso.bind("<KeyRelease>", lambda e: self.atualizar_calculo())

        tk.Label(frame, text="Peso em kg", bg=TEMA["painel"], fg=TEMA["muted"], font=(FONTE, 9)).pack(pady=(0, 14))

        self.lbl_valor = tk.Label(
            frame, text="Valor: R$ 0,00", bg=TEMA["painel"], fg=TEMA["total"], font=(FONTE_MONO, 13, "bold")
        )
        self.lbl_valor.pack(pady=(0, 18))

        self.btn_adicionar = BotaoArredondado(
            frame, text="Adicionar à pesagem", command=self.adicionar_item, bg=TEMA["desabilitado"],
            fg=TEMA["sobre_destaque"], hover=TEMA["destaque_hover"], fundo_pai=TEMA["painel"],
            raio=999, font=(FONTE, 11, "bold"), pady=12, state="disabled"
        )
        self.btn_adicionar.pack(fill="x")

    def _montar_ticket(self, pai):
        frame = tk.Frame(pai, bg=TEMA["fundo"])
        frame.grid(row=0, column=2, sticky="nsew", padx=(10, 0), pady=6)

        tk.Label(frame, text="Pesagem atual", bg=TEMA["fundo"], fg=TEMA["texto"], font=(FONTE, 11)).pack(anchor="w", pady=(0, 8))

        linha_cliente = tk.Frame(frame, bg=TEMA["fundo"])
        linha_cliente.pack(fill="x", pady=(0, 6))
        tk.Label(
            linha_cliente, text="Cliente (opcional)", bg=TEMA["fundo"], fg=TEMA["muted"], font=(FONTE, 9)
        ).pack(side="left")
        BotaoArredondado(
            linha_cliente, text="Novo", icone="mais", bg=TEMA["destaque_claro"], fg=TEMA["destaque_escuro"],
            fundo_pai=TEMA["fundo"], raio=999, font=(FONTE, 9, "bold"), padx=12, pady=4,
            command=lambda: self.abrir_cadastro_cliente(ao_salvar=self._selecionar_cliente_na_pesagem)
        ).pack(side="right")

        cartao_combo = CartaoArredondado(
            frame, raio=14, padx=10, pady=4, sombra=False, ajustar=True, borda=TEMA["linha"]
        )
        cartao_combo.pack(fill="x", pady=(0, 10))
        self.combo_cliente = ttk.Combobox(cartao_combo.interior, state="readonly", font=(FONTE, 10))
        self.combo_cliente.pack(fill="x")
        self._atualizar_combo_clientes()

        cartao_lista = CartaoArredondado(frame, raio=16, padx=10, pady=8)
        cartao_lista.pack(fill="both", expand=True)
        self.lista_ticket = tk.Listbox(
            cartao_lista.interior, height=3, bg=TEMA["painel"], fg=TEMA["texto"], relief="flat", bd=0,
            font=(FONTE_MONO, 10), highlightthickness=0, activestyle="none",
            selectbackground=TEMA["painel_ativo"], selectforeground=TEMA["texto"]
        )
        self.lista_ticket.pack(fill="both", expand=True)

        linha_total = tk.Frame(frame, bg=TEMA["fundo"])
        linha_total.pack(fill="x", pady=(10, 8))
        tk.Label(linha_total, text="Total", bg=TEMA["fundo"], fg=TEMA["muted"], font=(FONTE, 10)).pack(side="left")
        self.lbl_total = tk.Label(
            linha_total, text="R$ 0,00", bg=TEMA["fundo"], fg=TEMA["total"], font=(FONTE_MONO, 17, "bold")
        )
        self.lbl_total.pack(side="right")

        botao_contorno(frame, "Remover selecionado", self.remover_item, "lixeira").pack(fill="x", pady=(0, 6))
        botao_cheio(
            frame, "Finalizar e salvar no histórico", self.finalizar_pesagem, "check", cor=TEMA["total"]
        ).pack(fill="x", pady=(0, 6))
        botao_contorno(frame, "Gerar relatório (.txt)", self.gerar_relatorio_atual, "documento").pack(fill="x", pady=(0, 6))
        botao_contorno(frame, "Limpar pesagem", self.limpar_pesagem, "lixeira").pack(fill="x")

    # ---------- Lista rolável (usada em várias abas) ----------
    def _criar_area_rolavel(self, pai, coluna, linha=1):
        """Cria um Canvas+Scrollbar dentro de 'pai' na coluna dada e devolve a frame interna rolável."""
        container = tk.Frame(pai, bg=TEMA["fundo"])
        container.grid(row=linha, column=coluna, sticky="nsew", padx=(0, 0) if coluna == 0 else (16, 0))
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        canvas = tk.Canvas(container, bg=TEMA["fundo"], highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        area_interna = tk.Frame(canvas, bg=TEMA["fundo"])

        area_interna.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        janela_id = canvas.create_window((0, 0), window=area_interna, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(janela_id, width=e.width))
        def _atualizar_barra(inicio, fim):
            scrollbar.set(inicio, fim)
            if float(inicio) <= 0.0 and float(fim) >= 1.0:
                scrollbar.grid_remove()  # tudo cabe na tela: esconde a barra
            else:
                scrollbar.grid()

        canvas.configure(yscrollcommand=_atualizar_barra)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(4, 0))

        def _rolar(event):
            delta = -1 * (event.delta // 120) if event.delta else (-1 if event.num == 4 else 1)
            canvas.yview_scroll(delta, "units")

        for alvo in (canvas, area_interna):
            alvo.bind("<MouseWheel>", _rolar)
            alvo.bind("<Button-4>", _rolar)
            alvo.bind("<Button-5>", _rolar)

        return area_interna, _rolar

    def _ligar_rolagem(self, widget, rolar):
        """Faz a roda do mouse rolar a lista mesmo com o cursor sobre um cartão."""
        for evento in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            widget.bind(evento, rolar)
        for filho in widget.winfo_children():
            self._ligar_rolagem(filho, rolar)

    # ---------- Aba Histórico ----------
    def _montar_aba_historico(self, pai):
        frame = tk.Frame(pai, bg=TEMA["fundo"])
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1, uniform="hist")
        frame.columnconfigure(1, weight=1, uniform="hist")
        frame.rowconfigure(1, weight=1)

        tk.Label(
            frame, text="Pesagens finalizadas", bg=TEMA["fundo"], fg=TEMA["texto"], font=(FONTE, 11)
        ).grid(row=0, column=0, sticky="w", pady=(6, 8))
        tk.Label(
            frame, text="Itens da pesagem selecionada", bg=TEMA["fundo"], fg=TEMA["texto"], font=(FONTE, 11)
        ).grid(row=0, column=1, sticky="w", padx=(16, 0), pady=(6, 8))

        self.area_lista_historico, rolar_hist = self._criar_area_rolavel(frame, coluna=0)
        self.area_detalhe_historico, rolar_det = self._criar_area_rolavel(frame, coluna=1)

        botao_contorno(
            frame, "Atualizar lista", self.atualizar_historico, icone="atualizar"
        ).grid(row=2, column=0, sticky="ew", pady=(10, 0))

        self._registros_historico = []
        self._botoes_registro = []
        self._indice_selecionado = None
        self._rolar_hist = rolar_hist
        self._rolar_det = rolar_det
        self.atualizar_historico()

    def atualizar_historico(self):
        for widget in self.area_lista_historico.winfo_children():
            widget.destroy()
        for widget in self.area_detalhe_historico.winfo_children():
            widget.destroy()

        registros = self.historico.listar()
        self._registros_historico = registros
        self._botoes_registro = []
        self._indice_selecionado = None

        if not registros:
            tk.Label(
                self.area_lista_historico, text="Nenhuma pesagem finalizada ainda.",
                bg=TEMA["fundo"], fg=TEMA["muted"], font=(FONTE, 10)
            ).pack(anchor="w", pady=8)
            return

        for idx, reg in enumerate(registros):
            qtd_itens = len(reg["itens"])
            cliente = reg.get("cliente") or "Cliente não informado"
            btn = BotaoArredondado(
                self.area_lista_historico,
                text=f"{cliente}\n{reg['data']}\n{qtd_itens} item(ns)  •  R$ {reg['total']:.2f}",
                alinhamento="w", sombra=True, raio=16, font=(FONTE, 10), font_sec=(FONTE, 9),
                fg_sec=TEMA["muted"], padx=18, pady=10, command=lambda i=idx: self._selecionar_registro(i)
            )
            btn.pack(fill="x", pady=(2, 3), padx=(0, 4))
            for evento in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                btn.bind(evento, self._rolar_hist)
            self._botoes_registro.append(btn)

        self._selecionar_registro(0)

    def _selecionar_registro(self, idx):
        for i, btn in enumerate(self._botoes_registro):
            btn.configure(bg=TEMA["painel_ativo"] if i == idx else TEMA["painel"])
        self._indice_selecionado = idx

        for widget in self.area_detalhe_historico.winfo_children():
            widget.destroy()

        if idx >= len(self._registros_historico):
            return
        registro = self._registros_historico[idx]
        for item in registro["itens"]:
            cartao = CartaoArredondado(
                self.area_detalhe_historico, raio=14, padx=16, pady=10, ajustar=True
            )
            cartao.pack(fill="x", pady=(2, 3), padx=(0, 4))
            tk.Label(
                cartao.interior, text=item["nome"], font=(FONTE, 10),
                bg=TEMA["painel"], fg=TEMA["texto"], anchor="w"
            ).pack(fill="x")
            tk.Label(
                cartao.interior, text=f"{item['peso']:.2f} kg  •  R$ {item['valor']:.2f}",
                font=(FONTE, 9), bg=TEMA["painel"], fg=TEMA["muted"], anchor="w"
            ).pack(fill="x")
            self._ligar_rolagem(cartao, self._rolar_det)

        cartao_total = CartaoArredondado(
            self.area_detalhe_historico, bg=TEMA["destaque_claro"], raio=14, padx=16, pady=10,
            ajustar=True, sombra=False
        )
        cartao_total.pack(fill="x", pady=(10, 3), padx=(0, 4))
        tk.Label(
            cartao_total.interior, text="Total da pesagem", font=(FONTE, 9),
            bg=TEMA["destaque_claro"], fg=TEMA["destaque_escuro"], anchor="w"
        ).pack(fill="x")
        tk.Label(
            cartao_total.interior, text=f"R$ {registro['total']:.2f}", font=(FONTE_MONO, 17, "bold"),
            bg=TEMA["destaque_claro"], fg=TEMA["destaque_escuro"], anchor="w"
        ).pack(fill="x")
        self._ligar_rolagem(cartao_total, self._rolar_det)

    # ---------- Edição de preços ----------
    def abrir_edicao_precos(self):
        janela = tk.Toplevel(self.root)
        janela.title("Editar preços dos materiais")
        janela.configure(bg=TEMA["fundo"])
        janela.geometry("420x620")
        janela.resizable(False, False)
        janela.transient(self.root)
        janela.grab_set()

        container = tk.Frame(janela, bg=TEMA["fundo"])
        container.pack(fill="both", expand=True, padx=24, pady=22)
        container.rowconfigure(2, weight=1)
        container.columnconfigure(0, weight=1)

        tk.Label(
            container, text="Preço por kg (R$)", bg=TEMA["fundo"], fg=TEMA["texto"], font=(FONTE, 16, "bold")
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            container, text="Altere os valores e clique em salvar.", bg=TEMA["fundo"],
            fg=TEMA["muted"], font=(FONTE, 9)
        ).grid(row=1, column=0, sticky="w", pady=(2, 12))

        area, rolar = self._criar_area_rolavel(container, coluna=0, linha=2)
        entradas = {}
        for m in self.precos.listar():
            linha = tk.Frame(area, bg=TEMA["fundo"])
            linha.pack(fill="x", pady=4, padx=(0, 6))
            tk.Label(
                linha, text=m["nome"], bg=TEMA["fundo"], fg=TEMA["texto"], font=(FONTE, 10), anchor="w"
            ).pack(side="left")
            campo = EntradaArredondada(
                linha, fundo_pai=TEMA["fundo"], bg=TEMA["painel"], justify="right",
                font=(FONTE_MONO, 11), largura_chars=9, raio=999, pady=7
            )
            campo.pack(side="right")
            campo.entry.insert(0, f"{m['preco']:.2f}")
            entradas[m["nome"]] = campo.entry
            self._ligar_rolagem(linha, rolar)

        lbl_erro = tk.Label(
            container, text="", bg=TEMA["fundo"], fg=TEMA["erro"], font=(FONTE, 9), anchor="w"
        )
        lbl_erro.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        def salvar():
            novos = {}
            for nome, entrada in entradas.items():
                texto = entrada.get().replace(",", ".").strip()
                try:
                    valor = float(texto)
                    if valor < 0:
                        raise ValueError
                except ValueError:
                    lbl_erro.configure(text=f"Preço inválido para {nome}.")
                    return
                novos[nome] = valor
            self.precos.atualizar_precos(novos)
            self._atualizar_textos_materiais()
            janela.destroy()

        botao_cheio(container, "Salvar", salvar, fundo_pai=TEMA["fundo"], pady=11, fonte=(FONTE, 11, "bold")).grid(
            row=4, column=0, sticky="ew", pady=(14, 6)
        )
        botao_contorno(container, "Cancelar", janela.destroy).grid(row=5, column=0, sticky="ew")

    def _atualizar_textos_materiais(self):
        for m in self.precos.listar():
            btn = self.botoes_material.get(m["nome"])
            if btn:
                btn.configure(text=f"{m['nome']}\nR$ {m['preco']:.2f}/kg")

        if self.material_selecionado:
            atualizado = next(
                (m for m in self.precos.listar() if m["nome"] == self.material_selecionado["nome"]), None
            )
            if atualizado:
                self.material_selecionado = atualizado
                self.lbl_material.configure(text=f"{atualizado['nome']} — R$ {atualizado['preco']:.2f}/kg")
                self.atualizar_calculo()

    # ---------- Seletor de cliente na pesagem ----------
    def _atualizar_combo_clientes(self, selecionar_id=None):
        anterior = selecionar_id
        if anterior is None:
            idx = self.combo_cliente.current()
            if 0 < idx < len(self._ids_combo):
                anterior = self._ids_combo[idx]

        lista = self.clientes.listar()
        contagem = {}
        for c in lista:
            contagem[c["nome"]] = contagem.get(c["nome"], 0) + 1

        valores = ["Sem cliente (avulso)"]
        self._ids_combo = [None]
        for c in lista:
            rotulo = c["nome"] if contagem[c["nome"]] == 1 else f"{c['nome']} (…{c['documento'][-4:]})"
            valores.append(rotulo)
            self._ids_combo.append(c["id"])

        self.combo_cliente["values"] = valores
        self.combo_cliente.current(self._ids_combo.index(anterior) if anterior in self._ids_combo else 0)

    def _selecionar_cliente_na_pesagem(self, cliente):
        self._atualizar_combo_clientes(selecionar_id=cliente["id"])

    def _aplicar_cliente_no_ticket(self):
        idx = self.combo_cliente.current()
        cliente = self.clientes.obter(self._ids_combo[idx]) if 0 < idx < len(self._ids_combo) else None
        self.ticket.cliente = cliente["nome"] if cliente else ""
        self.ticket.cliente_id = cliente["id"] if cliente else None

    # ---------- Aba Clientes ----------
    def _montar_aba_clientes(self, pai):
        self._msg_filtro = "Formato dd/mm/aaaa. Para um único dia, use a mesma data nos dois campos."

        frame = tk.Frame(pai, bg=TEMA["fundo"])
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=2, uniform="clientes")
        frame.columnconfigure(1, weight=3, uniform="clientes")
        frame.rowconfigure(1, weight=1)

        # Coluna da esquerda: lista de clientes
        topo = tk.Frame(frame, bg=TEMA["fundo"])
        topo.grid(row=0, column=0, sticky="ew", pady=(6, 8))
        tk.Label(topo, text="Clientes cadastrados", bg=TEMA["fundo"], fg=TEMA["texto"], font=(FONTE, 11)).pack(side="left")
        botao_cheio(
            topo, "Novo cliente",
            lambda: self.abrir_cadastro_cliente(ao_salvar=self._selecionar_cliente_na_lista),
            icone="mais", pady=5, padx=14
        ).pack(side="right")
        self.area_lista_clientes, self._rolar_clientes = self._criar_area_rolavel(frame, coluna=0)

        # Coluna da direita: dados do cliente, filtro por data e histórico dele
        direita = tk.Frame(frame, bg=TEMA["fundo"])
        direita.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(16, 0), pady=(6, 0))
        direita.columnconfigure(0, weight=1)
        direita.rowconfigure(3, weight=1)

        self.lbl_cliente_nome = tk.Label(
            direita, text="Selecione um cliente", bg=TEMA["fundo"], fg=TEMA["texto"],
            font=(FONTE, 15, "bold"), anchor="w"
        )
        self.lbl_cliente_nome.grid(row=0, column=0, sticky="ew")
        self.lbl_cliente_dados = tk.Label(
            direita, text="", bg=TEMA["fundo"], fg=TEMA["muted"], font=(FONTE, 9), anchor="w", justify="left"
        )
        self.lbl_cliente_dados.grid(row=1, column=0, sticky="ew", pady=(2, 8))

        barra = CartaoArredondado(direita, raio=16, padx=14, pady=10, ajustar=True)
        barra.grid(row=2, column=0, sticky="ew", pady=(0, 8), padx=(0, 4))
        interno = tk.Frame(barra.interior, bg=TEMA["painel"])
        interno.pack(fill="x")

        def entrada_data():
            campo = EntradaArredondada(
                interno, fundo_pai=TEMA["painel"], largura_chars=10, font=(FONTE_MONO, 10),
                justify="center", raio=999, pady=6, padx=10
            )
            campo.entry.bind("<Return>", lambda e: self._renderizar_pesagens_cliente())
            return campo

        tk.Label(interno, text="De", bg=TEMA["painel"], fg=TEMA["muted"], font=(FONTE, 9)).pack(side="left")
        campo_de = entrada_data()
        campo_de.pack(side="left", padx=(6, 10))
        self.entry_data_de = campo_de.entry
        tk.Label(interno, text="Até", bg=TEMA["painel"], fg=TEMA["muted"], font=(FONTE, 9)).pack(side="left")
        campo_ate = entrada_data()
        campo_ate.pack(side="left", padx=(6, 10))
        self.entry_data_ate = campo_ate.entry

        botao_cheio(
            interno, "Filtrar", self._renderizar_pesagens_cliente, fundo_pai=TEMA["painel"], pady=6, padx=14
        ).pack(side="left", padx=(0, 6))
        botao_contorno(
            interno, "Limpar", self._limpar_filtro, fundo_pai=TEMA["painel"], pady=6, padx=12
        ).pack(side="left")

        self.lbl_filtro_msg = tk.Label(
            barra.interior, text=self._msg_filtro, bg=TEMA["painel"], fg=TEMA["muted"],
            font=(FONTE, 8), anchor="w", justify="left", wraplength=420
        )
        self.lbl_filtro_msg.pack(fill="x", pady=(8, 0))

        self.area_pesagens_cliente, self._rolar_pesagens = self._criar_area_rolavel(direita, coluna=0, linha=3)

        cartao_resumo = CartaoArredondado(
            direita, bg=TEMA["destaque_claro"], raio=16, padx=16, pady=9, ajustar=True, sombra=False
        )
        cartao_resumo.grid(row=4, column=0, sticky="ew", pady=(8, 0), padx=(0, 4))
        self.lbl_resumo = tk.Label(
            cartao_resumo.interior, text="", bg=TEMA["destaque_claro"], fg=TEMA["destaque_escuro"],
            font=(FONTE_MONO, 11, "bold"), anchor="w"
        )
        self.lbl_resumo.pack(fill="x")

        self._atualizar_lista_clientes()

    def _atualizar_lista_clientes(self):
        for widget in self.area_lista_clientes.winfo_children():
            widget.destroy()
        self._botoes_cliente = {}

        lista = self.clientes.listar()
        if not lista:
            tk.Label(
                self.area_lista_clientes, text="Nenhum cliente cadastrado ainda.\nClique em \"Novo cliente\".",
                bg=TEMA["fundo"], fg=TEMA["muted"], font=(FONTE, 10), justify="left"
            ).pack(anchor="w", pady=8)
            return

        for c in lista:
            ativo = c["id"] == self._cliente_sel_id
            btn = BotaoArredondado(
                self.area_lista_clientes,
                text=f"{c['nome']}\n{formatar_documento(c['documento'])}  •  {formatar_telefone(c['numero'])}",
                bg=TEMA["painel_ativo"] if ativo else TEMA["painel"], alinhamento="w", sombra=True,
                raio=16, font=(FONTE, 10), font_sec=(FONTE, 9), fg_sec=TEMA["muted"], padx=18, pady=10,
                command=lambda cid=c["id"]: self._mostrar_cliente(cid)
            )
            btn.pack(fill="x", pady=(2, 3), padx=(0, 4))
            for evento in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                btn.bind(evento, self._rolar_clientes)
            self._botoes_cliente[c["id"]] = btn

    def _selecionar_cliente_na_lista(self, cliente):
        self._mostrar_cliente(cliente["id"])

    def _mostrar_cliente(self, cliente_id):
        self._cliente_sel_id = cliente_id
        for cid, btn in self._botoes_cliente.items():
            btn.configure(bg=TEMA["painel_ativo"] if cid == cliente_id else TEMA["painel"])
        self._renderizar_pesagens_cliente()

    def _atualizar_painel_cliente(self):
        if self._cliente_sel_id:
            self._renderizar_pesagens_cliente()

    @staticmethod
    def _parse_data(texto):
        texto = texto.strip()
        return datetime.strptime(texto, "%d/%m/%Y").date() if texto else None

    def _ler_periodo(self):
        """Devolve (data_inicial, data_final, mensagem_de_erro)."""
        try:
            de = self._parse_data(self.entry_data_de.get())
            ate = self._parse_data(self.entry_data_ate.get())
        except ValueError:
            return None, None, "Data inválida. Use o formato dd/mm/aaaa."
        if de and ate and de > ate:
            return None, None, "A data inicial é maior que a data final."
        return de, ate, ""

    def _limpar_filtro(self):
        self.entry_data_de.delete(0, "end")
        self.entry_data_ate.delete(0, "end")
        self._renderizar_pesagens_cliente()

    def _renderizar_pesagens_cliente(self):
        for widget in self.area_pesagens_cliente.winfo_children():
            widget.destroy()

        cliente = self.clientes.obter(self._cliente_sel_id) if self._cliente_sel_id else None
        if not cliente:
            self.lbl_cliente_nome.configure(text="Selecione um cliente")
            self.lbl_cliente_dados.configure(text="")
            self.lbl_resumo.configure(text="")
            return

        self.lbl_cliente_nome.configure(text=cliente["nome"])
        dados = f"{formatar_documento(cliente['documento'])}   •   {formatar_telefone(cliente['numero'])}"
        if cliente.get("email"):
            dados += f"   •   {cliente['email']}"
        self.lbl_cliente_dados.configure(text=dados)

        de, ate, erro = self._ler_periodo()
        if erro:
            self.lbl_filtro_msg.configure(text=erro, fg=TEMA["erro"])
        else:
            self.lbl_filtro_msg.configure(text=self._msg_filtro, fg=TEMA["muted"])

        pesagens = []
        for reg in self.historico.listar():
            if reg.get("cliente_id") != cliente["id"]:
                continue
            try:
                dia = datetime.strptime(reg["data"], "%d/%m/%Y %H:%M").date()
            except ValueError:
                dia = None
            if dia is not None and ((de and dia < de) or (ate and dia > ate)):
                continue
            pesagens.append(reg)

        if not pesagens:
            texto = "Nenhuma pesagem neste período." if (de or ate) else "Este cliente ainda não tem pesagens."
            tk.Label(
                self.area_pesagens_cliente, text=texto, bg=TEMA["fundo"], fg=TEMA["muted"], font=(FONTE, 10)
            ).pack(anchor="w", pady=8)

        for reg in pesagens:
            cartao = CartaoArredondado(
                self.area_pesagens_cliente, raio=14, padx=16, pady=10, ajustar=True
            )
            cartao.pack(fill="x", pady=(2, 3), padx=(0, 4))
            tk.Label(
                cartao.interior, text=f"{reg['data']}   •   R$ {reg['total']:.2f}", bg=TEMA["painel"],
                fg=TEMA["texto"], font=(FONTE, 10), anchor="w"
            ).pack(fill="x", pady=(0, 4))
            linhas = "\n".join(
                f"{item['nome']:<10} {item['peso']:>7.2f} kg   R$ {item['valor']:>8.2f}" for item in reg["itens"]
            )
            tk.Label(
                cartao.interior, text=linhas, bg=TEMA["painel"], fg=TEMA["muted"], font=(FONTE_MONO, 9),
                anchor="w", justify="left"
            ).pack(fill="x")
            self._ligar_rolagem(cartao, self._rolar_pesagens)

        total = sum(reg["total"] for reg in pesagens)
        self.lbl_resumo.configure(text=f"{len(pesagens)} pesagem(ns)   •   Total: R$ {total:.2f}")

    # ---------- Cadastro de cliente ----------
    def abrir_cadastro_cliente(self, ao_salvar=None):
        janela = tk.Toplevel(self.root)
        janela.title("Novo cliente")
        janela.configure(bg=TEMA["fundo"])
        janela.geometry("400x580")
        janela.resizable(False, False)
        janela.transient(self.root)
        janela.grab_set()

        container = tk.Frame(janela, bg=TEMA["fundo"])
        container.pack(fill="both", expand=True, padx=24, pady=22)
        tk.Label(
            container, text="Cadastro de cliente", bg=TEMA["fundo"], fg=TEMA["texto"], font=(FONTE, 16, "bold")
        ).pack(anchor="w", pady=(0, 4))

        def campo(rotulo):
            tk.Label(container, text=rotulo, bg=TEMA["fundo"], fg=TEMA["muted"], font=(FONTE, 9)).pack(
                anchor="w", pady=(10, 4)
            )
            entrada = EntradaArredondada(
                container, fundo_pai=TEMA["fundo"], bg=TEMA["painel"], font=(FONTE, 11), raio=999, pady=8
            )
            entrada.pack(fill="x")
            return entrada.entry

        e_nome = campo("Nome completo")
        e_numero = campo("Número (telefone com DDD)")
        e_doc = campo("CPF ou CNPJ")
        e_email = campo("E-mail (opcional)")

        lbl_erro = tk.Label(
            container, text="", bg=TEMA["fundo"], fg=TEMA["erro"], font=(FONTE, 9),
            anchor="w", justify="left", wraplength=340
        )
        lbl_erro.pack(fill="x", pady=(10, 0))

        def salvar():
            try:
                cliente = self.clientes.criar(e_nome.get(), e_numero.get(), e_doc.get(), e_email.get())
            except ValueError as erro:
                lbl_erro.configure(text=str(erro))
                return
            self._atualizar_combo_clientes()
            self._atualizar_lista_clientes()
            janela.destroy()
            if ao_salvar:
                ao_salvar(cliente)

        botao_cheio(container, "Salvar cliente", salvar, pady=11, fonte=(FONTE, 11, "bold")).pack(
            fill="x", pady=(14, 6)
        )
        botao_contorno(container, "Cancelar", janela.destroy).pack(fill="x")

        janela.bind("<Return>", lambda e: salvar())
        e_nome.focus_set()

    # ---------- Lógica da pesagem ----------
    def selecionar_material(self, material):
        self.material_selecionado = material
        for nome, btn in self.botoes_material.items():
            btn.configure(bg=TEMA["painel"] if nome != material["nome"] else TEMA["painel_ativo"])
        self.lbl_material.configure(text=f"{material['nome']} — R$ {material['preco']:.2f}/kg")
        self.atualizar_calculo()

    def atualizar_calculo(self):
        texto = self.entry_peso.get().replace(",", ".")
        try:
            peso = float(texto) if texto else 0.0
        except ValueError:
            peso = 0.0

        self.lbl_peso_visor.configure(text=f"{peso:.2f} kg")

        if self.material_selecionado and peso > 0:
            valor = peso * self.material_selecionado["preco"]
            self.lbl_valor.configure(text=f"Valor: R$ {valor:.2f}")
            self.btn_adicionar.configure(state="normal", bg=TEMA["destaque"], cursor="hand2")
        else:
            self.lbl_valor.configure(text="Valor: R$ 0,00")
            self.btn_adicionar.configure(state="disabled", bg=TEMA["desabilitado"], cursor="arrow")

    def adicionar_item(self):
        texto = self.entry_peso.get().replace(",", ".")
        try:
            peso = float(texto)
        except ValueError:
            return
        if not self.material_selecionado or peso <= 0:
            return

        item = self.ticket.adicionar(
            nome=self.material_selecionado["nome"], peso=peso, preco=self.material_selecionado["preco"]
        )
        linha = f"{item.nome:<10} {item.peso:>6.2f} kg   R$ {item.valor:>8.2f}"
        self.lista_ticket.insert("end", linha)

        self.entry_peso.delete(0, "end")
        self.atualizar_calculo()
        self._atualizar_total_visor()

    def remover_item(self):
        selecao = self.lista_ticket.curselection()
        if not selecao:
            messagebox.showinfo("Remover item", "Selecione um item da lista para remover.")
            return
        idx = selecao[0]
        item = self.ticket.itens[idx]
        confirmar = messagebox.askyesno(
            "Remover item",
            f"Remover \"{item.nome}\" ({item.peso:.2f} kg — R$ {item.valor:.2f}) da pesagem?"
        )
        if not confirmar:
            return
        self.lista_ticket.delete(idx)
        self.ticket.remover(idx)
        self._atualizar_total_visor()

    def limpar_pesagem(self):
        if self.ticket.esta_vazio():
            return
        confirmar = messagebox.askyesno(
            "Limpar pesagem",
            f"Isso vai apagar todos os {len(self.ticket.itens)} item(ns) da pesagem atual (R$ {self.ticket.total:.2f}). Continuar?"
        )
        if not confirmar:
            return
        self._resetar_pesagem()

    def _resetar_pesagem(self):
        """Zera a pesagem atual (itens e nome do cliente), sem pedir confirmação."""
        self.ticket.limpar()
        self.lista_ticket.delete(0, "end")
        self.combo_cliente.current(0)
        self._atualizar_total_visor()

    def _atualizar_total_visor(self):
        self.lbl_total.configure(text=f"R$ {self.ticket.total:.2f}")

    def finalizar_pesagem(self):
        if self.ticket.esta_vazio():
            messagebox.showinfo("Finalizar pesagem", "Adicione ao menos um item antes de finalizar.")
            return
        self._aplicar_cliente_no_ticket()
        registro = self.historico.registrar(self.ticket)
        self.atualizar_historico()
        self._atualizar_painel_cliente()
        messagebox.showinfo(
            "Pesagem salva", f"Pesagem de R$ {registro['total']:.2f} salva no histórico."
        )
        self._resetar_pesagem()

    def gerar_relatorio_atual(self):
        if self.ticket.esta_vazio():
            messagebox.showinfo("Gerar relatório", "Adicione ao menos um item antes de gerar o relatório.")
            return
        self._aplicar_cliente_no_ticket()
        caminho = gerar_relatorio(self.ticket)
        messagebox.showinfo("Relatório gerado", f"Relatório salvo em:\n{caminho}")

    def _sair(self):
        self.root.destroy()
        if self.ao_sair:
            self.ao_sair()
