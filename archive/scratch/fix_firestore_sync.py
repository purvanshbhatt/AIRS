import re

with open("app/db/firestore.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix sync_orgs_from_firestore
org_replacement = """                if not getattr(org, "name", None):
                    org.name = f"Unknown Org ({org_id})"
                try:
                    with db_session.begin_nested():
                        db_session.add(org)
                        db_session.flush()
                except Exception as row_exc:
                    logger.warning("Failed to insert org %s: %s", org_id, row_exc)
                    continue
            count += 1"""

content = re.sub(
    r'                db_session\.add\(org\)\n            count \+= 1',
    org_replacement,
    content,
    count=1
)

# Fix sync_assessments_from_firestore
# We will wrap the inside of the assessment doc loop with a begin_nested()
assessment_target = r"""            existing = db_session\.query\(Assessment\)\.filter\(Assessment\.id == assessment_id\)\.first\(\)
            if existing:
                assessment = existing
            else:
                assessment = Assessment\(id=assessment_id, organization_id=org_id\)
                db_session\.add\(assessment\)"""

assessment_replacement = """            try:
                with db_session.begin_nested():
                    existing = db_session.query(Assessment).filter(Assessment.id == assessment_id).first()
                    if existing:
                        assessment = existing
                    else:
                        assessment = Assessment(id=assessment_id, organization_id=org_id)
                        db_session.add(assessment)"""

content = re.sub(assessment_target, assessment_replacement, content, count=1)

# And close the try/except at the end of the loop
end_target = r"""                    db_session\.add\(f\)\n"""

end_replacement = """                    db_session.add(f)
            
            except Exception as row_exc:
                logger.warning("Failed to insert assessment %s: %s", assessment_id, row_exc)
                continue
"""

# Find the LAST match of end_target within sync_assessments_from_firestore
# It's better to just do a string replace since we know where it is
parts = content.split("db_session.add(f)")
if len(parts) >= 2:
    # the last db_session.add(f) before db_session.commit()
    content = "db_session.add(f)".join(parts[:-1]) + """db_session.add(f)
                    db_session.flush()
            except Exception as row_exc:
                logger.warning("Failed to insert assessment %s: %s", assessment_id, row_exc)
                continue""" + parts[-1]

with open("app/db/firestore.py", "w", encoding="utf-8") as f:
    f.write(content)

print("firestore.py modified!")
