**# 🔄 pfsense2opnsense

Converte o backup `config.xml` do **pfSense** para o formato compatível com **OPNsense**, incluindo suporte completo ao **Dnsmasq DNS & DHCP**.

---

## ✨ O que ele migra

| # | Item | Detalhes |
|---|------|----------|
| ✅ | **Sistema** | Hostname, domínio, timezone, servidores DNS, senha root |
| ✅ | **Interfaces** | WAN, LAN e interfaces adicionais com IP estático ou DHCP |
| ✅ | **VLANs** | Tags, interface pai, descrição e interface lógica (ex: `em1.10`) |
| ✅ | **Rotas estáticas** | Rede de destino, gateway e descrição |
| ✅ | **Gateways** | Nome, IP, interface e protocolo |
| ✅ | **DHCP ranges** | Pool de IPs por interface (formato Dnsmasq) |
| ✅ | **Reservas DHCP** | MAC address → IP fixo, hostname e descrição |
| ✅ | **Aliases** | Hosts, redes e portas |
| ✅ | **Regras de firewall** | Tipo, interface, protocolo, origem e destino |
| ✅ | **Regras NAT** | Port forward e outbound NAT |
| ✅ | **Novo usuário admin** | Cria usuário extra com acesso total ao WebConfigurator |
| ⚠️ | **Não migrado** | OpenVPN, IPsec, certificados SSL, captive portal |

---

## 📋 Pré-requisitos

- Python 3.8+
- Biblioteca `bcrypt` (necessária para criar novo usuário com senha)

```bash
pip install bcrypt
```

---

## 🚀 Como usar

### Conversão simples

```bash
python3 pfsense2opnsense.py -i config-pfSense.xml
```

### Definindo o arquivo de saída

```bash
python3 pfsense2opnsense.py -i config-pfSense.xml -o meu-opnsense.xml
```

### Com criação de novo usuário admin (modo interativo)

O script vai pedir o nome de usuário, nome completo e senha:

```bash
python3 pfsense2opnsense.py -i config-pfSense.xml --new-user
```

### Com criação de novo usuário admin (modo não-interativo)

```bash
python3 pfsense2opnsense.py -i config-pfSense.xml --new-user \
  --username joao \
  --fullname "João Silva" \
  --password minhasenha
```

---

## 📊 Exemplo de saída

```
════════════════════════════════════════════════════════════════
  🔄  RELATÓRIO DE MIGRAÇÃO  pfSense → OPNsense
════════════════════════════════════════════════════════════════

  📄 Arquivo gerado : config-opnsense.xml

──────────────────────────────────────────────────────────────
  🖥️  SISTEMA
──────────────────────────────────────────────────────────────
  🏷️  Hostname  : meu-router
  🌐 Domínio   : home.arpa
  🕐 Timezone  : America/Fortaleza
  🔍 DNS       : 8.8.8.8, 1.1.1.1

──────────────────────────────────────────────────────────────
  🔌 INTERFACES  (2)
──────────────────────────────────────────────────────────────
  ✅ wan (em0) — DHCP
  ✅ lan (em1) — 192.168.1.1/24  [LAN]

──────────────────────────────────────────────────────────────
  🏮 VLANs  (2)
──────────────────────────────────────────────────────────────
  ✅ em1.10  tag=10  [VLAN_CORP]
  ✅ em1.20  tag=20  [VLAN_GUEST]

──────────────────────────────────────────────────────────────
  📡 DHCP RANGES  (1)
──────────────────────────────────────────────────────────────
  ✅ lan: 192.168.1.100 – 192.168.1.200

──────────────────────────────────────────────────────────────
  📋 RESERVAS DHCP  (1)
──────────────────────────────────────────────────────────────
  ✅ aa:bb:cc:dd:ee:ff → 192.168.1.10  hostname: servidor  [meu servidor]

════════════════════════════════════════════════════════════════
  📥 COMO IMPORTAR NO OPNSENSE
════════════════════════════════════════════════════════════════

  1️⃣  Acesse o OPNsense: https://<ip-do-opnsense>
  2️⃣  System → Configuration → Backups
  3️⃣  Seção "Restore" → selecione o arquivo gerado
  4️⃣  Clique em "Restore configuration"
  5️⃣  Aguarde o reinício automático ✅
```

---

## 📥 Como importar no OPNsense

Após gerar o arquivo convertido:

1. Acesse o OPNsense pelo navegador: `https://<ip-do-opnsense>`
2. Faça login com o usuário `root`
3. Vá em **System → Configuration → Backups**
4. Na seção **Restore**, clique em **Browse** e selecione o arquivo gerado
5. Clique em **Restore configuration** e confirme
6. O OPNsense vai reiniciar automaticamente

### ✔️ Após reiniciar, verifique

| Serviço | Caminho no OPNsense |
|---------|---------------------|
| Interfaces | Interfaces → Overview |
| VLANs | Interfaces → Other Types → VLANs |
| DHCP ranges | Services → Dnsmasq DNS & DHCP → DHCP ranges |
| Reservas DHCP | Services → Dnsmasq DNS & DHCP → Hosts |
| Firewall | Firewall → Rules |
| Aliases | Firewall → Aliases |
| Rotas | System → Routes → Configuration |
| Gateways | System → Gateways → Single |

---

## ⚙️ Argumentos

| Argumento | Obrigatório | Descrição |
|-----------|-------------|-----------|
| `-i`, `--input` | ✅ Sim | Arquivo de entrada (pfSense `config.xml`) |
| `-o`, `--output` | ❌ Não | Arquivo de saída (padrão: `config-opnsense.xml`) |
| `--new-user` | ❌ Não | Cria um novo usuário admin no OPNsense |
| `--username` | ❌ Não | Nome do novo usuário (requer `--new-user`) |
| `--fullname` | ❌ Não | Nome completo do novo usuário |
| `--password` | ❌ Não | Senha do novo usuário (prefira o modo interativo) |

---

## ⚠️ O que não é migrado

Os itens abaixo precisam ser configurados manualmente no OPNsense após a importação:

- **OpenVPN** (servidor e cliente)
- **IPsec / WireGuard**
- **Certificados SSL**
- **Captive Portal**
- **Plugins extras** instalados no pfSense

---

## 🧪 Testado com

- pfSense **2.7.x / 23.x**
- OPNsense **24.1+**
---

## 📄 Licença

MIT — use à vontade.**
