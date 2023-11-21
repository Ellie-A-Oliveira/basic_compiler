from abc import abstractmethod
from enum import Enum
from typing import List, Self

SyntaxKind = Enum(
    "SyntaxKind",
    [
        "NumberToken",
        "WhitespaceToken",
        "PlusToken",
        "MinusToken",
        "StarToken",
        "SlashToken",
        "OpenParenthesisToken",
        "CloseParenthesisToken",
        "BadToken",
        "EndOfFileToken",
        "NumberExpression",
        "BinaryExpression",
    ],
)


class SyntaxNode:
    @abstractmethod
    def get_kind(self) -> SyntaxKind:
        return self.kind

    @abstractmethod
    def get_children(self) -> List[Self]:
        return []


class SyntaxToken(SyntaxNode):
    kind: SyntaxKind
    position: int
    text: str
    value: dict

    def __init__(self, kind: SyntaxKind, position: int, text: str, value: dict):
        self.kind = kind
        self.position = position
        self.text = text
        self.value = value

    def get_children(self) -> List[SyntaxNode]:
        return []

    def __repr__(self) -> str:
        return f"{self.kind.name}: {self.text} at {self.position}"


class Lexer:
    text: str
    position: int
    diagnostics: List[str] = []

    def __init__(self, text: str):
        self.text = text
        self.position = 0

    def get_current(self):
        if self.position >= len(self.text):
            return "\0"
        return self.text[self.position]

    def next(self):
        self.position += 1

    def next_token(self) -> SyntaxToken:
        if self.position >= len(self.text):
            return SyntaxToken(SyntaxKind.EndOfFileToken, self.position, "\0", None)

        if str.isdigit(self.get_current()):
            start = self.position

            while str.isdigit(self.get_current()):
                self.next()

            text = self.text[start : self.position]
            value: int
            try:
                value = int(text)
            except ValueError:
                self.diagnostics.append(f"The number {self.text} isn't a valid int")

            return SyntaxToken(SyntaxKind.NumberToken, start, text, value)

        if str.isspace(self.get_current()):
            start = self.position

            while str.isspace(self.get_current()):
                self.next()

            text = self.text[start : self.position]
            return SyntaxToken(SyntaxKind.WhitespaceToken, start, text, None)

        if self.get_current() == "+":
            syntax_token = SyntaxToken(SyntaxKind.PlusToken, self.position, "+", None)
            self.next()
            return syntax_token
        elif self.get_current() == "-":
            syntax_token = SyntaxToken(SyntaxKind.MinusToken, self.position, "-", None)
            self.next()
            return syntax_token
        elif self.get_current() == "*":
            syntax_token = SyntaxToken(SyntaxKind.StarToken, self.position, "*", None)
            self.next()
            return syntax_token
        elif self.get_current() == "/":
            syntax_token = SyntaxToken(SyntaxKind.SlashToken, self.position, "/", None)
            self.next()
            return syntax_token
        elif self.get_current() == "(":
            syntax_token = SyntaxToken(
                SyntaxKind.OpenParenthesisToken, self.position, "(", None
            )
            self.next()
            return syntax_token
        elif self.get_current() == ")":
            syntax_token = SyntaxToken(
                SyntaxKind.CloseParenthesisToken, self.position, ")", None
            )
            self.next()
            return syntax_token

        self.diagnostics.append(f"ERROR: bad character input: '{self.get_current()}'")
        self.next()
        return SyntaxToken(
            SyntaxKind.BadToken, self.position, self.text[self.position - 1 : 1], None
        )


class ExpressionSyntax(SyntaxNode):
    print


class NumberExpressionSyntax(ExpressionSyntax):
    number_token: SyntaxToken

    def __init__(self, number_token: SyntaxToken):
        self.number_token = number_token

    def get_kind(self):
        return SyntaxKind.NumberExpression

    def get_children(self) -> List[SyntaxNode]:
        return [self.number_token]


class BinaryExpressionSyntax(ExpressionSyntax):
    left: ExpressionSyntax
    operator_token: SyntaxToken
    right: ExpressionSyntax

    def __init__(
        self,
        left: ExpressionSyntax,
        operator_token: SyntaxToken,
        right: ExpressionSyntax,
    ):
        self.left = left
        self.operator_token = operator_token
        self.right = right

    def get_kind(self):
        return SyntaxKind.BinaryExpression

    def get_children(self) -> List[SyntaxNode]:
        return [self.left, self.operator_token, self.right]


class SyntaxTree:
    diagnostics: List[str]
    root: ExpressionSyntax
    endOfFileToken: SyntaxToken

    def __init__(
        self,
        diagnostics: List[str],
        root: ExpressionSyntax,
        endOfFileToken: SyntaxToken,
    ):
        self.diagnostics = diagnostics
        self.root = root
        self.endOfFileToken = endOfFileToken


