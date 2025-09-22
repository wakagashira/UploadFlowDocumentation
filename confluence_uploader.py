import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfluenceUploader:
    def __init__(self, client):
        self.client = client

    # ------------------------------
    # Upload Flow Doc (unchanged)
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

        if fields:
            headers = ["Field", "Type"]
            rows = [[f.get("name", ""), f.get("type", "")] for f in fields if isinstance(f, dict)]
            table = self._build_table(headers, rows)
            content["content"].append(table)

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

        preserved_blocks = []
        try:
            page = self.client.get_page(title, parent_id)
            if page:
                raw = page.get("body", {}).get("atlas_doc_format", {}).get("value", "")
                parsed = json.loads(raw)
                # keep everything up to "Fields" heading
                for block in parsed.get("content", []):
                    preserved_blocks.append(block)
                    if block.get("type") == "heading":
                        heading_text = "".join(
                            span.get("text", "")
                            for para in block.get("content", [])
                            for span in para.get("content", [])
                            if span.get("type") == "text"
                        )
                        if heading_text == "Fields":
                            break
        except Exception as e:
            logger.warning("Could not parse existing page for %s: %s", title, e)

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

        # --- Fields section (regenerated) ---
        if fields:
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
                if f.get("type") in ["double", "currency"]:
                    length_scale = f"{f.get('precision','')},{f.get('scale','')}"
                else:
                    length_scale = str(f.get("length") or "")

                picklist_vals = ""
                if isinstance(f.get("picklistValues"), list):
                    picklist_vals = ", ".join([p.get("value", "") for p in f["picklistValues"]])

                refs = ""
                if isinstance(f.get("referenceTo"), list):
                    refs = ", ".join(f["referenceTo"])

                notes = f.get("inlineHelpText", "") or f.get("description", "")

                rows.append([
                    f"{f.get('label','')} ({f.get('name','')})",
                    f.get("type", ""),
                    length_scale,
                    "✅" if not f.get("nillable", True) else "❌",
                    "✅" if f.get("unique", False) else "❌",
                    f.get("defaultValue", ""),
                    picklist_vals,
                    refs,
                    notes,
                ])

            table = self._build_table(headers, rows)
            preserved_blocks.append(table)

        # --- Child relationships (regenerated) ---
        if isinstance(meta.get("childRelationships"), list):
            preserved_blocks.append(
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
            preserved_blocks.append(table)

        # --- Timestamp footer ---
        preserved_blocks.append(
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

        new_content = {
            "type": "doc",
            "version": 1,
            "content": preserved_blocks,
        }

        self.client.create_or_update_page(
            parent_id=parent_id,
            title=title,
            body=json.dumps(new_content),
            representation="atlas_doc_format",
        )

    # ------------------------------
    # Table Builder
    # ------------------------------
    def _build_table(self, headers, rows):
        """Build a Fabric JSON table for Confluence Cloud."""
        table = {
            "type": "table",
            "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
            "content": []
        }

        header_row = {"type": "tableRow", "content": []}
        for h in headers:
            header_row["content"].append({
                "type": "tableHeader",
                "attrs": {},
                "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": str(h)}]}
                ],
            })
        table["content"].append(header_row)

        for row in rows:
            row_obj = {"type": "tableRow", "content": []}
            for cell in row:
                row_obj["content"].append({
                    "type": "tableCell",
                    "attrs": {},
                    "content": [
                        {"type": "paragraph", "content": [{"type": "text", "text": str(cell)}]}
                    ],
                })
            table["content"].append(row_obj)

        return table
