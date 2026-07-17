import pdfplumber
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÕES ---
URL = "https://despadoc.despawin.com/login"
USUARIO = "joao.silva@vigorito.com.br"
SENHA = "9KPwiYSe2AyHKIhhBhbE0sFOVibFw5hrJLC1uQHsOcUh"

def extrair_placas_do_filtro_especifico(caminho_pdf):
    placas = []
    regex_placa = r'[A-Z]{3}\d[A-Z0-9]\d{2}'
    
    with pdfplumber.open(caminho_pdf) as pdf:
        texto_completo = ""
        for page in pdf.pages:
            texto_completo += page.extract_text() + "\n"
        
        partes = re.split(r'FILTRO:', texto_completo, flags=re.IGNORECASE)
        
        if len(partes) >= 4:
            bloco_alvo = partes[3] 
            if "GRAVAME" in bloco_alvo.upper():
                placas = re.findall(regex_placa, bloco_alvo)
        return list(dict.fromkeys(placas))

def executar():
    print("Iniciando extração da 3ª planilha (FILTRO: GRAVAME)...")
    placas = extrair_placas_do_filtro_especifico("relatorio_estoque_organizado.pdf")
    
    if not placas:
        print("Nenhuma placa encontrada na planilha alvo.")
        return
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    wait = WebDriverWait(driver, 20)
    
    try:
        driver.get(URL)
        
        # LOGIN
        wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div/div[1]/div[1]/div[2]/form/div[1]/div[2]/div[2]/input'))).send_keys(USUARIO)
        driver.find_element(By.XPATH, '/html/body/div/div[1]/div[1]/div[2]/form/div[2]/div[2]/input').send_keys(SENHA)
        driver.find_element(By.XPATH, '/html/body/div/div[1]/div[1]/div[2]/button').click()
        
        input("### LOGIN REALIZADO. Feche os pop-ups manualmente e pressione ENTER no terminal... ###")
        
        # MENU LATERAL
        elemento_pai = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/nav/div[1]/div[1]')))
        driver.execute_script("arguments[0].click();", elemento_pai)
        time.sleep(1.5)
        
        # NAVEGAÇÃO
        wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[1]/nav/div/ul/div[2]/div[1]'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[1]/nav/div/ul/div[2]/div[2]/div[1]/p'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div[1]/div[1]/div[2]/div[2]/a/div/button'))).click()
        
        # PREENCHIMENTO
        campo_placa = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[9]/div/div/div/div/div[2]/div/div[1]/div/div/div/div[1]/div/div[2]/div/input')))
        botao_mais = driver.find_element(By.XPATH, '/html/body/div[9]/div/div/div/div/div[2]/div/div[1]/div/div/div/div[2]/button')
        
        for placa in placas:
            campo_placa.click()
            campo_placa.send_keys(placa)
            driver.execute_script("arguments[0].click();", botao_mais)
            time.sleep(0.8)
            
        # CONSULTAR LOTE
        driver.find_element(By.XPATH, '/html/body/div[9]/div/div/div/div/div[2]/div/div[2]/button/p').click()
        time.sleep(5) 
        
        # --- FUNÇÃO ATUALIZADA: ITERAR SOBRE PROCESSOS ---
        for i in range(len(placas)):
            # XPath que busca o botão azul na tabela de resultados
            xpath_botao = f"(//button[contains(@class, 'mat-focus-indicator') or contains(@class, 'icon')])[{i+1}]"
            botao_abrir = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_botao)))
            
            # Clicar usando JavaScript para evitar erro de elemento sobreposto
            driver.execute_script("arguments[0].click();", botao_abrir)
            time.sleep(3)
            
            # Rolar para ler campos
            driver.execute_script("window.scrollTo(0, 800);")
            time.sleep(1)
            
            # Leitura dos textos (XPaths para Restrição Financeira)
            try:
                gravame_info = driver.find_element(By.XPATH, "//div[contains(text(), 'GRAVAMES')]//following::div[contains(text(), 'Restrição Financeira')][1]").text
                intencao_info = driver.find_element(By.XPATH, "//div[contains(text(), 'INTENÇÃO DE GRAVAME')]//following::div[contains(text(), 'Restrição Financeira')][1]").text
                
                if "Nada Consta" in gravame_info or "-------" in gravame_info:
                    print(f"Placa {placas[i]}: FALTA INCLUIR GRAVAME")
                else:
                    print(f"Placa {placas[i]}: PODE DAR ANDAMENTO")
            except:
                print(f"Erro ao ler campos da placa {placas[i]}")
            
            # Voltar
            driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[1]/div[1]/div[1]/div[1]/div[1]/button/p').click()
            time.sleep(2)

        print("Automação finalizada com sucesso!")
        
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        input("Pressione ENTER para fechar o navegador...")
        driver.quit()

if __name__ == "__main__":
    executar()