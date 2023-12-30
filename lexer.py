# 枚举类型，表示词法单元的类型
class TokenType:
    PROGRAMSYM, BEGINSYM, ENDSYM, CONSTSYM, VARSYM, WHILESYM, DOSYM, IFSYM, THENSYM, \
        IDENT, NUMBER, PLUSSYM, MINUSSYM, TIMESSYM, SLASHSYM, BECOMESSYM, \
        EQLSYM, NEQSYM, LESSYM, GTRSYM, LEQSYM, GEQSYM, \
        LPARENSYM, RPARENSYM, COMMASYM, SEMICOLONSYM, ERROR, EOF = range(28)


# 结构体，表示一个词法单元
class Token:
    def __init__(self, token_type, value):
        self.type = token_type  # 词法单元类型
        self.value = value  # 词法单元的值


# 词法分析器类
class PL0Lexer:
    def __init__(self, filename):
        # with open(filename, 'r') as file:
        #     self.source = file.read()  # 将文件内容读取为字符串
        self.input = open(filename, 'r', encoding='utf-8')  # 输入文件流
        self.current_char = ' '  # 当前字符
        self.keywords = ["PROGRAM", "BEGIN", "END", "CONST", "VAR", "WHILE", "DO", "IF", "THEN"]
        self.current_token = None  # 当前词法单元
        self.line = 1  # 词法分析结果增加行列信息，用于错误处理
        self.col = 1

    # 返回当前行列数
    def get_line(self):
        return self.line

    def get_col(self):
        return self.col  # -1

    # 获取下一个字符，同时记录这个字符所在的行列数
    def get_next_char(self):
        char = self.input.read(1)

        self.current_char = char
        if self.current_char == '\n':  # 读到换行符，则行数加一
            self.line += 1
            self.col = 0
        elif self.current_char.isspace():  # 读到空格
            self.col = self.col
        else:  # 否则列数加一
            self.col += 1
        # if self.current_char == '\n':
        #     print("char:", "换行符", "line:", self.line, "col:", self.col)
        # else:
        #     print("char:", char, "line:", self.line, "col:", self.col)

    # 跳过空白字符
    def skip_whitespace(self):
        while self.current_char.isspace() or self.current_char == '\n':
            self.get_next_char()

    # 识别关键字或标识符
    def scan_identifier_or_keyword(self):
        identifier = ''
        while self.current_char.isalnum():
            identifier += self.current_char
            self.get_next_char()

        if self.current_char != '\n':
            self.col -= (len(identifier) - 1)  # 如果碰到换行符，在col=0之后又减去了这个长度
        # 判断是否是关键字
        if identifier in self.keywords:
            return Token(self.keywords.index(identifier), identifier)
        else:
            # 不是关键字，是标识符
            return Token(TokenType.IDENT, identifier)

    # 识别整数
    def scan_number(self):
        integer = ''
        while self.current_char.isdigit():
            integer += self.current_char
            self.get_next_char()
            self.col -= len(integer) - 1
        return Token(TokenType.NUMBER, integer)

    # 识别运算符
    def scan_operator(self):
        op = self.current_char
        self.get_next_char()

        # 根据运算符返回对应的 TokenType
        operator_map = {
            '+': TokenType.PLUSSYM,
            '-': TokenType.MINUSSYM,
            '*': TokenType.TIMESSYM,
            '/': TokenType.SLASHSYM
        }

        return Token(operator_map[op], op) if op in operator_map else self.scan_error()

    # 识别赋值运算符或错误
    def scan_becomes_or_error(self):
        op = self.current_char
        self.get_next_char()

        if self.current_char == '=':
            op += self.current_char
            self.get_next_char()
            self.col -= len(op) - 1
            return Token(TokenType.BECOMESSYM, op)
        else:
            return self.scan_error()

    # 识别关系运算符
    def scan_relational_operator(self):
        op = self.current_char
        self.get_next_char()

        if self.current_char == '=':
            op += self.current_char
            self.get_next_char()

        # 根据关系运算符返回对应的 TokenType
        relational_operators = {
            '=': TokenType.EQLSYM,
            '<>': TokenType.NEQSYM,
            '<': TokenType.LESSYM,
            '>': TokenType.GTRSYM,
            '<=': TokenType.LEQSYM,
            '>=': TokenType.GEQSYM
        }

        self.col -= len(op) - 1
        return Token(relational_operators[op], op) if op in relational_operators else self.scan_error()

    # 识别界符
    def scan_delimiter(self):
        delimiter = self.current_char
        self.get_next_char()

        # 根据界符返回对应的 TokenType
        delimiter_map = {
            '(': TokenType.LPARENSYM,
            ')': TokenType.RPARENSYM,
            ',': TokenType.COMMASYM,
            ';': TokenType.SEMICOLONSYM
        }

        return Token(delimiter_map[delimiter], delimiter) if delimiter in delimiter_map else self.scan_error()

    # 识别错误
    def scan_error(self):
        error = self.current_char
        self.get_next_char()
        return Token(TokenType.ERROR, error)

    # 获取下一个词法单元
    def get_next_token(self):
        self.skip_whitespace()

        if self.current_char:
            if self.current_char.isalpha():
                return self.scan_identifier_or_keyword()
            elif self.current_char.isdigit():
                return self.scan_number()
            elif self.current_char in ['+', '-', '*', '/']:
                return self.scan_operator()
            elif self.current_char == ':':
                return self.scan_becomes_or_error()
            elif self.current_char in ['=', '<', '>']:
                return self.scan_relational_operator()
            elif self.current_char in ['(', ')', ',', ';']:
                return self.scan_delimiter()
            else:
                return self.scan_error()
        else:
            return Token(TokenType.EOF, 'EOF')  # 读完输入文件时返回EOF


if __name__ == "__main__":
    filename = "pl0_program.txt"
    lexer = PL0Lexer(filename)

    while True:
        token = lexer.get_next_token()
        # 读完整个文件
        if token.type == TokenType.EOF:
            break
        # 打印token信息
        print(f"({token.type}, {token.value})")

    lexer.input.close()
