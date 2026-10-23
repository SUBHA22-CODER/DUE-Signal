import pytest
from datetime import datetime, timezone, timedelta
import mcp_server.db as dbmod

@pytest.mark.asyncio
async def test_full_crud_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setenv("DUE_SIGNAL_DB", str(tmp_path / "crud.db"))
    await dbmod.init_db()

    # 1. Create
    now = datetime.now(timezone.utc)
    due1 = (now + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
    created = await dbmod.add_deadline("CS301 Lab", "CS301", due1, 20.0)
    assert created["created"] is True
    item_id = created["id"]

    # 2. Read single
    item = await dbmod.get_deadline(item_id)
    assert item is not None
    assert item["title"] == "CS301 Lab"
    assert item["status"] == "pending"

    # 3. Update (Edit)
    due_updated = (now + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M")
    upd = await dbmod.update_deadline(item_id, "CS301 Lab Revised", "CS301", due_updated, 25.0)
    assert upd["updated"] is True

    item_upd = await dbmod.get_deadline(item_id)
    assert item_upd["title"] == "CS301 Lab Revised"
    assert item_upd["weight_pct"] == 25.0

    # 4. Mark Complete
    comp = await dbmod.mark_complete(item_id)
    assert comp["status"] == "completed"

    item_comp = await dbmod.get_deadline(item_id)
    assert item_comp["status"] == "completed"

    # 5. Reopen
    reop = await dbmod.reopen_deadline(item_id)
    assert reop["status"] == "pending"

    item_reop = await dbmod.get_deadline(item_id)
    assert item_reop["status"] == "pending"

    # 6. Delete
    deld = await dbmod.delete_deadline(item_id)
    assert deld["deleted"] is True

    item_gone = await dbmod.get_deadline(item_id)
    assert item_gone is None
