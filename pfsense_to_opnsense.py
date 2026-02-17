#!/usr/bin/env python3
"""
pfSense to OPNsense Configuration Converter
Converte arquivo de configuração XML do pfSense para OPNsense.

Uso: python3 pfsense_to_opnsense.py <arquivo_config_pfsense.xml>
Exemplo: python3 pfsense_to_opnsense.py config-pfsense-backup.xml
"""

import sys
import xml.etree.ElementTree as ET
from datetime import datetime
import re

# Cores ANSI
GREEN   = "\033[92m"
RED     = "\033[91m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
BOLD    = "\033[1m"
RESET   = "\033[0m"
DIM     = "\033[2m"


def print_header(title):
    """Imprime cabeçalho."""
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")


def print_status(status, message, details=""):
    """Imprime status da conversão."""
    if status == "ok":
        icon = f"{GREEN}✔{RESET}"
    elif status == "warning":
        icon = f"{YELLOW}⚠{RESET}"
    elif status == "error":
        icon = f"{RED}✘{RESET}"
    else:
        icon = f"{CYAN}→{RESET}"
    
    print(f"  {icon} {message}")
    if details:
        print(f"      {DIM}{details}{RESET}")


def convert_system_section(pfsense_root, opnsense_root):
    """Converte seção system."""
    print_header("🖥️  SYSTEM - Configurações do Sistema")
    
    pf_system = pfsense_root.find('system')
    if pf_system is None:
        print_status("warning", "Seção 'system' não encontrada no pfSense")
        return
    
    op_system = ET.SubElement(opnsense_root, 'system')
    
    # Campos compatíveis diretos
    compatible_fields = [
        'hostname', 'domain', 'timezone', 'timeservers',
        'dnsserver', 'dnsallowoverride', 'dnslocalhost'
    ]
    
    converted = 0
    for field in compatible_fields:
        element = pf_system.find(field)
        if element is not None:
            new_element = ET.SubElement(op_system, field)
            new_element.text = element.text
            converted += 1
    
    print_status("ok", f"Convertidos {converted} campos de sistema")
    
    # Campos que precisam atenção
    warnings = []
    
    if pf_system.find('webgui') is not None:
        webgui = pf_system.find('webgui')
        if webgui.find('protocol') is not None:
            warnings.append("Protocolo WebGUI precisa ser reconfigurado manualmente")
        if webgui.find('port') is not None:
            warnings.append("Porta WebGUI precisa ser reconfigurada manualmente")
    
    for warning in warnings:
        print_status("warning", warning)
    
    return op_system


def convert_interfaces(pfsense_root, opnsense_root):
    """Converte interfaces de rede."""
    print_header("🔌 INTERFACES - Configuração de Rede")
    
    pf_interfaces = pfsense_root.find('interfaces')
    if pf_interfaces is None:
        print_status("warning", "Seção 'interfaces' não encontrada")
        return
    
    op_interfaces = ET.SubElement(opnsense_root, 'interfaces')
    
    converted_count = 0
    for interface in pf_interfaces:
        op_interface = ET.SubElement(op_interfaces, interface.tag)
        
        # Campos compatíveis
        compatible_fields = [
            'descr', 'if', 'ipaddr', 'subnet', 'gateway',
            'enable', 'spoofmac', 'mtu', 'media', 'mediaopt'
        ]
        
        for field in compatible_fields:
            element = interface.find(field)
            if element is not None:
                new_element = ET.SubElement(op_interface, field)
                new_element.text = element.text
        
        converted_count += 1
        descr = interface.find('descr')
        name = descr.text if descr is not None else interface.tag
        print_status("ok", f"Interface '{name}' ({interface.tag}) convertida")
    
    print_status("info", f"Total: {converted_count} interfaces convertidas")
    
    return op_interfaces


