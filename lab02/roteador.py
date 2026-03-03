# -*- coding: utf-8 -*-

import copy
import csv
import json
import threading
import time
from argparse import ArgumentParser

import requests
from flask import Flask, jsonify, request

class Router:
    """
    Representa um roteador que executa o algoritmo de Vetor de Distância.
    """

    def __init__(self, my_address, neighbors, my_network, update_interval=1):
        """
        Inicializa o roteador.

        :param my_address: O endereço (ip:porta) deste roteador.
        :param neighbors: Um dicionário contendo os vizinhos diretos e o custo do link.
                          Ex: {'127.0.0.1:5001': 5, '127.0.0.1:5002': 10}
        :param my_network: A rede que este roteador administra diretamente.
                           Ex: '10.0.1.0/24'
        :param update_interval: O intervalo em segundos para enviar atualizações, o tempo que o roteador espera 
                                antes de enviar atualizações para os vizinhos.        """
        self.my_address = my_address
        self.neighbors = neighbors
        self.my_network = my_network
        self.update_interval = update_interval

        # TODO: Este é o local para criar e inicializar sua tabela de roteamento.
        #
        # 1. Crie a estrutura de dados para a tabela de roteamento. Um dicionário é
        #    uma ótima escolha, onde as chaves são as redes de destino (ex: '10.0.1.0/24')
        #    e os valores são outro dicionário contendo 'cost' e 'next_hop'.
        #    Ex: {'10.0.1.0/24': {'cost': 0, 'next_hop': '10.0.1.0/24'}}
        #
        # 2. Adicione a rota para a rede que este roteador administra diretamente
        #    (a rede em 'self.my_network'). O custo para uma rede diretamente
        #    conectada é 0, e o 'next_hop' pode ser a própria rede ou o endereço do roteador.
        #
        # 3. Adicione as rotas para seus vizinhos diretos, usando o dicionário
        #    'self.neighbors'. Para cada vizinho, o 'cost' é o custo do link direto
        #    e o 'next_hop' é o endereço do próprio vizinho.

        # Lock para evitar condições de corrida entre a thread periódica e o Flask
        self.lock = threading.Lock()

        self.routing_table = {}
        self.routing_table[self.my_network] = {
            'cost': 0,
            'next_hop': self.my_network
        }

        # for vizinho_address, link_cost in self.neighbors.items():
        #     self.routing_table[vizinho_address] = {
        #         'cost': link_cost,
        #         'next_hop': vizinho_address
        #     }

        print(self.tentar_sumarizar("192.168.20.0/24", "192.168.21.0/24"))
        print(self.tentar_sumarizar("192.168.0.0/24", "192.168.1.0/24"))
        print(self.tentar_sumarizar("10.0.0.0/23", "10.0.2.0/23"))
        print(self.tentar_sumarizar("172.16.0.0/25", "172.16.0.128/25"))
        print("")
        print(self.tentar_sumarizar("192.168.20.0/24", "192.168.22.0/24"))
        print(self.tentar_sumarizar("192.168.21.0/24", "192.168.22.0/24"))
        print(self.tentar_sumarizar("192.168.20.0/24", "192.168.20.128/25"))
        
        tabela = {
    "10.0.0.0/24": {"cost": 2, "next_hop": "127.0.0.1:5001"},
    "10.0.1.0/24": {"cost": 3, "next_hop": "127.0.0.1:5001"},
}
        tabela2 = {
    "10.0.0.0/24": {"cost": 2, "next_hop": "127.0.0.1:5001"},
    "10.0.2.0/24": {"cost": 3, "next_hop": "127.0.0.1:5001"},
}
        
        tabela3 = {
    "10.0.0.0/24": {"cost": 2, "next_hop": "127.0.0.1:5001"},
    "10.0.1.0/24": {"cost": 3, "next_hop": "127.0.0.1:5002"},
}
        
        tabela4 = {
    "10.0.0.0/24": {"cost": 1, "next_hop": "127.0.0.1:5001"},
    "10.0.1.0/24": {"cost": 2, "next_hop": "127.0.0.1:5001"},
    "10.0.2.0/24": {"cost": 3, "next_hop": "127.0.0.1:5001"},
    "10.0.3.0/24": {"cost": 4, "next_hop": "127.0.0.1:5001"},
}
        
        

        print("sumarizar tabela")
        print("1")
        print(self.sumarizar_tabela(tabela))
        print("2")

        print(self.sumarizar_tabela(tabela2))
        print("3")

    
        
        print(self.sumarizar_tabela(tabela23))
        print("4")

        print(self.sumarizar_tabela(tabela4))


        print("Tabela de roteamento inicial:")
        print(json.dumps(self.routing_table, indent=4))

        # Inicia o processo de atualização periódica em uma thread separada
        self._start_periodic_updates()

    def _start_periodic_updates(self):
        """Inicia uma thread para enviar atualizações periodicamente."""
        thread = threading.Thread(target=self._periodic_update_loop)
        thread.daemon = True
        thread.start()

    def _periodic_update_loop(self):
        """Loop que envia atualizações de roteamento em intervalos regulares."""
        while True:
            time.sleep(self.update_interval)
            print(f"[{time.ctime()}] Enviando atualizações periódicas para os vizinhos...")
            try:
                self.send_updates_to_neighbors()
            except Exception as e:
                print(f"Erro durante a atualização periódida: {e}")

    

    def ip_para_int(self, ip_str):
        """
        Converte um endereço IP (ex: '192.168.20.0') para um inteiro de 32 bits.
        Sem uso de bibliotecas — apenas operações básicas.

        Exemplo: '192.168.20.0' -> 11000000.10101000.00010100.00000000
        """
        partes = ip_str.split('.')
        resultado = 0
        for parte in partes:
            resultado = (resultado << 8) | int(parte)
        return resultado

    def int_para_ip(self, numero):
        """
        Converte um inteiro de 32 bits de volta para string IP.
        Exemplo: 3232240640 -> '192.168.20.0'
        """
        partes = []
        for _ in range(4):
            partes.insert(0, str(numero & 0xFF))  # Pega os 8 bits menos significativos
            numero >>= 8
        return '.'.join(partes)

    
    

    def tentar_sumarizar(self, rede1, rede2):
        """
        Tenta agregar duas redes em uma super-rede.
        Retorna a super-rede (string 'ip/prefixo') se for possível, ou None.

        Condições para sumarização:
        - As duas redes devem ter o mesmo prefixo (/24, /23, etc.)
        - Devem ser "vizinhas" — diferir apenas no último bit do prefixo
        - O bit que as diferencia deve ser 0 na primeira e 1 na segunda
            (ou seja, a primeira é o bloco "par" e a segunda é o bloco "ímpar")

        Exemplo:
        192.168.20.0/24 + 192.168.21.0/24 -> 192.168.20.0/23
        Binário: ...00010100 e ...00010101 -> diferem só no último bit do /24
        """
        ip1_str, prefixo1_str = rede1.split('/')
        ip2_str, prefixo2_str = rede2.split('/')

        prefixo1 = int(prefixo1_str)
        prefixo2 = int(prefixo2_str)

        # As redes precisam ter o mesmo prefixo
        if prefixo1 != prefixo2:
            return None

        ip1 = self.ip_para_int(ip1_str)
        ip2 = self.ip_para_int(ip2_str)

        # Calcula a máscara do prefixo atual
        # Ex: /24 -> 11111111.11111111.11111111.00000000
        mascara_atual = (0xFFFFFFFF << (32 - prefixo1)) & 0xFFFFFFFF

        # O novo prefixo é um bit menor (agrega dois blocos em um)
        novo_prefixo = prefixo1 - 1
        nova_mascara = (0xFFFFFFFF << (32 - novo_prefixo)) & 0xFFFFFFFF

        # Verifica se as duas redes pertencem ao mesmo bloco no novo prefixo
        # Isso é: ambas têm a mesma parte de rede fcom o prefixo reduzido
        if (ip1 & nova_mascara) != (ip2 & nova_mascara):
            return None

        # Verifica que as redes são exatamente adjacentes:
        # O XOR entre elas deve ser exatamente o bit que o novo prefixo "libera"
        bit_diferenca = 1 << (32 - prefixo1)
        if (ip1 ^ ip2) != bit_diferenca:
            return None

        # Calcula o endereço da super-rede (AND com nova máscara)
        novo_ip = ip1 & nova_mascara
        return f"{self.int_para_ip(novo_ip)}/{novo_prefixo}"
        
            
    
    def sumarizar_tabela(self, tabela):
        """
        Aplica sumarização de rotas em uma cópia da tabela de roteamento.

        Só sumariza rotas que:
        1. Estão no formato 'ip/prefixo' (ignora endereços ip:porta)
        2. Possuem o mesmo next_hop

        O custo da rota sumarizada é o MAIOR custo entre as rotas originais
        (comportamento conservador — anuncia o pior caso).

        Retorna a tabela sumarizada.
        """
        import copy
        tabela_resumida = copy.deepcopy(tabela)

        # Filtra apenas rotas no formato CIDR (ignora entradas ip:porta)
        def eh_cidr(destino):
            return '/' in destino

        houve_mudanca = True
        # Repete até não encontrar mais nenhum par sumarizável
        while houve_mudanca:
            houve_mudanca = False
            rotas_cidr = [dest for dest in tabela_resumida if eh_cidr(dest)]

            # Compara todos os pares de rotas
            for i in range(len(rotas_cidr)):
                for j in range(i + 1, len(rotas_cidr)):
                    rede_a = rotas_cidr[i]
                    rede_b = rotas_cidr[j]

                    # Condição principal: mesmo next_hop
                    if tabela_resumida[rede_a]['next_hop'] != tabela_resumida[rede_b]['next_hop']:
                        continue

                    # Tenta agregar as duas redes
                    super_rede = self.tentar_sumarizar(rede_a, rede_b)
                    if super_rede is None:
                        continue

                    # Encontrou um par sumarizável!
                    custo_a = tabela_resumida[rede_a]['cost']
                    custo_b = tabela_resumida[rede_b]['cost']
                    next_hop = tabela_resumida[rede_a]['next_hop']

                    print(f"  [SUMARIZAÇÃO] {rede_a} + {rede_b} -> {super_rede} "
                        f"(custo: max({custo_a}, {custo_b}) = {max(custo_a, custo_b)})")

                    # Remove as rotas específicas e adiciona a super-rede
                    del tabela_resumida[rede_a]
                    del tabela_resumida[rede_b]
                    tabela_resumida[super_rede] = {
                        'cost': max(custo_a, custo_b),
                        'next_hop': next_hop
                    }

                    houve_mudanca = True
                    break  # Reinicia a busca com a tabela atualizada
                if houve_mudanca:
                    break

        return tabela_resumida
    

    def send_updates_to_neighbors(self):
        """
        Envia a tabela de roteamento (potencialmente sumarizada) para todos os vizinhos.
        """
        # TODO: O código abaixo envia a tabela de roteamento *diretamente*.
        #
        # ESTE TRECHO DEVE SER CHAMAADO APOS A SUMARIZAÇÃO.
        #
        # dica:
        # 1. CRIE UMA CÓPIA da `self.routing_table` NÃO ALTERE ESTA VALOR.
        # 2. IMPLEMENTE A LÓGICA DE SUMARIZAÇÃO nesta cópia.
        # 3. ENVIE A CÓPIA SUMARIZADA no payload, em vez da tabela original.
        
        with self.lock:
            tabela_para_enviar = copy.deepcopy(self.routing_table)

        tabela_para_enviar = self.sumarizar_tabela(tabela_para_enviar)

        payload = {
            "sender_address": self.my_address,
            "routing_table": tabela_para_enviar
        }

        for neighbor_address in self.neighbors:
            url = f'http://{neighbor_address}/receive_update'
            try:
                print(f"Enviando tabela para {neighbor_address}")
                print(f"Tabela Enviada: {tabela_para_enviar}")
                requests.post(url, json=payload, timeout=5)
            except requests.exceptions.RequestException as e:
                print(f"Não foi possível conectar ao vizinho {neighbor_address}. Erro: {e}")

