"""安全數學運算工具模組 / Safe Arithmetic Evaluation Tool Module.

[正體中文]
本模組提供安全的四則運算與數學表達式求值功能：
【初學者必讀資安觀念】
在 Python 中，千萬不要使用內建的 `eval()` 來計算使用者或模型傳入的數學算式！
因為 `eval()` 會直接執行任意 Python 程式碼，例如 `eval("__import__('os').system('rm -rf /')")`，
將導致嚴重的遠端程式碼執行（Remote Code Execution, RCE）安全漏洞。

本模組使用 Python 的抽象語法樹（Abstract Syntax Tree, AST），僅白名單允許基礎數值與安全運算子
（加、減、乘、除、整除、取餘數、次方），嚴格禁止變數存取、函數呼叫與模組載入，確保 100% 安全。

[English]
This module provides safe arithmetic expression evaluation:
[Important Security Note for Beginners]
Never use Python's built-in `eval()` to calculate math expressions provided by users or LLMs!
`eval()` executes arbitrary Python code and introduces Remote Code Execution (RCE) vulnerabilities.

Instead, this module uses Python's Abstract Syntax Tree (`ast`) to safely evaluate expressions
by strictly whitelisting arithmetic operators and numerical constants, completely prohibiting
function calls, imports, and variable references.
"""

import ast
import operator
from collections.abc import Callable


# [正體中文] 定義運算子函數型別別名
# [English] Type aliases for binary and unary operator functions
BinaryOperator = Callable[[float, float], float]
UnaryOperator = Callable[[float], float]


# [正體中文] 允許的雙元運算子白名單（加、減、乘、除、整除、取餘數、乘方）
# [English] Whitelist of permitted binary arithmetic operators
_ALLOWED_BIN_OPS: dict[type[ast.operator], BinaryOperator] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

# [正體中文] 允許的單元運算子白名單（正號、負號）
# [English] Whitelist of permitted unary operators (positive, negation)
_ALLOWED_UNARY_OPS: dict[type[ast.unaryop], UnaryOperator] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_ast(node: ast.AST) -> float:
    """遞迴安全解析 AST 節點並計算數值 / Recursively evaluate AST nodes safely.

    [正體中文]
    只處理常數（Constant）、雙元運算（BinOp）與單元運算（UnaryOp）。
    若遇到任何其他節點（如 Call、Attribute、Name 等），立即拋出例外阻擋。

    [English]
    Only processes Constant, BinOp, and UnaryOp nodes.
    Any other node type (such as function Call, Attribute, Name) is rejected immediately.
    """
    # [正體中文] 數值常數節點（例如 42 或 3.14）
    # [English] Constant value node (e.g., 42 or 3.14)
    if isinstance(node, ast.Constant):
        value = node.value
        # [正體中文] 在 Python 中 bool 是 int 的子類別，需明確排除 True / False
        # [English] In Python, bool is a subclass of int; explicitly reject booleans
        if isinstance(value, bool):
            raise ValueError("Booleans are not supported")
        if isinstance(value, (int, float)):
            return float(value)
        raise ValueError(f"Unsupported constant type: {type(value).__name__}")

    # [正體中文] 雙元運算節點（例如 a + b、a * b）
    # [English] Binary operation node (e.g., a + b, a * b)
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BIN_OPS:
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        return _ALLOWED_BIN_OPS[type(node.op)](left, right)

    # [正體中文] 單元運算節點（例如 -5、+3）
    # [English] Unary operation node (e.g., -5, +3)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY_OPS:
        value = _eval_ast(node.operand)
        return _ALLOWED_UNARY_OPS[type(node.op)](value)

    # [正體中文] 遇到不受支援的節點型別時報錯
    # [English] Raise error for unsupported AST node types
    raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def evaluate_expression(expression: str) -> str:
    """安全計算數學運算式字串 / Evaluate a math expression safely.

    [正體中文]
    範例：`(4 * 4 * (33 / 22) + 12 - 20)`
    - 使用 `ast.parse(expression, mode="eval")` 解析表達式樹。
    - 若發生除以零、語法錯誤或惡意語法，捕捉例外並回傳錯誤訊息，不使系統崩潰。
    - 結果格式化去除不必要的浮點零尾數。

    [English]
    Example: `(4 * 4 * (33 / 22) + 12 - 20)`
    - Parses expression into an AST tree in 'eval' mode.
    - Catches any syntax or division errors gracefully without crashing the server.
    - Formats output to trim trailing floating-point zeros.
    """
    try:
        # [正體中文] 將字串解析為 AST 抽象語法樹
        # [English] Parse string expression into an Abstract Syntax Tree
        tree = ast.parse(expression, mode="eval")
        result = _eval_ast(tree.body)
    except Exception as exc:
        # [正體中文] 捕捉任何計算錯誤並以友善字串回傳給模型
        # [English] Catch any evaluation errors and return friendly error message to the model
        return f"Error: {exc}"

    # [正體中文] 保留 10 位小數並去除尾端多餘的 0 與小數點
    # [English] Format up to 10 decimal places and strip redundant trailing zeros
    formatted = f"{result:.10f}".rstrip("0").rstrip(".")
    return formatted or "0"
