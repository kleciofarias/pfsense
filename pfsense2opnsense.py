# pfsense2opnsense

Conversor de backup de configuração do **pfSense** para **OPNsense**, com suporte a **Dnsmasq DNS & DHCP** e **remapeamento de interfaces físicas** para migração entre hardwares diferentes.

> Migra hostname, domínio, DNS, interfaces, VLANs, reservas DHCP, ranges DHCP, rotas estáticas, gateways, aliases, regras de firewall e NAT — tudo em um único script Python sem dependências obrigatórias.

---

## Índice

- [Por que este script?](#por-que-este-script)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Uso rápido](#uso-rápido)
- [Mapeamento de interfaces físicas](#mapeamento-de-interfaces-físicas)
- [Criação de novo usuário admin](#criação-de-novo-usuário-admin)
- [Importando no OPNsense](#importando-no-opnsense)
- [O que é migrado](#o-que-é-migrado)
- [O que NÃO é migrado](#o-que-não-é-migrado)
- [Solução de problemas](#solução-de-problemas)
- [Referência completa de opções](#referência-completa-de-opções)

---

## Por que este script?

Migrar do pfSense para o OPNsense parece simples — os dois nasceram do mesmo código — mas na prática o XML mudou bastante. As principais dores são:

- O OPNsense moderno usa **Dnsmasq DNS & DHCP** como serviço unificado, com schema diferente do `<dhcpd>` do pfSense.
- Em **nova máquina**, as placas de rede mudam de nome (`em0` → `vtnet0`, `igb0` → `vmx0`...), e isso quebra interfaces, VLANs, regras de firewall, gateways etc.
- O hash de senha do pfSense (`$2y$`) não é aceito direto pelo OPNsense (`$2b$`).
- Itens como certificados, OpenVPN e IPsec precisam ser recriados manualmente.

Este script automatiza tudo que dá para automatizar e lista no relatório final o que sobrou para você ajustar à mão.

---

## Requisitos

- **Python 3.7+** (usa apenas a stdlib para o trabalho principal).
- **`bcrypt`** *(opcional)* — necessário apenas se você for usar `--new-user` para criar um usuário admin extra no OPNsense.

```bash
pip install bcrypt
```

Se o `bcrypt` não estiver instalado e você usar `--new-user`, o script ainda gera o XML, mas a senha do novo usuário precisará ser redefinida manualmente após o primeiro login.

---

## Instalação

Não há instalação — é um script único, sem dependências obrigatórias. Basta baixar:

```bash
curl -O https://exemplo.com/pfsense2opnsense.py
chmod +x pfsense2opnsense.py
```

Ou clonar o repositório e usar `python3 pfsense2opnsense.py` diretamente.

---

## Uso rápido

### 1. Conversão simples (mesmo hardware)

```bash
python3 pfsense2opnsense.py -i config-pfSense.xml
```

Gera `config-opnsense.xml` no diretório atual. Sem o flag `--keep-interfaces`, o script vai perguntar interativamente sobre cada interface física (veja a [seção abaixo](#mapeamento-de-interfaces-físicas)).

### 2. Mantendo os mesmos nomes de interface (sem prompt)

Quando o hardware é igual (ou você vai mover o disco para outra máquina com as mesmas placas):

```bash
python3 pfsense2opnsense.py -i config-pfSense.xml --keep-interfaces
```

### 3. Especificando arquivo de saída

```bash
python3 pfsense2opnsense.py -i config-pfSense.xml -o /tmp/opnsense-novo.xml
```

---

## Mapeamento de interfaces físicas

**Esta é a parte mais importante quando você troca de máquina.** Em um hardware novo, as placas de rede vão ter nomes diferentes:

| pfSense (antigo) | Possível nome na OPNsense (novo) |
|---|---|
| `em0`, `em1` (Intel) | `vtnet0`, `vtnet1` (VirtIO/Proxmox), `vmx0`, `vmx1` (VMware) |
| `igb0`, `igb1` (Intel I-series) | `re0`, `re1` (Realtek), `bge0` (Broadcom) |
| `bce0` | `ix0` (Intel 10G) |

Você tem **três formas** de informar o mapeamento ao script:

### Modo A — Interativo (padrão)

Apenas rode o script e ele vai listar cada interface física com seu contexto (LAN/WAN, IP, descrição) e pedir o novo nome:

```bash
python3 pfsense2opnsense.py -i config-pfSense.xml
```

Saída exemplo:

```
┌────────────────────────────────────────────────────────────┐
│  🔌  MAPEAMENTO DE INTERFACES FÍSICAS                      │
└────────────────────────────────────────────────────────────┘

  🔹 em0
     WAN  [Internet]  dhcp
     Novo nome na OPNsense [em0]: vtnet0

  🔹 em1
     LAN  [Rede Interna]  192.168.1.1/24
     Novo nome na OPNsense [em1]: vtnet1

  Resumo do mapeamento:
    em0  →  vtnet0
    em1  →  vtnet1

  Confirma o mapeamento? [S/n]:
```

Pressione **ENTER** para manter o mesmo nome de uma interface específica.

### Modo B — Linha de comando (`--map`)

Bom para automação ou quando você já sabe o mapeamento:

```bash
python3 pfsense2opnsense.py -i config-pfSense.xml \
    --map em0=vtnet0,em1=vtnet1,igb0=vmx0
```

O script não pergunta nada se todas as interfaces estiverem cobertas.

### Modo C — Manter tudo (`--keep-interfaces`)

```bash
python3 pfsense2opnsense.py -i config-pfSense.xml --keep-interfaces
```

### Como descobrir os nomes na nova máquina

Antes de rodar o script, instale o OPNsense na máquina nova com configuração mínima e, no **console** (menu opção 8 - Shell) ou via SSH:

```bash
# Lista todas as interfaces
ifconfig -l

# Detalhes de uma interface específica (MAC, link, velocidade)
ifconfig vtnet0
```

Anote os nomes (`vtnet0`, `vtnet1`...) e correlacione com os MACs das placas físicas. Depois rode o script com esse mapeamento.

> **Dica:** as VLANs são remapeadas automaticamente. Se você tinha `em2.20` no pfSense e mapear `em2 → vtnet2`, o script gera `vtnet2.20` em todos os lugares (interfaces, VLANs, vlanif).

---

## Criação de novo usuário admin

Por segurança, é boa prática criar um usuário admin extra além do `root` (que herda a senha do pfSense):

### Interativo

```bash
python3 pfsense2opnsense.py -i config-pfSense.xml --new-user
```

O script vai pedir nome de usuário, nome completo e senha.

### Não-interativo (cuidado com histórico do shell!)

```bash
python3 pfsense2opnsense.py -i config-pfSense.xml --new-user \
    --username joao \
    --fullname "João Silva" \
    --password 'senha-super-secreta'
```

> ⚠️ Senhas em linha de comando ficam no histórico do shell. Em produção, prefira o modo interativo ou use variáveis de ambiente lidas pelo seu wrapper.

O novo usuário é criado no grupo `admins` com acesso total ao WebConfigurator (privilégio `page-all`).

---

## Importando no OPNsense

Depois que o script gerar o `config-opnsense.xml`:

1. Instale o OPNsense na máquina nova (configuração mínima — pode usar a opção *Quick Install*).
2. Acesse a interface web: `https://<ip-do-opnsense>` (login `root` com a senha definida na instalação).
3. Vá em **System → Configuration → Backups**.
4. Em **Restore Backup**, clique em **Choose File** e selecione o XML gerado.
5. Clique em **Restore Configuration**.
6. O OPNsense vai reiniciar automaticamente. Aguarde ~1 minuto.
7. Faça login novamente — agora a senha do `root` será a mesma do pfSense original, e seu novo usuário (se criado) também estará disponível.

### Verificações pós-importação

Confira em cada menu se tudo veio certo:

| Item | Onde verificar |
|---|---|
| 🔌 Interfaces | Interfaces → Overview |
| 🏮 VLANs | Interfaces → Other Types → VLAN |
| 📡 DHCP ranges | Services → Dnsmasq DNS & DHCP → DHCP ranges |
| 📋 Reservas DHCP | Services → Dnsmasq DNS & DHCP → Hosts |
| 🛡️ Firewall | Firewall → Rules |
| 🏷️ Aliases | Firewall → Aliases |
| 🗺️ Rotas estáticas | System → Routes → Configuration |
| 🚪 Gateways | System → Gateways → Single |

---

## O que é migrado

✅ **Sistema** — hostname, domínio, timezone, servidores DNS, NTP, senha do root (com conversão de hash `$2y$` → `$2b$`).
✅ **Interfaces** — todas as interfaces lógicas (WAN, LAN, OPT1, OPT2...) com IP, máscara, descrição, IPv6.
✅ **VLANs** — com mapeamento automático do nome da interface pai.
✅ **DHCP** — ranges e reservas estáticas, migradas para o novo serviço **Dnsmasq DNS & DHCP**.
✅ **Rotas estáticas** e **gateways**.
✅ **Aliases** de firewall (hosts, redes, portas).
✅ **Regras de firewall** (filter rules) com origem, destino, protocolo, portas.
✅ **NAT** (port forwards básicos).
✅ **Bloqueio de bogons/RFC1918 na WAN** (configurado automaticamente).

---

## O que NÃO é migrado

⚠️ Algumas coisas precisam de recriação manual no OPNsense por diferenças estruturais entre os dois projetos:

- 🔐 **Certificados SSL/CA/PKI** — recrie em System → Trust → Certificates.
- 🌐 **OpenVPN servidor e cliente** — recrie em VPN → OpenVPN.
- 🔒 **IPsec** (túneis fase 1 e 2) — recrie em VPN → IPsec.
- 🚪 **Captive Portal** — recrie em Services → Captive Portal.
- 📦 **Pacotes instalados** (Suricata, pfBlockerNG, HAProxy etc.) — instale os equivalentes em System → Firmware → Plugins.
- 📊 **Configurações de monitoring/RRD** e estatísticas históricas.

O script lista no relatório final tudo que detectou no pfSense e não conseguiu migrar, para você ter a checklist em mãos.

---

## Solução de problemas

### "ImportError: No module named bcrypt"

Você está usando `--new-user` sem ter o `bcrypt` instalado. Rode:
```bash
pip install bcrypt
```
Ou então remova `--new-user` e crie o usuário manualmente depois pela interface web.

### Após importar, perdi acesso à interface web

Isso quase sempre é problema de **mapeamento de interfaces**. Conecte um monitor e teclado à máquina e veja, pelo menu do OPNsense, qual interface está como LAN. Se estiver na placa errada, use a opção **1) Assign interfaces** do menu console para corrigir, ou refaça a conversão com o `--map` correto.

### As VLANs não aparecem

Verifique se a interface pai (no exemplo, `vtnet2` se você usou `--map em2=vtnet2`) realmente existe na máquina nova. Sem o pai físico, as VLANs filhas não sobem.

### Erro "Cannot parse XML"

O backup do pfSense pode estar corrompido ou ter sido editado manualmente. Tente gerar um novo backup em **Diagnostics → Backup & Restore** no pfSense original e use esse.

### Reservas DHCP funcionam mas resolução de nomes não

O Dnsmasq DNS & DHCP precisa estar ativado em **Services → Dnsmasq DNS & DHCP → General** e a interface LAN precisa estar listada como "interface" — o script já faz isso, mas vale conferir.

---

## Referência completa de opções

```
python3 pfsense2opnsense.py [opções]

OPÇÕES OBRIGATÓRIAS
  -i, --input ARQUIVO       Arquivo de entrada (config.xml do pfSense)

OPÇÕES GERAIS
  -o, --output ARQUIVO      Arquivo de saída (padrão: config-opnsense.xml)
  -h, --help                Exibe a ajuda

MAPEAMENTO DE INTERFACES
  --map em0=vtnet0,em1=vtnet1
                            Mapeia nomes físicos antigos → novos
  --keep-interfaces         Mantém os nomes originais sem prompt

CRIAÇÃO DE USUÁRIO ADMIN
  --new-user                Cria um usuário admin adicional
  --username NOME           Nome de usuário (padrão: admin2)
  --fullname "NOME COMPLETO" Nome completo
  --password SENHA          Senha (não recomendado em CLI — use modo interativo)
```

---

## Exemplos completos

**Cenário 1 — Migração simples, mesmo hardware:**
```bash
python3 pfsense2opnsense.py -i pfsense-backup.xml --keep-interfaces
```

**Cenário 2 — Migração para nova máquina virtual (Proxmox/VirtIO):**
```bash
python3 pfsense2opnsense.py \
    -i pfsense-backup.xml \
    -o opnsense.xml \
    --map em0=vtnet0,em1=vtnet1,em2=vtnet2 \
    --new-user --username admin2 --fullname "Admin Backup"
```

**Cenário 3 — Migração interativa completa:**
```bash
python3 pfsense2opnsense.py -i pfsense-backup.xml --new-user
# (responde aos prompts de mapeamento e usuário)
```

---

## Licença

Use à vontade. Faça backup antes de testar em produção. Não há garantia: revise o XML gerado antes de importar em ambiente crítico.
