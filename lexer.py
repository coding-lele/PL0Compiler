# 枚举类型，表示词法单元的类型
class TokenType:
    PROGRAMSYM, BEGINSYM, ENDSYM, CONSTSYM, VARSYM, WHILESYM, DOSYM, IFSYM, THENSYM, \
        IDENT, NUMBER, PLUSSYM, MINUSSYM, TIMESSYM, SLASHSYM, BECOMESSYM, \
        EQLSYM, NEQSYM, LESSYM, GTRSYM, LEQSYM, GEQSYM, \
        LPARENSYM, RPARENSYM, COMMASYM, SEMICOLONSYM, ERROR = range(27)


# 结构体，表示一个词法单元
class Token:
    def __init__(self, token_type, value):
        self.type = token_type  # 词法单元类型
        self.value = value  # 词法单元的值


# 词法分析器类
class PL0Lexer:
    def __init__(self, filename):
        self.input = open(filename, 'r')
        self.current_char = ' '
        self.keywords = ["PROGRAM", "BEGIN", "END", "CONST", "VAR", "WHILE", "DO", "IF", "THEN"]
        self.current_token = None

    # 获取下一个字符
    def get_next_char(self):
        char = self.input.read(1)
        self.current_char = char

    # 跳过空白字符
    def skip_whitespace(self):
        while self.current_char.isspace() or self.current_char == '\n':
            self.get_next_char()

    # 识别关键字或标识符
    def scan_identifier_or_keyword(self):
        identifier = ''
        while self.current_char.isalnum() or self.current_char == '_':
            identifier += self.current_char
            self.get_next_char()

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

