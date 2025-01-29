#CÓDIGO FINAL, GRAÇAS A DEUS!!!!!!!!!!!!!

import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm  # Biblioteca para barra de progresso


#Algumas considerações:
#O formato de código HTML do site do "QuemFornece?" é extremamente ruim, não usa nenhum padrão para armazenar as informações
#e deixa toda a criação de divs e tabelas nas mãos do PHP, isso dificultou muito a coleta de dados, pois poderia simplesmente
#buscar uma div específica ou uma tabela específica ou até mesmo uma ID, mas todos esses dados está sendo processado pelo PHP
#isso gera diversos problemas pois não dá pra deixar de maneira 100% automatica e eficaz para a coleta em todos os sites
#ja que o código itera sobre URL's do código base HTML das páginas, então links que poderiam ser da empresa como exemplo:
# ajudaaqui.com.br ou instagram.com/empresanomex poderiam ser ignorados, portanto, precisei fazer uma lista de sites que devem
#ser ignorados para evitar problemas e acessos desnecessários.
#outro problema é que proxys e acessos demasiados de servidor podem ocasionar no bloqueio de acesso, não tive esse problema
#no QuemFornece? mas é possível que em outros sites esse problema ocorra. Sendo sincero, não sei como proceder se esse
#problema acontecer.


#AVISO!!!! O CÓDIGO É LENTO! MUITO LENTO! Esta é a minha primeira experiência utilizando Python com qualquer coisa 
#relacionado a web, não sei como deixar esse processo mais rápido ainda.

# Lista de URLs a serem evitadas (páginas desnecessárias)
urls_ignoradas = [
    "ajuda",
    "vantagens-para-fornecedores",
    "guiadefeiras",
    "planos",
    "buscas_homepage",
    "exemplo-de-plano",
    "como-encontrar-fornecedores-no-portal",
    "https://www.quemfornece.com/vantagens-para-fornecedores",
    "https://www.quemfornece.com/ajuda/como-encontrar-fornecedores-no-portal",
    "login",
    "contato",
    "criar-conta?tipo=comprador"
]

# Lista para armazenar URLs de fornecedores já acessados
urls_fornecedores_acessados = []

# Função para verificar se uma URL deve ser ignorada
def url_deve_ser_ignorada(url, exibir_logs):
    url = url.lower().strip()
    for termo in urls_ignoradas:
        if termo in url:
            if exibir_logs:
                print(f"[IGNORADO] URL ignorada: {url}")
            return True
    return False

# Função para coletar dados de fornecedores de uma página individual
def coletar_dados_fornecedor(url, exibir_logs):
    if url in urls_fornecedores_acessados:
        if exibir_logs:
            print(f"[IGNORADO] URL já acessada: {url}")
        return None

    if exibir_logs:
        print(f"[COLETANDO] Dados do fornecedor: {url}")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            contact_section = soup.find_all("div", class_="flex items-center")

            addresses = []
            phones = set()
            websites = set()

            for section in contact_section:
                text_blocks = section.find_all("div")
                for block in text_blocks:
                    text = block.get_text(strip=True)
                    if text and text not in addresses:
                        addresses.append(text)

            links = soup.find_all("a")
            exclude_keywords = ["whatsapp", "quemfornece", "facebook;com/quemfornece", "instagram.com/quemfornece", "linkedin"]
            for link in links:
                href = link.get("href", "")
                if any(keyword in href for keyword in exclude_keywords):
                    continue
                if href.startswith("tel:"):
                    phones.add(href.replace("tel:", "").strip())
                elif href.startswith("http"):
                    websites.add(href.strip())

            if exibir_logs:
                print(f"[RESULTADO] Endereços: {addresses}")
                print(f"[RESULTADO] Telefones: {list(phones)}")
                print(f"[RESULTADO] Sites: {list(websites)}")

            urls_fornecedores_acessados.append(url)
            return {
                "Nome_Fornecedor": url.split("/")[-1],
                "Enderecos": "; ".join(addresses),
                "Telefones": "; ".join(phones),
                "Sites": "; ".join(websites),
                "Site_QuemFornece": url
            }
        else:
            if exibir_logs:
                print(f"[ERRO] Código de status: {response.status_code} para {url}")
            return None
    except Exception as e:
        if exibir_logs:
            print(f"[ERRO] Falha ao coletar dados do fornecedor: {e}")
        return None

