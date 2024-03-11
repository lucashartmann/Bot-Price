import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from pushbullet import Pushbullet
import sys

sys.path.append(r'\Links')

from Links_Pichau import obter_urls_pichau

pb = Pushbullet('')

def configurar_webdriver():
    # Crie as opções do Firefox primeiro
    firefox_options = FirefoxOptions()
    firefox_options.add_argument("--disable-notifications")
    firefox_options.add_argument("--headless") 

    # Crie o driver do Firefox com as opções
    driver = webdriver.Firefox(options=firefox_options)

    return driver

urls_dos_produtos = obter_urls_pichau()

def extrair_informacoes_pichau(url_produto, preco_estipulado):
    print('iniciando extração')
    driver = configurar_webdriver()
    try:
        driver.get(url_produto)
        nome_produto_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'MuiTypography-root.jss39.MuiTypography-h6'))
        )
        nome_produto = nome_produto_element.text.strip()

        preco_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'jss88'))
        )
        preco_text = preco_element.text.strip().replace('R$', '').replace('\xa0', '').replace('.', '').replace(',', '.')
        preco_atual = float(preco_text)

    except Exception as e:
        print(f"Erro ao extrair informações da Pichau: {e}")
        nome_produto = None
        preco_atual = None

    finally:
        if preco_atual is not None and preco_atual <= preco_estipulado:
            pb.push_note("Produto em Promoção!",
                         f"{nome_produto} está abaixo de {preco_estipulado}.\nLink: {url_produto}")
            print(f"Realizando a compra na Pichau...")
        else:
            print("Produto não está abaixo do preço estipulado")
            driver.quit()

    return {"loja": "Pichau", "nome": nome_produto, "preco-ant": None, "preco": preco_atual, "link": url_produto}

def main():
    while True:
        for url, preco_estipulado in urls_dos_produtos:
            informacoes = extrair_informacoes_pichau(url, preco_estipulado)

        # Aguarda 1 segundo antes da próxima iteração
        time.sleep(1)

if __name__ == "__main__":
    main()
