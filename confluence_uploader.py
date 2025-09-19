import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ConfluenceUploader:
    def __init__(self, client):
        self.client = client

    # ------------------------------
    # Upload Flow Doc
    # ------------------------------
    def upload_flow_doc(self, parent_id, flow_name, label, status, process_type, fields):
        title = f"{flow_name}.flow-meta"

        logger.debug("Building Fabric JSON for flow %s", title)
        content = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 1},
                    "content": [{"type": "text", "text": f"Flow: {flow_name}"}],
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Label: ", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": label or ""},
                    ],
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Status: ", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": status or ""},
                    ],
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Process Type: ", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": process_type or ""},
                    ],
                },
            ],
        }

        # Add fields table if present
        if fields:
            headers = ["Field", "Type"]
            rows = [[f.get("name", ""), f.get("type", "")] for f in fields if isinstance(f, dict)]
            table = self._build_table(headers, rows)
            content["content"].append(table)

        # Footer
        content["content"].append(
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": f"Last Updated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        "marks": [{"type": "em"}],
                    }
                ],
            }
        )

        self.client.create_or_update_page(
            parent_id=parent_id,
            title=title,
            body=json.dumps(content),
            representation="atlas_doc_format",
        )

    # ------------------------------
    # Upload Object Doc
    # ------------------------------
    def upload_object_doc(self, parent_id, object_name, fields, meta):
        title = object_name

        # --- Normalize fields ---
        if not isinstance(fields, list):
            fields = []
        else:
            new_fields = []
            for f in fields:
                if isinstance(f, dict):
                    new_fields.append(f)
                else:
                    new_fields.append({"name": str(f), "label": str(f)})
            fields = new_fields

        # --- Normalize meta ---
        if not isinstance(meta, dict):
            meta = {}
        if not isinstance(meta.get("childRelationships"), list):
            meta["childRelationships"] = []
        if not isinstance(meta.get("recordTypeInfos"), list):
            meta["recordTypeInfos"] = []

        logger.debug("Building Fabric JSON for object %s", title)
        content = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 1},
                    "content": [{"type": "text", "text": f"Object: {object_name}"}],
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Label: ", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": meta.get("label", "")},
                    ],
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Custom: ", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": str(meta.get("custom", ""))},
                    ],
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "KeyPrefix: ", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": meta.get("keyPrefix", "")},
                    ],
                },
            ],
        }

        # Fields
        if fields:
            content["content"].append(
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": "Fields"}],
                }
            )

            headers = [
                "Label (API Name)",
                "Type",
                "Length/Precision/Scale",
                "Required",
                "Unique",
                "Default",
                "Picklist Values",
                "References",
                "Help Text",
            ]
            rows = []

            for f in sorted(fields, key=lambda x: x.get("label", "")):
                # Length/Precision/Scale
                if f.get("type") in ["double", "currency"]:
                    length_scale = f"{f.get('precision','')},{f.get('scale','')}"
                else:
                    length_scale = str(f.get("length") or "")

                # Picklist
                picklist_vals = ""
                if isinstance(f.get("picklistValues"), list):
                    picklist_vals = ", ".join([p.get("value", "") for p in f["picklistValues"]])

                # References
                refs = ""
                if isinstance(f.get("referenceTo"), list):
                    refs = ", ".join(f["referenceTo"])

                rows.append([
                    f"{f.get('label','')} ({f.get('name','')})",
                    f.get("type", ""),
                    length_scale,
                    "✅" if not f.get("nillable", True) else "❌",
                    "✅" if f.get("unique", False) else "❌",
                    f.get("defaultValue", ""),
                    picklist_vals,
                    refs,
                    f.get("inlineHelpText", ""),
                ])

            table = self._build_table(headers, rows)
            content["content"].append(table)

        # Child relationships
        if isinstance(meta.get("childRelationships"), list):
            content["content"].append(
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": "Child Relationships"}],
                }
            )

            headers = [
                "Child SObject",
                "Field",
                "Relationship Name",
                "Cascade Delete",
                "Restricted Delete",
            ]
            rows = []
            for cr in meta["childRelationships"]:
                rows.append([
                    cr.get("childSObject", ""),
                    cr.get("field", ""),
                    cr.get("relationshipName", ""),
                    "✅" if cr.get("cascadeDelete") else "❌",
                    "✅" if cr.get("restrictedDelete") else "❌",
                ])

            table = self._build_table(headers, rows)
            content["content"].append(table)

        # Footer
        content["content"].append(
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": f"Last Updated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        "marks": [{"type": "em"}],
                    }
                ],
            }
        )

        self.client.create_or_update_page(
            parent_id=parent_id,
            title=title,
            body=json.dumps(content),
            representation="atlas_doc_format",
        )

    # ------------------------------
    # Helper: Build Table
    # ------------------------------
    def _build_table(self, headers, rows):
        table = {"type": "table", "attrs": {"layout": "default"}, "content": []}

        # Header row
        header_row = {"type": "tableRow", "content": []}
        for h in headers:
            header_row["content"].append(
                {
                    "type": "tableHeader",
                    "attrs": {"colspan": 1, "rowspan": 1},
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": h}]}],
                }
            )
        table["content"].append(header_row)

        # Data rows
        for r in rows:
            row_node = {"type": "tableRow", "content": []}
            for cell in r:
                row_node["content"].append(
                    {
                        "type": "tableCell",
                        "attrs": {"colspan": 1, "rowspan": 1},
                        "content": [{"type": "paragraph", "content": [{"type": "text", "text": str(cell)}]}],
                    }
                )
            table["content"].append(row_node)

        return table
