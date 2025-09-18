import logging
from datetime import datetime
import re

class ConfluenceUploader:
    def __init__(self, client):
        self.client = client

    def upload_flow_doc(self, parent_id, name, meta):
        body = f"<h1>Flow: {name}</h1><p><strong>Label:</strong> {meta.get('label','')}</p>"
        logging.debug(f"Uploading flow {name}")
        self.client.create_or_update_page(parent_id, name, body)

    def upload_object_doc(self, parent_id, object_name, fields, meta):
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        def bool_icon(val):
            return "✅" if val else "❌"

        # --- Description + Notes sections (with markers) ---
        description_section = f"""
<h2>Description</h2>
<!-- DESC START -->
<p>{meta.get("description","") or "<i>No description available</i>"}</p>
<!-- DESC END -->
"""

        notes_section = """
<h2>Notes</h2>
<!-- NOTES START -->
<p><i>No notes yet</i></p>
<!-- NOTES END -->
"""

        # --- Metadata section ---
        record_types = meta.get("recordTypeInfos", [])
        rt_rows = []
        for rt in record_types:
            rt_rows.append(
                f"<tr><td>{rt.get('name','')}</td>"
                f"<td>{rt.get('recordTypeId','')}</td>"
                f"<td>{bool_icon(rt.get('defaultRecordTypeMapping', False))}</td></tr>"
            )
        rt_table = (
            "<table><tbody><tr><th>Name</th><th>ID</th><th>Default</th></tr>"
            + "".join(rt_rows) +
            "</tbody></table>"
        ) if rt_rows else "<p><i>No record types</i></p>"

        metadata_section = f"""
<h2>Metadata</h2>
<!-- META START -->
<table>
  <tbody>
    <tr><th>Property</th><th>Value</th></tr>
    <tr><td>Queryable</td><td>{bool_icon(meta.get('queryable', False))}</td></tr>
    <tr><td>Searchable</td><td>{bool_icon(meta.get('searchable', False))}</td></tr>
    <tr><td>Replicateable</td><td>{bool_icon(meta.get('replicateable', False))}</td></tr>
    <tr><td>Triggerable</td><td>{bool_icon(meta.get('triggerable', False))}</td></tr>
    <tr><td>Deprecated & Hidden</td><td>{bool_icon(meta.get('deprecatedAndHidden', False))}</td></tr>
    <tr><td>Layoutable</td><td>{bool_icon(meta.get('layoutable', False))}</td></tr>
    <tr><td>Record Types</td><td>{rt_table}</td></tr>
  </tbody>
</table>
<p><em>Last Updated by SF_CLI at {now_str}</em></p>
<!-- META END -->
"""

        # --- Fields section ---
        standard_fields = [f for f in fields if not f.get("custom", False)]
        custom_fields = [f for f in fields if f.get("custom", False)]

        def sort_key(f):
            required = not f.get("nillable", True)
            return (0 if required else 1, f.get("label", "").lower())

        standard_fields.sort(key=sort_key)
        custom_fields.sort(key=sort_key)

        def build_field_table(field_list):
            table = ["<table><tbody>"]
            table.append(
                "<tr><th>Label (API Name)</th><th>Type</th>"
                "<th>Length/Precision/Scale</th><th>Required</th>"
                "<th>Unique</th><th>Default</th><th>Picklist Values</th>"
                "<th>References</th><th>Help Text</th></tr>"
            )
            for f in field_list:
                length_scale = ""
                if f.get("length"):
                    length_scale = str(f.get("length"))
                elif f.get("precision") or f.get("scale"):
                    length_scale = f"{f.get('precision','')},{f.get('scale','')}"
                picklist_vals = ", ".join([p.get("value","") for p in f.get("picklistValues", [])]) if f.get("picklistValues") else ""
                refs = ", ".join(f.get("referenceTo", [])) if f.get("referenceTo") else ""
                api_name = f.get("name","")
                required_icon = bool_icon(not f.get("nillable", True))
                table.append(
                    f"<tr>"
                    f"<td><b>{f.get('label','')}</b> ({api_name})</td>"
                    f"<td>{f.get('type','')}</td>"
                    f"<td>{length_scale}</td>"
                    f"<td>{required_icon}</td>"
                    f"<td>{f.get('unique', False)}</td>"
                    f"<td>{f.get('defaultValue','')}</td>"
                    f"<td>{picklist_vals}</td>"
                    f"<td>{refs}</td>"
                    f"<td>{f.get('inlineHelpText','')}</td>"
                    f"</tr>"
                )
            table.append("</tbody></table>")
            return "\n".join(table)

        fields_section = f"""
<h2>Fields</h2>
<!-- FIELDS START -->

<h3>Standard Fields</h3>
{build_field_table(standard_fields)}

<h3>Custom Fields</h3>
{build_field_table(custom_fields)}

<p><em>Last Updated by SF_CLI at {now_str}</em></p>
<!-- FIELDS END -->
"""

        # --- Child Relationships section ---
        child_table = ["<table><tbody>"]
        child_table.append(
            "<tr><th>Child SObject</th><th>Field</th><th>Relationship Name</th>"
            "<th>Cascade Delete</th><th>Restricted Delete</th></tr>"
        )
        for cr in meta.get("childRelationships", []):
            child_table.append(
                f"<tr><td>{cr.get('childSObject','')}</td>"
                f"<td>{cr.get('field','')}</td>"
                f"<td>{cr.get('relationshipName','')}</td>"
                f"<td>{cr.get('cascadeDelete',False)}</td>"
                f"<td>{cr.get('restrictedDelete',False)}</td></tr>"
            )
        child_table.append("</tbody></table>")
        child_html = "\n".join(child_table)

        child_section = f"""
<h2>Child Relationships</h2>
<!-- CHILD START -->
{child_html}
<p><em>Last Updated by SF_CLI at {now_str}</em></p>
<!-- CHILD END -->
"""

        # --- Update existing page or create new ---
        existing_page = self.client.get_page(title=object_name, parent_id=parent_id)

        if existing_page:
            old_body = existing_page["body"]["storage"]["value"]
            new_body = old_body

            # Only add Description/Notes if missing; never overwrite if they exist
            if "<!-- DESC START -->" not in new_body:
                new_body = description_section + notes_section + new_body
            elif "<!-- NOTES START -->" not in new_body:
                desc_end = new_body.find("<!-- DESC END -->")
                if desc_end != -1:
                    before = new_body[:desc_end + len("<!-- DESC END -->")]
                    after = new_body[desc_end + len("<!-- DESC END -->"):]
                    new_body = before + notes_section + after

            # Replace Metadata
            if "<!-- META START -->" in new_body and "<!-- META END -->" in new_body:
                new_body = re.sub(
                    r"<!-- META START -->.*?<!-- META END -->",
                    metadata_section,
                    new_body,
                    flags=re.DOTALL
                )
                logging.debug(f"Updating metadata section for {object_name}")
            else:
                new_body = new_body + metadata_section

            # Replace Fields
            if "<!-- FIELDS START -->" in new_body and "<!-- FIELDS END -->" in new_body:
                new_body = re.sub(
                    r"<!-- FIELDS START -->.*?<!-- FIELDS END -->",
                    fields_section,
                    new_body,
                    flags=re.DOTALL
                )
                logging.debug(f"Updating fields section for {object_name}")
            else:
                new_body = new_body + fields_section

            # Replace Child Relationships
            if "<!-- CHILD START -->" in new_body and "<!-- CHILD END -->" in new_body:
                new_body = re.sub(
                    r"<!-- CHILD START -->.*?<!-- CHILD END -->",
                    child_section,
                    new_body,
                    flags=re.DOTALL
                )
                logging.debug(f"Updating child relationships section for {object_name}")
            else:
                new_body = new_body + child_section

            self.client.update_page(existing_page["id"], object_name, new_body)
        else:
            # Create new page with everything
            body = f"""
<h1>{object_name}</h1>
<p><strong>Label:</strong> {meta.get("label","")}</p>
<p><strong>Custom:</strong> {meta.get("custom","")}</p>
<p><strong>KeyPrefix:</strong> {meta.get("keyPrefix","")}</p>

{description_section}

{notes_section}

{metadata_section}

{fields_section}

{child_section}
"""
            self.client.create_or_update_page(parent_id=parent_id, title=object_name, body=body)
