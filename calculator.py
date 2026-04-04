import ast
import operator
import readline

#!/usr/bin/env python3


OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def eval_expr(node):
    if isinstance(node, ast.BinOp):
        left = eval_expr(node.left)
        right = eval_expr(node.right)
        op = OPS[type(node.op)]
        return op(left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = eval_expr(node.operand)
        op = OPS[type(node.op)]
        return op(operand)
    elif isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Expr):
        return eval_expr(node.value)
    else:
        raise ValueError("Unsupported expression")

def calculate(expression):
    tree = ast.parse(expression, mode="eval")
    return eval_expr(tree.body)

def main():
    print("Simple calculator. Type 'exit' or 'quit' to stop.")
    while True:
        try:
            line = input("> ").strip()
            if not line:
                continue
            if line.lower() in {"exit", "quit"}:
                break
            result = calculate(line)
            print(result)
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    main()