"""Cadastro de clientes (nome, número, CPF/CNPJ e e-mail opcional), salvo em dados/clientes.json."""

import json
import os
import re
import uuid
from datetime import datetime

PASTA_DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")
ARQUIVO_CLIENTES = os.path.join(PASTA_DADOS, "clientes.json")


def somente_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto or "")


def formatar_documento(documento: str) -> str:
    d = somente_digitos(documento)
    if len(d) == 11:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    if len(d) == 14:
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    return documento


def formatar_telefone(numero: str) -> str:
    d = somente_digitos(numero)
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return numero


class GerenciadorClientes:
    """Lê, valida e grava os clientes cadastrados."""

    def __init__(self):
        os.makedirs(PASTA_DADOS, exist_ok=True)
        self.clientes = self._carregar()

    def _carregar(self) -> list:
        if not os.path.exists(ARQUIVO_CLIENTES):
            return []
        try:
            with open(ARQUIVO_CLIENTES, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def _salvar(self):
        with open(ARQUIVO_CLIENTES, "w", encoding="utf-8") as f:
            json.dump(self.clientes, f, ensure_ascii=False, indent=2)

    def listar(self) -> list:
        return sorted(self.clientes, key=lambda c: c["nome"].casefold())

    def obter(self, cliente_id: str):
        return next((c for c in self.clientes if c["id"] == cliente_id), None)

    def criar(self, nome: str, numero: str, documento: str, email: str = "") -> dict:
        nome = " ".join((nome or "").split())
        numero_d = somente_digitos(numero)
        documento_d = somente_digitos(documento)
        email = (email or "").strip()

        if len(nome.split()) < 2:
            raise ValueError("Digite o nome completo (nome e sobrenome).")
        if not 10 <= len(numero_d) <= 13:
            raise ValueError("Número inválido. Digite com DDD (ex.: 11 91234-5678).")
        if len(documento_d) not in (11, 14):
            raise ValueError("CPF precisa ter 11 dígitos, ou CNPJ 14 dígitos.")
        if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            raise ValueError("E-mail inválido.")
        if any(c["documento"] == documento_d for c in self.clientes):
            raise ValueError("Já existe um cliente cadastrado com esse CPF/CNPJ.")

        cliente = {
            "id": uuid.uuid4().hex[:8],
            "nome": nome,
            "numero": numero_d,
            "documento": documento_d,
            "email": email,
            "criado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
        }
        self.clientes.append(cliente)
        self._salvar()
        return cliente
