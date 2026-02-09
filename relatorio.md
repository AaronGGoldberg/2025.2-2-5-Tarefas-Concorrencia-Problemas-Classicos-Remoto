# Relatório - Problema de Leitores/Escritores com sockets (Estacionamento)

## Contexto inicial do trabalho (introdução)
Este trabalho implementa uma solução para o problema clássico de leitores/escritores, usando
comunicação via sockets TCP. O cenário adotado é um estacionamento com 10 vagas, em que clientes
podem consultar a disponibilidade de vagas (leitura concorrente) e pegar/liberar vagas
(escrita exclusiva). O objetivo é demonstrar controle de concorrência e sincronização entre
processos remotos.

## Descrevendo a solução em Python para o problema de leitor/escritor

### Implementando o servidor e cliente
O servidor mantém a contagem de vagas disponíveis e responde a três comandos:
`consultar_vaga`, `pegar_vaga` e `liberar_vaga`. Para garantir consistência, ele usa um
lock de leitores/escritores: várias consultas podem ocorrer em paralelo, mas alterações
no número de vagas exigem exclusão mútua.

O cliente cria 50 threads (clientes concorrentes). Cada cliente tenta consultar a vaga,
pegar uma vaga quando houver disponibilidade, simula o uso com um tempo de passeio e, por fim,
libera a vaga.

### Tratando impasse
#### Qual a estratégia de tratamento de impasses
A estratégia utilizada é a **prevenção de deadlock** por meio de uma ordem única e simples
de aquisição de recursos: há apenas um recurso compartilhado (contagem de vagas) protegido por
um lock de leitores/escritores. Isso evita ciclos de espera, pois não há múltiplos recursos
com diferentes ordens de bloqueio.

#### Implementação do tratamento de impasse em Python
O lock de leitores/escritores foi implementado com `threading.Condition`, permitindo:
- Leitura concorrente quando não há escritores ativos ou esperando.
- Escrita exclusiva quando não há leitores ativos.
Com isso, o servidor garante que o estado de vagas não fica inconsistente e que não ocorre
deadlock por múltiplos locks.

## Executar o código e descrever comportamento observado
Para executar:
1. Em um terminal, iniciar o servidor: `python src/server.py`

![Registro do Servidor](/img/RegistroServer.png)

2. Em outro terminal, iniciar o cliente: `python src/cliente.py`

![Registro do Cliente](/img/RegistroClient.png)

Comportamento observado:
- Vários clientes consultam simultaneamente a quantidade de vagas.
- Apenas até 10 clientes conseguem pegar vagas ao mesmo tempo.
- Após o tempo de uso simulado, as vagas são liberadas e outros clientes conseguem entrar.

## Considerações finais
A implementação demonstra os principais conceitos de concorrência em sistemas distribuídos:
uso de sockets para comunicação, exclusão mútua para escrita, sincronização para coordenação
entre clientes e prevenção de deadlock por um esquema simples de bloqueio. O modelo de
leitores/escritores é adequado para cenários em que há muitas leituras e poucas escritas,
como no controle de vagas de um estacionamento.