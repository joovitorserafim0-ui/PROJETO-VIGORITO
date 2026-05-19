import time
import sqlite3
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoAlertPresentException

# ==========================================
# 1.  BASE DE DADOS
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
# 2. PROCESSO PRINCIPAL 
# ==========================================
def rodar_robo():
    inicializar_banco()
    
    # abre o navegador e maximiza a janela
    driver = webdriver.Chrome()
    driver.maximize_window()
    
    # Credenciais e URL
    seu_usuario = "USUARIO"
    sua_senha = "SENHA"
    url_inicial = "https://vigorito.fandi.com.br/Modulos/Vendas/Operacao/MonitoracaoForm.aspx?m=B1EEC33C726A60554BC78518D5F9B32C&Cna_Codigo=16"
    
    try:
        # 1. Acessa o link de erro/bloqueio inicial do Fandi
        print("Acessando o link do sistema Fandi Vigorito...")
        driver.get(url_inicial)
        
        # 2. AGUARDA CLICAR NO BOTÃO VOLTAR PARA HOME
        print("\n AGUARDANDO VOCÊ: Clique no botão 'Voltar para a Home' na tela...")
        
        driver.execute_script("window.clicado = false; window.addEventListener('click', () => { window.clicado = true; }, {once: true});")
        
        while True:
            foi_clicado = driver.execute_script("return window.clicado;")
            if foi_clicado:
                print(" Primeiro clique detectado!")
                break
            time.sleep(0.4)
            
        # 3. CONTAGEM 7 SEGUNDOS
        print("⏱ Iniciando contagem de 7 segundos para a página de login carregar...")
        for i in range(7, 0, -1):
            print(f"{i} segundos restantes...")
            time.sleep(1)
            
        # 4. PREENCHIMENTO AUTOMÁTICO DAS CREDENCIAIS E LOGIN
        print("\ Preenchendo usuário e senha automaticamente...")
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="v-16"]'))).send_keys(seu_usuario)
            driver.find_element(By.XPATH, '//*[@id="v-17"]').send_keys(sua_senha)
        except Exception:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            if len(inputs) >= 2:
                inputs[0].send_keys(seu_usuario)
                inputs[1].send_keys(sua_senha)
                
        print("Clicando no botão 'Entrar'...")
        driver.find_element(By.XPATH, '//*[@id="app"]/div/div/div/div/div/div[2]/div/div[4]/form/div/div[4]/button/span[3]').click()
        
        # Espera de 6 segundos após o login 
        print("\n⏱ Login efetuado. Aguardando 6 segundos para carregar o painel...")
        for i in range(6, 0, -1):
            print(f"{i} segundos restantes...")
            time.sleep(1)
        
        # 5. NAVEGAÇÃO AUTOMÁTICA ATÉ A TELA INTERNA 
        print(" Clicando automaticamente no botão 'Consultar'...")
        btn_consultar = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Consultar')] | //span[contains(text(), 'Consultar')]"))
        )
        driver.execute_script("arguments[0].click();", btn_consultar)
        
        time.sleep(2) # Pequena pausa para abrir o submenu
        
        print(" Clicando automaticamente na opção 'Despachante'...")
        btn_despachantes = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Despachante')] | //span[contains(text(), 'Despachante')]"))
        )
        driver.execute_script("arguments[0].click();", btn_despachantes)
        
        # Espera para a página carregar por completo o painel de filtros
        time.sleep(4)
        
        # ==========================================
        #  INTERVENÇÃO MANUAL 
        # ==========================================
        print("\n===  AGUARDANDO SUA AÇÃO MANUAL ===")
        print("A navegação foi feita! Agora, apenas CLIQUE na barra cinza 'FILTROS RAPIDOS' para abrir o menu.")
        print("=======================================")
        
        input("\n ASSIM QUE A MINI ABA ESTIVER ABERTA NA TELA, VENHA AQUI NO TERMINAL E APERTE [ENTER]... ")
        
        print("\n Perfeito! Ajustando foco nos componentes internos do iframe...")
        
        #  IFRAME
        try:
            driver.switch_to.default_content() 
            iframe_elemento = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )
            driver.switch_to.frame(iframe_elemento)
            print(" Foco do robô movido com sucesso para dentro do Iframe!")
        except Exception:
            print(" Nenhum iframe encontrado, continuando diretamente...")
        
        time.sleep(1)
        
        # 6. FILTROS 
        filtros_para_processar = ["SAIDA PENDENTE", "CARTÓRIO", "GRAVAME"]
        
        for nome_filtro in filtros_para_processar:
            print(f"\n Processando o Filtro: {nome_filtro}")
            
            # Localiza a caixinha de seleção 
            select_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="ctl00_ctl00_contentBase_content_ddlFiltros"]'))
            )
            
            #  Seleciona o filtro pelo texto mesmo se ele estiver invisível/escondido na aba fechada
            script_selecao = """
                var select = arguments[0];
                var textoFiltro = arguments[1];
                for (var i = 0; i < select.options.length; i++) {
                    if (select.options[i].text === textoFiltro) {
                        select.selectedIndex = i;
                        var event = new Event('change', { bubbles: true });
                        select.dispatchEvent(event);
                        break;
                    }
                }
            """
            driver.execute_script(script_selecao, select_element, nome_filtro)
            print(f"-> Filtro '{nome_filtro}' selecionado via Injeção de Comando.")
            time.sleep(1.5) 
            
            #  ANTI POP-UP
            try:
                alert = driver.switch_to.alert
                print(f" Pop-up do Fandi detectado: '{alert.text}'. Clicando em OK automaticamente...")
                alert.accept() 
            except NoAlertPresentException:
                pass
                
            print("⏱ Aguardando 7 segundos para a tabela atualizar com o filtro...")
            time.sleep(7) 
            
            # 7. CAPTURA AUTOMÁTICA DA TABELA DE DADOS
            print("-> Capturando dados do grid de veículos...")
            linhas_dados = driver.find_elements(By.CSS_SELECTOR, "#ctl00_ctl00_contentBase_content_grdMonitoracao tbody tr")
            
            conn = sqlite3.connect('estoque_fandi.db')
            cursor = conn.cursor()
            hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
            
            for i_linha in linhas_dados:
                try:
                    placa = i_linha.find_element(By.XPATH, "./td[11]").text.strip()
                    dt_entrada = i_linha.find_element(By.XPATH, "./td[5]").text.strip()
                    dt_alteracao = i_linha.find_element(By.XPATH, "./td[17]").text.strip()
                    situacao = i_linha.find_element(By.XPATH, "./td[18]").text.strip()
                    
                    if not placa or len(placa) < 5: 
                        continue
                    
                    # Trata a data de entrada para calcular os dias parado
                    data_base_str = dt_entrada[:10]
                    data_base = datetime.strptime(data_base_str, "%d/%m/%Y")
                    dias_parado = (datetime.now() - data_base).days
                    
                    # Salva ou Atualiza na base SQLite
                    cursor.execute('''
                        INSERT OR REPLACE INTO veiculos (placa, filtro_origem, dt_entrada, dt_alteracao, situacao, dias_parado, ultima_atualizacao)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (placa, nome_filtro, dt_entrada, dt_alteracao, situacao, dias_parado, hoje))
                    
                    # Exibição dos alertas no terminal
                    if dias_parado > 30:
                        print(f" AVERBADO (+30 DIAS) -> Placa: {placa} | Parado há: {dias_parado} dias | Filtro: {nome_filtro} | Situação: {situacao}")
                    elif dias_parado > 15:
                        print(f" ATENÇÃO (+15 DIAS) -> Placa: {placa} | Parado há: {dias_parado} dias | Filtro: {nome_filtro}")
                        
                except Exception:
                    continue
            
            conn.commit()
            conn.close()
            print(f" Filtro '{nome_filtro}' processado e atualizado.")
            
        print("\n Sucesso Absoluto! Sua base de dados foi montada e alimentada para os 3 filtros.")

    except Exception as erro_geral:
        import traceback
        print(f"\n Ocorreu um erro inesperado no fluxo do robô:")
        print(traceback.format_exc())
        
    finally:
        pass
# --- ADIÇÃO PARA RELATÓRIO PDF ---
try:
    import matplotlib.pyplot as plt
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
    import matplotlib.pyplot as plt

def gerar_relatorio_pdf():
    print("\n Gerando relatório PDF inteligente...")
    conn = sqlite3.connect('estoque_fandi.db')
    cursor = conn.cursor()
    # Pega todos os dados ordenados por filtro
    cursor.execute("SELECT placa, filtro_origem, dt_entrada, situacao, dias_parado FROM veiculos ORDER BY filtro_origem, dias_parado DESC")
    dados = cursor.fetchall()
    conn.close()

    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    ax.axis('off')
    
    hoje_str = datetime.now().strftime("%d/%m/%Y")
    texto = f"RELATÓRIO GERENCIAL - ESTOQUE FANDI\nData: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    texto += "="*75 + "\n\n"

    # Agrupa e processa por filtros
    filtros = ["SAIDA PENDENTE", "CARTÓRIO", "GRAVAME"]
    
    for f in filtros:
        texto += f"FILTRO: {f.upper()}\n"
        texto += f"{'PLACA':<12} | {'DIAS':<6} | {'STATUS ALERTA'}\n"
        texto += "-"*50 + "\n"
        
        encontrou = False
        for d in dados:
            if d[1] == f:
                encontrou = True
                placa, dias, situacao = d[0], d[4], d[3]
                
                # Lógica de Alertas
                status = "OK"
                if dias >= 30:
                    status = " AVERBADA (+30 DIAS)"
                elif dias >= 15:
                    status = " ATENÇÃO (+15 DIAS)"
                
                # Verifica se entrou hoje
                if d[2][:10] == hoje_str:
                    status = " ADICIONADO HOJE"
                
                texto += f"{placa:<12} | {dias:<6} | {status}\n"
        
        if not encontrou:
            texto += "Nenhum veículo encontrado.\n"
        texto += "\n"

    ax.text(0.05, 0.95, texto, fontsize=9, fontfamily='monospace', va='top')
    plt.savefig("relatorio_estoque_organizado.pdf")
    plt.close()
    print(" PDF 'relatorio_estoque_organizado.pdf' gerado com as separações!")
# ----------------------------------

if __name__ == "__main__":
    pass