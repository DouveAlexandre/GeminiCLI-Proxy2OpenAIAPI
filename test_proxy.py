#!/usr/bin/env python3
"""
Script de teste para o proxy Gemini-OpenAI
Testa diferentes cenários para identificar problemas no mapeamento
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional

class ProxyTester:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer qualquer-valor"  # Como configurado no config.json
        }
    
    def test_models_endpoint(self) -> bool:
        """Testa o endpoint /v1/models"""
        print("🔍 Testando endpoint /v1/models...")
        try:
            response = requests.get(f"{self.base_url}/v1/models", headers=self.headers)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Modelos disponíveis: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"❌ Erro: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Exceção: {e}")
            return False
    
    def test_simple_chat(self) -> bool:
        """Testa chat simples sem streaming"""
        print("\n🔍 Testando chat simples (sem streaming)...")
        
        payload = {
            "model": "gemini-2.5-pro",
            "messages": [
                {"role": "user", "content": "Olá! Como você está?"}
            ],
            "max_tokens": 100,
            "temperature": 0.7,
            "stream": False
        }
        
        try:
            print(f"Enviando requisição: {json.dumps(payload, indent=2)}")
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Resposta: {json.dumps(data, indent=2)}")
                
                # Verificar estrutura da resposta
                if self._validate_openai_response(data):
                    print("✅ Resposta válida no formato OpenAI")
                    return True
                else:
                    print("❌ Resposta inválida - estrutura incorreta")
                    return False
            else:
                print(f"❌ Erro: {response.status_code}")
                print(f"Resposta: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exceção: {e}")
            return False
    
    def test_streaming_chat(self) -> bool:
        """Testa chat com streaming"""
        print("\n🔍 Testando chat com streaming...")
        
        payload = {
            "model": "gemini-2.5-pro",
            "messages": [
                {"role": "user", "content": "Conte uma piada curta"}
            ],
            "max_tokens": 150,
            "temperature": 0.8,
            "stream": True
        }
        
        try:
            print(f"Enviando requisição streaming: {json.dumps(payload, indent=2)}")
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=30
            )
            
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("Recebendo chunks de streaming:")
                chunks_received = 0
                full_content = ""
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        print(f"Chunk raw: {line_str}")
                        
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]  # Remove 'data: '
                            
                            if data_str == '[DONE]':
                                print("✅ Stream finalizado com [DONE]")
                                break
                            
                            try:
                                chunk_data = json.loads(data_str)
                                chunks_received += 1
                                
                                # Extrair conteúdo do chunk
                                if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        full_content += content
                                        print(f"Conteúdo do chunk {chunks_received}: '{content}'")
                                
                            except json.JSONDecodeError as e:
                                print(f"❌ Erro ao decodificar chunk JSON: {e}")
                                print(f"Dados problemáticos: {data_str}")
                
                print(f"\n📊 Resumo do streaming:")
                print(f"Chunks recebidos: {chunks_received}")
                print(f"Conteúdo completo: '{full_content}'")
                
                if chunks_received > 0 and full_content:
                    print("✅ Streaming funcionando corretamente")
                    return True
                else:
                    print("❌ Streaming com problemas - poucos chunks ou sem conteúdo")
                    return False
            else:
                print(f"❌ Erro: {response.status_code}")
                print(f"Resposta: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exceção: {e}")
            return False
    
    def test_with_reasoning(self) -> bool:
        """Testa chat com reasoning habilitado"""
        print("\n🔍 Testando chat com reasoning...")
        
        payload = {
            "model": "gemini-2.5-pro",
            "messages": [
                {"role": "user", "content": "Resolva: Se um trem viaja a 80 km/h e precisa percorrer 240 km, quanto tempo levará?"}
            ],
            "max_tokens": 200,
            "temperature": 0.3,
            "include_reasoning": True,
            "stream": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=30
            )
            
            if response.status_code == 200:
                reasoning_found = False
                regular_content = ""
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: ') and not line_str.endswith('[DONE]'):
                            data_str = line_str[6:]
                            try:
                                chunk_data = json.loads(data_str)
                                if 'choices' in chunk_data:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        if content.startswith('<think>'):
                                            reasoning_found = True
                                            print(f"🧠 Reasoning detectado: {content}")
                                        else:
                                            regular_content += content
                            except:
                                pass
                
                print(f"Reasoning encontrado: {reasoning_found}")
                print(f"Conteúdo regular: '{regular_content}'")
                return True
            else:
                print(f"❌ Erro: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exceção: {e}")
            return False
    
    def test_malformed_request(self) -> bool:
        """Testa requisição malformada"""
        print("\n🔍 Testando requisição malformada...")
        
        try:
            # JSON inválido
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                data="{ invalid json",
                timeout=10
            )
            
            print(f"Status para JSON inválido: {response.status_code}")
            
            if response.status_code == 400:
                print("✅ Proxy rejeitou corretamente JSON inválido")
                return True
            else:
                print("❌ Proxy deveria retornar 400 para JSON inválido")
                return False
                
        except Exception as e:
            print(f"❌ Exceção: {e}")
            return False
    
    def _validate_openai_response(self, data: Dict[str, Any]) -> bool:
        """Valida se a resposta está no formato OpenAI correto"""
        required_fields = ['id', 'object', 'created', 'model', 'choices', 'usage']
        
        for field in required_fields:
            if field not in data:
                print(f"❌ Campo obrigatório ausente: {field}")
                return False
        
        if not isinstance(data['choices'], list) or len(data['choices']) == 0:
            print("❌ Campo 'choices' deve ser uma lista não vazia")
            return False
        
        choice = data['choices'][0]
        choice_required = ['index', 'message', 'finish_reason']
        
        for field in choice_required:
            if field not in choice:
                print(f"❌ Campo obrigatório ausente em choice: {field}")
                return False
        
        message = choice['message']
        if 'role' not in message or 'content' not in message:
            print("❌ Campos obrigatórios ausentes em message: role, content")
            return False
        
        return True
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Executa todos os testes"""
        print("🚀 Iniciando testes do proxy Gemini-OpenAI")
        print("=" * 60)
        
        results = {}
        
        # Verificar se o servidor está rodando
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            if response.status_code != 200:
                print("❌ Servidor não está respondendo corretamente")
                return {"server_running": False}
        except:
            print("❌ Servidor não está rodando ou não acessível")
            print("💡 Certifique-se de que o proxy está rodando com: npm start")
            return {"server_running": False}
        
        # Executar testes
        tests = [
            ("models_endpoint", self.test_models_endpoint),
            ("simple_chat", self.test_simple_chat),
            ("streaming_chat", self.test_streaming_chat),
            ("reasoning_chat", self.test_with_reasoning),
            ("malformed_request", self.test_malformed_request)
        ]
        
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ Teste {test_name} falhou com exceção: {e}")
                results[test_name] = False
            
            time.sleep(1)  # Pequena pausa entre testes
        
        # Resumo final
        print(f"\n{'='*60}")
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"{test_name:20} | {status}")
            if result:
                passed += 1
        
        print(f"\nResultado: {passed}/{total} testes passaram")
        
        if passed == total:
            print("🎉 Todos os testes passaram! O proxy está funcionando corretamente.")
        else:
            print("⚠️  Alguns testes falharam. Verifique os logs acima para detalhes.")
        
        return results

def main():
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:11434"
    
    print(f"Testando proxy em: {base_url}")
    
    tester = ProxyTester(base_url)
    results = tester.run_all_tests()
    
    # Exit code baseado nos resultados
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()