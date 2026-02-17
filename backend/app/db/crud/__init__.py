"""CRUD operations for all business entities.

This module re-exports all CRUD functions for backward compatibility.
Individual entity modules can also be imported directly.
"""

from app.db.crud.todo import (
    create_todo,
    get_todo,
    get_todos,
    update_todo,
    delete_todo,
    get_todos_by_urgency_importance,
    get_unclassified_todos,
    get_todos_by_project,
    count_active_todos_for_project,
    get_distinct_tags,
)

from app.db.crud.knowledge import (
    create_knowledge,
    get_knowledge,
    get_knowledges,
    update_knowledge,
    delete_knowledge,
    get_knowledge_by_uri,
)

from app.db.crud.task_plan import (
    create_task_plan,
    get_task_plan,
    get_task_plan_by_todo_id,
    update_task_plan,
    upsert_task_plan,
    delete_task_plan,
)

from app.db.crud.organization import (
    create_organization,
    get_organization,
    get_organizations,
    update_organization,
    delete_organization,
    get_organization_by_name,
)

from app.db.crud.project import (
    create_project,
    get_project,
    get_projects,
    update_project,
    delete_project,
    get_project_by_name_and_organization,
)

from app.db.crud.slp_assessment import (
    create_slp_assessment,
    get_slp_assessment,
    get_slp_assessments,
    update_slp_assessment,
    delete_slp_assessment,
)

from app.db.crud.meeting import (
    create_meeting_ref,
    get_meeting_ref,
    get_meeting_ref_by_meeting_id,
    get_meeting_refs,
    update_meeting_ref,
    delete_meeting_ref,
    get_meeting_refs_by_project,
    get_meeting_refs_by_organization,
)

from app.db.crud.asset import (
    create_asset,
    get_asset,
    get_assets,
    update_asset,
    delete_asset,
    get_assets_by_project,
    get_assets_by_todo,
)

from app.db.crud.person import (
    create_person,
    get_person,
    get_persons,
    update_person,
    delete_person,
    get_persons_by_project,
    get_persons_by_organization,
)

__all__ = [
    # Todo
    "create_todo",
    "get_todo",
    "get_todos",
    "update_todo",
    "delete_todo",
    "get_todos_by_urgency_importance",
    "get_unclassified_todos",
    "get_todos_by_project",
    "count_active_todos_for_project",
    "get_distinct_tags",
    # Knowledge
    "create_knowledge",
    "get_knowledge",
    "get_knowledges",
    "update_knowledge",
    "delete_knowledge",
    "get_knowledge_by_uri",
    # TaskPlan
    "create_task_plan",
    "get_task_plan",
    "get_task_plan_by_todo_id",
    "update_task_plan",
    "upsert_task_plan",
    "delete_task_plan",
    # Organization
    "create_organization",
    "get_organization",
    "get_organizations",
    "update_organization",
    "delete_organization",
    "get_organization_by_name",
    # Project
    "create_project",
    "get_project",
    "get_projects",
    "update_project",
    "delete_project",
    "get_project_by_name_and_organization",
    # SLP Assessment
    "create_slp_assessment",
    "get_slp_assessment",
    "get_slp_assessments",
    "update_slp_assessment",
    "delete_slp_assessment",
    # MeetingRef
    "create_meeting_ref",
    "get_meeting_ref",
    "get_meeting_ref_by_meeting_id",
    "get_meeting_refs",
    "update_meeting_ref",
    "delete_meeting_ref",
    "get_meeting_refs_by_project",
    "get_meeting_refs_by_organization",
    # Asset
    "create_asset",
    "get_asset",
    "get_assets",
    "update_asset",
    "delete_asset",
    "get_assets_by_project",
    "get_assets_by_todo",
    # Person
    "create_person",
    "get_person",
    "get_persons",
    "update_person",
    "delete_person",
    "get_persons_by_project",
    "get_persons_by_organization",
]

