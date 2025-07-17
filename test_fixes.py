#!/usr/bin/env python3
"""
Script para testar as correções do proxy
"""

import requests
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor

def test_concurrent_requests():
    """Testa requisições concorrentes para verificar se o erro de headers foi corrigido"""
    print("🔄 Testando requisições concorrentes...")
    
    def make_request(i):
        try:
            response = requests.post(
                "http://localhost:11434/v1/chat/completions",
                json={
                    "model": "gemini-2.5-pro",
                    "messages": [{"role": "user", "content": f"Diga apenas: Teste {i}"}],
                    "stream": False,
                    "max_tokens": 50
                },
                timeout=10
            )
            return f"Request {i}: Status {response.status_code}"
        except Exception as e:
            return f"Request {i}: Error {e}"
    
    # Fazer 5 requisições simultâneas
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request, i) for i in range(1, 6)]
        results = [future.result() for future in futures]
    
    for result in results:
        print(f"  {result}")
    
    return all("Status 200" in result for result in results)

def test_content_field():
    """Testa se o campo content está presente na resposta não-streaming"""
    print("\n📝 Testando campo content na resposta...")
    
    try:
        response = requests.post(
            "http://localhost:11434/v1/chat/completions",
            json={
                "model": "gemini-2.5-pro",
                "messages": [{"role": "user", "content": "Responda apenas: Olá mundo"}],
                "stream": False,
                "max_tokens": 50
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Resposta completa: {json.dumps(data, indent=2)}")
            
            # Verificar se tem content
            if 'choices' in data and len(data['choices']) > 0:
                message = data['choices'][0].get('message', {})
                content = message.get('content')
                
                if content is not None:
                    print(f"  ✅ Campo content presente: '{content}'")
                    return True
                else:
                    print(f"  ❌ Campo content ausente na message: {message}")
                    return False
            else:
                print(f"  ❌ Estrutura de choices inválida")
                return False
        else:
            print(f"  ❌ Status code: {response.status_code}")
            print(f"  Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Exceção: {e}")
        return False

def test_streaming_stability():
    """Testa estabilidade do streaming"""
    print("\n🌊 Testando estabilidade do streaming...")
    
    try:
        response = requests.post(
            "http://localhost:11434/v1/chat/completions",
            json={
                "model": "gemini-2.5-pro",
                "messages": [{"role": "user", "content": "Conte uma história muito curta"}],
                "stream": True,
                "max_tokens": 100
            },
            stream=True,
            timeout=20
        )
        
        if response.status_code == 200:
            chunks = []
            content_parts = []
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    chunks.append(line_str)
                    
                    if line_str.startswith('data: ') and not line_str.endswith('[DONE]'):
                        data_str = line_str[6:]
                        try:
                            chunk_data = json.loads(data_str)
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    content_parts.append(content)
                        except:
                            pass
            
            full_content = ''.join(content_parts)
            print(f"  Chunks recebidos: {len(chunks)}")
            print(f"  Conteúdo completo: '{full_content}'")
            
            return len(chunks) > 0 and len(full_content) > 0
        else:
            print(f"  ❌ Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Exceção: {e}")
        return False

def test_error_handling():
    """Testa tratamento de erros"""
    print("\n🚨 Testando tratamento de erros...")
    
    # Teste com JSON malformado
    try:
        response = requests.post(
            "http://localhost:11434/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            data="{ invalid json",
            timeout=5
        )
        
        if response.status_code == 400:
            print("  ✅ JSON malformado rejeitado corretamente")
            return True
        else:
            print(f"  ❌ Status inesperado para JSON malformado: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Exceção: {e}")
        return False

def main():
    print("🔧 TESTANDO CORREÇÕES DO PROXY")
    print("=" * 50)
    
    # Verificar se servidor está rodando
    try:
        response = requests.get("http://localhost:11434/v1/models", timeout=5)
        if response.status_code != 200:
            print("❌ Servidor não está respondendo")
            return
    except:
        print("❌ Servidor não está acessível")
        print("💡 Execute: npm start")
        return
    
    tests = [
        ("Requisições Concorrentes", test_concurrent_requests),
        ("Campo Content", test_content_field),
        ("Estabilidade Streaming", test_streaming_stability),
        ("Tratamento de Erros", test_error_handling)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Teste {test_name} falhou: {e}")
            results[test_name] = False
        
        time.sleep(1)  # Pausa entre testes
    
    # Resumo
    print(f"\n{'='*50}")
    print("📊 RESUMO DOS TESTES DE CORREÇÃO")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:25} | {status}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todas as correções funcionaram!")
    else:
        print("⚠️  Algumas correções ainda precisam de ajustes")

if __name__ == "__main__":
    main()