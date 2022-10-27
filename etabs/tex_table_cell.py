from typing import Tuple


class TexTableCell:
    def __init__(
        self,
        value: str,
        row: int,
        col: int,
        width: int = 1,
        height: int = 1,
        l_sep: str = "",
        r_sep: str = "",
    ):
        self.raw_value = value
        self.row = row
        self.col = col
        self.width = width
        self.height = height
        self.bold, self.italic = False, False
        self.l_sep, self.r_sep = l_sep, r_sep

    def bounds(self) -> Tuple[int, int, int, int]:
        """Returns the bounds of the cell."""
        return (
            self.row,
            self.col,
            self.row + self.height - 1,
            self.col + self.width - 1,
        )

    @property
    def styled_value(self) -> str:
        """Returns the value of the cell with the style applied."""
        ans = self.raw_value
        if self.bold:
            ans = r"\textbf{" + ans + "}"
        if self.italic:
            ans = r"\textit{" + ans + "}"
        return ans

    def __getitem__(self, idx) -> str:
        row, col = idx
        assert self.row <= row < self.row + self.height, "Row out of bounds"
        assert self.col <= col < self.col + self.width, "Col out of bounds"

        if self.width == 1 and self.height == 1:
            return self.styled_value

        if row == self.row and col == self.col:
            ans = self.styled_value
            col_style = self.l_sep + "c" + self.r_sep
            if self.height > 1:
                ans = r"\multirow{" + str(self.height) + "}{*}{" + ans + "}"
            if self.width > 1:
                ans = (
                    r"\multicolumn{"
                    + str(self.width)
                    + "}{"
                    + col_style
                    + "}{"
                    + ans
                    + "}"
                )
            return ans

        return ""

    def table_value(self, row: int, col: int) -> str:
        """Returns the value of the cell with the & separator if needed."""
        assert self.row <= row < self.row + self.height, "Row out of bounds"
        assert self.col <= col < self.col + self.width, "Col out of bounds"
        ans = self[row, col]
        if row != self.row or col == self.col + self.width - 1:
            ans += " & "
        return ans
