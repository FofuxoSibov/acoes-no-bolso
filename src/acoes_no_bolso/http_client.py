"""Ponto único para criar clientes HTTP usados pelo backend."""

from __future__ import annotations

import httpx


def create_http_client() -> httpx.Client:
    """Cria o cliente síncrono compartilhável da aplicação.

    O cliente não recebe tokens neste nível: cada integração adiciona somente os
    cabeçalhos que lhe pertencem, evitando o envio acidental de credenciais para
    outros domínios.
    """

    return httpx.Client(
        timeout=httpx.Timeout(15.0),
        headers={"Accept": "application/json"},
        follow_redirects=False,
    )

