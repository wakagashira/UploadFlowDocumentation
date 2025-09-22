import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfluenceUploader:
    def __init__(self, client):
        self.client = client

    # ---- utils ----
    def _flatten_text(self, node):
        """Recursively collect all 'text' from a Fabric JSON node."""
        out = []
        def walk(n):
            if isinstance(n, dict):
                if n.get("type") == "text" and "text" in n:
                    out.append(n["text"])
                for child in n.get("content", []) or []:
                    walk(child)
            elif isinstance(n, list):
                for child in n:
                    walk(child)
        walk(node)
        return "".join(out)

    def _get_heading_text(self, heading_block):
        txt = self._flatten_text(heading_block).strip()
        return " ".join(txt.split())  # normalize spaces

    # ------------------------------
    # Upload Object Doc
    # ------------------------------
    def upload_object_doc(self, parent_id, object_name, fields, meta):
        title = object_name
        preserved_blocks = []
        page_found = False
        fields_found = False

        try:
            page = self.client.get_page(title, parent_id)
            if page:
                page_found = True
                raw = page.get("body", {}).get("atlas_doc_format", {}).get("value", "")
                if raw:
                    parsed = json.loads(raw)
                    for block in parsed.get("content", []):
                        if block.get("type") == "heading":
                            heading_text = self._get_heading_text(block)
                            if heading_text.lower().startswith("fields"):
                                fields_found = True
                                break  # stop before old Fields and below
                        preserved_blocks.append(block)
        except Exception as e:
            logger.warning("Could not parse existing page for %s: %s", title, e)

        # If no preserved blocks (new page), create default top headers
        if not page_found or not preserved_blocks:
            preserved_blocks = [
                {"type": "heading", "attrs": {"level": 1},
                 "content": [{"type": "text", "text": f"Object: {object_name}"}]},
                {"type": "paragraph", "content": [
                    {"type": "text", "text": "Label: ", "marks": [{"type": "strong"}]},
                    {"type": "text", "text": meta.get("label", "")}]},
                {"type": "paragraph", "content": [
                    {"type": "text", "text": "Custom: ", "marks": [{"type": "strong"}]},
                    {"type": "text", "text": str(meta.get("custom", ""))}]},
                {"type": "paragraph", "content": [
                    {"type": "text", "text": "KeyPrefix: ", "marks": [{"type": "strong"}]},
                    {"type": "text", "text": meta.get("keyPrefix", "")}]},
                {"type": "heading", "attrs": {"level": 2},
                 "content": [{"type": "text", "text": "Description"}]},
                {"type": "paragraph", "content": [
                    {"type": "text", "text": meta.get("description", "")}]},
                {"type": "heading", "attrs": {"level": 2},
                 "content": [{"type": "text", "text": "Description Notes"}]},
                {"type": "paragraph", "content": [{"type": "text", "text": ""}]},
                {"type": "heading", "attrs": {"level": 2},
                 "content": [{"type": "text", "text": "Custom Notes"}]},
                {"type": "paragraph", "content": [{"type": "text", "text": ""}]},
            ]

        # --- Fresh Fields section ---
        if fields:
            preserved_blocks.append(
                {"type": "heading", "attrs": {"level": 2},
                 "content": [{"type": "text", "text": "Fields"}]}
            )
            headers = ["Label (API Name)", "Type", "Length/Precision/Scale",
                       "Required", "Unique", "Default", "Picklist Values",
                       "References", "Help Text"]
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
                    f.get("type", ""), length_scale,
                    "✅" if not f.get("nillable", True) else "❌",
                    "✅" if f.get("unique", False) else "❌",
                    f.get("defaultValue", ""), picklist_vals, refs, notes
                ])
            table = self._build_table(headers, rows)
            preserved_blocks.append(table)

        # --- Fresh Child Relationships ---
        if isinstance(meta.get("childRelationships"), list):
            preserved_blocks.append(
                {"type": "heading", "attrs": {"level": 2},
                 "content": [{"type": "text", "text": "Child Relationships"}]}
            )
            headers = ["Child SObject", "Field", "Relationship Name",
                       "Cascade Delete", "Restricted Delete"]
            rows = []
            for cr in meta["childRelationships"]:
                rows.append([
                    cr.get("childSObject", ""), cr.get("field", ""),
                    cr.get("relationshipName", ""),
                    "✅" if cr.get("cascadeDelete") else "❌",
                    "✅" if cr.get("restrictedDelete") else "❌"
                ])
            table = self._build_table(headers, rows)
            preserved_blocks.append(table)

        # --- Fresh Validation Rules ---
        if isinstance(meta.get("validationRules"), list) and meta["validationRules"]:
            preserved_blocks.append(
                {"type": "heading", "attrs": {"level": 2},
                 "content": [{"type": "text", "text": "Validation Rules"}]}
            )
            headers = ["Name", "Description", "Error Condition Formula", "Error Message"]
            rows = []
            for r in meta["validationRules"]:
                rows.append([
                    r.get("fullName", ""), r.get("description", ""),
                    r.get("errorConditionFormula", ""), r.get("errorMessage", "")
                ])
            table = self._build_table(headers, rows)
            preserved_blocks.append(table)

        # --- Timestamp footer ---
        preserved_blocks.append(
            {"type": "paragraph", "content": [
                {"type": "text",
                 "text": f"Last Updated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                 "marks": [{"type": "em"}]}]}
        )

        new_content = {"type": "doc", "version": 1, "content": preserved_blocks}
        self.client.create_or_update_page(
            parent_id=parent_id, title=title,
            body=json.dumps(new_content), representation="atlas_doc_format"
        )

    # ------------------------------
    # Table Builder
    # ------------------------------
    def _build_table(self, headers, rows):
        table = {"type": "table",
                 "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
                 "content": []}
        header_row = {"type": "tableRow", "content": []}
        for h in headers:
            header_row["content"].append({
                "type": "tableHeader", "attrs": {},
                "content": [{"type": "paragraph",
                             "content": [{"type": "text", "text": str(h)}]}]
            })
        table["content"].append(header_row)
        for row in rows:
            row_obj = {"type": "tableRow", "content": []}
            for cell in row:
                row_obj["content"].append({
                    "type": "tableCell", "attrs": {},
                    "content": [{"type": "paragraph",
                                 "content": [{"type": "text", "text": str(cell)}]}]
                })
            table["content"].append(row_obj)
        return table
