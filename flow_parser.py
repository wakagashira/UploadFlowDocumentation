import xml.etree.ElementTree as ET

def parse_flow_file(file_path):
    """Parse a .flow-meta.xml file into structured info"""
    tree = ET.parse(file_path)
    root = tree.getroot()
    ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}

    flow_data = {
        "file": file_path,
        "label": root.findtext("sf:label", default="", namespaces=ns),
        "apiName": root.findtext("sf:apiVersion", default="", namespaces=ns),
        "processType": root.findtext("sf:processType", default="", namespaces=ns),
        "status": root.findtext("sf:status", default="", namespaces=ns),
        "description": root.findtext("sf:description", default="", namespaces=ns),
        "elements": []
    }

    for elem in root.findall("sf:elements", ns):
        flow_data["elements"].append({
            "name": elem.findtext("sf:name", default="", namespaces=ns),
            "type": elem.findtext("sf:type", default="", namespaces=ns),
            "label": elem.findtext("sf:label", default="", namespaces=ns),
        })

    return flow_data
