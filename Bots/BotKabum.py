import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from pushbullet import Pushbullet
from bs4 import BeautifulSoup
import requests
import sys

sys.path.append(r'\Links')

from Links_Kabum import obter_urls_kabum

pb = Pushbullet('')

def configurar_webdriver():
    # Crie as opções do Firefox primeiro
    firefox_options = FirefoxOptions()
    firefox_options.add_argument("--disable-notifications")
    firefox_options.add_argument("--headless") 

    # Crie o driver do Firefox com as opções
    driver = webdriver.Firefox(options=firefox_options)

    return driver

urls_dos_produtos = obter_urls_kabum()

def extrair_informacoes_kabum(url_produto, preco_estipulado):
    print('iniciando extração')
    driver = configurar_webdriver()
    response = requests.get(url_produto)
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        driver.get(url_produto)
        name_tag = soup.find('h1', class_='sc-89bddf0f-6 dVrDvy')
        if name_tag:
            nome_produto = name_tag.text.strip()

        price_tag = soup.find('h4', class_='sc-5492faee-2 hAMMrD finalPrice')
        if price_tag:
            # Remover caracteres não numéricos e substituir vírgulas por pontos
            preco_text = ''.join(filter(str.isdigit, price_tag.text))
            preco_text = preco_text[:-2] + '.' + preco_text[-2:]
            preco_atual = float(preco_text)

    except Exception as e:
        print(f"Erro ao extrair informações da Pichau: {e}")
        nome_produto = None
        preco_atual = None

    finally:
        if preco_atual is not None and preco_atual <= preco_estipulado:
            pb.push_note("Produto em Promoção!",
                         f"{nome_produto} está abaixo de {preco_estipulado}.\nLink: {url_produto}")
            print(f"Realizando a compra na Kabum...")
        else:
            print("Produto não está abaixo do preço estipulado")
            driver.quit()

    return {"loja": "Kabum", "nome": nome_produto, "preco-ant": None, "preco": preco_atual, "link": url_produto}

def main():
    while True:
        for url, preco_estipulado in urls_dos_produtos:
            informacoes = extrair_informacoes_kabum(url, preco_estipulado)

        # Aguarda 1 segundo antes da próxima iteração
        time.sleep(1)

if __name__ == "__main__":
    main()