# Função para navegar por cada página de categoria e coletar os fornecedores
def coletar_fornecedores_por_categoria(url_categoria, letra_atual, exibir_logs):
    if exibir_logs:
        print(f"[ACESSANDO] Categoria: {url_categoria}")
    try:
        response = requests.get(url_categoria)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            fornecedores = []

            links_fornecedores = soup.find_all("a", href=True)
            for link in links_fornecedores:
                url_fornecedor = link['href']
                if "fornecedor" in url_fornecedor:
                    url_completa = "https://www.quemfornece.com" + url_fornecedor if url_fornecedor.startswith('/') else url_fornecedor
                    if not url_deve_ser_ignorada(url_completa, exibir_logs):
                        dados_fornecedor = coletar_dados_fornecedor(url_completa, exibir_logs)
                        if dados_fornecedor:
                            fornecedores.append(dados_fornecedor)
            return fornecedores
        else:
            if exibir_logs:
                print(f"[ERRO] Código de status: {response.status_code} para {url_categoria}")
            return []
    except Exception as e:
        if exibir_logs:
            print(f"[ERRO] Falha ao acessar categoria: {e}")
        return []

# Função para iterar por todas as letras de A a Z
def coletar_todas_as_categorias(modo_teste, exibir_logs):
    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    fornecedores_por_letra = []

    for letra in letras:
        print(f"[INICIANDO] Coleta para a letra {letra}")
        pagina_atual = 156 if modo_teste and letra == "A" else 1
        paginas_sem_dados = 0

        with tqdm(desc=f"Letra {letra}", unit="página", disable=False) as barra:
            while True:
                log_pagina = f"[PÁGINA] Letra {letra}, página {pagina_atual}"
                barra.set_description_str(log_pagina)  # Atualiza descrição na barra
                print(log_pagina)

                url_letra = f"https://www.quemfornece.com/categorias-por-letra/{letra}?page={pagina_atual}"

                try:
                    response = requests.get(url_letra)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "html.parser")
                        categorias = soup.find_all("a", href=True)
                        dados_coletados = False

                        for categoria in categorias:
                            url_categoria = categoria['href']
                            if not url_deve_ser_ignorada(url_categoria, exibir_logs):
                                url_categoria_completa = "https://www.quemfornece.com" + url_categoria if url_categoria.startswith('/') else url_categoria
                                fornecedores = coletar_fornecedores_por_categoria(url_categoria_completa, letra, exibir_logs)
                                if fornecedores:
                                    dados_coletados = True
                                    fornecedores_por_letra.extend(fornecedores)

                        if not dados_coletados:
                            paginas_sem_dados += 1
                        else:
                            paginas_sem_dados = 0

                        if paginas_sem_dados >= 2:
                            print(f"[FIM] Chegou ao final da letra {letra}.")
                            break

                        pagina_atual += 1
                        barra.update(1)
                    else:
                        if exibir_logs:
                            print(f"[ERRO] Código de status: {response.status_code} para {url_letra}")
                        break
                except Exception as e:
                    if exibir_logs:
                        print(f"[ERRO] Falha na coleta de letra {letra}: {e}")
                    break
    return fornecedores_por_letra

# Pergunta inicial sobre o modo de teste
modo_teste = input("Deseja iniciar na página 156 da letra A para teste? (s/n): ").strip().lower() == 's'

# Pergunta inicial sobre exibir logs ou barra de carregamento
exibir_logs = input("Deseja exibir logs detalhados? (s/n): ").strip().lower() == 's'

# Executa a coleta de todas as categorias
resultado_final = coletar_todas_as_categorias(modo_teste, exibir_logs)

# Exportação para Excel
df = pd.DataFrame(resultado_final)
df.to_excel("fornecedores_teste.xlsx" if modo_teste else "fornecedores.xlsx", index=False)
print("[FINALIZADO] Dados exportados para 'fornecedores_teste.xlsx'!" if modo_teste else "[FINALIZADO] Dados exportados para 'fornecedores.xlsx'!")
