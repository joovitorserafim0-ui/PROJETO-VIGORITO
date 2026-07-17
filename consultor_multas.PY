import subprocess
import sys
import os
import time
import sqlite3
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from fpdf import FPDF
import PyPDF2

# ==========================================
# 0. INSTALAÇÃO AUTOMÁTICA DE BIBLIOTECAS
# ==========================================
def instalar_bibliotecas():
    libs = ['selenium', 'fpdf', 'PyPDF2']
    for lib in libs:
        try:
            __import__(lib)
        except ImportError:
            print(f"Instalando {lib}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

instalar_bibliotecas()

# ==========================================
# 1. FUNÇÃO DE LEITURA DO JOÃO (NOVA)
# ==========================================
def ler_placas_multa_joao():
    placas_com_multa = set()
    caminho_pdf = "relatorio_estoque_organizado.pdf"
    
    if not os.path.exists(caminho_pdf):
        print(f"AVISO: Arquivo {caminho_pdf} não encontrado. Nenhuma multa será filtrada.")
        return placas_com_multa

    try:
        reader = PyPDF2.PdfReader(caminho_pdf)
        regex_placa = r'[A-Z]{3}[- ]?[0-9][A-Z0-9][0-9]{2}'
        
        for pagina in reader.pages:
            texto = pagina.extract_text()
            if texto:
                for linha in texto.split('\n'):
                    if 'multa' in linha.lower():
                        match = re.search(regex_placa, linha)
                        if match:
                            placa_limpa = match.group().replace("-", "").replace(" ", "").upper()
                            placas_com_multa.add(placa_limpa)
        print(f"Sucesso: {len(placas_com_multa)} placas com multa identificadas no PDF do João.")
    except Exception as e:
        print(f"Erro ao ler PDF do João: {e}")
    
    return placas_com_multa

# ==========================================
# 2. BASE DE DADOS
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
    conn.commit()
    conn.close()

# ==========================================
# 3. PROCESSO PRINCIPAL (ROBÔ)
# ==========================================
def rodar_robo(placas_multadas):
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
        
        try:
            wait = WebDriverWait(driver, 15)
            campo_user = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div/div/div/div[2]/div[1]/div[4]/form/div/div[1]/div/div/div[1]/div/div[3]/input')))
            campo_user.send_keys(seu_usuario)
            driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div/div/div[2]/div[1]/div[4]/form/div/div[2]/button').click()
            time.sleep(4)
            campo_senha = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div/div/div/div[2]/div[1]/div[4]/form/div/div[2]/div/div/div[1]/div/div[3]/input')))
            campo_senha.send_keys(sua_senha)
            driver.find_element(By.XPATH, '//*[@id="app"]/div/div/div/div/div/div[2]/div/div[4]/form/div/div[4]/button/span[3]').click()
        except Exception as e:
            print("Erro no login: ", e)
        
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
        filtros_para_processar = ["CONTAS A PAGAR", "CONTAS A RECEBER"]
        
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
            
            conn.commit(); conn.close()

        # --- NOVA FUNÇÃO: BUSCA PLACAS FALTANTES ---
        conn = sqlite3.connect('estoque_fandi.db')
        cursor = conn.cursor()
        cursor.execute("SELECT placa FROM veiculos")
        isabella_db = {r[0].replace("-", "").replace(" ", "").upper() for r in cursor.fetchall()}
        conn.close()

        pendentes = [p for p in placas_multadas if p not in isabella_db]
        
        for placa in pendentes:
            try:
                campo_placa = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ctl00_ctl00_contentBase_content_tbxPlaca"]')))
                campo_placa.clear()
                campo_placa.send_keys(placa)
                
                select = driver.find_element(By.XPATH, '/html/body/form/div[3]/div[2]/table/tbody/tr/td/table/tbody/tr/td/div/div/div[1]/div[2]/span/div/div/div/div[1]/div/div/div/div/table[4]/tbody/tr[2]/td[4]/select')
                select.send_keys("Saída")
                
                campo_placa.send_keys(Keys.ENTER)
                campo_placa.send_keys(Keys.ENTER)
                time.sleep(3)
                
                dt_str = driver.find_element(By.XPATH, "//*[@id='xpath_a_ajustar']").text
                dias = (datetime.now() - datetime.strptime(dt_str, "%d/%m/%Y")).days
                
                conn = sqlite3.connect('estoque_fandi.db')
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO veiculos VALUES (?,?,?,?,?,?,?)", (placa, "PENDENTE", dt_str, "", "SAÍDA", dias, datetime.now().strftime("%d/%m/%Y")))
                conn.commit(); conn.close()
            except: continue

    except Exception as e: print(e)
    finally: driver.quit()

# ==========================================
# 4. RELATÓRIO PDF
# ==========================================
def gerar_relatorio_pdf(placas_multadas):
    print("\n Gerando relatório PROCESSOS ISABELA...")
    conn = sqlite3.connect('estoque_fandi.db')
    cursor = conn.cursor()
    cursor.execute("SELECT placa, filtro_origem, dt_entrada, situacao, dias_parado, dt_alteracao FROM veiculos")
    dados = cursor.fetchall()
    placas_isabella = {d[0].replace("-", "").replace(" ", "").upper() for d in dados}
    conn.close()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    pdf.set_fill_color(0, 51, 102)
    pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"PROCESSOS ISABELA", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, f"Funcionario: Joao Vitor Serafim da Silva", ln=True)
    pdf.ln(5)

    filtros = ["CONTAS A PAGAR", "CONTAS A RECEBER"]
    for f in filtros:
        dados_filtro = [d for d in dados if d[1] == f]
        dados_filtro.sort(key=lambda x: int(x[0][-1]) if x[0][-1].isdigit() else 99)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"FILTRO: {f} (Qtd: {len(dados_filtro)})", ln=True)
        pdf.set_font("Arial", size=10)
        
        pdf.set_fill_color(0, 51, 102)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(50, 7, "PLACA", 1, 0, 'C', True)
        pdf.cell(40, 7, "DIAS", 1, 0, 'C', True)
        pdf.cell(100, 7, "STATUS", 1, 1, 'C', True)
        
        pdf.set_text_color(0, 0, 0) 
        for d in dados_filtro:
            placa, dias = d[0], d[4]
            placa_comparacao = placa.replace("-", "").replace(" ", "").upper()
            
            if placa_comparacao in placas_multadas:
                pdf.set_fill_color(255, 200, 200)
                alerta = "MULTA PROCESSO SAÍDA"
                preencher = True
            elif dias <= 4:
                alerta, preencher = "PROCESSOS EM DIA", False
            elif dias <= 15:
                alerta, preencher = "VERIFICAR PROCESSO", False
            else:
                alerta, preencher = "PROCESSO EM RISCO", False
            
            if not preencher: pdf.set_fill_color(255, 255, 255)
            
            pdf.cell(50, 7, f"{placa}", 1, 0, 'C', preencher)
            pdf.cell(40, 7, f"{dias}", 1, 0, 'C', preencher)
            pdf.cell(100, 7, f"{alerta}", 1, 1, 'C', preencher)
        pdf.ln(5)

    placas_nao_encontradas = [p for p in placas_multadas if p not in placas_isabella]
    if placas_nao_encontradas:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "PLACAS QUE NÃO CONSTAM NOS FILTROS", ln=True)
        pdf.set_fill_color(200, 200, 200)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(95, 7, "PLACA", 1, 0, 'C', True)
        pdf.cell(95, 7, "STATUS", 1, 1, 'C', True)
        pdf.set_font("Arial", size=10)
        for p in placas_nao_encontradas:
            pdf.cell(95, 7, f"{p}", 1, 0, 'C')
            pdf.cell(95, 7, "PLACA NÃO IDENTIFICADO NOS FILTROS", 1, 1, 'C')

    pdf.output("PROCESSOS ISABELLA.pdf")
    print(" PDF 'PROCESSOS ISABELLA.pdf' atualizado com sucesso!")

# ==========================================
# EXECUÇÃO PRINCIPAL
# ==========================================
if __name__ == "__main__":
    try:
        placas = ler_placas_multa_joao()
        rodar_robo(placas)
        gerar_relatorio_pdf(placas)
    except KeyboardInterrupt:
        print("\n[!] Robô interrompido pelo usuário. Finalizando...")
        sys.exit(0)