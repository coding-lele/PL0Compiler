from lexer import *


class InterCodeGen:
    # 结构体，表示中间代码的一条指令
    class IntermediateCode:
        def __init__(self, op, arg1=None, arg2=None, result=None, line=None):
            self.op = op
            self.arg1 = arg1
            self.arg2 = arg2
            self.result = result
            self.line = line

        def __str__(self):
            return (f'{self.line}: '
                    f'({self.op}, '
                    f'{self.arg1 if self.arg1 else "-"}, '
                    f'{self.arg2 if self.arg2 else "-"}, '
                    f'{self.result})')

        def write_back(self, result):
            self.result = result

    def __init__(self):
        self.code: dict[int: InterCodeGen.IntermediateCode] = {}  # 用dict便于回填
        self.temp_counter = 0  # 记录当前临时变量
        self.line_counter = 100  # 当前行数
        self.stack = []
        self.var_dict = {}
        self.const_dict = {}
        self.while_stack = []  # 记录循环开始的行和需要回填的行
        self.if_stack = []  # 记录需要回填的行

    def __str__(self):  # 字符串累计输出
        res = ''
        for c in self.code:
            res += f'{self.code[c]}\n'
        return res

    def emit(self, op, result, arg1=None, arg2=None):
        self.code[self.line_counter] = self.IntermediateCode(op, arg1, arg2, result, self.line_counter)
        #self.code[self.line_counter] = self.IntermediateCode('=', 1, None, 'x', self.line_counter )
        print(f'emit: {self.code[self.line_counter]}')
        self.line_counter += 1


