import subprocess
import sys
import os

# ==========================================
# 0. INSTALAÇÃO AUTOMÁTICA DE BIBLIOTECAS
# ==========================================
def instalar_bibliotecas():
    libs = ['selenium', 'fpdf']
    for lib in libs:
        try:
            __import__(lib)
        except ImportError:
            print(f"Instalando {lib}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

instalar_bibliotecas()

import time
import sqlite3
import smtplib
from email.message import EmailMessage
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException
from fpdf import FPDF

# ==========================================
# 1. BASE DE DADOS
# ==========================================
def inicializar_banco():
    conn = sqlite3.connect('estoque_fandi.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS veiculos (
            placa TEXT PRIMARY KEY,
            filtro_origem TEXT,
            dt_entrada TEXT,
            dt_alteracao TEXT,
            situacao TEXT,
            dias_parado INTEGER,
            ultima_atualizacao TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS motivos_parada (
            placa TEXT PRIMARY KEY,
            motivo TEXT,
            data_registro TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ==========================================
# 2. PROCESSO PRINCIPAL
# ==========================================
def rodar_robo():
    inicializar_banco()
    driver = webdriver.Chrome()
    driver.maximize_window()
    seu_usuario = "JOAO.SERAFIM@VIGORITO"
    sua_senha = "Joao@0407"
    url_inicial = "https://vigorito.fandi.com.br/Modulos/Vendas/Operacao/MonitoracaoForm.aspx?m=B1EEC33C726A60554BC78518D5F9B32C&Cna_Codigo=16"
    
    try:
        driver.get(url_inicial)
        driver.execute_script("window.clicado = false; window.addEventListener('click', () => { window.clicado = true; }, {once: true});")
        while True:
            if driver.execute_script("return window.clicado;"): break
            time.sleep(0.4)
        time.sleep(7)
        
        # --- ETAPA 1: PREENCHER USUÁRIO E CLICAR EM PRÓXIMO ---
        try:
            wait = WebDriverWait(driver, 15)
            campo_user = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div/div/div/div[2]/div[1]/div[4]/form/div/div[1]/div/div/div[1]/div/div[3]/input')))
            campo_user.send_keys(seu_usuario)
            driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div/div/div[2]/div[1]/div[4]/form/div/div[2]/button').click()
            time.sleep(4)
        except Exception as e:
            print("Erro na etapa 1: ", e)

        # --- ETAPA 2: PREENCHER SENHA E CLICAR EM ENTRAR ---
        try:
            # Aguarda e preenche a senha com o seu XPath específico
            campo_senha = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div/div/div/div[2]/div[1]/div[4]/form/div/div[2]/div/div/div[1]/div/div[3]/input')))
            campo_senha.send_keys(sua_senha)
            # Clica no botão de entrar
            driver.find_element(By.XPATH, '//*[@id="app"]/div/div/div/div/div/div[2]/div/div[4]/form/div/div[4]/button/span[3]').click()
        except Exception as e:
            print("Erro na etapa 2: ", e)
        
        time.sleep(6)
        btn_consultar = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Consultar')] | //span[contains(text(), 'Consultar')]")))
        driver.execute_script("arguments[0].click();", btn_consultar)
        time.sleep(2) 
        btn_despachantes = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Despachante')] | //span[contains(text(), 'Despachante')]")))
        driver.execute_script("arguments[0].click();", btn_despachantes)
        time.sleep(4)
        input("\n AGUARDANDO AÇÃO MANUAL... APERTE [ENTER] NO TERMINAL AO ABRIR FILTROS: ")
        try:
            driver.switch_to.default_content() 
            iframe_elemento = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
            driver.switch_to.frame(iframe_elemento)
        except: pass
        time.sleep(1)
        filtros_para_processar = ["SAIDA PENDENTE", "CARTÓRIO", "GRAVAME", "FECHAMENTO", "S DESPACHANTE"]
        for nome_filtro in filtros_para_processar:
            select_element = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ctl00_ctl00_contentBase_content_ddlFiltros"]')))
            driver.execute_script("arguments[0].selectedIndex = Array.from(arguments[0].options).findIndex(o => o.text === arguments[1]); arguments[0].dispatchEvent(new Event('change'));", select_element, nome_filtro)
            time.sleep(8) 
            linhas_dados = driver.find_elements(By.CSS_SELECTOR, "#ctl00_ctl00_contentBase_content_grdMonitoracao tbody tr")
            conn = sqlite3.connect('estoque_fandi.db'); cursor = conn.cursor()
            hoje = datetime.now().strftime("%d/%m/%Y %H:%M"); placas_novas = []
            for i_linha in linhas_dados:
                try:
                    placa = i_linha.find_element(By.XPATH, "./td[11]").text.strip()
                    if not placa or len(placa) < 5: continue
                    placas_novas.append(placa)
                    dt_entrada = i_linha.find_element(By.XPATH, "./td[5]").text.strip()
                    dt_alteracao = i_linha.find_element(By.XPATH, "./td[17]").text.strip()
                    dias_parado = (datetime.now() - datetime.strptime(dt_entrada[:10], "%d/%m/%Y")).days
                    cursor.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?,?,?)", (placa, nome_filtro, dt_entrada, dt_alteracao, i_linha.find_element(By.XPATH, "./td[18]").text.strip(), dias_parado, hoje))
                except: continue
            cursor.execute(f"DELETE FROM veiculos WHERE filtro_origem = ? AND placa NOT IN ({','.join(['?']*len(placas_novas))})", [nome_filtro] + placas_novas)
            conn.commit(); conn.close()
    except Exception as e: print(e)
    finally: driver.quit()

# ==========================================
# 3. RELATÓRIO PDF
# ==========================================
def gerar_relatorio_pdf():
    print("\n Gerando relatório personalizado Vigorito Chevrolet...")
    conn = sqlite3.connect('estoque_fandi.db')
    cursor = conn.cursor()
    cursor.execute("SELECT placa, filtro_origem, dt_entrada, situacao, dias_parado, dt_alteracao FROM veiculos")
    dados = cursor.fetchall()
    cursor.execute("SELECT placa, motivo FROM motivos_parada")
    motivos_db = {row[0].upper(): row[1] for row in cursor.fetchall()}
    conn.close()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # --- PERSONALIZAÇÃO VIGORITO ---
    try:
        pdf.image('logo_vigorito.png', 10, 8, 40)
    except:
        pass 
    
    pdf.set_fill_color(0, 51, 102) # Azul Vigorito
    pdf.rect(0, 0, 210, 30, 'F')
    
    pdf.set_text_color(255, 255, 255) # Texto Branco no cabeçalho
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"RELATORIO GERENCIAL - VIGORITO CHEVROLET", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # Identificação do usuário e supervisora
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, f"Funcionario: Joao Vitor Serafim da Silva", ln=True)
    pdf.cell(0, 5, f"Supervisora: Augusta Souza", ln=True)
    pdf.cell(0, 5, f"Processo: Saida", ln=True)
    pdf.ln(5)
    # --------------------------------

    # Filtros padrão
    filtros = ["SAIDA PENDENTE", "CARTÓRIO", "GRAVAME", "FECHAMENTO"]
    for f in filtros:
        dados_filtro = [d for d in dados if d[1] == f]
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"FILTRO: {f} (Qtd: {len(dados_filtro)})", ln=True)
        pdf.set_font("Arial", size=10)
        
        pdf.set_fill_color(0, 51, 102)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(30, 7, "PLACA", 1, 0, 'C', True)
        pdf.cell(20, 7, "DIAS", 1, 0, 'C', True)
        pdf.cell(40, 7, "STATUS", 1, 0, 'C', True)
        pdf.cell(100, 7, "MOTIVO", 1, 1, 'C', True)
        
        pdf.set_text_color(0, 0, 0) 
        
        dados_ordenados = sorted(dados_filtro, key=lambda x: int(x[0][-1]) if x[0][-1].isdigit() else 99)
        
        for d in dados_ordenados:
            placa, dias, situacao = d[0], d[4], d[3]
            status = "OK"
            if dias >= 30: status = "AVERBADA(+30)"
            elif dias >= 15: status = "ATENCAO(+15)"
            motivo = "PEND. OK FINANCEIRO" if f == "FECHAMENTO" else motivos_db.get(placa.upper(), "NENHUM")
            
            pdf.cell(30, 7, f"{placa}", 1)
            pdf.cell(20, 7, f"{dias}", 1)
            pdf.cell(40, 7, f"{status}", 1)
            pdf.cell(100, 7, f"{motivo}", 1, 1)
        pdf.ln(5)

    # --- NOVA FUNÇÃO: PLACAS FINALIZADAS (DT. ALTERAÇÃO = HOJE + S DESPACHANTE) ---
    hoje_str = datetime.now().strftime("%d/%m/%Y")
    # d[1] é filtro_origem, d[5] é dt_alteracao (index 5 no SELECT)
    placas_finalizadas = [d for d in dados if d[1] == "S DESPACHANTE" and d[5].startswith(hoje_str)]
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"PLACAS FINALIZADAS HOJE ({hoje_str}) - (Qtd: {len(placas_finalizadas)})", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.set_fill_color(0, 150, 0) # Verde
    pdf.set_text_color(255, 255, 255)
    pdf.cell(30, 7, "PLACA", 1, 0, 'C', True)
    pdf.cell(160, 7, "DATA DE ALTERAÇÃO", 1, 1, 'C', True)
    pdf.set_text_color(0, 0, 0)
    
    for d in placas_finalizadas:
        pdf.cell(30, 7, f"{d[0]}", 1)
        pdf.cell(160, 7, f"{d[5]}", 1, 1)
    
    pdf.output("relatorio_estoque_organizado.pdf")
    print(" PDF 'relatorio_estoque_organizado.pdf' gerado com sucesso!")

# ==========================================
# 4. ENVIO DE EMAIL
# ==========================================
def enviar_email():
    msg = EmailMessage()
    msg['Subject'] = f"Relatório Diário de Estoque Fandi - {datetime.now().strftime('%d/%m/%Y')}"
    msg['From'] = "joovitorserafim0@gmail.com"
    msg['To'] = "augusta.souza@vigorito.com.br"
    msg.set_content("Segue em anexo o relatório diário.")
    with open("relatorio_estoque_organizado.pdf", "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="relatorio.pdf")
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login("joovitorserafim0@gmail.com", "quywhbjkwbyrdeds")
        smtp.send_message(msg)
    print("Email enviado com sucesso!")

if __name__ == "__main__":
    rodar_robo()
    gerar_relatorio_pdf()
    if input("\n Enviar relatório por e-mail para augusta.souza@vigorito.com.br? (s/n): ").lower() == 's':
        enviar_email()