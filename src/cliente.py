#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente TCP para gerenciamento de vagas de estacionamento.
O cliente envia comandos ao servidor para consultar,
pegar e liberar vagas.

Autor: ChatGPT e Copilot com orientação e revisão de Minora
Data: 2024-06-15

Procure por FIXME para identificar pontos que precisam de implementação adicional.

"""

import threading
import socket
import os
import time
import random
import logging
from dotenv import load_dotenv


def configurar_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    return logging.getLogger('cliente')


logger = configurar_logger()

class ClienteEstacionamento(threading.Thread):

    def __init__(self, socket_cliente, cliente_id):
        threading.Thread.__init__(self)
        self.socket_cliente = socket_cliente
        self.cliente_id = cliente_id

    def run(self):

        try:
            while True:
                if self.consultar_vaga():
                    if self.pegar_vaga():
                        self.passear()
                        self.liberar_vaga()
                        break
                time.sleep(random.uniform(0.2, 0.8))
        finally:
            self.socket_cliente.close()
            logger.info('Cliente %s finalizou a conexao', self.cliente_id)

    def consultar_vaga(self):

        resposta = self._enviar_comando('consultar_vaga')
        try:
            vagas = int(resposta)
        except ValueError:
            logger.error('Cliente %s recebeu resposta invalida: %s', self.cliente_id, resposta)
            return False
        logger.info('Cliente %s consultou vagas: %s disponiveis', self.cliente_id, vagas)
        return vagas > 0

    def pegar_vaga(self):

        resposta = self._enviar_comando('pegar_vaga')
        logger.info('Cliente %s tentou pegar vaga: %s', self.cliente_id, resposta)
        return resposta == '1'

    def liberar_vaga(self):

        resposta = self._enviar_comando('liberar_vaga')
        logger.info('Cliente %s liberou vaga: %s', self.cliente_id, resposta)
        return resposta == '1'
    
    def passear(self):

        tempo = random.uniform(0.5, 2.0)
        logger.info('Cliente %s usando vaga por %.2f segundos', self.cliente_id, tempo)
        time.sleep(tempo)

    def _enviar_comando(self, comando):
        logger.debug('Cliente %s enviando comando: %s', self.cliente_id, comando)
        self.socket_cliente.sendall(comando.encode('utf-8'))
        resposta = self.socket_cliente.recv(1024)
        return resposta.decode('utf-8').strip()

def criar_socket_cliente():
    # Cria e retorna um socket TCP para o cliente.
    load_dotenv()
    PORTA = int(os.getenv('PORT', 5000))

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect(('localhost', PORTA))

    return cliente

def main():

    clientes = []
    for indice in range(1, 51):
        socket_cliente = criar_socket_cliente()
        logger.info('Cliente %s conectado ao servidor', indice)
        cliente = ClienteEstacionamento(socket_cliente, indice)
        cliente.start()
        clientes.append(cliente)

    for cliente in clientes:
        cliente.join()

if __name__ == "__main__":
    main()            