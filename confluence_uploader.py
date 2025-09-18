import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfluenceUploader:
    def __init__(self, client):
        self.client = client

    #
    # ---- Helper builders for Fabric JSON ----
    #
    def heading(self, text, level=2):
        return {"type": "heading", "attrs": {"level": level}, "content": [{"type": "text", "text": text}]}

    def paragraph(self, text, italic=False, bold=False):
        marks = []
        if italic:
            marks.append({"type": "em"})
        if bold:
            marks.append({"type": "strong"})
        node = {"type": "text", "text": text}
        if marks:
            node["marks"] = marks
        return {"type": "paragraph", "content": [node]}

    def table(self, headers, rows):
        table_node = {"type": "table", "content": []}
        # header row
        header_cells = [{"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": h}]}]} for h in headers]
        table_node["content"].append({"type": "tableRow", "content": header_cells})
        # data rows
        for row in rows:
            cells = []
            for cell in row:
                cell_content = {"type": "paragraph", "content": []}
                if cell:
                    cell_content["content"].append({"type": "text", "text": str(cell)})
                cells.append({"type": "tableCell", "content": [cell_content]})
            table_node["content"].append({"type": "tableRow", "content": cells})
        return table_node

    #
    # ---- Main upload function ----
    #
    def upload_object_doc(self, parent_id, object_name, fields, meta):
        # Step 1: fetch existing page
        existing_page = self.client.get_page(object_name, parent_id)

        # Step 2: parse existing Fabric doc or start new
        if existing_page and "body" in existing_page and "atlas_doc_format" in existing_page["body"]:
            try:
                atlas_doc = json.loads(existing_page["body"]["atlas_doc_format"]["value"])
                logger.debug("Parsed existing atlas_doc_format JSON")
            except Exception:
                atlas_doc = {"type": "doc", "version": 1, "content": []}
        else:
            atlas_doc = {"type": "doc", "version": 1, "content": []}

        content = atlas_doc.get("content", [])

        #
        # Step 3: build Metadata, Fields, Child Relationships
        #
        # Metadata table
        meta_headers = ["Property", "Value"]
        meta_rows = [
            ["Queryable", "✅" if meta.get("queryable") else "❌"],
            ["Searchable", "✅" if meta.get("searchable") else "❌"],
            ["Replicateable", "✅" if meta.get("replicateable") else "❌"],
            ["Triggerable", "✅" if meta.get("triggerable") else "❌"],
            ["Deprecated & Hidden", "✅" if meta.get("deprecatedAndHidden") else "❌"],
            ["Layoutable", "✅" if meta.get("layoutable") else "❌"],
        ]
        rt_infos = meta.get("recordTypeInfos", [])
        if rt_infos:
            rt_table = self.table(
                ["Name", "ID", "Default"],
                [[r.get("name"), r.get("recordTypeId"), "✅" if r.get("defaultRecordTypeMapping") else "❌"] for r in rt_infos],
            )
            meta_rows.append(["Record Types", "See below"])
        metadata_nodes = [self.heading("Metadata", 2), self.table(meta_headers, meta_rows)]
        if rt_infos:
            metadata_nodes.append(rt_table)

        # Fields table
        field_headers = ["Label (API Name)", "Type", "Length/Precision/Scale", "Required", "Unique", "Default", "Picklist Values", "References", "Help Text"]
        field_rows = []
        for f in sorted(fields, key=lambda x: x.get("label", "")):
            length_scale = f.get("length") or (f"{f.get('precision','')},{f.get('scale','')}" if f.get("precision") or f.get("scale") else "")
            picklist_vals = ", ".join([p.get("value","") for p in f.get("picklistValues", [])]) if f.get("picklistValues") else ""
            refs = ", ".join(f.get("referenceTo", [])) if f.get("referenceTo") else ""
            field_rows.append([
                f"{f.get('label','')} ({f.get('name','')})",
                f.get("type",""),
                length_scale,
                "✅" if not f.get("nillable", True) else "❌",
                "✅" if f.get("unique", False) else "❌",
                f.get("defaultValue",""),
                picklist_vals,
                refs,
                f.get("inlineHelpText","")
            ])
        fields_nodes = [self.heading("Fields", 2), self.table(field_headers, field_rows)]

        # Child Relationships table
        cr_headers = ["Child SObject", "Field", "Relationship Name", "Cascade Delete", "Restricted Delete"]
        cr_rows = []
        for cr in meta.get("childRelationships", []):
            cr_rows.append([
                cr.get("childSObject",""),
                cr.get("field",""),
                cr.get("relationshipName",""),
                "✅" if cr.get("cascadeDelete",False) else "❌",
                "✅" if cr.get("restrictedDelete",False) else "❌"
            ])
        child_nodes = [self.heading("Child Relationships", 2), self.table(cr_headers, cr_rows)]

        #
        # Step 4: rebuild doc with preserved Description/Notes
        #
        new_content = []
        has_desc = any(n for n in content if n.get("type")=="heading" and n["content"][0]["text"]=="Description")
        has_notes = any(n for n in content if n.get("type")=="heading" and n["content"][0]["text"]=="Notes")

        # Always keep top title
        new_content.append(self.heading(object_name, 1))
        new_content.append(self.paragraph(f"Label: {meta.get('label','')}", bold=True))
        new_content.append(self.paragraph(f"Custom: {meta.get('custom','')}"))
        new_content.append(self.paragraph(f"KeyPrefix: {meta.get('keyPrefix','')}"))

        # Description
        if has_desc:
            # keep existing description section
            desc_index = next(i for i,n in enumerate(content) if n.get("type")=="heading" and n["content"][0]["text"]=="Description")
            new_content.extend(content[desc_index:desc_index+2])
        else:
            new_content.append(self.heading("Description", 2))
            new_content.append(self.paragraph("No description available", italic=True))

        # Notes
        if has_notes:
            notes_index = next(i for i,n in enumerate(content) if n.get("type")=="heading" and n["content"][0]["text"]=="Notes")
            new_content.extend(content[notes_index:notes_index+2])
        else:
            new_content.append(self.heading("Notes", 2))
            new_content.append(self.paragraph("No notes yet", italic=True))

        # Always refresh Metadata, Fields, Child Relationships
        new_content.extend(metadata_nodes)
        new_content.extend(fields_nodes)
        new_content.extend(child_nodes)

        # Add last updated
        new_content.append(self.paragraph(f"Last Updated by SF_CLI at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", italic=True))

        atlas_doc["content"] = new_content
        atlas_json = json.dumps(atlas_doc)

        # Step 5: update/create page in Fabric format
        self.client.create_or_update_page(
            parent_id=parent_id,
            title=object_name,
            body=json.dumps({
                "type": "doc",
                "version": 1,
                "content": new_content
            })
        )
