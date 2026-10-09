"""The deparse reader: base R's `data/*.R` files (ChickWeight, infert, sleep and four more),
evaluated to frames without R (ADR 0003). Its one design decision is the grammar, the subset
of R those seven files use; anything outside it raises with the file and the construct named.
The reader is for those files, not for R."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

TOKEN = re.compile(
    r"""(?P<skip>\s+|\#[^\n]*)
      | (?P<number>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)
      | (?P<string>"[^"\\]*")
      | (?P<name>[A-Za-z.][A-Za-z0-9._]*)
      | (?P<op><-|[-~|:=(),])
      | (?P<other>.)""",
    re.VERBOSE,
)
# the attributes structure() sets on a frame, nlme's groupedData ones among them: a plain frame
# keeps none of them, so they are parsed and never evaluated (`formula = weight ~ Time | Chick`)
DROPPED = ('row.names', 'class', 'formula', 'outer', 'labels', 'units')


@dataclass(frozen=True)
class Symbol:
    name: str


@dataclass(frozen=True)
class Op:
    op: str
    left: Node | None  # None for a unary operator
    right: Node


@dataclass(frozen=True)
class Call:
    name: str
    arguments: list[tuple[str | None, Node]]  # (keyword or None, value) in call order


Node = Call | Op | Symbol | float | str | None  # None is NA
Value = list | pd.Categorical | dict | pd.DataFrame  # a vector, a factor, a list, a frame


class DeparseError(ValueError):
    pass


# ==============================================================================================
# deparse reader
# ==============================================================================================


class Deparse:
    def __init__(self, file: Path):
        self.file = file
        self.tokens = self._tokenize(file.read_text(encoding='utf-8'))
        self.at = 0

    def frames(self) -> dict[str, pd.DataFrame]:
        """The frame the file assigns, under the name it assigns it to; the statements after
        it may only reset a formula attribute's environment, which the frame drops anyway."""
        statements = self._statements()
        target, value = statements[0]
        for later, _ in statements[1:]:
            if not (isinstance(later, Call) and later.name == 'environment'):
                raise self._error('a second statement')
        frame = self._evaluate(value)
        if not isinstance(frame, pd.DataFrame):
            raise self._error('an object that is no data frame')
        name = target  # `"ChickWeight" <-`
        if isinstance(target, Symbol):  # `sleep <-`
            name = target.name
        return {name: frame}

    def _error(self, construct: str) -> DeparseError:
        return DeparseError(f'{self.file}: {construct} is outside the deparse subset')

    # ------------------------------------------------------------------------------------------
    # pipeline: text -> tokens -> statements -> frame
    # ------------------------------------------------------------------------------------------

    def _tokenize(self, text: str) -> list[tuple[str, str]]:
        """(kind, text) pairs; whitespace and comments dropped."""
        tokens = []
        for match in TOKEN.finditer(text):
            kind = match.lastgroup
            if kind == 'other':
                raise self._error(f'character {match.group()!r}')
            if kind != 'skip':
                tokens.append((kind, match.group()))
        return tokens

    def _statements(self) -> list[tuple[Node | None, Node]]:
        """(target, value) per statement; the target is None where nothing is assigned."""
        statements = []
        while self.at < len(self.tokens):
            statements.append(self._statement())
        return statements

    def _statement(self) -> tuple[Node | None, Node]:
        expression = self._expression()
        if self._peek() != '<-':
            return None, expression
        self._take('<-')
        return expression, self._expression()

    def _expression(self) -> Node:
        """Binary operators left to right: only `:` is evaluated; `~` and `|` occur in the
        formula attributes structure() drops, so their precedence never matters."""
        node = self._unary()
        while self._peek() in (':', '~', '|'):
            _, op = self._take()
            node = Op(op, node, self._unary())
        return node

    def _unary(self) -> Node:
        """Unary minus binds tighter than `:` in R: `-1:3` runs from -1 to 3."""
        if self._peek() in ('-', '~'):
            _, op = self._take()
            return Op(op, None, self._unary())
        return self._primary()

    def _primary(self) -> Node:
        kind, text = self._take()
        if kind == 'number':
            return float(text)  # R reads every literal without `L` as a double
        if kind == 'string':
            return text[1:-1]
        if text == 'NA':
            return None
        if kind == 'name' and self._peek() == '(':
            return self._call(text)
        if kind == 'name':
            return Symbol(text)
        raise self._error(f'token {text!r}')

    def _call(self, name: str) -> Call:
        self._take('(')
        arguments = []
        if self._peek() != ')':
            arguments.append(self._argument())
        while self._peek() == ',':
            self._take(',')
            arguments.append(self._argument())
        self._take(')')
        return Call(name, arguments)

    def _argument(self) -> tuple[str | None, Node]:
        is_keyword = self.at + 1 < len(self.tokens) and self.tokens[self.at + 1][1] == '='
        if not is_keyword:
            return None, self._expression()
        _, keyword = self._take()
        self._take('=')
        return keyword, self._expression()

    def _peek(self) -> str | None:
        if self.at == len(self.tokens):
            return None
        return self.tokens[self.at][1]

    def _take(self, expected: str | None = None) -> tuple[str, str]:
        if self.at == len(self.tokens):
            raise self._error('the end of the file inside an expression')
        kind, text = self.tokens[self.at]
        if expected is not None and text != expected:
            raise self._error(f'token {text!r} where {expected!r} belongs')
        self.at += 1
        return kind, text

    # ------------------------------------------------------------------------------------------
    # evaluation: a vector is a list of floats, ints, strings and None (NA)
    # ------------------------------------------------------------------------------------------

    def _evaluate(self, node: Node) -> Value:
        if isinstance(node, Call):
            return self._apply(node)
        if isinstance(node, Op):
            return self._operate(node)
        if isinstance(node, Symbol):
            raise self._error(f'variable {node.name}')
        return [node]  # a literal is a vector of length one

    def _apply(self, call: Call) -> Value:
        if call.name == 'c':
            return self._combine(call)
        if call.name == 'list':
            return self._columns(call)
        if call.name == 'data.frame':
            return self._frame(self._columns(call))
        if call.name == 'structure':
            return self._structure(call)
        if call.name in ('factor', 'ordered'):
            return self._factor(call)
        if call.name == 'gl':
            return self._levels(call)
        if call.name in ('rep', 'rep.int'):
            return self._repeat(call)
        raise self._error(f'function {call.name}()')

    def _operate(self, node: Op) -> Value:
        right = self._evaluate(node.right)
        if node.op == '-' and node.left is None:
            return [-value for value in right]
        if node.op == ':':  # R's a:b of whole numbers is integer
            start = self._whole(self._evaluate(node.left))
            return list(range(start, self._whole(right) + 1))
        raise self._error(f'operator {node.op}')

    def _arguments(self, call: Call, keywords: tuple[str, ...] = ()) -> tuple[list, dict]:
        """The call's positional values and its keyword values, evaluated."""
        positional, named = [], {}
        for keyword, node in call.arguments:
            if keyword is None:
                positional.append(self._evaluate(node))
            elif keyword in keywords:
                named[keyword] = self._evaluate(node)
            else:
                raise self._error(f'argument {keyword}= of {call.name}()')
        return positional, named

    def _combine(self, call: Call) -> list:
        vectors, _ = self._arguments(call)
        return [value for vector in vectors for value in vector]

    def _columns(self, call: Call) -> dict[str, Value]:
        """list() and data.frame(): every argument is a named column."""
        columns = {}
        for keyword, node in call.arguments:
            if keyword is None:
                raise self._error(f'an unnamed element of {call.name}()')
            if call.name == 'data.frame' and keyword == 'row.names':  # LifeCycleSavings
                continue  # an argument of data.frame(), not a column
            columns[keyword] = self._evaluate(node)
        return columns

    def _frame(self, columns: dict[str, Value]) -> pd.DataFrame:
        frame = {}
        for name, values in columns.items():
            frame[name] = values
            if isinstance(values, list):
                frame[name] = self._vector(values)
        return pd.DataFrame(frame)

    def _vector(self, values: list) -> np.ndarray | list:
        """R's type of the vector: character, integer (32-bit, as R stores it), else double;
        an integer vector with NA is double, as pyreadr's frames have it (readers.numbersAsFloat)."""
        if any(isinstance(value, str) for value in values):
            return values
        if all(isinstance(value, int) for value in values):  # NA, None, is no int
            return np.array(values, dtype=np.int32)
        return np.array(values, dtype=float)  # None becomes NaN

    def _structure(self, call: Call) -> pd.DataFrame:
        """A list made a frame by its attributes; the attributes themselves are dropped."""
        _, body = call.arguments[0]
        for keyword, _ in call.arguments[1:]:
            if keyword not in DROPPED:
                raise self._error(f'attribute {keyword}= of structure()')
        return self._frame(self._evaluate(body))

    def _factor(self, call: Call) -> pd.Categorical:
        """factor() and ordered(): levels sorted (numbers as numbers) unless given, labels as R
        prints the levels unless given. `ordered` is dropped, as pyreadr drops it from the
        frames R saves, so that a frame is the same whichever reader made it; the registry's
        `types` declare an ordered column."""
        (values,), options = self._arguments(call, ('levels', 'labels'))
        levels = options.get('levels', sorted(set(values) - {None}))
        labels = options.get('labels', [self._label(level) for level in levels])
        codes = pd.Index(levels).get_indexer(values)  # -1, R's NA, for NA and unmatched values
        return pd.Categorical.from_codes(codes, categories=labels)

    @staticmethod
    def _label(level: float | str) -> str:
        """as.character() of a level: a whole number without a decimal point."""
        if isinstance(level, float) and level.is_integer():
            return str(int(level))
        return str(level)

    def _levels(self, call: Call) -> pd.Categorical:
        """gl(n, k): n levels `1` to `n`, each repeated k times."""
        (n, k), _ = self._arguments(call)
        n, k = self._whole(n), self._whole(k)
        codes = np.repeat(np.arange(n), k)  # (n * k,)
        return pd.Categorical.from_codes(codes, categories=[str(level + 1) for level in range(n)])

    def _repeat(self, call: Call) -> list:
        """rep(x, times) and rep.int(x, times): the whole vector, `times` over."""
        (values, times), _ = self._arguments(call)
        return values * self._whole(times)

    @staticmethod
    def _whole(value: list) -> int:
        """The one number of a range end or a count."""
        (number,) = value
        return int(number)
