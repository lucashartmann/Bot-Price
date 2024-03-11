import time
import openpyxl
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from pushbullet import Pushbullet
from selenium.webdriver.common.action_chains import ActionChains
from openpyxl import load_workbook
import sys
from multiprocessing import Pool

sys.path.append(r'\Links')

from Links_Pichau import obter_urls_pichau
from Links_Kabum import obter_urls_kabum
from Links_Amazon import obter_urls_amazon
from Links_Terabyte import obter_urls_terabyte


# Lista de URLs dos produtos que você deseja monitorar, com preço estipulado


urls_pichau = obter_urls_pichau()
urls_amazon = obter_urls_amazon()
urls_terabyte = obter_urls_terabyte()
urls_kabum = obter_urls_kabum()


pb = Pushbullet('')     


def configurar_webdriver():
    # Crie as opções do Firefox primeiro
    firefox_options = FirefoxOptions()
    firefox_options.add_argument("--disable-notifications")
    firefox_options.add_argument("--headless") 

    # Crie o driver do Firefox com as opções
    driver = webdriver.Firefox(options=firefox_options)

    return driver


def extrair_info(url_produto, preco_estipulado):
    loja = None
    driver = configurar_webdriver()  # Configure o driver aqui
    try:
        print(f"Extraindo informações de: {url_produto}") 
        driver.get(url_produto)
        
        loja_selectors = {
            "kabum.com.br": {
                "nome_produto": ".sc-89bddf0f-6.dVrDvy",
                "preco": ".sc-5492faee-2.hAMMrD.finalPrice"
            },
            "pichau.com.br": {
                "nome_produto": ".MuiTypography-root.jss39.MuiTypography-h6",
                "preco": ".jss88"
            },
            "terabyteshop.com.br": {
                "nome_produto": "tit-prod",
                "preco": "val-prod valVista"
            },
            # Adicione mais seletores para outras lojas
        }

        for loja_url, selectors in loja_selectors.items():
            if loja_url in url_produto:
                print(f"Loja encontrada: {loja_url}")  # Adicione este print
                loja = loja_url
                nome_produto = driver.find_element(By.CSS_SELECTOR, selectors["nome_produto"]).text.strip()
                preco_text = driver.find_element(By.CSS_SELECTOR, selectors["preco"]).text.strip().replace('R$', '').replace('.', '').replace(',', '.')
                preco_atual = float(preco_text)
                break
        
        
        if loja is None:
            raise ValueError("Loja não suportada ou URL inválida")
        
        return {
            "loja": loja,
            "nome": nome_produto,
            "preco-ant": None,
            "preco": preco_atual,
            "link": url_produto
        }
    except Exception as e:
        print(f"Erro ao extrair informações da URL {url_produto}: {e}")
        return {
            "loja": None,
            "nome": None,
            "preco-ant": None,
            "preco": None,
            "link": url_produto
        }
    finally:
        driver.quit()

if __name__ == '__main__':
    processed_urls = set()  # Conjunto para armazenar os URLs processados

    with Pool() as pool:
        for url_list in [urls_pichau, urls_amazon, urls_terabyte, urls_kabum]:
            for url_produto, preco_estipulado in url_list:
                if url_produto not in processed_urls:  # Verifica se o URL já foi processado
                    results.append(pool.apply_async(extrair_info, args=(url_produto, preco_estipulado)))
                    processed_urls.add(url_produto)  # Adiciona o URL ao conjunto de URLs processados

    pool.close()
    pool.join()


store_functions = {
    "kabum.com.br": extrair_info,
    "pichau.com.br": extrair_info,
    "terabyteshop.com.br": extrair_info,
    "amazon.com.br": extrair_info,
}

for loja, urls_loja in {
    "kabum.com.br": urls_kabum,
    "pichau.com.br": urls_pichau,
    "terabyteshop.com.br": urls_terabyte,
    "amazon.com.br": urls_amazon,
}.items():
    for url_produto, preco_estipulado in urls_loja:
        print(f"Analyzing URL: {url_produto}")

        store_name = None
        for key in store_functions.keys():
            if key in url_produto:
                store_name = key
                break
        if store_name is not None:
            extraction_func = store_functions[store_name]
            
        informacoes = extraction_func(url_produto, preco_estipulado)
           
        if informacoes["preco"] is not None and informacoes["preco"] < preco_estipulado:
            push = pb.push_note(
                "Produto em Promoção!",
                f"{informacoes['nome']} está abaixo de {preco_estipulado}.\nLink: {informacoes['link']}"
            )
        else:
            print(f"Preço atual ({informacoes['preco']}) não está abaixo do preço estipulado ({preco_estipulado}). Não enviando notificação.")
