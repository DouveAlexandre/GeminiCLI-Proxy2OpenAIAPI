#!/usr/bin/env python3
"""
Script de teste rápido para debugging específico do proxy
"""

import requests
import json

def test_simple_request():
    """Teste básico para ver a resposta crua"""
    url = "http://localhost:11434/v1/chat/completions"
    
    payload = {
        "model": "gemini-2.5-pro",
        "messages": [
            {"role": "user", "content": "Diga apenas 'Olá mundo'"}
        ],
        "max_tokens": 50,
        "temperature": 0.1,
        "stream": False
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test"
    }
    
    print("Enviando requisição...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\nJSON Response: {json.dumps(data, indent=2)}")
                
                # Verificar se tem o campo content
                if 'choices' in data and len(data['choices']) > 0:
                    message = data['choices'][0].get('message', {})
                    content = message.get('content')
                    print(f"\nConteúdo extraído: '{content}'")
                else:
                    print("\n❌ Estrutura de resposta inesperada")
                    
            except json.JSONDecodeError as e:
                print(f"\n❌ Erro ao decodificar JSON: {e}")
        else:
            print(f"\n❌ Erro HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Exceção: {e}")

def test_streaming_request():
    """Teste de streaming para ver chunks crus"""
    url = "http://localhost:11434/v1/chat/completions"
    
    payload = {
        "model": "gemini-2.5-pro",
        "messages": [
            {"role": "user", "content": "Conte até 5"}
        ],
        "max_tokens": 100,
        "temperature": 0.1,
        "stream": True
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test"
    }
    
    print("\n" + "="*50)
    print("TESTE DE STREAMING")
    print("="*50)
    
    try:
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("\nChunks recebidos:")
            chunk_count = 0
            
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    line_str = line.decode('utf-8')
                    print(f"Chunk {chunk_count}: {line_str}")
                    
                    if line_str.startswith('data: ') and not line_str.endswith('[DONE]'):
                        data_str = line_str[6:]
                        try:
                            chunk_data = json.loads(data_str)
                            print(f"  -> Parsed: {json.dumps(chunk_data, indent=4)}")
                        except:
                            print(f"  -> Erro ao parsear JSON")
                    
                    if chunk_count > 20:  # Limite para evitar spam
                        print("... (limitando output)")
                        break
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exceção: {e}")

if __name__ == "__main__":
    print("🔍 TESTE RÁPIDO DO PROXY")
    print("="*50)
    
    # Teste não-streaming
    test_simple_request()
    
    # Teste streaming
    test_streaming_request()
    
    print("\n✅ Testes concluídos")