# 语法分析器（包含中间代码生成）
class PL0Parser:
    def __init__(self, tokens):
        self.token_list = tokens
        self.current_index = 0
        self.intermediate_code_list = []
        self.intermediate_code_index = 0
        # 创建 InterCodeGen 的实例
        self.inter_code_gen = InterCodeGen()

    def parse(self):
        self.program()

    def match(self, expected_type):
        if self.current_index < len(self.token_list) and self.token_list[self.current_index].type == expected_type:
            self.current_index += 1
        else:
            # 处理错误，可以输出错误信息或进行其他错误处理
            pass

    def program(self):
        self.program_header()
        self.subprogram()

    def program_header(self):
        self.match(TokenType.PROGRAMSYM)
        self.match(TokenType.IDENT)

    def subprogram(self):
        if self.token_list[self.current_index].type == TokenType.CONSTSYM:
            self.constant_declaration()

        if self.token_list[self.current_index].type == TokenType.VARSYM:
            self.variable_declaration()

        self.statements()

    def constant_declaration(self):
        self.match(TokenType.CONSTSYM)
        self.constant_definition()

        while self.token_list[self.current_index].type == TokenType.COMMASYM:
            self.match(TokenType.COMMASYM)
            self.constant_definition()

        self.match(TokenType.SEMICOLONSYM)

    def constant_definition(self):
        self.match(TokenType.IDENT)
        self.match(TokenType.EQLSYM)
        self.unsigned_integer()

    def unsigned_integer(self):
        self.match(TokenType.NUMBER)

        while self.token_list[self.current_index].type == TokenType.NUMBER:
            self.match(TokenType.NUMBER)

    def variable_declaration(self):
        self.match(TokenType.VARSYM)
        self.identifier()

        while self.token_list[self.current_index].type == TokenType.COMMASYM:
            self.match(TokenType.COMMASYM)
            self.identifier()

        self.match(TokenType.SEMICOLONSYM)

    def identifier(self):
        self.match(TokenType.IDENT)

        while self.token_list[self.current_index].type == TokenType.IDENT \
                or self.token_list[self.current_index].type == TokenType.NUMBER:
            if self.token_list[self.current_index].type == TokenType.IDENT:
                self.match(TokenType.IDENT)
            elif self.token_list[self.current_index].type == TokenType.NUMBER:
                self.match(TokenType.NUMBER)

    def compound_statement(self):
        self.match(TokenType.BEGINSYM)
        self.statements()

        while self.token_list[self.current_index].type == TokenType.SEMICOLONSYM:
            self.match(TokenType.SEMICOLONSYM)
            self.statements()

        self.match(TokenType.ENDSYM)

    def statements(self):
        current_token_type = self.token_list[self.current_index].type

        if current_token_type == TokenType.IDENT:
            self.assignment_statement()
        elif current_token_type == TokenType.IFSYM:
            self.conditional_statement()
        elif current_token_type == TokenType.WHILESYM:
            self.loop_statement()
        elif current_token_type == TokenType.BEGINSYM:
            self.compound_statement()
        else:
            # 处理 <空语句>
            pass

    # <赋值语句> -> <标识符> := <表达式>
    # 赋值语句 需要进行中间代码生成
    def assignment_statement(self):
        var_name = self.token_list[self.current_index].value  # 获取标识符的名称
        print(var_name)
        self.identifier()
        self.match(TokenType.BECOMESSYM)
        expr_result = self.expression()
        self.inter_code_gen.emit(':=', arg1=expr_result, arg2=None, result=var_name)
        print(1111)

    # <表达式> -> [+|-]项 | <表达式> <加法运算符> <项>
    def expression(self):
        if self.token_list[self.current_index].type in [TokenType.PLUSSYM, TokenType.MINUSSYM]:
            self.match(self.token_list[self.current_index].type)

        term_result = self.term()

        # 就是这里会报错
        while self.is_addition_operator(self.token_list[self.current_index].type):
            self.match(self.token_list[self.current_index].type)
            self.term()

        return term_result

    # <项> -> <因子> | <项> <乘法运算符> <因子>
    def term(self):
        factor_result = self.factor()

        # while self.is_multiplication_operator(self.token_list[self.current_index].type):
        #     self.match(self.token_list[self.current_index].type)
        #     self.factor()

        return factor_result

    # 测试简单的赋值语句
    # < 因子 > -> < 标识符 > | < 无符号整数 > | (< 表达式 >)
    def factor(self):
        if self.token_list[self.current_index].type == TokenType.IDENT:
            print("var")
            var_name = self.token_list[self.current_index].value
            self.identifier()
            return var_name  # 返回标识符
        elif self.token_list[self.current_index].type == TokenType.NUMBER:
            print("const")
            num_value = self.token_list[self.current_index].value
            self.match(TokenType.NUMBER)
            return num_value  # 返回数字值
        # 处理表达式
        elif self.token_list[self.current_index].type == TokenType.LPARENSYM:
            self.match(TokenType.LPARENSYM)
            expr_result = self.expression()
            self.match(TokenType.RPARENSYM)
            return expr_result
        else:
            # 处理错误或报告问题
            pass

    def is_addition_operator(self, token_type):
        return token_type in [TokenType.PLUSSYM, TokenType.MINUSSYM]

    def is_multiplication_operator(self, token_type):
        return token_type in [TokenType.TIMESSYM, TokenType.SLASHSYM]

    def conditional_statement(self):
        self.match(TokenType.IFSYM)
        self.condition()
        self.match(TokenType.THENSYM)
        self.statements()

    def loop_statement(self):
        self.match(TokenType.WHILESYM)
        self.condition()
        self.match(TokenType.DOSYM)
        self.statements()

    def condition(self):
        self.expression()
        self.relational_operator()
        self.expression()

    def relational_operator(self):
        token_type = self.token_list[self.current_index].type
        if token_type in [TokenType.EQLSYM, TokenType.NEQSYM, TokenType.LESSYM, TokenType.LEQSYM, TokenType.GTRSYM,
                          TokenType.GEQSYM]:
            self.match(token_type)
        else:
            # 处理错误或报告问题
            pass


if __name__ == "__main__":
    filename = "pl0_program.txt"
    lexer = PL0Lexer(filename)

    token_list = []
    while lexer.current_char:
        token = lexer.get_next_token()
        token_list.append(token)

        # 打印token信息
        print(f"({token.type}, {token.value})")

    lexer.input.close()

    parser = PL0Parser(token_list)
    parser.parse()
