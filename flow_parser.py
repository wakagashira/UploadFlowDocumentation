import xml.etree.ElementTree as ET
import re

def strip_ns(tag):
    """Remove namespace from tag like {http://soap...}decisions -> decisions"""
    return re.sub(r"^\{.*\}", "", tag)

def parse_flow_file(file_path):
    """Parse a .flow-meta.xml file into structured info"""
    tree = ET.parse(file_path)
    root = tree.getroot()

    flow_data = {
        "file": file_path,
        "label": "",
        "apiName": "",
        "processType": "",
        "status": "",
        "description": "",
        "elements": []
    }

    # Tags that represent flow "elements"
    element_tags = [
        "actionCalls", "assignments", "decisions", "recordCreates",
        "recordLookups", "recordUpdates", "recordDeletes",
        "screens", "loops", "subflows"
    ]

    for child in root:
        tag = strip_ns(child.tag)

        if tag == "label":
            flow_data["label"] = child.text or ""
        elif tag == "apiVersion":
            flow_data["apiName"] = child.text or ""
        elif tag == "processType":
            flow_data["processType"] = child.text or ""
        elif tag == "status":
            flow_data["status"] = child.text or ""
        elif tag == "description":
            flow_data["description"] = child.text or ""
        elif tag in element_tags:
            # Parse element details manually
            name = ""
            label = ""
            for e in child:
                etag = strip_ns(e.tag)
                if etag == "name":
                    name = e.text or ""
                elif etag == "label":
                    label = e.text or ""
            elem_data = {"name": name, "type": tag, "label": label}
            flow_data["elements"].append(elem_data)

    return flow_data
