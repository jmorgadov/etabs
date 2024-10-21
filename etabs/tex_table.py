from __future__ import annotations

from enum import Enum
from typing import Any, Callable, List, Set, Tuple, Union

from etabs.tex_table_cell import TexTableCell


def _texcmd(
    cmd: str,
    body: List[str],
    opts: Union[str, None] = None,
    args: Union[str, None] = None,
) -> List[str]:
    code_lines = [
        r"\begin{"
        + cmd
        + "}"
        + (f"[{opts}]" if opts is not None else "")
        + (f"{{{args}}}" if args is not None else "")
    ]
    code_lines.extend(["    " + line for line in body])
    code_lines.append(r"\end{" + cmd + "}")
    return code_lines


def _flat(items: List[Any]) -> List[Any]:
    final = []
    for item in items:
        if isinstance(item, list):
            final.extend(_flat(item))
        else:
            final.append(item)
    return final


class RuleType(Enum):
    TOP = 0
    MID = 1
    BOTTOM = 2


class TexTable:
    def __init__(
        self,
        centered: bool = True,
        caption: Union[str, None] = None,
        caption_after_table: bool = False,
        position: str = "h!",
        star: bool = False,
        empty_value: str = "",
        label: Union[str, None] = None,
        cmd: str = "figure",
    ):

        self.col_styles: List[str] = []
        self.seps: List[str] = []
        self.centered = centered
        self.caption = caption
        self.caption_after_table = caption_after_table
        self.position = position
        self.star = star
        self.empty_value = empty_value
        self.label = label
        self.cmd = cmd
        self.table: List[List[TexTableCell]] = []

        self._dependencies: Set[str] = set()
        self._rules: List[Tuple[int, str]] = []
        self._lines: List[Tuple[int, str]] = []

    @property
    def col_count(self) -> int:
        """Returns the number of columns in the table."""
        return len(self.col_styles)

    @property
    def row_count(self) -> int:
        """Returns the number of rows in the table."""
        return len(self.table)

    @property
    def _str_col_sty(self) -> str:
        _sty = ""
        for sep, col in zip(self.seps, self.col_styles):
            _sty += sep + col
        _sty += self.seps[-1]
        return _sty

    @property
    def dependencies(self) -> List[str]:
        """Returns a list of latex packages needed to render the table."""
        return list(self._dependencies)

    def _depends_on(self, depenency: str):
        """Add a dependency to the table."""
        self._dependencies.add(depenency)

    def _get_indexing_bounds(
        self, i: Union[int, slice], j: Union[int, slice]
    ) -> Tuple[int, int, int, int]:
        row, col, to_row, to_col = 0, 0, 0, 0
        if isinstance(i, slice):
            row = i.start if i.start is not None else 0
            to_row = (i.stop - 1) if i.stop is not None else len(self.table) - 1
        elif isinstance(i, int):
            row = to_row = i
        else:
            raise ValueError("Invalid row index")

        if isinstance(j, slice):
            col = j.start if j.start is not None else 0
            to_col = (j.stop - 1) if j.stop is not None else self.col_count - 1
        elif isinstance(j, int):
            col = to_col = j
        else:
            raise ValueError("Invalid column index")
        return row, col, to_row, to_col

    def add_rule(
        self, row: Union[int, None] = None, rule_type: RuleType = RuleType.MID
    ):
        """
        Add a rule to the table.

        Parameters
        ----------
        row : int, optional
            The row to add the rule to, by default None.

            If None, the rule is placed after the last row added to the table.
        rule_type : RuleType
            The type of rule to add, by default RuleType.MID.
        """
        self._depends_on("booktabs")

        if rule_type == RuleType.TOP:
            rule = r"\toprule"
        elif rule_type == RuleType.MID:
            rule = r"\midrule"
        elif rule_type == RuleType.BOTTOM:
            rule = r"\bottomrule"
        else:
            raise ValueError("Invalid rule type")

        self._rules.append((len(self.table) if row is None else row, rule))

    def add_cline(
        self, row: Union[int, None], from_col: int = 0, to_col: Union[int, None] = None
    ):
        """
        Add a line in top of a row.

        Parameters
        ----------
        row : int, optional
            The row to add the line to, by default None.

            If None, the line is placed on top of the last row added to
            the table.
        from_col : int, optional
            The column to start the line at, by default 0.
        to_col : int, optional
            The column to end the line at, by default None.

            If None, the line is drawn to the end of the row.
        """
        self._depends_on("booktabs")

        to_col = self.col_count - 1 if to_col is None else to_col
        row = len(self.table) if row is None else row

        line = r"\cline{" + str(from_col + 1) + "-" + str(to_col + 1) + "} "
        return self._lines.append((row, line.strip()))

    def add_cmidrule(
        self,
        row: Union[int, None],
        from_col: int = 0,
        to_col: Union[int, None] = None,
        options: str = "lr",
    ):
        """
        Add a mid rule in top of a row.

        Parameters
        ----------
        row : int, optional
            The row to add the line to, by default None.

            If None, the line is placed on top of the last row added to
            the table.
        from_col : int, optional
            The column to start the line at, by default 0.
        to_col : int, optional
            The column to end the line at, by default None.

            If None, the line is drawn to the end of the row.
        options : str, optional
            The options for the line, by default "lr".
        """
        self._depends_on("booktabs")

        to_col = self.col_count - 1 if to_col is None else to_col
        row = len(self.table) if row is None else row

        line = (
            r"\cmidrule("
            + options
            + "){"
            + str(from_col + 1)
            + "-"
            + str(to_col + 1)
            + "} "
        )
        return self._lines.append((row, line.strip()))

    def add_row(
        self,
        *values: Union[Any, None],
        start: int = 0,
        prep: Union[Callable, None] = None,
    ):
        """
        Add a row to the table.

        Parameters
        ----------
        *values : Any
            The values to add to the row.
        start : int, optional
            The column to start adding values to, by default 0.
        prep : Callable, optional
            A function to apply to each value before adding it to the
            table, by default None. (None means the identity function)
        """

        prep = prep or (lambda x: x)
        _values = [
            str(prep(val)) if val is not None else self.empty_value for val in values
        ]

        # Fill in empty values
        if start > 0:
            _values = [self.empty_value] * start + _values
        if len(_values) < self.col_count:
            _values += [self.empty_value] * (self.col_count - len(_values))
        elif len(_values) > self.col_count:
            for _ in range(len(_values) - self.col_count):
                self.add_col()

        # Add the row
        self.table.append(
            [
                TexTableCell(
                    val,
                    len(self.table),
                    i,
                    l_sep=self.seps[i],
                    r_sep=self.seps[i + 1],
                )
                for i, val in enumerate(_values)
            ]
        )

    def add_col(
        self,
        *values: Union[Any, None],
        start: int = 0,
        prep: Union[Callable, None] = None,
    ):
        """
        Add a column to the table.

        Parameters
        ----------
        *values : Any
            The values to add to the column.
        start : int, optional
            The row to start adding values to, by default 0.
        prep : Callable, optional
            A function to apply to each value before adding it to the
            table, by default None. (None means the identity function)
        """
        self.col_styles.append("c")
        self.seps.append("")
        if len(self.col_styles) == 1:
            self.seps.append("")

        prep = prep or (lambda x: x)
        _values = [str(prep(val)) for val in values]

        # Fill in empty values
        if start > 0:
            _values = [self.empty_value] * start + _values
        if len(_values) < self.row_count:
            _values += [self.empty_value] * (self.row_count - len(_values))
        elif len(_values) > self.row_count:
            for _ in range(len(_values) - self.row_count):
                self.add_row()

        # Add the column
        for i, val in enumerate(_values):
            self.table[i].append(
                TexTableCell(
                    val,
                    i,
                    len(self.table[i]),
                    l_sep=self.seps[-2],
                    r_sep=self.seps[-1],
                )
            )

    def merge(
        self,
        value: str,
        row: int,
        col: int,
        width: Union[int, None] = None,
        height: Union[int, None] = None,
        to_row: Union[int, None] = None,
        to_col: Union[int, None] = None,
    ):
        """
        Merge cells in the table.

        Parameters
        ----------
        value : str
            The value to put in the merged cell.
        row : int
            The row to start merging at.
        col : int
            The column to start merging at.
        width : int, optional
            The number of columns to merge, by default None.
        height : int, optional
            The number of rows to merge, by default None.
        to_row : int, optional
            The row to end merging at, by default None.
        to_col : int, optional
            The column to end merging at, by default None.
        """
        if not 0 <= row < len(self.table):
            raise ValueError(f"Invalid row index: {row}")
        if not 0 <= col < self.col_count:
            raise ValueError(f"Invalid column index: {col}")

        if width is None and to_col is None and height is None and to_row is None:
            ValueError(
                "Must specify a width or a height by using the parms `width` "
                "and `height` (or the `to_row` and `to_col`)"
            )

        if width is not None and to_col is not None:
            ValueError("Cannot specify both `width` and `to_col`")

        if height is not None and to_row is not None:
            ValueError("Cannot specify both `height` and `to_row`")

        if to_row is None:
            assert height is not None
            to_row = row + height - 1
        else:
            height = to_row - row + 1

        if to_col is None:
            assert width is not None
            to_col = col + width - 1
        else:
            width = to_col - col + 1

        assert (
            to_row is not None
            and to_col is not None
            and height is not None
            and width is not None
        )

        if not row <= to_row < len(self.table):
            raise ValueError(f"Invalid height: {height}")
        if not col <= to_col < self.col_count:
            raise ValueError(f"Invalid width: {width}")

        for _row in range(row, to_row + 1):
            for _col in range(col, to_col + 1):
                cell = self.table[_row][_col]
                c_r0, c_c0, c_r1, c_c1 = cell.bounds()
                if c_r0 < _row or c_c0 < col or c_r1 > to_row or c_c1 > to_col:
                    raise ValueError(
                        "Invalid cell bounds. There is a cell inside the "
                        "boundaries that is not fully contained in the "
                        "merge area."
                    )

        if height > 1:
            self._depends_on("multirow")

        # Merge cells
        new_cell = TexTableCell(
            value,
            row=row,
            col=col,
            width=width,
            height=height,
            l_sep=self.seps[col],
            r_sep=self.seps[to_col + 1],
        )
        for _row in range(row, to_row + 1):
            for _col in range(col, to_col + 1):
                self.table[_row][_col] = new_cell

    def render_deps(self) -> str:
        """Render the dependencies latex code as string."""
        return "\n".join([f"\\usepackage{{{dep}}}" for dep in self.dependencies])

    def render(self) -> str:
        """Render the table latex code as a string."""

        rows = [
            "".join(
                [cell.table_value(row, col) for col, cell in enumerate(row_cells)]
            ).removesuffix(" & ")
            + r" \\"
            for row, row_cells in enumerate(self.table)
        ]

        # Add top lines
        for r_idx, tline in self._lines:
            if not 0 <= r_idx < len(rows):
                raise ValueError(f"Invalid line index {r_idx}")
            rows[r_idx] = tline + " " + rows[r_idx]

        # Add rules
        self._rules.sort(key=lambda x: x[0])
        for added, rule in enumerate(self._rules):
            i, tex = rule
            if not 0 <= i < len(rows):
                raise ValueError(f"Invalid rule index {i}")
            rows.insert(i + added, tex)

        caption_line = r"\caption{" + self.caption + "}" if self.caption else ""
        if self.label is not None:
            if self.caption is None:
                raise ValueError("Cannot have a label without a caption")
            caption_line += r"\label{" + self.label + "}"

        code_lines = _texcmd(
            cmd=self.cmd + ("*" if self.star else ""),
            opts=self.position,
            body=_flat(
                [
                    r"\centering" if self.centered else "",
                    caption_line if not self.caption_after_table else "",
                    _texcmd(
                        cmd="tabular",
                        args=self._str_col_sty,
                        body=rows,
                    ),
                    caption_line if self.caption_after_table else "",
                ]
            ),
        )
        return "\n".join(code_lines)

    def __getitem__(
        self, idx: Tuple[Union[int, slice], Union[int, slice]]
    ) -> TexTableSlice:
        i, j = idx
        row, col, to_row, to_col = self._get_indexing_bounds(i, j)
        return TexTableSlice(self, row, col, to_row, to_col)

    def __setitem__(self, idx, value):
        i, j = idx
        _val = str(value)

        if isinstance(i, int) and isinstance(j, int):
            self.table[i][j].raw_value = _val
            return

        # Needs merge
        row, col, to_row, to_col = self._get_indexing_bounds(i, j)
        self.merge(_val, row, col, to_row=to_row, to_col=to_col)


