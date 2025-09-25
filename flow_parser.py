import os
import re
import xml.etree.ElementTree as ET

def _strip_ns(tag: str) -> str:
    return re.sub(r"^\{.*\}", "", tag or "")

def _text(node) -> str:
    return (node.text or "").strip() if node is not None else ""

def parse_flow_file(file_path: str) -> dict:
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Derive DeveloperName from filename (before ".flow-meta.xml")
    base = os.path.basename(file_path)
    developer_name = base.split(".flow-meta.xml")[0]

    flow = {
        "file": file_path,
        "label": "",
        "developerName": developer_name,
        "apiVersion": "",          # correct field name (was mis-shown as API Name)
        "processType": "",
        "status": "",
        "description": "",
        "elements": [],            # [{type, label, name, object, field?}]
        "objects": set(),
        "fields": set(),
    }

    # Parse top-level metadata
    for child in root:
        tag = _strip_ns(child.tag)
        if tag == "label":
            flow["label"] = _text(child)
        elif tag == "apiVersion":
            flow["apiVersion"] = _text(child)
        elif tag == "processType":
            flow["processType"] = _text(child)
        elif tag == "status":
            flow["status"] = _text(child)
        elif tag == "description":
            flow["description"] = _text(child)

    # Tags that represent flow elements (common set)
    element_tags = {
        "actionCalls", "assignments", "decisions",
        "recordCreates", "recordLookups", "recordUpdates", "recordDeletes",
        "screens", "loops", "subflows"
    }

    # Walk children and collect element info + object/field refs
    for elem in root:
        etag = _strip_ns(elem.tag)
        if etag in element_tags:
            name, label, obj = "", "", ""
            # Scan direct children for common properties
            for c in elem:
                ctag = _strip_ns(c.tag)
                val = _text(c)
                if ctag == "name":
                    name = val
                elif ctag == "label":
                    label = val
                elif ctag in ("object", "sObject"):
                    obj = val
                    if val:
                        flow["objects"].add(val)

            # Deep scan descendants to collect any field-ish nodes
            # (handles <field>, <fieldApiName>, <targetField>, etc.)
            for d in elem.iter():
                dtag = _strip_ns(d.tag).lower()
                dval = _text(d)
                if not dval:
                    continue
                # Collect fields if tag name includes "field" but ignore non-field metadata
                if ("field" in dtag) and dtag not in {"fieldtype", "fieldset", "fieldvalues"}:
                    flow["fields"].add(dval)
                # Also collect any extra object references we might encounter
                if dtag in {"object", "sobject"}:
                    flow["objects"].add(dval)

            flow["elements"].append({
                "type": etag,
                "label": label,
                "name": name,
                "object": obj
            })

    # Normalize for JSON
    flow["objects"] = sorted(flow["objects"])
    flow["fields"]  = sorted(flow["fields"])
    return flow
