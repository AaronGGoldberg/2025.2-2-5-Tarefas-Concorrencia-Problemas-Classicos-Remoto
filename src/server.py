#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor TCP para gerenciamento de vagas de estacionamento.
O servidor escuta conexões de clientes e responde a comandos para consultar,
pegar e liberar vagas.

Autor: ChatGPT e Copilot com orientação e revisão de Minora
Data: 2024-06-15

Procure por FIXME para identificar pontos que precisam de implementação adicional.

"""
import socket
import os
import threading
import logging
from dotenv import load_dotenv

VAGAS_TOTAIS = 10


class LeitoresEscritoresLock:
    """Lock de leitores/escritores com preferência para escritores."""

    def __init__(self):
        self._condicao = threading.Condition()
        self._leitores = 0
        self._escritor_ativo = False
        self._escritores_esperando = 0

    def adquirir_leitura(self):
        with self._condicao:
            while self._escritor_ativo or self._escritores_esperando > 0:
                self._condicao.wait()
            self._leitores += 1

    def liberar_leitura(self):
        with self._condicao:
            self._leitores -= 1
            if self._leitores == 0:
                self._condicao.notify_all()

    def adquirir_escrita(self):
        with self._condicao:
            self._escritores_esperando += 1
            while self._escritor_ativo or self._leitores > 0:
                self._condicao.wait()
            self._escritores_esperando -= 1
            self._escritor_ativo = True

    def liberar_escrita(self):
        with self._condicao:
            self._escritor_ativo = False
            self._condicao.notify_all()


lock_leitores_escritores = LeitoresEscritoresLock()
vagas_disponiveis = VAGAS_TOTAIS


def configurar_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    return logging.getLogger('servidor')


logger = configurar_logger()

def escutar_cliente(nova_conexao, endereco):
    """Função para tratar a comunicação com cada cliente"""

    global vagas_disponiveis
    cliente_id = f'{endereco[0]}:{endereco[1]}'
    logger.info('Cliente conectado: %s', cliente_id)
    possui_vaga = False
    
    try:
        while True:
            mensagem = nova_conexao.recv(1024)
            if not mensagem:
                break            
            comando = mensagem.decode("utf-8").strip()

            logger.info('Comando recebido de %s: %s', cliente_id, comando)
            
            if comando == 'consultar_vaga':
                # retorna quantidade de vagas disponíveis

                lock_leitores_escritores.adquirir_leitura()
                try:
                    resposta = str(vagas_disponiveis)
                finally:
                    lock_leitores_escritores.liberar_leitura()
                logger.info('Consulta de vagas por %s: %s disponiveis', cliente_id, resposta)
                nova_conexao.send(resposta.encode('utf-8'))
                
            elif comando == 'pegar_vaga':
                # retorna 1 se vaga foi alocada com sucesso
                #     ou 0 se não há vagas disponíveis

                if possui_vaga:
                    resposta = str(0)
                    logger.warning('Cliente %s ja possui vaga; alocacao negada', cliente_id)
                    nova_conexao.send(resposta.encode('utf-8'))
                    continue

                lock_leitores_escritores.adquirir_escrita()
                try:
                    if vagas_disponiveis > 0:
                        vagas_disponiveis -= 1
                        possui_vaga = True
                        resposta = str(1)
                        logger.info(
                            'Vaga alocada para %s. Restantes: %s',
                            cliente_id,
                            vagas_disponiveis,
                        )
                    else:
                        resposta = str(0)
                        logger.info('Sem vagas para %s no momento', cliente_id)
                finally:
                    lock_leitores_escritores.liberar_escrita()
                nova_conexao.send(resposta.encode('utf-8'))
                
            elif comando == 'liberar_vaga':
                # retorna 1 se vaga foi liberada com sucesso
                #     ou 0 se não o cliente não possuía vaga alocada
                # caso de sucesso, lembrar de fechar a conexão e finalizar esta função

                if not possui_vaga:
                    resposta = str(0)
                    logger.warning('Cliente %s tentou liberar sem possuir vaga', cliente_id)
                    nova_conexao.send(resposta.encode('utf-8'))
                    continue

                lock_leitores_escritores.adquirir_escrita()
                try:
                    vagas_disponiveis += 1
                    possui_vaga = False
                    resposta = str(1)
                    logger.info(
                        'Vaga liberada por %s. Disponiveis: %s',
                        cliente_id,
                        vagas_disponiveis,
                    )
                finally:
                    lock_leitores_escritores.liberar_escrita()
                nova_conexao.send(resposta.encode('utf-8'))
                break
                
            else:
                # retorna -1 para comando inválido
                resposta = '-1'
                logger.error('Comando invalido de %s: %s', cliente_id, comando)
                nova_conexao.send(resposta.encode('utf-8'))
                
    finally:
        nova_conexao.close()
        logger.info('Cliente desconectado: %s', cliente_id)

def iniciar_servidor():
    """Função para iniciar o servidor TCP"""
    load_dotenv()
    PORTA = int(os.getenv('PORT', 5000))

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('localhost', PORTA))
    servidor.listen(5)
    logger.info('Servidor escutando na porta %s', PORTA)
    logger.info('Aguardando conexoes de clientes...')
    return servidor

def main():
    servidor = iniciar_servidor()
    try:
        while True:
            nova_conexao, endereco = servidor.accept()
            thread = threading.Thread(target=escutar_cliente, args=(nova_conexao, endereco))
            thread.daemon = True
            thread.start()
        
    finally:
        servidor.close()
        logger.info('Servidor encerrado')

if __name__ == '__main__':
    main()       