def convert_firewall_rules(pfsense_root, opnsense_root):
    """Converte regras de firewall."""
    print_header("🛡️  FIREWALL - Regras de Segurança")
    
    pf_filter = pfsense_root.find('filter')
    if pf_filter is None:
        print_status("warning", "Seção 'filter' não encontrada")
        return
    
    op_filter = ET.SubElement(opnsense_root, 'filter')
    
    rules = pf_filter.findall('rule')
    if not rules:
        print_status("warning", "Nenhuma regra de firewall encontrada")
        return
    
    converted_count = 0
    warnings = []
    
    for rule in rules:
        op_rule = ET.SubElement(op_filter, 'rule')
        
        # Campos compatíveis
        compatible_fields = [
            'type', 'interface', 'ipprotocol', 'protocol',
            'source', 'destination', 'descr', 'disabled',
            'log', 'quick'
        ]
        
        for field in compatible_fields:
            element = rule.find(field)
            if element is not None:
                if field in ['source', 'destination']:
                    # Copia sub-elementos
                    new_element = ET.SubElement(op_rule, field)
                    for sub in element:
                        sub_elem = ET.SubElement(new_element, sub.tag)
                        sub_elem.text = sub.text
                else:
                    new_element = ET.SubElement(op_rule, field)
                    new_element.text = element.text
        
        converted_count += 1
    
    print_status("ok", f"Convertidas {converted_count} regras de firewall")
    print_status("warning", "IMPORTANTE: Revise TODAS as regras manualmente no OPNsense!")
    
    return op_filter


def convert_nat_rules(pfsense_root, opnsense_root):
    """Converte regras NAT."""
    print_header("🔀 NAT - Network Address Translation")
    
    pf_nat = pfsense_root.find('nat')
    if pf_nat is None:
        print_status("warning", "Seção 'nat' não encontrada")
        return
    
    op_nat = ET.SubElement(opnsense_root, 'nat')
    
    # Port Forward
    outbound = pf_nat.findall('outbound')
    rule_count = pf_nat.findall('rule')
    
    converted_outbound = 0
    converted_rules = 0
    
    for out in outbound:
        op_out = ET.SubElement(op_nat, 'outbound')
        for child in out:
            new_child = ET.SubElement(op_out, child.tag)
            new_child.text = child.text
        converted_outbound += 1
    
    for rule in rule_count:
        op_rule = ET.SubElement(op_nat, 'rule')
        for child in rule:
            if child.tag in ['source', 'destination']:
                new_element = ET.SubElement(op_rule, child.tag)
                for sub in child:
                    sub_elem = ET.SubElement(new_element, sub.tag)
                    sub_elem.text = sub.text
            else:
                new_child = ET.SubElement(op_rule, child.tag)
                new_child.text = child.text
        converted_rules += 1
    
    if converted_outbound > 0:
        print_status("ok", f"Convertidas {converted_outbound} regras NAT Outbound")
    if converted_rules > 0:
        print_status("ok", f"Convertidas {converted_rules} regras Port Forward")
    
    if converted_outbound == 0 and converted_rules == 0:
        print_status("warning", "Nenhuma regra NAT encontrada")
    
    return op_nat


def convert_dhcp_server(pfsense_root, opnsense_root):
    """Converte configurações DHCP."""
    print_header("📡 DHCP SERVER - Servidor DHCP")
    
    pf_dhcpd = pfsense_root.find('dhcpd')
    if pf_dhcpd is None:
        print_status("warning", "Seção 'dhcpd' não encontrada")
        return
    
    op_dhcpd = ET.SubElement(opnsense_root, 'dhcpd')
    
    converted = 0
    for interface in pf_dhcpd:
        op_interface = ET.SubElement(op_dhcpd, interface.tag)
        
        compatible_fields = [
            'enable', 'range', 'defaultleasetime', 'maxleasetime',
            'gateway', 'domain', 'dnsserver', 'ntpserver'
        ]
        
        for field in compatible_fields:
            element = interface.find(field)
            if element is not None:
                if field == 'range':
                    new_range = ET.SubElement(op_interface, 'range')
                    for sub in element:
                        sub_elem = ET.SubElement(new_range, sub.tag)
                        sub_elem.text = sub.text
                else:
                    new_element = ET.SubElement(op_interface, field)
                    new_element.text = element.text
        
        converted += 1
        print_status("ok", f"Interface DHCP '{interface.tag}' convertida")
    
    print_status("info", f"Total: {converted} configurações DHCP convertidas")
    
    return op_dhcpd


