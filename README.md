# 🔄 pfSense to OPNsense Configuration Converter

Script Python que converte arquivos de configuração do **pfSense** para **OPNsense**, facilitando a migração entre os dois firewalls.

---

## 📋 Índice

- [O que o script faz](#-o-que-o-script-faz)
- [Requisitos](#-requisitos)
- [Instalação](#-instalação)
- [Como usar](#-como-usar)
- [O que é convertido](#-o-que-é-convertido)
- [Limitações importantes](#-limitações-importantes)
- [Processo de migração recomendado](#-processo-de-migração-recomendado)
- [Configurações que precisam ajuste manual](#-configurações-que-precisam-ajuste-manual)
- [Avisos críticos](#-avisos-críticos)
- [Exemplo de saída](#-exemplo-de-saída)

---

## 🎯 O que o script faz

Este script automatiza a conversão do arquivo de configuração XML do pfSense para o formato compatível com OPNsense. Ele **NÃO** faz uma migração completa e automática - é uma ferramenta para **acelerar o processo inicial** de migração.

### ✅ Vantagens

- ✔️ Economiza horas de reconfiguração manual
- ✔️ Preserva a estrutura básica de rede
- ✔️ Mantém regras de firewall e NAT como base
- ✔️ Converte aliases, gateways e rotas
- ✔️ Gera relatório detalhado do que foi convertido

### ⚠️ Importante saber

- ❌ **NÃO é uma migração 100% automática**
- ❌ Configurações VPN precisam ser refeitas
- ❌ Plugins/pacotes não são convertidos
- ❌ Certificados devem ser reimportados
- ❌ **SEMPRE teste em ambiente não-produção primeiro**

---

## 💻 Requisitos

- **Python 3.6+** instalado
- Arquivo de backup/configuração do pfSense (`.xml`)
- Acesso ao OPNsense para importar o arquivo gerado

### Dependências

Nenhuma dependência externa é necessária - o script usa apenas bibliotecas padrão do Python:
- `xml.etree.ElementTree` (parsing XML)
- `sys`, `datetime` (utilitários)

---

## 📦 Instalação

1. **Baixe o script:**
   ```bash
   # Nenhuma instalação necessária, apenas baixe o arquivo
   wget https://seu-servidor.com/pfsense_to_opnsense.py
   # ou
   curl -O https://seu-servidor.com/pfsense_to_opnsense.py
   ```

2. **Torne executável (opcional):**
   ```bash
   chmod +x pfsense_to_opnsense.py
   ```

---

## 🚀 Como usar

### Passo 1: Exportar configuração do pfSense

No pfSense:
1. Acesse: **Diagnostics** → **Backup & Restore**
2. Clique em **Download configuration as XML**
3. Salve o arquivo (ex: `config-pfsense-backup.xml`)

### Passo 2: Executar o conversor

```bash
python3 pfsense_to_opnsense.py config-pfsense-backup.xml
```

### Passo 3: Arquivo gerado

O script cria um arquivo com timestamp:
```
opnsense_config_20240217_143025.xml
```

### Passo 4: Importar no OPNsense

⚠️ **IMPORTANTE: Faça backup do OPNsense antes!**

No OPNsense:
1. Acesse: **System** → **Configuration** → **Backups**
2. Faça **Download** do backup atual
3. Clique em **Restore Configuration**
4. Faça upload do arquivo `opnsense_config_XXXXX.xml`
5. Clique em **Restore Configuration**
6. O sistema irá reiniciar

---

## 📊 O que é convertido

### ✅ Seções Convertidas Automaticamente

| Categoria | O que é convertido | Observações |
|-----------|-------------------|-------------|
| 🖥️ **System** | Hostname, domínio, timezone, DNS | ✔️ Direto |
| 🔌 **Interfaces** | WAN, LAN, VLANs, IPs, máscaras | ✔️ Precisa validação |
| 🌐 **Gateways** | Todos os gateways configurados | ✔️ Validar monitoramento |
| 🗺️ **Rotas Estáticas** | Todas as rotas manuais | ✔️ Testar conectividade |
| 🛡️ **Firewall Rules** | Regras de allow/block | ⚠️ **REVISAR TODAS** |
| 🔀 **NAT** | Port Forward, Outbound NAT | ⚠️ Testar funcionamento |
| 📡 **DHCP Server** | Pools, ranges, opções DHCP | ✔️ Validar leases |
| 📋 **Aliases** | Hosts, redes, portas | ✔️ Direto |

### ❌ O que NÃO é convertido

- ❌ **VPN** (OpenVPN, IPsec, WireGuard)
- ❌ **Certificados SSL/TLS**
- ❌ **Usuários e grupos**
- ❌ **Plugins/Pacotes**
- ❌ **Configurações de WebGUI** (porta, protocolo)
- ❌ **Captive Portal**
- ❌ **Traffic Shaper**
- ❌ **DNS Resolver/Forwarder** configurações avançadas

---

## ⚠️ Limitações importantes

### 1. Compatibilidade de versões

- Script testado: pfSense 2.6+ → OPNsense 23.7+
- Versões antigas podem ter incompatibilidades

### 2. Plugins e Pacotes

pfSense e OPNsense têm **ecossistemas de plugins diferentes**:

| pfSense | OPNsense Equivalente |
|---------|---------------------|
| pfBlockerNG | OPNsense Firewall/Sensei |
| Suricata | Suricata (reconfigurar) |
| Squid | Squid (reconfigurar) |
| HAProxy | HAProxy (reconfigurar) |

### 3. Regras de Firewall

As regras são **convertidas**, mas:
- ⚠️ Sintaxe pode ter pequenas diferenças
- ⚠️ Aliases devem existir primeiro
- ⚠️ Gateways devem estar configurados
- ⚠️ **SEMPRE revisar antes de ativar**

### 4. NAT e Port Forwarding

- Regras básicas são convertidas
- Configurações avançadas precisam revisão
- Testar cada port forward individualmente

---

## 🔧 Processo de migração recomendado

### Fase 1: Preparação (1-2 dias)

1. ✅ Documente configuração atual do pfSense
2. ✅ Faça backup completo do pfSense
3. ✅ Liste todos os plugins/pacotes instalados
4. ✅ Anote configurações de VPN
5. ✅ Exporte certificados SSL manualmente

### Fase 2: Conversão (1 dia)

6. ✅ Execute o script de conversão
7. ✅ Analise o relatório gerado
8. ✅ Identifique o que precisa ser refeito manualmente

### Fase 3: Teste em Lab (3-5 dias)

9. ✅ Monte ambiente de teste com OPNsense
10. ✅ Importe configuração convertida
11. ✅ Reconfigure VPNs manualmente
12. ✅ Reinstale plugins equivalentes
13. ✅ Teste TODAS as funcionalidades:
    - [ ] Conectividade internet
    - [ ] Regras de firewall
    - [ ] NAT/Port forwarding
    - [ ] DHCP
    - [ ] DNS
    - [ ] VPN
    - [ ] Acesso remoto
14. ✅ Documente diferenças e ajustes necessários

### Fase 4: Produção (com janela de manutenção)

15. ✅ Agende janela de manutenção
16. ✅ Faça backup final do pfSense
17. ✅ Execute migração em produção
18. ✅ Teste imediatamente após migração
19. ✅ Tenha plano de rollback pronto

---

## 🔨 Configurações que precisam ajuste manual

### 1. WebGUI (Obrigatório)

```
OPNsense → System → Settings → Administration
- Porta: 443 (ou sua porta customizada)
- Protocolo: HTTPS
- Certificado SSL
```

### 2. VPN OpenVPN (Refazer do zero)

```
OPNsense → VPN → OpenVPN → Servers/Clients
- Recriar servidores
- Recriar clientes
- Reimportar certificados
- Exportar novos configs para clientes
```

### 3. IPsec VPN (Refazer do zero)

```
OPNsense → VPN → IPsec → Connections
- Recriar túneis
- Configurar Phase 1 e Phase 2
- Testar conectividade
```

### 4. Certificados SSL

```
OPNsense → System → Trust → Certificates
- Importar CA
- Importar certificados
- Associar ao WebGUI/VPN
```

### 5. Usuários e Grupos

```
OPNsense → System → Access → Users
- Recriar usuários administrativos
- Configurar autenticação (LDAP/RADIUS se aplicável)
```

### 6. DNS Resolver

```
OPNsense → Services → Unbound DNS
- Configurar domínios locais
- Host overrides
- Domain overrides
```

### 7. Plugins/Pacotes

```
OPNsense → System → Firmware → Plugins
- Instalar equivalentes aos do pfSense
- Reconfigurar do zero
```

---

## 🚨 Avisos críticos

### ⛔ NUNCA faça isso:

1. ❌ **Importar direto em produção sem testar**
2. ❌ **Assumir que tudo funcionará automaticamente**
3. ❌ **Pular a revisão das regras de firewall**
4. ❌ **Não fazer backup do OPNsense antes de importar**
5. ❌ **Migrar sem janela de manutenção**

### ✅ SEMPRE faça isso:

1. ✅ **Teste em ambiente isolado primeiro**
2. ✅ **Revise TODAS as regras de firewall**
3. ✅ **Teste TODAS as funcionalidades críticas**
4. ✅ **Tenha plano de rollback**
5. ✅ **Documente todas as mudanças**

---

## 📸 Exemplo de saída

```
╔════════════════════════════════════════════════════════════════════╗
║  pfSense → OPNsense Configuration Converter                        ║
╚════════════════════════════════════════════════════════════════════╝

  Arquivo de entrada: config-pfsense-backup.xml
  Arquivo de saída:   opnsense_config_20240217_143025.xml
  Data/Hora:          17/02/2024 14:30:25

═══════════════════════════════════════════════════════════════════════
  🔄 INICIANDO CONVERSÃO pfSense → OPNsense
═══════════════════════════════════════════════════════════════════════

  ✔ Arquivo pfSense carregado: config-pfsense-backup.xml
  → Versão pfSense detectada: 2.6.0

═══════════════════════════════════════════════════════════════════════
  🖥️  SYSTEM - Configurações do Sistema
═══════════════════════════════════════════════════════════════════════

  ✔ Convertidos 6 campos de sistema
  ⚠ Protocolo WebGUI precisa ser reconfigurado manualmente
  ⚠ Porta WebGUI precisa ser reconfigurada manualmente

═══════════════════════════════════════════════════════════════════════
  🔌 INTERFACES - Configuração de Rede
═══════════════════════════════════════════════════════════════════════

  ✔ Interface 'WAN' (wan) convertida
  ✔ Interface 'LAN' (lan) convertida
  ✔ Interface 'DMZ' (opt1) convertida
  → Total: 3 interfaces convertidas

═══════════════════════════════════════════════════════════════════════
  🌐 GATEWAYS - Gateways de Rede
═══════════════════════════════════════════════════════════════════════

  ✔ Gateway 'WAN_DHCP' (192.168.1.1) convertido
  ✔ Gateway 'DMZ_GW' (10.0.10.1) convertido
  → Total: 2 gateways convertidos

═══════════════════════════════════════════════════════════════════════
  🗺️  STATIC ROUTES - Rotas Estáticas
═══════════════════════════════════════════════════════════════════════

  ✔ Rota 10.20.0.0/16 via WAN_DHCP convertida
  ✔ Rota 172.16.0.0/12 via DMZ_GW convertida
  → Total: 2 rotas estáticas convertidas

═══════════════════════════════════════════════════════════════════════
  🛡️  FIREWALL - Regras de Segurança
═══════════════════════════════════════════════════════════════════════

  ✔ Convertidas 47 regras de firewall
  ⚠ IMPORTANTE: Revise TODAS as regras manualmente no OPNsense!

═══════════════════════════════════════════════════════════════════════
  🔀 NAT - Network Address Translation
═══════════════════════════════════════════════════════════════════════

  ✔ Convertidas 3 regras NAT Outbound
  ✔ Convertidas 8 regras Port Forward

═══════════════════════════════════════════════════════════════════════
  📡 DHCP SERVER - Servidor DHCP
═══════════════════════════════════════════════════════════════════════

  ✔ Interface DHCP 'lan' convertida
  ✔ Interface DHCP 'opt1' convertida
  → Total: 2 configurações DHCP convertidas

═══════════════════════════════════════════════════════════════════════
  📋 ALIASES - Grupos e Listas
═══════════════════════════════════════════════════════════════════════

  ✔ Alias 'RFC1918' convertido
  ✔ Alias 'Servidores_Internos' convertido
  ✔ Alias 'Portas_Web' convertido
  → Total: 3 aliases convertidos

═══════════════════════════════════════════════════════════════════════
  💾 SALVANDO CONFIGURAÇÃO
═══════════════════════════════════════════════════════════════════════

  ✔ Arquivo salvo: opnsense_config_20240217_143025.xml
  ✔ Conversão concluída com sucesso!

═══════════════════════════════════════════════════════════════════════
  ⚠️  AVISOS IMPORTANTES - LEIA COM ATENÇÃO!
═══════════════════════════════════════════════════════════════════════

   1. BACKUP: Faça backup completo do OPNsense ANTES de importar
   2. TESTE: Este é um arquivo de BASE, não use em produção sem testar
   3. MANUAL: Você DEVE revisar e ajustar TODAS as configurações manualmente
   4. PLUGINS: Pacotes/plugins do pfSense não são compatíveis
   5. WEBGUI: Porta e protocolo da WebGUI devem ser reconfigurados
   6. CERTIFICADOS: Certificados SSL/TLS devem ser reimportados
   7. VPN: Configurações de OpenVPN/IPsec precisam revisão manual
   8. PACKAGES: Reinstale pacotes equivalentes no OPNsense
   9. FIREWALL: REVISE TODAS as regras de firewall antes de ativar
  10. NAT: Regras NAT podem precisar ajustes manuais
  11. GATEWAYS: Verifique se os gateways foram importados corretamente
  12. ROTAS: Valide todas as rotas estáticas após importação

  ⚠️  NUNCA aplique esta configuração diretamente em produção!
  ⚠️  Use em ambiente de TESTE primeiro!

═══════════════════════════════════════════════════════════════════════
```

---

## 🆘 Troubleshooting

### Erro: "xml.etree.ElementTree.ParseError"

**Problema:** Arquivo XML corrompido ou inválido

**Solução:**
```bash
# Verifique se o arquivo é um XML válido
xmllint config-pfsense-backup.xml
```

### Erro: "No module named 'xml'"

**Problema:** Python não instalado corretamente

**Solução:**
```bash
# Reinstale Python
sudo apt install python3
```

### Configuração não funciona após importação

**Problema:** Configurações incompatíveis ou faltando dados

**Solução:**
1. Revise o log de boot do OPNsense: `System → Log Files → General`
2. Verifique se todos os gateways estão UP
3. Valide interfaces: `Interfaces → Assignments`
4. Teste regras de firewall uma por uma

---

## 📚 Recursos adicionais

### Documentação Oficial

- [OPNsense Documentation](https://docs.opnsense.org/)
- [pfSense Documentation](https://docs.netgate.com/pfsense/en/latest/)

### Comunidade

- [OPNsense Forum](https://forum.opnsense.org/)
- [Reddit r/OPNsenseFirewall](https://reddit.com/r/OPNsenseFirewall)

### Comparação pfSense vs OPNsense

- [Diferenças principais](https://docs.opnsense.org/manual/how-tos/migrate_to_opnsense.html)

---

## 📝 Licença

Este script é fornecido "como está", sem garantias de qualquer tipo.
Use por sua própria conta e risco.

---

## 👤 Autor

Script criado para facilitar migrações de pfSense para OPNsense.

---

## ⭐ Contribuindo

Encontrou um bug ou tem sugestões? Entre em contato ou abra uma issue!

---

**Última atualização:** 17/02/2024


