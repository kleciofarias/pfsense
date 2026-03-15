#!/usr/bin/env python3
"""
pfsense2opnsense.py
Converte backup config.xml do pfSense para OPNsense com Dnsmasq DNS & DHCP.

Uso:
  python3 pfsense2opnsense.py -i config-pfSense.xml
  python3 pfsense2opnsense.py -i config-pfSense.xml -o config-opnsense.xml --new-user
  python3 pfsense2opnsense.py -i config-pfSense.xml --new-user \
      --username joao --password minhasenha --fullname "João Silva"
"""

import argparse
import getpass
import ipaddress
import sys
import uuid
import xml.etree.ElementTree as ET

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

# ── helpers ──────────────────────────────────────────────────────────────────

def tx(el, tag, default=''):
    if el is None:
        return default
    v = el.findtext(tag, default)
    return v.strip() if v else default

def u():
    return str(uuid.uuid4())

def se(parent, tag, text=None):
    el = ET.SubElement(parent, tag)
    if text is not None:
        el.text = text
    return el

def empty(parent, tag):
    ET.SubElement(parent, tag)

def hash_password(password):
    if HAS_BCRYPT:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=10))
        return hashed.decode()
    else:
        print("[AVISO] Módulo 'bcrypt' não encontrado. Instale com: pip install bcrypt")
        print("        A senha do novo usuário precisará ser redefinida manualmente.")
        return ''

def prompt_new_user(args):
    print("\n── Criação de novo usuário admin ──────────────────────────────")
    username = args.username or input("  Nome de usuário [admin2]: ").strip() or 'admin2'
    fullname = args.fullname or input(f"  Nome completo [{username}]: ").strip() or username
    password = args.password
    if not password:
        while True:
            password = getpass.getpass("  Senha: ")
            confirm  = getpass.getpass("  Confirme a senha: ")
            if password == confirm:
                break
            print("  Senhas não conferem, tente novamente.")
    return username, fullname, password


# ── conversão ─────────────────────────────────────────────────────────────────