class TexTableSlice:
    def __init__(self, table: TexTable, row: int, col: int, to_row: int, to_col: int):
        self.table = table
        self.row = row
        self.col = col
        self.to_row = to_row
        self.to_col = to_col

        self._value = None
        if self.row == self.to_row and self.col == self.to_col:
            self._value = self.table.table[self.row][self.col].raw_value
        _cell = self.table.table[self.row][self.col]

        if all(cell is _cell for cell in self):
            self._value = _cell.raw_value

    @property
    def value(self) -> str:
        """Returns the value of the slice."""
        if self._value is not None:
            return self._value
        raise ValueError("Table slice has multiple values")

    def set_value(self, value: str):
        """Set the value for each cell of the slice."""
        for cell in self:
            cell.raw_value = value

    def for_each(self, func: Callable[[str], Any]):
        """Apply a function to the value of each cell of the slice."""
        for cell in self:
            cell.raw_value = func(cell.raw_value)

    def __iter__(self):
        for i in range(self.row, self.to_row + 1):
            for j in range(self.col, self.to_col + 1):
                yield self.table.table[i][j]

    def set_bold(self, val: bool):
        """Sets the bold value of the slice."""
        for i in range(self.row, self.to_row + 1):
            for j in range(self.col, self.to_col + 1):
                self.table.table[i][j].bold = val

    def set_italic(self, val: bool):
        """Sets the italic value of the slice."""
        for i in range(self.row, self.to_row + 1):
            for j in range(self.col, self.to_col + 1):
                self.table.table[i][j].italic = val

    def set_background_color(self, val: str):
        """Set the background color of the slice."""
        self.table._depends_on("colortbl")
        self.table._depends_on("xcolor")

        for i in range(self.row, self.to_row + 1):
            for j in range(self.col, self.to_col + 1):
                self.table.table[i][j].background_color = val

    def set_rotation(self, degree: float, options: str = "origin=c"):
        """Set the rotation of the slice."""
        self.table._depends_on("graphicx")

        for i in range(self.row, self.to_row + 1):
            for j in range(self.col, self.to_col + 1):
                self.table.table[i][j].rotate_degree = str(degree)
                self.table.table[i][j].rotate_options = options
