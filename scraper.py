import time
import random
import os
import gzip
from datetime import datetime
from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp 

def aguardar_exec():
    tempo_espera = random.uniform(2.5, 6.0)
    time.sleep(tempo_espera)

def salvar_camada_bronze(html, empresa, hash_url):
    hoje = datetime.now()
    caminho_pasta = os.path.join("bronze_dados", hoje.strftime("%Y"), hoje.strftime("%m"), hoje.strftime("%d"))
    os.makedirs(caminho_pasta, exist_ok=True)
    nome_arquivo = f"{empresa}_{hash_url}.html.gz"
    caminho_completo = os.path.join(caminho_pasta, nome_arquivo)
    
    with gzip.open(caminho_completo, 'wt', encoding='utf-8') as f:
        f.write(html)
    print(f"arquivo salvo: {caminho_completo}")

def processar_reclamacoes(lista_urls):
    sb = sb_cdp.Chrome(locale="pt-BR")
    endpoint_url = sb.get_endpoint_url()
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(endpoint_url)
            context = browser.contexts[0]
            pagina = context.pages[0]

            for url in lista_urls:
                url = url.strip()
                if not url: continue
                
                try:
                    print(f"\nurl acessada: {url}")
                    pagina.goto(url)
                    
                    try: # detector de ad
                        seletor_anuncio = 'button[data-ra-ads-interstitial-close]'
                        pagina.wait_for_selector(seletor_anuncio, timeout=3000)
                        pagina.click(seletor_anuncio)
                        print("anuncio fechado")
                        time.sleep(1)
                    except:
                        pass
                    
                    pagina.wait_for_selector('p[data-testid="complaint-description"]', timeout=15000)
                    
                    html_bruto = pagina.content()
                    
                    partes_url = url.strip('/').split('/')
                    empresa = partes_url[3] if len(partes_url) > 3 else "desconhecida"
                    hash_url = url.split('_')[-1].strip('/') if '_' in url else str(int(time.time()))
                    
                    salvar_camada_bronze(html_bruto, empresa, hash_url)
                    
                except Exception as e:
                    print(f"falha ao processar {url}. erro: {e}")
                
                aguardar_exec()

            browser.close()
            
    finally:
        sb.driver.quit()

if __name__ == "__main__":
    if os.path.exists("urls.txt"):
        with open("urls.txt", "r", encoding="utf-8") as arquivo:
            urls_alvo = arquivo.readlines()
        
        if urls_alvo:
            processar_reclamacoes(urls_alvo)
        else:
            print("arquivo de urls vazio")
    else:
        print("arquivo de url inexistente")