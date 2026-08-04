import os
import re

file_path = r"C:\Users\husey\kiro2\backend\api\diary_api.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add imports
imports_to_add = """from core.cqrs.bus import CommandBus, get_command_bus
from application.commands.diary import (
    CreateSummaryCommand, UpdateSummaryCommand, DeleteSummaryCommand,
    CreateGoalCommand, UpdateGoalCommand, UpdateGoalProgressCommand, AdjustGoalCommand, CreateGoalRetrospectiveCommand, DeleteGoalCommand,
    AnalyzeEntriesForInsightsCommand, DeleteInsightCommand,
    CreateReflectionCommand, CreateLearningEntryCommand, RecordReviewCommand, LinkConceptsCommand,
    TrackEmotionalStateCommand, CreateExportCommand, CreateShareLinkCommand, CreateEncryptedBackupCommand
)
"""

if "from core.cqrs.bus import CommandBus" not in content:
    content = content.replace("from core.database import get_async_session", 
                              imports_to_add + "\nfrom core.database import get_async_session")


def replace_endpoint_body(content, endpoint_start, command_name, args_mapping):
    # Find the function definition
    pattern = re.compile(rf"({endpoint_start}[\s\S]*?)(?=\n\n|\Z)")
    match = pattern.search(content)
    if not match:
        print(f"Failed to find {endpoint_start}")
        return content
        
    func_text = match.group(1)
    
    # We replace everything after docstring
    # Find docstring end
    doc_end = func_text.find('"""\n', func_text.find('"""') + 3)
    if doc_end == -1:
        doc_end = func_text.find('"""', func_text.find('"""') + 3)
        
    if doc_end != -1:
        doc_end += 4
        
        indent = "    "
        new_body = f"{indent}command = {command_name}({args_mapping})\n"
        new_body += f"{indent}command_bus = get_command_bus()\n"
        new_body += f"{indent}return await command_bus.execute(command)"
        
        new_func = func_text[:doc_end] + "\n" + new_body
        
        # In the function signature, we also need to add command_bus dependency if we wanted, 
        # but using `get_command_bus()` directly inside the function is also fine, as `auth.py` does.
        
        return content.replace(func_text, new_func)
    return content


content = replace_endpoint_body(content, r"@router.post\(\"/summary\"", "CreateSummaryCommand", "request=request, persist_file=persist_file, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.put\(\"/summary/{entry_id}\"", "UpdateSummaryCommand", "entry_id=entry_id, request=request, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.delete\(\"/summary/{entry_id}\"", "DeleteSummaryCommand", "entry_id=entry_id, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.post\(\"/goals\"", "CreateGoalCommand", "request=request, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.put\(\"/goals/{goal_id}\"", "UpdateGoalCommand", "goal_id=goal_id, request=request, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.patch\(\"/goals/{goal_id}/progress\"", "UpdateGoalProgressCommand", "goal_id=goal_id, request=request, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.post\(\"/goals/{goal_id}/adjust\"", "AdjustGoalCommand", "goal_id=goal_id, reason=reason, new_target_value=new_target_value, new_target_date=new_target_date, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.post\(\"/goals/{goal_id}/retrospective\"", "CreateGoalRetrospectiveCommand", "goal_id=goal_id, lessons_learned=lessons_learned, success_factors=success_factors, challenges_faced=challenges_faced, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.delete\(\"/goals/{goal_id}\"", "DeleteGoalCommand", "goal_id=goal_id, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.post\(\"/insights/analyze\"", "AnalyzeEntriesForInsightsCommand", "start_date=start_date, end_date=end_date, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.delete\(\"/insights/{insight_id}\"", "DeleteInsightCommand", "insight_id=insight_id, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.post\(\"/reflection\"", "CreateReflectionCommand", "request=request, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.post\(\"/learning\"", "CreateLearningEntryCommand", "request=request, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.post\(\"/learning/{entry_id}/review\"", "RecordReviewCommand", "entry_id=entry_id, remembered=remembered, quality=quality, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.post\(\"/learning/{entry_id}/link\"", "LinkConceptsCommand", "entry_id=entry_id, concepts=concepts, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.post\(\"/emotional\"", "TrackEmotionalStateCommand", "request=request, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.post\(\"/export\"", "CreateExportCommand", "request=request, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.post\(\"/export/share\"", "CreateShareLinkCommand", "request=request, user_id=current_user.id, db=db")
content = replace_endpoint_body(content, r"@router.post\(\"/backup/encrypted\"", "CreateEncryptedBackupCommand", "password=password, user_id=current_user.id, db=db")


with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
