"""Interface Tkinter da Balança de Materiais, organizada em abas."""

import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

from materiais import MATERIAIS, TEMA
from modelo import Ticket
from armazenamento import GerenciadorHistorico, gerar_relatorio
from precos import GerenciadorPrecos
from clientes import GerenciadorClientes, formatar_documento, formatar_telefone


class BalancaApp:
    def __init__(self, root: tk.Tk, empresa: str = "", ao_sair=None):
        self.root = root
        self.empresa = empresa
        self.ao_sair = ao_sair
        self.root.title(f"Balança de Materiais — {empresa}" if empresa else "Balança de Materiais")
        self.root.configure(bg=TEMA["fundo"])
        self.root.geometry("920x620")
        self.root.minsize(860, 600)

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
        style.configure("TLabel", background=TEMA["fundo"], foreground=TEMA["texto"], font=("Segoe UI Semibold", 10))
        style.configure("Painel.TLabel", background=TEMA["painel"], foreground=TEMA["texto"], font=("Segoe UI Semibold", 10))
        style.configure("Muted.TLabel", background=TEMA["fundo"], foreground=TEMA["muted"], font=("Segoe UI Semibold", 9))
        style.configure("Titulo.TLabel", background=TEMA["fundo"], foreground=TEMA["texto"], font=("Segoe UI Semibold", 16, "bold"))

        style.configure(
            "TCombobox", fieldbackground=TEMA["painel"], background=TEMA["painel"],
            foreground=TEMA["texto"], arrowcolor=TEMA["texto"], bordercolor=TEMA["linha"],
            lightcolor=TEMA["painel"], darkcolor=TEMA["painel"], padding=6
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", TEMA["painel"])],
            foreground=[("readonly", TEMA["texto"])],
            selectbackground=[("readonly", TEMA["painel"])],
            selectforeground=[("readonly", TEMA["texto"])],
        )
        self.root.option_add("*TCombobox*Listbox.background", TEMA["painel"])
        self.root.option_add("*TCombobox*Listbox.foreground", TEMA["texto"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", TEMA["cobre"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", TEMA["fundo"])
        self.root.option_add("*TCombobox*Listbox.font", "{Segoe UI Semibold} 10")

    # ---------- Estrutura em abas ----------
    def _montar_abas(self):
        cabecalho = ttk.Frame(self.root, padding=(20, 16, 20, 0))
        cabecalho.pack(fill="x")

        linha_topo = ttk.Frame(cabecalho)
        linha_topo.pack(fill="x")
        titulo_box = ttk.Frame(linha_topo)
        titulo_box.pack(side="left")
        ttk.Label(titulo_box, text="Balança de Materiais", style="Titulo.TLabel").pack(anchor="w")
        subtitulo = f"Empresa: {self.empresa}" if self.empresa else "Pese, calcule e acompanhe o histórico das suas pesagens."
        ttk.Label(titulo_box, text=subtitulo, style="Muted.TLabel").pack(anchor="w", pady=(2, 10))

        if self.ao_sair:
            tk.Button(
                linha_topo, text="Sair", font=("Segoe UI Semibold", 9),
                bg=TEMA["fundo"], fg=TEMA["muted"], relief="flat", padx=10, pady=6,
                command=self._sair
            ).pack(side="right")

        self.abas_nomes = ["Pesagem", "Histórico", "Clientes"]
        self.aba_atual = 0
        self.animando = False

        barra_abas = tk.Frame(self.root, bg=TEMA["fundo"])
        barra_abas.pack(fill="x", padx=20, pady=(4, 0))

        self.botoes_aba = []
        for i, nome in enumerate(self.abas_nomes):
            btn = tk.Button(
                barra_abas, text=nome, font=("Segoe UI Semibold", 10),
                bg=TEMA["fundo"], fg=TEMA["texto"] if i == 0 else TEMA["muted"],
                activebackground=TEMA["fundo"], activeforeground=TEMA["texto"],
                relief="flat", bd=0, padx=16, pady=8, cursor="hand2",
                command=lambda idx=i: self._trocar_aba(idx),
            )
            btn.pack(side="left")
            self.botoes_aba.append(btn)

        self.linha_indicador = tk.Frame(barra_abas, bg=TEMA["cobre"], height=2)
        self.linha_indicador.place(x=0, y=34, width=90, height=2)

        # Área de conteúdo: dois painéis sobrepostos, deslizam ao trocar de aba
        self.area_conteudo = tk.Frame(self.root, bg=TEMA["fundo"])
        self.area_conteudo.pack(fill="both", expand=True, padx=20, pady=(8, 16))

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

        # Posiciona a linha indicadora certinho embaixo do 1º botão assim que a janela desenhar
        self.root.after(50, self._posicionar_indicador_inicial)

    def _posicionar_indicador_inicial(self):
        btn = self.botoes_aba[self.aba_atual]
        self.linha_indicador.place(x=btn.winfo_x(), y=btn.winfo_y() + btn.winfo_height() - 2,
                                    width=btn.winfo_width(), height=2)

    def _trocar_aba(self, indice):
        if indice == self.aba_atual or self.animando:
            return

        direcao = 1 if indice > self.aba_atual else -1
        origem = self.paineis_aba[self.aba_atual]
        destino = self.paineis_aba[indice]

        destino.place(relx=direcao, rely=0, relwidth=1, relheight=1)
        destino.lift()

        btn_novo = self.botoes_aba[indice]
        btn_antigo = self.botoes_aba[self.aba_atual]
        btn_novo.configure(fg=TEMA["texto"])
        btn_antigo.configure(fg=TEMA["muted"])

        x_origem = self.botoes_aba[self.aba_atual].winfo_x()
        largura_origem = self.botoes_aba[self.aba_atual].winfo_width()
        x_destino = btn_novo.winfo_x()
        largura_destino = btn_novo.winfo_width()
        y_indicador = btn_novo.winfo_y() + btn_novo.winfo_height() - 2

        self.aba_atual = indice
        self.animando = True
        self._animar_transicao(
            origem, destino, direcao,
            x_origem, largura_origem, x_destino, largura_destino, y_indicador,
            passo=0, total_passos=14
        )

    def _animar_transicao(self, origem, destino, direcao, x_a, larg_a, x_b, larg_b, y_indicador, passo, total_passos):
        t = passo / total_passos
        t_suave = 1 - (1 - t) ** 3  # ease-out: começa rápido, termina suave

        origem.place(relx=-direcao * t_suave, rely=0, relwidth=1, relheight=1)
        destino.place(relx=direcao * (1 - t_suave), rely=0, relwidth=1, relheight=1)

        x_atual = x_a + (x_b - x_a) * t_suave
        largura_atual = larg_a + (larg_b - larg_a) * t_suave
        self.linha_indicador.place(x=x_atual, y=y_indicador, width=largura_atual, height=2)

        if passo >= total_passos:
            self.animando = False
            return

        self.root.after(
            12, lambda: self._animar_transicao(
                origem, destino, direcao, x_a, larg_a, x_b, larg_b, y_indicador, passo + 1, total_passos
            )
        )

    # ---------- Aba Pesagem ----------
    def _montar_aba_pesagem(self, pai):
        pai.columnconfigure(0, weight=1)
        pai.columnconfigure(1, weight=1)
        pai.columnconfigure(2, weight=1)
        pai.rowconfigure(0, weight=1)

        self._montar_lista_materiais(pai)
        self._montar_painel_visor(pai)
        self._montar_ticket(pai)

    def _montar_lista_materiais(self, pai):
        frame = ttk.Frame(pai, padding=10)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=10)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        cabecalho_materiais = ttk.Frame(frame)
        cabecalho_materiais.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(cabecalho_materiais, text="Materiais", style="Muted.TLabel").pack(side="left")
        tk.Button(
            cabecalho_materiais, text="Editar preços", font=("Segoe UI Semibold", 8, "underline"),
            bg=TEMA["fundo"], fg=TEMA["cobre"], relief="flat", bd=0, cursor="hand2",
            activebackground=TEMA["fundo"], activeforeground=TEMA["cobre"],
            command=self.abrir_edicao_precos
        ).pack(side="right")

        # Área rolável: um Canvas com uma Frame dentro, mais a Scrollbar
        canvas = tk.Canvas(frame, bg=TEMA["fundo"], highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        area_interna = tk.Frame(canvas, bg=TEMA["fundo"])

        area_interna.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        janela_id = canvas.create_window((0, 0), window=area_interna, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(janela_id, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")

        def _rolar_com_mouse(event):
            # Windows/Mac usam event.delta; Linux usa Button-4/5
            delta = -1 * (event.delta // 120) if event.delta else (-1 if event.num == 4 else 1)
            canvas.yview_scroll(delta, "units")

        for alvo in (canvas, area_interna):
            alvo.bind("<MouseWheel>", _rolar_com_mouse)   # Windows / macOS
            alvo.bind("<Button-4>", _rolar_com_mouse)      # Linux (scroll up)
            alvo.bind("<Button-5>", _rolar_com_mouse)      # Linux (scroll down)

        self.botoes_material = {}
        for m in self.precos.listar():
            btn = tk.Button(
                area_interna, text=f"{m['nome']}\nR$ {m['preco']:.2f}/kg",
                font=("Segoe UI Semibold", 10), bg=TEMA["painel"], fg=TEMA["texto"],
                activebackground=TEMA["painel_ativo"], activeforeground=TEMA["texto"],
                relief="flat", bd=0, justify="left", anchor="w", padx=12, pady=10,
                command=lambda mat=m: self.selecionar_material(mat),
            )
            btn.pack(fill="x", pady=3)
            btn.bind("<MouseWheel>", _rolar_com_mouse)
            btn.bind("<Button-4>", _rolar_com_mouse)
            btn.bind("<Button-5>", _rolar_com_mouse)
            self.botoes_material[m["nome"]] = btn

    def _montar_painel_visor(self, pai):
        frame = ttk.Frame(pai, style="Painel.TFrame", padding=20)
        frame.grid(row=0, column=1, sticky="nsew", padx=8, pady=10)

        self.lbl_material = tk.Label(
            frame, text="Selecione um material", bg=TEMA["painel"], fg=TEMA["muted"], font=("Segoe UI Semibold", 10)
        )
        self.lbl_material.pack(pady=(10, 6))

        self.lbl_peso_visor = tk.Label(
            frame, text="0.00 kg", bg=TEMA["painel"], fg=TEMA["cobre"], font=("Consolas", 32, "bold")
        )
        self.lbl_peso_visor.pack(pady=(0, 16))

        self.entry_peso = tk.Entry(
            frame, font=("Consolas", 14), justify="center",
            bg=TEMA["fundo"], fg=TEMA["texto"], insertbackground=TEMA["texto"], relief="flat"
        )
        self.entry_peso.pack(fill="x", ipady=8, pady=(0, 4))
        self.entry_peso.bind("<KeyRelease>", lambda e: self.atualizar_calculo())

        ttk.Label(frame, text="Peso em kg", style="Painel.TLabel").pack(pady=(0, 14))

        self.lbl_valor = tk.Label(
            frame, text="Valor: R$ 0,00", bg=TEMA["painel"], fg=TEMA["total"], font=("Consolas", 13, "bold")
        )
        self.lbl_valor.pack(pady=(0, 18))

        self.btn_adicionar = tk.Button(
            frame, text="Adicionar à pesagem", font=("Segoe UI Semibold", 11, "bold"),
            bg=TEMA["cobre"], fg="#1a1300", relief="flat", padx=10, pady=10,
            state="disabled", command=self.adicionar_item
        )
        self.btn_adicionar.pack(fill="x")

    def _montar_ticket(self, pai):
        frame = ttk.Frame(pai, padding=10)
        frame.grid(row=0, column=2, sticky="nsew", padx=(8, 0), pady=10)

        ttk.Label(frame, text="Pesagem atual", style="Muted.TLabel").pack(anchor="w", pady=(0, 8))

        linha_cliente = tk.Frame(frame, bg=TEMA["fundo"])
        linha_cliente.pack(fill="x", pady=(0, 4))
        ttk.Label(linha_cliente, text="Cliente (opcional)", style="Muted.TLabel").pack(side="left")
        tk.Button(
            linha_cliente, text="+ Novo", font=("Segoe UI Semibold", 8, "underline"),
            bg=TEMA["fundo"], fg=TEMA["cobre"], relief="flat", bd=0, cursor="hand2",
            activebackground=TEMA["fundo"], activeforeground=TEMA["cobre"],
            command=lambda: self.abrir_cadastro_cliente(ao_salvar=self._selecionar_cliente_na_pesagem)
        ).pack(side="right")
        self.combo_cliente = ttk.Combobox(frame, state="readonly", font=("Segoe UI Semibold", 10))
        self.combo_cliente.pack(fill="x", pady=(0, 10))
        self._atualizar_combo_clientes()

        self.lista_ticket = tk.Listbox(
            frame, height=4, bg=TEMA["fundo"], fg=TEMA["texto"], relief="flat",
            font=("Consolas", 10), highlightthickness=0, selectbackground=TEMA["painel"]
        )
        self.lista_ticket.pack(fill="both", expand=True)

        linha_total = tk.Frame(frame, bg=TEMA["fundo"])
        linha_total.pack(fill="x", pady=(10, 6))
        tk.Label(linha_total, text="Total", bg=TEMA["fundo"], fg=TEMA["muted"], font=("Segoe UI Semibold", 10)).pack(side="left")
        self.lbl_total = tk.Label(
            linha_total, text="R$ 0,00", bg=TEMA["fundo"], fg=TEMA["total"], font=("Consolas", 16, "bold")
        )
        self.lbl_total.pack(side="right")

        tk.Button(
            frame, text="Remover selecionado", font=("Segoe UI Semibold", 9),
            bg=TEMA["painel"], fg=TEMA["texto"], relief="flat", padx=6, pady=6,
            command=self.remover_item
        ).pack(fill="x", pady=(4, 4))

        tk.Button(
            frame, text="Finalizar e salvar no histórico", font=("Segoe UI Semibold", 9, "bold"),
            bg=TEMA["total"], fg="#122016", relief="flat", padx=6, pady=8,
            command=self.finalizar_pesagem
        ).pack(fill="x", pady=(0, 4))

        tk.Button(
            frame, text="Gerar relatório (.txt)", font=("Segoe UI Semibold", 9),
            bg=TEMA["fundo"], fg=TEMA["muted"], relief="flat", padx=6, pady=6,
            highlightbackground=TEMA["linha"], command=self.gerar_relatorio_atual
        ).pack(fill="x", pady=(0, 4))

        tk.Button(
            frame, text="Limpar pesagem", font=("Segoe UI Semibold", 9),
            bg=TEMA["fundo"], fg=TEMA["muted"], relief="flat", padx=6, pady=6,
            highlightbackground=TEMA["linha"], command=self.limpar_pesagem
        ).pack(fill="x")

    # ---------- Aba Histórico ----------
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
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        def _rolar(event):
            delta = -1 * (event.delta // 120) if event.delta else (-1 if event.num == 4 else 1)
            canvas.yview_scroll(delta, "units")

        for alvo in (canvas, area_interna):
            alvo.bind("<MouseWheel>", _rolar)
            alvo.bind("<Button-4>", _rolar)
            alvo.bind("<Button-5>", _rolar)

        return area_interna, _rolar

    def _montar_aba_historico(self, pai):
        frame = ttk.Frame(pai, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        ttk.Label(frame, text="Pesagens finalizadas", style="Muted.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Label(frame, text="Itens da pesagem selecionada", style="Muted.TLabel").grid(row=0, column=1, sticky="w", padx=(16, 0), pady=(0, 8))

        self.area_lista_historico, rolar_hist = self._criar_area_rolavel(frame, coluna=0)
        self.area_detalhe_historico, rolar_det = self._criar_area_rolavel(frame, coluna=1)

        tk.Button(
            frame, text="Atualizar lista", font=("Segoe UI Semibold", 9),
            bg=TEMA["fundo"], fg=TEMA["muted"], relief="flat", padx=6, pady=6,
            command=self.atualizar_historico
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
                bg=TEMA["fundo"], fg=TEMA["muted"], font=("Segoe UI Semibold", 10)
            ).pack(anchor="w", pady=8)
            return

        for idx, reg in enumerate(registros):
            qtd_itens = len(reg["itens"])
            cliente = reg.get("cliente") or "Cliente não informado"
            btn = tk.Button(
                self.area_lista_historico,
                text=f"{cliente}\n{reg['data']}\n{qtd_itens} item(ns)  •  R$ {reg['total']:.2f}",
                font=("Segoe UI Semibold", 10), bg=TEMA["painel"], fg=TEMA["texto"],
                activebackground=TEMA["painel_ativo"], activeforeground=TEMA["texto"],
                relief="flat", bd=0, justify="left", anchor="w", padx=12, pady=10,
                command=lambda i=idx: self._selecionar_registro(i),
            )
            btn.pack(fill="x", pady=3)
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
            card = tk.Frame(self.area_detalhe_historico, bg=TEMA["painel"])
            card.pack(fill="x", pady=3)
            tk.Label(
                card, text=item["nome"], font=("Segoe UI Semibold", 10),
                bg=TEMA["painel"], fg=TEMA["texto"], anchor="w", padx=12
            ).pack(fill="x", pady=(10, 0))
            tk.Label(
                card, text=f"{item['peso']:.2f} kg  •  R$ {item['valor']:.2f}",
                font=("Segoe UI Semibold", 9), bg=TEMA["painel"], fg=TEMA["muted"], anchor="w", padx=12
            ).pack(fill="x", pady=(0, 10))
            for widget in (card, *card.winfo_children()):
                for evento in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                    widget.bind(evento, self._rolar_det)

        card_total = tk.Frame(self.area_detalhe_historico, bg=TEMA["fundo"], highlightbackground=TEMA["linha"], highlightthickness=1)
        card_total.pack(fill="x", pady=(10, 3))
        tk.Label(
            card_total, text="Total da pesagem", font=("Segoe UI Semibold", 9),
            bg=TEMA["fundo"], fg=TEMA["muted"], anchor="w", padx=12
        ).pack(fill="x", pady=(10, 0))
        tk.Label(
            card_total, text=f"R$ {registro['total']:.2f}", font=("Consolas", 16, "bold"),
            bg=TEMA["fundo"], fg=TEMA["total"], anchor="w", padx=12
        ).pack(fill="x", pady=(0, 10))
        for widget in (card_total, *card_total.winfo_children()):
            for evento in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                widget.bind(evento, self._rolar_det)

    def abrir_edicao_precos(self):
        janela = tk.Toplevel(self.root)
        janela.title("Editar preços dos materiais")
        janela.configure(bg=TEMA["fundo"])
        janela.geometry("320x440")
        janela.resizable(False, False)
        janela.transient(self.root)
        janela.grab_set()

        container = ttk.Frame(janela, padding=20)
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="Preço por kg (R$)", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(
            container, text="Altere os valores e clique em salvar.", style="Muted.TLabel"
        ).pack(anchor="w", pady=(2, 14))

        entradas = {}
        for m in self.precos.listar():
            linha = tk.Frame(container, bg=TEMA["fundo"])
            linha.pack(fill="x", pady=4)
            tk.Label(linha, text=m["nome"], bg=TEMA["fundo"], fg=TEMA["texto"], font=("Segoe UI Semibold", 10), width=10, anchor="w").pack(side="left")
            entrada = tk.Entry(
                linha, font=("Consolas", 11), bg=TEMA["painel"], fg=TEMA["texto"],
                insertbackground=TEMA["texto"], relief="flat", justify="right", width=10
            )
            entrada.insert(0, f"{m['preco']:.2f}")
            entrada.pack(side="right", ipady=4)
            entradas[m["nome"]] = entrada

        lbl_erro = tk.Label(container, text="", bg=TEMA["fundo"], fg="#c96b5c", font=("Segoe UI Semibold", 9))
        lbl_erro.pack(anchor="w", pady=(10, 0))

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

        tk.Button(
            container, text="Salvar", font=("Segoe UI Semibold", 11, "bold"),
            bg=TEMA["cobre"], fg="#1a1300", relief="flat", padx=10, pady=10,
            command=salvar
        ).pack(fill="x", pady=(16, 6))
        tk.Button(
            container, text="Cancelar", font=("Segoe UI Semibold", 9),
            bg=TEMA["fundo"], fg=TEMA["muted"], relief="flat", padx=6, pady=6,
            command=janela.destroy
        ).pack(fill="x")

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
    def _ligar_rolagem(self, widget, rolar):
        """Faz a roda do mouse rolar a lista mesmo com o cursor sobre um cartão."""
        for evento in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            widget.bind(evento, rolar)
        for filho in widget.winfo_children():
            self._ligar_rolagem(filho, rolar)

    def _montar_aba_clientes(self, pai):
        self._msg_filtro = "Formato dd/mm/aaaa. Para um único dia, use a mesma data nos dois campos."

        frame = ttk.Frame(pai, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=2, uniform="clientes")
        frame.columnconfigure(1, weight=3, uniform="clientes")
        frame.rowconfigure(1, weight=1)

        # Coluna da esquerda: lista de clientes
        topo = ttk.Frame(frame)
        topo.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(topo, text="Clientes cadastrados", style="Muted.TLabel").pack(side="left")
        tk.Button(
            topo, text="+ Novo cliente", font=("Segoe UI Semibold", 9, "bold"),
            bg=TEMA["cobre"], fg="#1a1300", relief="flat", padx=10, pady=4, cursor="hand2",
            command=lambda: self.abrir_cadastro_cliente(ao_salvar=self._selecionar_cliente_na_lista)
        ).pack(side="right")
        self.area_lista_clientes, self._rolar_clientes = self._criar_area_rolavel(frame, coluna=0)

        # Coluna da direita: dados do cliente, filtro por data e histórico dele
        direita = tk.Frame(frame, bg=TEMA["fundo"])
        direita.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(16, 0))
        direita.columnconfigure(0, weight=1)
        direita.rowconfigure(3, weight=1)

        self.lbl_cliente_nome = tk.Label(
            direita, text="Selecione um cliente", bg=TEMA["fundo"], fg=TEMA["texto"],
            font=("Segoe UI Semibold", 14, "bold"), anchor="w"
        )
        self.lbl_cliente_nome.grid(row=0, column=0, sticky="ew")
        self.lbl_cliente_dados = tk.Label(
            direita, text="", bg=TEMA["fundo"], fg=TEMA["muted"],
            font=("Segoe UI Semibold", 9), anchor="w", justify="left"
        )
        self.lbl_cliente_dados.grid(row=1, column=0, sticky="ew", pady=(2, 8))

        barra = tk.Frame(direita, bg=TEMA["painel"])
        barra.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        interno = tk.Frame(barra, bg=TEMA["painel"])
        interno.pack(fill="x", padx=10, pady=(8, 4))

        def entrada_data():
            return tk.Entry(
                interno, width=10, font=("Consolas", 10), justify="center", bg=TEMA["fundo"],
                fg=TEMA["texto"], insertbackground=TEMA["texto"], relief="flat"
            )

        tk.Label(interno, text="De", bg=TEMA["painel"], fg=TEMA["muted"], font=("Segoe UI Semibold", 9)).pack(side="left")
        self.entry_data_de = entrada_data()
        self.entry_data_de.pack(side="left", padx=(6, 10), ipady=4)
        tk.Label(interno, text="Até", bg=TEMA["painel"], fg=TEMA["muted"], font=("Segoe UI Semibold", 9)).pack(side="left")
        self.entry_data_ate = entrada_data()
        self.entry_data_ate.pack(side="left", padx=(6, 10), ipady=4)
        for entrada in (self.entry_data_de, self.entry_data_ate):
            entrada.bind("<Return>", lambda e: self._renderizar_pesagens_cliente())

        tk.Button(
            interno, text="Filtrar", font=("Segoe UI Semibold", 9, "bold"),
            bg=TEMA["cobre"], fg="#1a1300", relief="flat", padx=10, pady=3, cursor="hand2",
            command=self._renderizar_pesagens_cliente
        ).pack(side="left", padx=(0, 6))
        tk.Button(
            interno, text="Limpar", font=("Segoe UI Semibold", 9),
            bg=TEMA["painel"], fg=TEMA["muted"], relief="flat", padx=6, pady=3, cursor="hand2",
            command=self._limpar_filtro
        ).pack(side="left")

        self.lbl_filtro_msg = tk.Label(
            barra, text=self._msg_filtro, bg=TEMA["painel"], fg=TEMA["muted"],
            font=("Segoe UI Semibold", 8), anchor="w", justify="left", wraplength=400
        )
        self.lbl_filtro_msg.pack(fill="x", padx=10, pady=(0, 8))

        self.area_pesagens_cliente, self._rolar_pesagens = self._criar_area_rolavel(direita, coluna=0, linha=3)
        self.lbl_resumo = tk.Label(
            direita, text="", bg=TEMA["painel"], fg=TEMA["total"],
            font=("Consolas", 11, "bold"), anchor="w", padx=12, pady=8
        )
        self.lbl_resumo.grid(row=4, column=0, sticky="ew", pady=(8, 0))

        self._atualizar_lista_clientes()

    def _atualizar_lista_clientes(self):
        for widget in self.area_lista_clientes.winfo_children():
            widget.destroy()
        self._botoes_cliente = {}

        lista = self.clientes.listar()
        if not lista:
            tk.Label(
                self.area_lista_clientes, text="Nenhum cliente cadastrado ainda.\nClique em \"+ Novo cliente\".",
                bg=TEMA["fundo"], fg=TEMA["muted"], font=("Segoe UI Semibold", 10), justify="left"
            ).pack(anchor="w", pady=8)
            return

        for c in lista:
            ativo = c["id"] == self._cliente_sel_id
            btn = tk.Button(
                self.area_lista_clientes,
                text=f"{c['nome']}\n{formatar_documento(c['documento'])}  •  {formatar_telefone(c['numero'])}",
                font=("Segoe UI Semibold", 10), bg=TEMA["painel_ativo"] if ativo else TEMA["painel"],
                fg=TEMA["texto"], activebackground=TEMA["painel_ativo"], activeforeground=TEMA["texto"],
                relief="flat", bd=0, justify="left", anchor="w", padx=12, pady=10,
                command=lambda cid=c["id"]: self._mostrar_cliente(cid),
            )
            btn.pack(fill="x", pady=3)
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
            self.lbl_filtro_msg.configure(text=erro, fg="#c96b5c")
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
                self.area_pesagens_cliente, text=texto, bg=TEMA["fundo"], fg=TEMA["muted"],
                font=("Segoe UI Semibold", 10)
            ).pack(anchor="w", pady=8)

        for reg in pesagens:
            card = tk.Frame(self.area_pesagens_cliente, bg=TEMA["painel"])
            card.pack(fill="x", pady=3)
            tk.Label(
                card, text=f"{reg['data']}   •   R$ {reg['total']:.2f}", bg=TEMA["painel"],
                fg=TEMA["texto"], font=("Segoe UI Semibold", 10), anchor="w", padx=12
            ).pack(fill="x", pady=(10, 4))
            linhas = "\n".join(
                f"{item['nome']:<10} {item['peso']:>7.2f} kg   R$ {item['valor']:>8.2f}" for item in reg["itens"]
            )
            tk.Label(
                card, text=linhas, bg=TEMA["painel"], fg=TEMA["muted"], font=("Consolas", 9),
                anchor="w", justify="left", padx=12
            ).pack(fill="x", pady=(0, 10))
            self._ligar_rolagem(card, self._rolar_pesagens)

        total = sum(reg["total"] for reg in pesagens)
        self.lbl_resumo.configure(text=f"{len(pesagens)} pesagem(ns)   •   Total: R$ {total:.2f}")

    # ---------- Cadastro de cliente ----------
    def abrir_cadastro_cliente(self, ao_salvar=None):
        janela = tk.Toplevel(self.root)
        janela.title("Novo cliente")
        janela.configure(bg=TEMA["fundo"])
        janela.geometry("360x470")
        janela.resizable(False, False)
        janela.transient(self.root)
        janela.grab_set()

        container = ttk.Frame(janela, padding=20)
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="Cadastro de cliente", style="Titulo.TLabel").pack(anchor="w", pady=(0, 6))

        def campo(rotulo):
            ttk.Label(container, text=rotulo, style="Muted.TLabel").pack(anchor="w", pady=(8, 3))
            entrada = tk.Entry(
                container, font=("Segoe UI Semibold", 11), bg=TEMA["painel"], fg=TEMA["texto"],
                insertbackground=TEMA["texto"], relief="flat"
            )
            entrada.pack(fill="x", ipady=6)
            return entrada

        e_nome = campo("Nome completo")
        e_numero = campo("Número (telefone com DDD)")
        e_doc = campo("CPF ou CNPJ")
        e_email = campo("E-mail (opcional)")

        lbl_erro = tk.Label(
            container, text="", bg=TEMA["fundo"], fg="#c96b5c", font=("Segoe UI Semibold", 9),
            anchor="w", justify="left", wraplength=310
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

        tk.Button(
            container, text="Salvar cliente", font=("Segoe UI Semibold", 11, "bold"),
            bg=TEMA["cobre"], fg="#1a1300", relief="flat", padx=10, pady=10, command=salvar
        ).pack(fill="x", pady=(14, 6))
        tk.Button(
            container, text="Cancelar", font=("Segoe UI Semibold", 9),
            bg=TEMA["fundo"], fg=TEMA["muted"], relief="flat", padx=6, pady=6, command=janela.destroy
        ).pack(fill="x")

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
            self.btn_adicionar.configure(state="normal")
        else:
            self.lbl_valor.configure(text="Valor: R$ 0,00")
            self.btn_adicionar.configure(state="disabled")

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