def convert_aliases(pfsense_root, opnsense_root):
    """Converte aliases (grupos de IPs/Portas)."""
    print_header("📋 ALIASES - Grupos e Listas")
    
    pf_aliases = pfsense_root.find('aliases')
    if pf_aliases is None:
        print_status("warning", "Seção 'aliases' não encontrada")
        return
    
    op_aliases = ET.SubElement(opnsense_root, 'aliases')
    
    aliases_list = pf_aliases.findall('alias')
    if not aliases_list:
        print_status("warning", "Nenhum alias encontrado")
        return
    
    converted = 0
    for alias in aliases_list:
        op_alias = ET.SubElement(op_aliases, 'alias')
        
        for child in alias:
            new_child = ET.SubElement(op_alias, child.tag)
            new_child.text = child.text
        
        converted += 1
        name = alias.find('name')
        name_text = name.text if name is not None else "unknown"
        print_status("ok", f"Alias '{name_text}' convertido")
    
    print_status("info", f"Total: {converted} aliases convertidos")
    
    return op_aliases


def convert_gateways(pfsense_root, opnsense_root):
    """Converte gateways."""
    print_header("🌐 GATEWAYS - Gateways de Rede")
    
    pf_gateways = pfsense_root.find('gateways')
    if pf_gateways is None:
        print_status("warning", "Seção 'gateways' não encontrada")
        return
    
    op_gateways = ET.SubElement(opnsense_root, 'gateways')
    
    gateway_list = pf_gateways.findall('gateway_item')
    if not gateway_list:
        print_status("warning", "Nenhum gateway encontrado")
        return
    
    converted = 0
    for gateway in gateway_list:
        op_gateway = ET.SubElement(op_gateways, 'gateway_item')
        
        # Campos compatíveis
        compatible_fields = [
            'interface', 'gateway', 'name', 'weight', 'ipprotocol',
            'interval', 'descr', 'monitor', 'monitor_disable',
            'defaultgw', 'latencylow', 'latencyhigh', 'losslow', 'losshigh'
        ]
        
        for field in compatible_fields:
            element = gateway.find(field)
            if element is not None:
                new_element = ET.SubElement(op_gateway, field)
                new_element.text = element.text
        
        converted += 1
        name = gateway.find('name')
        gw_ip = gateway.find('gateway')
        name_text = name.text if name is not None else "unknown"
        gw_text = gw_ip.text if gw_ip is not None else "N/A"
        print_status("ok", f"Gateway '{name_text}' ({gw_text}) convertido")
    
    print_status("info", f"Total: {converted} gateways convertidos")
    
    return op_gateways


def convert_static_routes(pfsense_root, opnsense_root):
    """Converte rotas estáticas."""
    print_header("🗺️  STATIC ROUTES - Rotas Estáticas")
    
    pf_routes = pfsense_root.find('staticroutes')
    if pf_routes is None:
        print_status("warning", "Seção 'staticroutes' não encontrada")
        return
    
    op_routes = ET.SubElement(opnsense_root, 'staticroutes')
    
    route_list = pf_routes.findall('route')
    if not route_list:
        print_status("warning", "Nenhuma rota estática encontrada")
        return
    
    converted = 0
    for route in route_list:
        op_route = ET.SubElement(op_routes, 'route')
        
        # Campos compatíveis
        compatible_fields = [
            'network', 'gateway', 'descr', 'disabled'
        ]
        
        for field in compatible_fields:
            element = route.find(field)
            if element is not None:
                new_element = ET.SubElement(op_route, field)
                new_element.text = element.text
        
        converted += 1
        network = route.find('network')
        gateway = route.find('gateway')
        net_text = network.text if network is not None else "unknown"
        gw_text = gateway.text if gateway is not None else "unknown"
        print_status("ok", f"Rota {net_text} via {gw_text} convertida")
    
    print_status("info", f"Total: {converted} rotas estáticas convertidas")
    
    return op_routes