# --- API Endpoints ---
# Instância do Flask e do Roteador (serão inicializadas no main)
app = Flask(__name__)
router_instance = None

@app.route('/routes', methods=['GET'])
def get_routes():
    """Endpoint para visualizar a tabela de roteamento atual."""
    # TODO: Aluno! Este endpoint está parcialmente implementado para ajudar na depuração.
    # Você pode mantê-lo como está ou customizá-lo se desejar.
    # - mantenha o routing_table como parte da resposta JSON.
    if router_instance:
        return jsonify({
            "message": "Não implementado!.",
            "vizinhos" : router_instance.neighbors,
            "my_network": router_instance.my_network,
            "my_address": router_instance.my_address,
            "update_interval": router_instance.update_interval,
            "routing_table": router_instance.routing_table # Exibe a tabela de roteamento atual (a ser implementada)
        })
    return jsonify({"error": "Roteador não inicializado"}), 500

@app.route('/receive_update', methods=['POST'])
def receive_update():
    """Endpoint que recebe atualizações de roteamento de um vizinho."""
    if not request.json:
        return jsonify({"error": "Invalid request"}), 400

    update_data = request.json
    sender_address = update_data.get("sender_address")
    sender_table = update_data.get("routing_table")

    if not sender_address or not isinstance(sender_table, dict):
        return jsonify({"error": "Missing sender_address or routing_table"}), 400

    print(f"Recebida atualização de {sender_address}:")
    print(json.dumps(sender_table, indent=4))

    # TODO: Implemente a lógica de Bellman-Ford aqui.
    #
    # 1. Verifique se o remetente é um vizinho conhecido.
    # 2. Obtenha o custo do link direto para este vizinho a partir de `router_instance.neighbors`.
    # 3. Itere sobre cada rota (`network`, `info`) na `sender_table` recebida.
    # 4. Calcule o novo custo para chegar à `network`:
    #    novo_custo = custo_do_link_direto + info['cost']
    # 5. Verifique sua própria tabela de roteamento:
    #    a. Se você não conhece a `network`, adicione-a à sua tabela com o
    #       `novo_custo` e o `next_hop` sendo o `sender_address`.
    #    b. Se você já conhece a `network`, verifique se o `novo_custo` é menor
    #       que o custo que você já tem. Se for, atualize sua tabela com o
    #       novo custo e o novo `next_hop`.
    #    c. (Opcional, mas importante para robustez): Se o `next_hop` para uma rota
    #       for o `sender_address`, você deve sempre atualizar o custo, mesmo que
    #       seja maior (isso ajuda a propagar notícias de links quebrados).
    #
    # 6. Mantenha um registro se sua tabela mudou ou não. Se mudou, talvez seja
    #    uma boa ideia imprimir a nova tabela no console.

    if sender_address not in router_instance.neighbors:
        print(f"  [IGNORADO] {sender_address} não é um vizinho conhecido.")
        return jsonify({"status": "ignored", "message": "Sender is not a known neighbor"}), 200

    # 2. Obtém o custo do link direto para este vizinho
    link_cost = router_instance.neighbors[sender_address]

    # Controle para saber se a tabela foi alterada nesta atualização
    table_changed = False

    with router_instance.lock:

        # 3. Itera sobre cada rota anunciada pelo vizinho
        for network, info in sender_table.items():

            # Nunca sobrescreve a própria rede diretamente conectada
            if network == router_instance.my_network:
                continue

            # Proteção adicional: ignora rotas que são super-redes da própria rede
            # Ex: se minha rede é 10.0.0.0/24, ignoro 10.0.0.0/22 recebida de vizinho
            if '/' in network:
                ip_rede, prefixo = network.split('/')
                ip_minha, prefixo_minha = router_instance.my_network.split('/')
                if int(prefixo) < int(prefixo_minha):  # prefixo menor = rede maior = possível super-rede
                    ip_r = router_instance.ip_para_int(ip_rede)
                    ip_m = router_instance.ip_para_int(ip_minha.split('/')[0] if '/' in ip_minha else ip_minha)
                    mascara = (0xFFFFFFFF << (32 - int(prefixo))) & 0xFFFFFFFF
                    if (ip_r & mascara) == (ip_m & mascara):
                        print(f"  [IGNORADO] {network} é super-rede da própria rede {router_instance.my_network}")
                        continue

            # 4. Calcula o novo custo pelo caminho passando pelo remetente
            #    Fórmula de Bellman-Ford: d(x) = min(custo_link + custo_vizinho)
            novo_custo = link_cost + info['cost']

            # 5. Compara com o que já temos na tabela
            rota_atual = router_instance.routing_table.get(network)

            if rota_atual is None:
                # 5a. Destino desconhecido — adiciona à tabela
                router_instance.routing_table[network] = {
                    'cost': novo_custo,
                    'next_hop': sender_address
                }
                print(f"  [NOVA ROTA]  {network} via {sender_address} | custo: {novo_custo}")
                table_changed = True

            elif novo_custo < rota_atual['cost']:
                # 5b. Caminho mais barato encontrado — atualiza
                router_instance.routing_table[network] = {
                    'cost': novo_custo,
                    'next_hop': sender_address
                }
                print(f"  [ATUALIZADO] {network} via {sender_address} | custo: {rota_atual['cost']} -> {novo_custo}")
                table_changed = True

            elif rota_atual['next_hop'] == sender_address:
                # 5c. O custo da rota atual já passa por este vizinho.
                #     Deve atualizar mesmo que o custo aumente, pois o vizinho
                #     pode estar reportando uma degradação ou falha no caminho.
                if rota_atual['cost'] != novo_custo:
                    print(f"  [REVISADO]   {network} via {sender_address} | custo: {rota_atual['cost']} -> {novo_custo}")
                    router_instance.routing_table[network]['cost'] = novo_custo
                    table_changed = True

        # 6. Se a tabela mudou, exibe o novo estado no console
        if table_changed:
            print(f"\n  Tabela de roteamento atualizada:")
            print(json.dumps(router_instance.routing_table, indent=4))
        else:
            print(f"  [SEM MUDANÇAS] Tabela mantida.")

        # ─────────────────────────────────────────────────────────────────────────

    return jsonify({"status": "success", "message": "Update received"}), 200

