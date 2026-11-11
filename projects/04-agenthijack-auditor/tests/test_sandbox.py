from agenthijack.engine.sandbox import ToolSandbox
from agenthijack.models import SecurityPolicyMode, ToolCall


def test_sandbox_executes_valid_call():
    sandbox = ToolSandbox()
    call = ToolCall(
        tool_name="run_sql_query",
        arguments={"query": "SELECT count(*) FROM employees"},
    )
    res = sandbox.execute_call(call, SecurityPolicyMode.STRICT_LEAST_PRIVILEGE)
    assert res.success is True
    assert res.output["rows"][0][0] == 3


def test_sandbox_rejects_unknown_tool():
    sandbox = ToolSandbox()
    call = ToolCall(
        tool_name="unregistered_tool",
        arguments={"action": "test"},
    )
    res = sandbox.execute_call(call)
    assert res.success is False
    assert "NoSuchToolError" in (res.error or "")
