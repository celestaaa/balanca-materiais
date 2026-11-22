"""Janela inicial: login e criação de conta da empresa."""

import tkinter as tk
from tkinter import ttk

from estilo import TEMA, FONTE
from widgets import BotaoArredondado, EntradaArredondada, CabecalhoDegrade
from autenticacao import GerenciadorUsuarios


class TelaLogin(tk.Tk):
    def __init__(self, ao_logar):
        """ao_logar: função chamada com os dados do usuário quando o login der certo."""
        super().__init__()
        self.ao_logar = ao_logar
        self.usuarios = GerenciadorUsuarios()
        self.modo = "login"  # ou "cadastro"

        self.title("Balança de Materiais — Acesso")
        self.configure(bg=TEMA["fundo"])
        self.geometry("400x560")
        self.resizable(False, False)

        self._montar_estilo()
        self._montar_layout()

    def _montar_estilo(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=TEMA["fundo"])
        style.configure("TLabel", background=TEMA["fundo"], foreground=TEMA["texto"], font=(FONTE, 10))
        style.configure("Muted.TLabel", background=TEMA["fundo"], foreground=TEMA["muted"], font=(FONTE, 9))
        style.configure("Titulo.TLabel", background=TEMA["fundo"], foreground=TEMA["texto"], font=(FONTE, 16, "bold"))
        style.configure("Erro.TLabel", background=TEMA["fundo"], foreground=TEMA["erro"], font=(FONTE, 9))

    def _montar_layout(self):
        CabecalhoDegrade(
            self, "Balança de Materiais", "Pesagem e cotação de materiais",
            fundo_pai=TEMA["fundo"], altura=88
        ).pack(fill="x", padx=14, pady=(14, 0))

        self.container = ttk.Frame(self, padding=(30, 22, 30, 22))
        self.container.pack(fill="both", expand=True)
        self._renderizar()

    def _limpar_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def _campo(self, label_texto, mostrar=None):
        ttk.Label(self.container, text=label_texto, style="Muted.TLabel").pack(anchor="w", pady=(10, 4))
        campo = EntradaArredondada(
            self.container, fundo_pai=TEMA["fundo"], bg=TEMA["painel"], font=(FONTE, 11),
            raio=999, show=mostrar or "", pady=9
        )
        campo.pack(fill="x")
        return campo.entry

    def _botao_principal(self, texto, comando, cor):
        return BotaoArredondado(
            self.container, text=texto, command=comando, bg=cor, fg=TEMA["sobre_destaque"],
            hover=TEMA["destaque_hover"], fundo_pai=TEMA["fundo"], raio=999,
            font=(FONTE, 11, "bold"), pady=12
        )

    def _botao_secundario(self, texto, comando):
        return BotaoArredondado(
            self.container, text=texto, command=comando, bg=TEMA["painel"], fg=TEMA["muted"],
            borda=TEMA["linha"], fundo_pai=TEMA["fundo"], raio=999, font=(FONTE, 9), pady=9
        )

    # ---------- Modo login ----------
    def _renderizar(self):
        self._limpar_container()
        if self.modo == "login":
            self.geometry("400x560")
            self._renderizar_login()
        else:
            self.geometry("400x720")
            self._renderizar_cadastro()

    def _renderizar_login(self):
        ttk.Label(self.container, text="Acessar conta", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self.container, text="Entre com a conta da sua empresa.", style="Muted.TLabel").pack(anchor="w", pady=(2, 0))

        self.entry_usuario = self._campo("Usuário")
        self.entry_senha = self._campo("Senha", mostrar="*")

        self.lbl_erro = ttk.Label(self.container, text="", style="Erro.TLabel")
        self.lbl_erro.pack(anchor="w", pady=(10, 0))

        self._botao_principal("Entrar", self._tentar_login, TEMA["destaque"]).pack(fill="x", pady=(14, 8))
        self._botao_secundario("Criar conta da empresa", self._ir_para_cadastro).pack(fill="x")

        self.entry_usuario.focus_set()
        self.bind("<Return>", lambda e: self._tentar_login())

    def _tentar_login(self):
        usuario = self.entry_usuario.get()
        senha = self.entry_senha.get()
        dados = self.usuarios.validar_login(usuario, senha)
        if dados:
            self.destroy()
            self.ao_logar(dados)
        else:
            self.lbl_erro.configure(text="Usuário ou senha inválidos.")

    def _ir_para_cadastro(self):
        self.modo = "cadastro"
        self.unbind("<Return>")
        self._renderizar()

    # ---------- Modo cadastro ----------
    def _renderizar_cadastro(self):
        ttk.Label(self.container, text="Criar conta", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self.container, text="Cadastre o acesso da sua empresa.", style="Muted.TLabel").pack(anchor="w", pady=(2, 0))

        self.entry_empresa = self._campo("Nome da empresa")
        self.entry_novo_usuario = self._campo("Usuário")
        self.entry_nova_senha = self._campo("Senha", mostrar="*")
        self.entry_confirmar_senha = self._campo("Confirmar senha", mostrar="*")

        self.lbl_erro = ttk.Label(self.container, text="", style="Erro.TLabel")
        self.lbl_erro.pack(anchor="w", pady=(10, 0))

        self._botao_principal("Criar conta", self._tentar_cadastrar, TEMA["total"]).pack(fill="x", pady=(14, 8))
        self._botao_secundario("Já tenho conta — Entrar", self._ir_para_login).pack(fill="x")

        self.bind("<Return>", lambda e: self._tentar_cadastrar())

    def _ir_para_login(self):
        self.modo = "login"
        self.unbind("<Return>")
        self._renderizar()

    def _tentar_cadastrar(self):
        empresa = self.entry_empresa.get()
        usuario = self.entry_novo_usuario.get()
        senha = self.entry_nova_senha.get()
        confirmar = self.entry_confirmar_senha.get()

        if senha != confirmar:
            self.lbl_erro.configure(text="As senhas não coincidem.")
            return

        try:
            self.usuarios.criar_usuario(empresa, usuario, senha)
        except ValueError as e:
            self.lbl_erro.configure(text=str(e))
            return

        self._ir_para_login()
        self.lbl_erro.configure(text="Conta criada! Faça login para continuar.")
        self.lbl_erro.configure(foreground=TEMA["total"])