class Evaluator:
    root: ExpressionSyntax

    def __init__(self, root: ExpressionSyntax):
        self.root = root

    def evaluate(self):
        return self.evaluate_expression(self.root)

    def evaluate_expression(self, root: ExpressionSyntax):
        if isinstance(root, NumberExpressionSyntax):
            return int(root.number_token.value)

        if isinstance(root, BinaryExpressionSyntax):
            left = self.evaluate_expression(root.left)
            right = self.evaluate_expression(root.right)

            if root.operator_token.kind == SyntaxKind.PlusToken:
                return left + right
            elif root.operator_token.kind == SyntaxKind.MinusToken:
                return left - right
            elif root.operator_token.kind == SyntaxKind.StarToken:
                return left * right
            elif root.operator_token.kind == SyntaxKind.SlashToken:
                return left / right
            else:
                raise Exception(
                    f"Unexpected binary operator {root.operator_token.kind}"
                )

        raise Exception(f"Unexpected node {root.get_kind().name}")


class Parser:
    tokens: List[SyntaxToken]
    position: int
    diagnostics: List[str] = []

    def __init__(self, text: str):
        tokens: List[SyntaxToken] = []
        self.position = 0

        lexer = Lexer(text)
        token = lexer.next_token()

        while token.kind is not SyntaxKind.EndOfFileToken:
            if (
                token.kind is not SyntaxKind.WhitespaceToken
                and token.kind is not SyntaxKind.BadToken
            ):
                tokens.append(token)
            token = lexer.next_token()

        self.tokens = tokens
        self.diagnostics.extend(lexer.diagnostics)

    def peek(self, offset: int) -> SyntaxToken:
        index = self.position + offset

        if index >= len(self.tokens):
            return self.tokens[len(self.tokens) - 1]

        return self.tokens[index]

    def get_current(self) -> SyntaxToken:
        return self.peek(0)

    def next_token(self) -> SyntaxToken:
        current = self.get_current()
        self.position += 1
        return current

    def match(self, kind: SyntaxKind) -> SyntaxToken:
        if self.get_current().kind == kind:
            return self.next_token()

        self.diagnostics.append(
            f"ERROR: Unexpected token <{self.get_current().kind.name}>, expected <{kind.name}>"
        )

        return SyntaxToken(kind, self.get_current().position, None, None)

    def parse(self) -> SyntaxTree:
        expression = self.parse_term()
        endOfFileToken = self.match(SyntaxKind.EndOfFileToken)
        return SyntaxTree(self.diagnostics, expression, endOfFileToken)

    def parse_term(self) -> ExpressionSyntax:
        left = self.parse_primary_expression()

        while (
            self.get_current().kind == SyntaxKind.PlusToken
            or self.get_current().kind == SyntaxKind.MinusToken
        ):
            operator_token = self.next_token()
            right = self.parse_factor()
            left = BinaryExpressionSyntax(left, operator_token, right)

        return left

    def parse_factor(self) -> ExpressionSyntax:
        left = self.parse_primary_expression()

        while (
            self.get_current().kind == SyntaxKind.StarToken
            or self.get_current().kind == SyntaxKind.SlashToken
        ):
            operator_token = self.next_token()
            right = self.parse_primary_expression()
            left = BinaryExpressionSyntax(left, operator_token, right)

        return left

    def parse_primary_expression(self) -> ExpressionSyntax:
        number_token = self.match(SyntaxKind.NumberToken)
        return NumberExpressionSyntax(number_token)


def pretty_print(node: SyntaxNode, indent="", is_last=True):
    # └──
    # ├──
    # │

    marker: str
    if is_last:
        marker = "└──"
    else:
        marker = "├──"

    display_message = f"{indent}{marker}{node.get_kind().name}"

    if isinstance(node, SyntaxToken) and node.value:
        display_message += f" {node.value}"

    print(display_message)

    if is_last:
        indent += "    "
    else:
        indent += "│   "

    last_child: SyntaxNode
    if len(node.get_children()) > 0:
        last_child = node.get_children()[-1]

    for child in node.get_children():
        pretty_print(child, indent, child == last_child)


def main():
    while True:
        line = input("> ")
        if not line or str.isspace(line):
            return

        parser = Parser(line)
        syntax_tree = parser.parse()

        pretty_print(syntax_tree.root)

        if len(syntax_tree.diagnostics) > 0:
            for diagnostic in syntax_tree.diagnostics:
                print(diagnostic)
        else:
            evaluator = Evaluator(syntax_tree.root)
            result = evaluator.evaluate()
            print(result)


if __name__ == "__main__":
    main()