def convert(src, dst, create_user=False, args=None):
    pf       = ET.parse(src).getroot()
    sys_pf   = pf.find('system')
    domain   = tx(sys_pf, 'domain', 'home.arpa')
    dns_list = [d.text.strip() for d in pf.findall('./system/dnsserver')
                if d.text and d.text.strip()]

    # coleta de dados para o relatório
    report = {
        'hostname':    tx(sys_pf, 'hostname', 'opnsense'),
        'domain':      domain,
        'timezone':    tx(sys_pf, 'timezone', ''),
        'dns':         dns_list,
        'interfaces':  [],
        'routes':      [],
        'gateways':    [],
        'dhcp_ranges': [],
        'reservas':    [],
        'aliases':     [],
        'fw_rules':    [],
        'nat_rules':   [],
        'vlans':       [],
        'new_user':    None,
        'not_migrated': [],
    }

    opn = ET.Element('opnsense')

    # ── system ────────────────────────────────────────────────────────────────
    sys_el = se(opn, 'system')
    se(sys_el, 'optimization', 'normal')
    se(sys_el, 'hostname', report['hostname'])
    se(sys_el, 'domain',   domain)
    se(sys_el, 'timezone', tx(sys_pf, 'timezone', 'America/Sao_Paulo'))
    for ip in dns_list:
        se(sys_el, 'dnsserver', ip)
    se(sys_el, 'dnsallowoverride', '1')
    se(sys_el, 'nextuid', '2000')
    se(sys_el, 'nextgid', '2000')
    se(sys_el, 'timeservers', tx(sys_pf, 'timeservers', '0.opnsense.pool.ntp.org'))

    # root user
    pf_user   = pf.find('./system/user')
    root_user = se(sys_el, 'user')
    se(root_user, 'name',      'root')
    se(root_user, 'descr',     'System Administrator')
    se(root_user, 'scope',     'system')
    se(root_user, 'groupname', 'admins')
    se(root_user, 'uid',       '0')
    if pf_user is not None:
        h = tx(pf_user, 'bcrypt-hash')
        if h:
            se(root_user, 'password', h.replace('$2y$', '$2b$'))
    se(root_user, 'shell', '/bin/sh')

    # novo usuário (opcional)
    new_user_info = None
    if create_user:
        username, fullname, password = prompt_new_user(args)
        pw_hash       = hash_password(password)
        new_user_info = (username, fullname, pw_hash)
        report['new_user'] = (username, fullname)

        nu = se(sys_el, 'user')
        se(nu, 'name',      username)
        se(nu, 'descr',     fullname)
        se(nu, 'scope',     'system')
        se(nu, 'groupname', 'admins')
        se(nu, 'uid',       '2000')
        if pw_hash:
            se(nu, 'password', pw_hash)
        se(nu, 'priv',  'page-all')
        se(nu, 'shell', '/bin/sh')
        sys_el.find('nextuid').text = '2001'

    grp = se(sys_el, 'group')
    se(grp, 'name',        'admins')
    se(grp, 'description', 'System Administrators')
    se(grp, 'scope',       'system')
    se(grp, 'gid',         '1999')
    se(grp, 'member',      '0')
    if new_user_info:
        se(grp, 'member', '2000')
    se(grp, 'priv', 'page-all')

    wg = se(sys_el, 'webgui')
    se(wg, 'protocol', 'https')
    se(wg, 'port',     '443')
    se(sys_el, 'serialspeed',          '115200')
    se(sys_el, 'primaryconsole',       'video')
    se(sys_el, 'disablenatreflection', 'yes')

    # ── interfaces ────────────────────────────────────────────────────────────
    ifaces_el      = se(opn, 'interfaces')
    pf_ifaces      = pf.find('./interfaces')
    lan_iface_name = 'lan'
    if pf_ifaces is not None:
        for iface in pf_ifaces:
            name   = iface.tag.lower()
            phys   = tx(iface, 'if')
            ipaddr = tx(iface, 'ipaddr')
            prefix = tx(iface, 'subnet')
            descr  = tx(iface, 'descr') or name.upper()

            if ipaddr and ipaddr != 'dhcp' and lan_iface_name == 'lan':
                lan_iface_name = name

            opn_if = se(ifaces_el, name)
            se(opn_if, 'enable')
            se(opn_if, 'if', phys)
            se(opn_if, 'descr', descr)
            if ipaddr == 'dhcp':
                se(opn_if, 'ipaddr', 'dhcp')
                report['interfaces'].append(f'{name} ({phys}) — DHCP')
            elif ipaddr:
                se(opn_if, 'ipaddr', ipaddr)
                if prefix:
                    se(opn_if, 'subnet', prefix)
                report['interfaces'].append(f'{name} ({phys}) — {ipaddr}/{prefix}  [{descr}]')
            else:
                report['interfaces'].append(f'{name} ({phys}) — sem IP  [{descr}]')

            ipaddrv6 = tx(iface, 'ipaddrv6')
            if ipaddrv6:
                se(opn_if, 'ipaddrv6', ipaddrv6)
            if name == 'wan':
                se(opn_if, 'blockpriv',   '1')
                se(opn_if, 'blockbogons', '1')

    # ── rotas estáticas ───────────────────────────────────────────────────────
    sroutes = None
    for r in pf.findall('./staticroutes/route'):
        net = tx(r, 'network')
        gw  = tx(r, 'gateway')
        dsc = tx(r, 'descr')
        if not (net and gw):
            continue
        if sroutes is None:
            sroutes = se(opn, 'staticroutes')
        sr = se(sroutes, 'route')
        se(sr, 'network', net)
        se(sr, 'gateway', gw)
        if dsc:
            se(sr, 'descr', dsc)
        report['routes'].append(f'{net} via {gw}' + (f'  [{dsc}]' if dsc else ''))

    # ── gateways ──────────────────────────────────────────────────────────────
    gws_el = se(opn, 'gateways')
    for gw in pf.findall('./gateways/gateway_item'):
        name = tx(gw, 'name')
        if not name:
            continue
        g = se(gws_el, 'gateway_item')
        for tag in ('interface','gateway','name','weight','ipprotocol','descr','defaultgw'):
            v = tx(gw, tag)
            if v:
                se(g, tag, v)
        report['gateways'].append(f'{name} — {tx(gw,"gateway")} via {tx(gw,"interface")}')

    # ── Dnsmasq DNS & DHCP ────────────────────────────────────────────────────
    pf_dhcpd = pf.find('./dhcpd')

    dm = se(opn, 'dnsmasq')
    dm.set('version',     '1.0.8')
    dm.set('description', 'Dnsmasq DNS and DHCP')

    se(dm, 'enable',             '1')
    se(dm, 'regdhcp',            '0')
    se(dm, 'regdhcpstatic',      '1')
    se(dm, 'dhcpfirst',          '0')
    se(dm, 'strict_order',       '0')
    se(dm, 'domain_needed',      '0')
    se(dm, 'no_private_reverse', '0')
    se(dm, 'no_resolv',          '0')
    se(dm, 'log_queries',        '0')
    se(dm, 'no_hosts',           '0')
    se(dm, 'strictbind',         '0')
    se(dm, 'dnssec',             '0')
    empty(dm, 'regdhcpdomain')
    se(dm, 'interface', lan_iface_name)
    empty(dm, 'port')
    empty(dm, 'dns_forward_max')
    empty(dm, 'cache_size')
    empty(dm, 'local_ttl')
    empty(dm, 'add_mac')
    se(dm, 'add_subnet',   '0')
    se(dm, 'strip_subnet', '0')

    dhcp_gen = se(dm, 'dhcp')
    empty(dhcp_gen, 'no_interface')
    se(dhcp_gen, 'fqdn',             '1')
    se(dhcp_gen, 'domain',           domain)
    se(dhcp_gen, 'local',            '1')
    empty(dhcp_gen, 'lease_max')
    se(dhcp_gen, 'authoritative',    '0')
    se(dhcp_gen, 'default_fw_rules', '1')
    empty(dhcp_gen, 'reply_delay')
    se(dhcp_gen, 'enable_ra',        '0')
    se(dhcp_gen, 'nosync',           '0')
    se(dhcp_gen, 'log_dhcp',         '0')
    se(dhcp_gen, 'log_quiet',        '0')
    se(dm, 'no_ident', '1')

    # reservas
    if pf_dhcpd is not None:
        for pf_iface_el in pf_dhcpd:
            for sm in pf_iface_el.findall('staticmap'):
                mac      = tx(sm, 'mac')
                ip       = tx(sm, 'ipaddr')
                hostname = tx(sm, 'hostname')
                descr    = tx(sm, 'descr')
                if not mac or not ip:
                    continue
                h = se(dm, 'hosts')
                h.set('uuid', u())
                se(h, 'host',       hostname or '')
                se(h, 'domain',     domain)
                se(h, 'local',      '0')
                se(h, 'ip',         ip)
                empty(h, 'cnames')
                empty(h, 'client_id')
                se(h, 'hwaddr',     mac)
                empty(h, 'lease_time')
                se(h, 'ignore',     '0')
                empty(h, 'set_tag')
                se(h, 'descr',      descr)
                empty(h, 'comments')
                empty(h, 'aliases')
                label = f'{mac} → {ip}'
                if hostname: label += f'  hostname: {hostname}'
                if descr:    label += f'  [{descr}]'
                report['reservas'].append(label)

    # ranges
    if pf_dhcpd is not None:
        for pf_iface_el in pf_dhcpd:
            iface_name = pf_iface_el.tag.lower()
            range_el   = pf_iface_el.find('range')
            if range_el is None:
                continue
            r_from = tx(range_el, 'from')
            r_to   = tx(range_el, 'to')
            if not (r_from and r_to):
                continue
            dr = se(dm, 'dhcp_ranges')
            dr.set('uuid', u())
            se(dr, 'interface',   iface_name)
            empty(dr, 'set_tag')
            se(dr, 'start_addr',  r_from)
            se(dr, 'end_addr',    r_to)
            empty(dr, 'subnet_mask')
            empty(dr, 'constructor')
            empty(dr, 'mode')
            empty(dr, 'prefix_len')
            empty(dr, 'lease_time')
            se(dr, 'domain_type', 'range')
            se(dr, 'domain',      domain)
            se(dr, 'nosync',      '0')
            empty(dr, 'ra_mode')
            empty(dr, 'ra_priority')
            empty(dr, 'ra_mtu')
            empty(dr, 'ra_interval')
            empty(dr, 'ra_router_lifetime')
            empty(dr, 'description')
            report['dhcp_ranges'].append(f'{iface_name}: {r_from} – {r_to}')

    # ── VLANs ────────────────────────────────────────────────────────────────
    pf_vlans = pf.findall('./vlans/vlan')
    vlans_el = se(opn, 'vlans')
    vlans_el.set('version', '1.0.0')
    for vlan in pf_vlans:
        parent_if = tx(vlan, 'if')
        tag       = tx(vlan, 'tag')
        descr     = tx(vlan, 'descr')
        pcp       = tx(vlan, 'pcp', '0')
        if not parent_if or not tag:
            continue
        vlanif = f'{parent_if}.{tag}'
        v = se(vlans_el, 'vlan')
        se(v, 'if',     parent_if)
        se(v, 'tag',    tag)
        se(v, 'pcp',    pcp)
        se(v, 'descr',  descr)
        se(v, 'vlanif', vlanif)
        report['vlans'].append(f'{vlanif}  tag={tag}' + (f'  [{descr}]' if descr else ''))

        # adiciona interface lógica para cada VLAN
        vlan_iface = se(ifaces_el, vlanif.replace('.', '_'))
        se(vlan_iface, 'if',    vlanif)
        se(vlan_iface, 'descr', descr or f'VLAN {tag}')

    # ── aliases ───────────────────────────────────────────────────────────────

    pf_aliases = pf.findall('./aliases/alias')
    if pf_aliases:
        aliases_el = se(opn, 'aliases')
        for a in pf_aliases:
            name = tx(a, 'name')
            if not name:
                continue
            al = se(aliases_el, 'alias')
            se(al, 'name', name)
            se(al, 'type', tx(a, 'type'))
            addr = tx(a, 'address')
            if addr:
                se(al, 'content', addr.strip())
            descr = tx(a, 'descr')
            if descr:
                se(al, 'descr', descr)
            atype = tx(a, 'type')
            report['aliases'].append(f'{name} ({atype})' + (f'  [{descr}]' if descr else ''))

    # ── firewall ──────────────────────────────────────────────────────────────
    pf_rules = pf.findall('./filter/rule')
    if pf_rules:
        filter_el = se(opn, 'filter')
        for r in pf_rules:
            if tx(r, 'associated-rule-id'):
                continue
            rule = se(filter_el, 'rule')
            rtype = tx(r, 'type', 'pass')
            iface = tx(r, 'interface')
            proto = tx(r, 'protocol')
            descr = tx(r, 'descr')
            se(rule, 'type', rtype)
            if iface: se(rule, 'interface', iface)
            if proto: se(rule, 'protocol', proto)
            for side in ('source', 'destination'):
                side_el = r.find(side)
                if side_el is None:
                    continue
                out = se(rule, side)
                if side_el.find('any') is not None:
                    se(out, 'any')
                else:
                    net  = tx(side_el, 'network')
                    addr = tx(side_el, 'address')
                    port = tx(side_el, 'port')
                    if net:    se(out, 'network', net)
                    elif addr: se(out, 'address', addr)
                    if port:   se(out, 'port', port)
            if descr: se(rule, 'descr', descr)
            se(rule, 'enabled', '1')
            label = f'[{rtype.upper()}] iface={iface}'
            if proto: label += f' proto={proto}'
            if descr: label += f'  "{descr}"'
            report['fw_rules'].append(label)

    # ── NAT ───────────────────────────────────────────────────────────────────
    pf_nat = pf.findall('./nat/rule')
    if pf_nat:
        nat_el = se(opn, 'nat')
        for r in pf_nat:
            nr = se(nat_el, 'rule')
            descr = tx(r, 'descr')
            for tag in ('interface','protocol','target','local-port','descr'):
                v = tx(r, tag)
                if v: se(nr, tag, v)
            for side in ('source', 'destination'):
                side_el = r.find(side)
                if side_el is not None:
                    out = se(nr, side)
                    if side_el.find('any') is not None:
                        se(out, 'any')
                    else:
                        for sub in ('address','port','network'):
                            v = tx(side_el, sub)
                            if v: se(out, sub, v)
            report['nat_rules'].append(descr or f'NAT {tx(r,"interface")}')

    # itens não migrados
    checks = [
        ('./openvpn/openvpn-server', 'OpenVPN servidor'),
        ('./openvpn/openvpn-client', 'OpenVPN cliente'),
        ('./ipsec/phase1',       'IPsec'),
        ('./cert',               'Certificados SSL'),
        ('./captiveportal',      'Captive Portal'),
    ]
    for xpath, label in checks:
        els = pf.findall(xpath)
        if els and any(len(list(e)) > 0 or e.text for e in els):
            report['not_migrated'].append(label)

    # ── write XML ─────────────────────────────────────────────────────────────
    ET.indent(opn, space='  ')
    with open(dst, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0"?>\n')
        ET.ElementTree(opn).write(f, encoding='unicode', xml_declaration=False)

    return report


# ── relatório ─────────────────────────────────────────────────────────────────

def print_report(report, dst):
    SEP  = '─' * 62
    SEP2 = '═' * 62

    print(f'\n{SEP2}')
    print(f'  🔄  RELATÓRIO DE MIGRAÇÃO  pfSense → OPNsense')
    print(f'{SEP2}')

    print(f'\n  📄 Arquivo gerado : {dst}')

    print(f'\n{SEP}')
    print(f'  🖥️  SISTEMA')
    print(f'{SEP}')
    print(f'  🏷️  Hostname  : {report["hostname"]}')
    print(f'  🌐 Domínio   : {report["domain"]}')
    print(f'  🕐 Timezone  : {report["timezone"]}')
    print(f'  🔍 DNS       : {", ".join(report["dns"]) or "nenhum"}')

    if report['new_user']:
        u, fn = report['new_user']
        print(f'\n{SEP}')
        print(f'  👤 NOVO USUÁRIO ADMIN')
        print(f'{SEP}')
        print(f'  👤 Usuário   : {u}')
        print(f'  📝 Nome      : {fn}')
        print(f'  🔑 Grupo     : admins (acesso total ao WebConfigurator)')

    def section(icon, title, items, empty_msg='nenhum'):
        print(f'\n{SEP}')
        print(f'  {icon} {title}  ({len(items)})')
        print(f'{SEP}')
        if items:
            for item in items:
                print(f'  ✅ {item}')
        else:
            print(f'  ➖ {empty_msg}')

    section('🔌', 'INTERFACES',         report['interfaces'])
    section('🏮', 'VLANs',              report['vlans'],        'nenhuma')
    section('🗺️ ', 'ROTAS ESTÁTICAS',   report['routes'],       'nenhuma')
    section('🚪', 'GATEWAYS',           report['gateways'],     'nenhum')
    section('📡', 'DHCP RANGES',        report['dhcp_ranges'],  'nenhum')
    section('📋', 'RESERVAS DHCP',      report['reservas'],     'nenhuma')
    section('🏷️ ', 'ALIASES',           report['aliases'],      'nenhum')
    section('🛡️ ', 'REGRAS DE FIREWALL',report['fw_rules'],     'nenhuma')
    section('🔀', 'REGRAS NAT',         report['nat_rules'],    'nenhuma')

    if report['not_migrated']:
        print(f'\n{SEP}')
        print(f'  ⚠️  NÃO MIGRADO (configurar manualmente no OPNsense)')
        print(f'{SEP}')
        for item in report['not_migrated']:
            print(f'  ⚠️  {item}')

    print(f'\n{SEP2}')
    print(f'  📥 COMO IMPORTAR NO OPNSENSE')
    print(f'{SEP2}')
    print(f"""
  1️⃣  Acesse o OPNsense pelo navegador
       🌐 https://<ip-do-opnsense>

  2️⃣  Faça login
       👤 Usuário: root (senha original do pfSense)

  3️⃣  No menu superior vá em:
       ⚙️  System → Configuration → Backups

  4️⃣  Na seção "Restore", clique em "Browse" e selecione:
       📄 {dst}

  5️⃣  Clique em "Restore configuration" e confirme.

  6️⃣  O OPNsense vai reiniciar automaticamente. 🔄

  7️⃣  Após reiniciar, verifique cada serviço:
       🔌 Interfaces  → Interfaces → Overview
       📡 DHCP ranges → Services → Dnsmasq DNS & DHCP → DHCP ranges
       📋 Reservas    → Services → Dnsmasq DNS & DHCP → Hosts
       🛡️  Firewall    → Firewall → Rules
       🏷️  Aliases     → Firewall → Aliases
       🗺️  Rotas       → System → Routes → Configuration
       🚪 Gateways    → System → Gateways → Single""")

    if report['new_user']:
        print(f"""
  8️⃣  Faça login com o novo usuário criado:
       👤 Usuário : {report['new_user'][0]}
       🔑 (senha definida durante a conversão)""")

    print(f'\n{SEP2}')
    print(f'  ✅ Migração concluída com sucesso!')
    print(f'{SEP2}\n')


def main():
    parser = argparse.ArgumentParser(
        description='Converte config.xml do pfSense para OPNsense (Dnsmasq DHCP)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python3 pfsense2opnsense.py -i config-pfSense.xml
  python3 pfsense2opnsense.py -i config-pfSense.xml --new-user
  python3 pfsense2opnsense.py -i config-pfSense.xml --new-user \\
      --username joao --fullname "João Silva" --password minhasenha
        """
    )
    parser.add_argument('-i', '--input',   required=True,
                        help='Arquivo de entrada (pfSense config.xml)')
    parser.add_argument('-o', '--output',  default='config-opnsense.xml',
                        help='Arquivo de saída (padrão: config-opnsense.xml)')
    parser.add_argument('--new-user',      action='store_true',
                        help='Criar novo usuário admin no OPNsense')
    parser.add_argument('--username',      default='')
    parser.add_argument('--fullname',      default='')
    parser.add_argument('--password',      default='')
    args = parser.parse_args()

    if not HAS_BCRYPT and args.new_user:
        print("[AVISO] 'bcrypt' não instalado. Rode: pip install bcrypt")

    report = convert(
        src=args.input, dst=args.output,
        create_user=args.new_user, args=args
    )

    print_report(report, args.output)

if __name__ == '__main__':
    main()

