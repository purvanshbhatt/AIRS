import os

def fix_firestore():
    with open("app/db/firestore.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_lines = []
    in_org_loop = False
    in_assessment_loop = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Org sync logic fix
        if line.startswith("                db_session.add(org)"):
            if "if not getattr(org, \"name\", None):" not in lines[i-1]:
                new_lines.append('                if not getattr(org, "name", None):\n')
                new_lines.append('                    org.name = f"Unknown Org ({org_id})"\n')
                new_lines.append('                try:\n')
                new_lines.append('                    with db_session.begin_nested():\n')
                new_lines.append('                        db_session.add(org)\n')
                new_lines.append('                        db_session.flush()\n')
                new_lines.append('                except Exception as row_exc:\n')
                new_lines.append('                    logger.warning("Failed to insert org %s: %s", org_id, row_exc)\n')
                new_lines.append('                    continue\n')
                i += 1
                continue
                
        # Assessment sync logic fix
        if line.startswith("            existing = db_session.query(Assessment).filter(Assessment.id == assessment_id).first()"):
            new_lines.append('            try:\n')
            new_lines.append('                with db_session.begin_nested():\n')
            new_lines.append('                    ' + line.lstrip())
            in_assessment_loop = True
            i += 1
            continue
            
        if in_assessment_loop:
            # We are inside the rest of the loop.
            # We need to indent every line by 4 spaces.
            # until we hit "            restored += 1"
            if line.startswith("            restored += 1"):
                # end of the loop block
                new_lines.append('                    db_session.flush()\n')
                new_lines.append('            except Exception as row_exc:\n')
                new_lines.append('                logger.warning("Failed to insert assessment %s: %s", assessment_id, row_exc)\n')
                new_lines.append('                continue\n')
                new_lines.append(line)
                in_assessment_loop = False
                i += 1
                continue
            elif line.strip() == "":
                new_lines.append("\n")
            else:
                new_lines.append("    " + line)
            i += 1
            continue
            
        new_lines.append(line)
        i += 1
        
    with open("app/db/firestore.py", "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    print("firestore.py modified successfully!")

fix_firestore()
