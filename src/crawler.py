import sqlite3
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp

def inserir_fila_banco(hash_url, empresa, url_completa, status):
    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        conexao = sqlite3.connect('./src/db/controle_fila.db')
        cursor = conexao.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO fila_reclamacoes 
            (hash_url, empresa, url_completa, status_reclamacao, precisa_baixar, data_ultima_verificacao)
            VALUES (?, ?, ?, ?, 1, ?)
        ''', (hash_url, empresa, url_completa, status, data_atual))
        
        
        if cursor.rowcount == 1: #1 = link novo, 0 = link velho a ser ignorado
            print(f"reclamação inserida na fila: {hash_url}, status: {status}")
            
        conexao.commit()
        
    except Exception as e:
        print(f"erro url: {hash_url}: {e}")
        
    finally:
        conexao.close()

def extrair_dados_da_pagina(pagina, empresa):
    print(f"Analisando HTML para a empresa {empresa}...")
    try:
        seletor_card_reclamacao = f'a[href^="/{empresa}/"]'
        pagina.wait_for_selector(seletor_card_reclamacao, timeout=10000)
        
        elementos_links = pagina.locator(seletor_card_reclamacao).all()
        
        for elemento in elementos_links:
            href = elemento.get_attribute('href')
            if not href:
                continue
            
            if '_' not in href:
                continue 
                
            url_completa = f"https://www.reclameaqui.com.br{href}"
            
            try:
                hash_url = href.strip('/').split('_', 1)[1]
                
                if len(hash_url) < 10: #filtro de hashs muito curtos
                    print(f"link filtrado: {url_completa}")
                    continue
                    
            except Exception:
                continue
            
            status = "Pendente" 
            texto_elemento = elemento.inner_text().lower()
            if "respondida" in texto_elemento:
                status = "Respondida"
            elif "resolvido" in texto_elemento or "resolvida" in texto_elemento:
                status = "Resolvida"
            elif "não resolvido" in texto_elemento or "não resolvida" in texto_elemento: # isso aqui tem que ser não respondida
                status = "Não Resolvida"
                
            inserir_fila_banco(hash_url, empresa, url_completa, status)
            
    except Exception as e:
        print(f"falha ao extrair a página: {e}")

def aguardar_exec():
    tempo_espera = random.uniform(2.5, 6.0)
    print(f"Jitter ativo: aguardando {tempo_espera:.2f} segundos antes da próxima página...")
    time.sleep(tempo_espera)

def iniciar_crawler(empresa, url_base, total_paginas):
    sb = sb_cdp.Chrome(locale="pt-BR") #navegador camuflado do cloudflare
    endpoint_url = sb.get_endpoint_url()
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(endpoint_url)
            context = browser.contexts[0]
            pagina = context.pages[0]

            for numero_pagina in range(1, total_paginas + 1):
                url_paginada = f"{url_base}?pagina={numero_pagina}"
                print(f"\npágina {numero_pagina}/{total_paginas} acessando: {url_paginada}")
                
                try:
                    pagina.goto(url_paginada)
                    time.sleep(5) 
                    
                    extrair_dados_da_pagina(pagina, empresa)
                except Exception as e:
                    print(f"erro ao carregar a página {numero_pagina}: {e}")
                
                if numero_pagina < total_paginas:
                    aguardar_exec()

            browser.close()
    finally:
        sb.driver.quit()