if __name__ == '__main__':
    parser = ArgumentParser(description="Simulador de Roteador com Vetor de Distância")
    parser.add_argument('-p', '--port', type=int, default=5000, help="Porta para executar o roteador.")
    parser.add_argument('-f', '--file', type=str, required=True, help="Arquivo CSV de configuração de vizinhos.")
    parser.add_argument('--network', type=str, required=True, help="Rede administrada por este roteador (ex: 10.0.1.0/24).")
    parser.add_argument('--interval', type=int, default=10, help="Intervalo de atualização periódica em segundos.")
    args = parser.parse_args()

    # Leitura do arquivo de configuração de vizinhos
    neighbors_config = {}
    try:
        with open(args.file, mode='r') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                neighbors_config[row['vizinho']] = int(row['custo'])
    except FileNotFoundError:
        print(f"Erro: Arquivo de configuração '{args.file}' não encontrado.")
        exit(1)
    except (KeyError, ValueError) as e:
        print(f"Erro no formato do arquivo CSV: {e}. Verifique as colunas 'vizinho' e 'custo'.")
        exit(1)

    my_full_address = f"127.0.0.1:{args.port}"
    print("--- Iniciando Roteador ---")
    print(f"Endereço: {my_full_address}")
    print(f"Rede Local: {args.network}")
    print(f"Vizinhos Diretos: {neighbors_config}")
    print(f"Intervalo de Atualização: {args.interval}s")
    print("--------------------------")

    router_instance = Router(
        my_address=my_full_address,
        neighbors=neighbors_config,
        my_network=args.network,
        update_interval=args.interval
    )

    # Inicia o servidor Flask
    app.run(host='0.0.0.0', port=args.port, debug=False)