def create_opnsense_config(pfsense_file):
    """Converte arquivo pfSense para OPNsense."""
    print_header("🔄 INICIANDO CONVERSÃO pfSense → OPNsense")
    
    # Ler arquivo pfSense
    try:
        tree = ET.parse(pfsense_file)
        pfsense_root = tree.getroot()
        print_status("ok", f"Arquivo pfSense carregado: {pfsense_file}")
    except Exception as e:
        print_status("error", f"Erro ao ler arquivo: {str(e)}")
        return None
    
    # Verificar se é pfSense
    version = pfsense_root.find('version')
    if version is not None:
        print_status("info", f"Versão pfSense detectada: {version.text}")
    
    # Criar estrutura OPNsense
    opnsense_root = ET.Element('opnsense')
    
    # Adicionar versão OPNsense
    version_elem = ET.SubElement(opnsense_root, 'version')
    version_elem.text = '24.1'  # Versão atual do OPNsense
    
    # Converter seções
    convert_system_section(pfsense_root, opnsense_root)
    convert_interfaces(pfsense_root, opnsense_root)
    convert_gateways(pfsense_root, opnsense_root)
    convert_static_routes(pfsense_root, opnsense_root)
    convert_firewall_rules(pfsense_root, opnsense_root)
    convert_nat_rules(pfsense_root, opnsense_root)
    convert_dhcp_server(pfsense_root, opnsense_root)
    convert_aliases(pfsense_root, opnsense_root)
    
    return opnsense_root


def save_config(root, output_file):
    """Salva configuração OPNsense."""
    try:
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        print_status("ok", f"Arquivo salvo: {output_file}")
        return True
    except Exception as e:
        print_status("error", f"Erro ao salvar: {str(e)}")
        return False


def print_final_warnings():
    """Imprime avisos finais importantes."""
    print_header("⚠️  AVISOS IMPORTANTES - LEIA COM ATENÇÃO!")
    
    warnings = [
        "BACKUP: Faça backup completo do OPNsense ANTES de importar",
        "TESTE: Este é um arquivo de BASE, não use em produção sem testar",
        "MANUAL: Você DEVE revisar e ajustar TODAS as configurações manualmente",
        "PLUGINS: Pacotes/plugins do pfSense não são compatíveis",
        "WEBGUI: Porta e protocolo da WebGUI devem ser reconfigurados",
        "CERTIFICADOS: Certificados SSL/TLS devem ser reimportados",
        "VPN: Configurações de OpenVPN/IPsec precisam revisão manual",
        "PACKAGES: Reinstale pacotes equivalentes no OPNsense",
        "FIREWALL: REVISE TODAS as regras de firewall antes de ativar",
        "NAT: Regras NAT podem precisar ajustes manuais",
        "GATEWAYS: Verifique se os gateways foram importados corretamente",
        "ROTAS: Valide todas as rotas estáticas após importação",
    ]
    
    for i, warning in enumerate(warnings, 1):
        print(f"  {YELLOW}{i:2d}.{RESET} {warning}")
    
    print(f"\n{BOLD}{RED}  ⚠️  NUNCA aplique esta configuração diretamente em produção!{RESET}")
    print(f"{BOLD}{RED}  ⚠️  Use em ambiente de TESTE primeiro!{RESET}\n")


def main():
    if len(sys.argv) < 2:
        print(f"\n{BOLD}pfSense to OPNsense Configuration Converter{RESET}")
        print(f"\n{BOLD}Uso:{RESET}")
        print(f"  python3 pfsense_to_opnsense.py <arquivo_config_pfsense.xml>")
        print(f"\n{BOLD}Exemplo:{RESET}")
        print(f"  python3 pfsense_to_opnsense.py config-backup-pfsense.xml\n")
        sys.exit(1)
    
    input_file = sys.argv[1]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"opnsense_config_{timestamp}.xml"
    
    print(f"\n{BOLD}{CYAN}╔{'═'*68}╗{RESET}")
    print(f"{BOLD}{CYAN}║  pfSense → OPNsense Configuration Converter                      ║{RESET}")
    print(f"{BOLD}{CYAN}╚{'═'*68}╝{RESET}")
    print(f"\n  {BOLD}Arquivo de entrada:{RESET} {input_file}")
    print(f"  {BOLD}Arquivo de saída:{RESET}   {output_file}")
    print(f"  {BOLD}Data/Hora:{RESET}          {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    # Converter
    opnsense_root = create_opnsense_config(input_file)
    
    if opnsense_root is None:
        print_status("error", "Falha na conversão!")
        sys.exit(1)
    
    # Salvar
    print_header("💾 SALVANDO CONFIGURAÇÃO")
    if save_config(opnsense_root, output_file):
        print_status("ok", "Conversão concluída com sucesso!")
    else:
        print_status("error", "Falha ao salvar arquivo!")
        sys.exit(1)
    
    # Avisos finais
    print_final_warnings()
    
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")


if __name__ == "__main__":
    main()
