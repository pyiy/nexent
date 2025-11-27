from fastmcp import FastMCP
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# 创建 MCP 服务
local_mcp_service = FastMCP("local")

# 数据库连接字符串
DATABASE_URL = "postgresql://postgres.vcfrtyjaokoklaebnfuh:mFL7HK2AtIcDHOQe@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"

def get_connection():
    """获取 psycopg2 数据库连接"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def format_table(rows):
    """将查询结果格式化为纯文本表格"""
    if not rows:
        return "⚠️ 查询返回为空"

    headers = list(rows[0].keys())
    # 计算每列最大宽度
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, h in enumerate(headers):
            col_widths[i] = max(col_widths[i], len(str(row[h])))

    # 构造分隔符
    sep = "+".join("-" * (w + 2) for w in col_widths)
    sep = f"+{sep}+"

    # 构造表头
    header_row = "| " + " | ".join(h.ljust(w) for h, w in zip(headers, col_widths)) + " |"

    # 构造数据行
    data_rows = []
    for row in rows:
        data_rows.append("| " + " | ".join(str(row[h]).ljust(w) for h, w in zip(headers, col_widths)) + " |")

    # 拼接表格
    table = [sep, header_row, sep] + data_rows + [sep]
    return "\n".join(table)

# 异步数据库查询工具
@local_mcp_service.tool(
    name="query_database",
    description="输入 SQL 查询数据库，返回查询结果"
)
async def query_database(sql: str, output_format: str = "table") -> str:
    """
    sql: 查询语句
    output_format: 输出格式，可选 'table' 或 'json'
    """
    conn = None
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                if cur.description:  # 查询语句
                    rows = cur.fetchall()
                    if output_format.lower() == "json":
                        return json.dumps(rows, indent=2, ensure_ascii=False)
                    else:
                        return format_table(rows)
                else:  # 非查询语句
                    return f"❌ 非查询语句，拒绝执行"
    except Exception as e:
        return f"❌ 执行出错: {e}"
    finally:
        if 'conn' in locals():
            conn.close()

# 示例测试工具
@local_mcp_service.tool(
    name="demo_tool",
    description="测试工具示例"
)
async def demo_tool(para_1: str, para_2: int) -> str:
    print("demo_tool 被调用")
    print("para_1:", para_1)
    print("para_2:", para_2)
    return "success"

# 启动 MCP 服务
if __name__ == "__main__":
    local_mcp_service.run()
