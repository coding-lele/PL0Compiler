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
        # self.code[self.line_counter] = self.IntermediateCode('=', 1, None, 'x', self.line_counter )
        print(f'emit: {self.code[self.line_counter]}')
        self.line_counter += 1


# 错误处理
class SyntaxError(Exception):
    def __init__(self, message, line, col):
        super().__init__(message)
        self.line = line
        self.col = col


# 语法分析器（包含中间代码生成）
class PL0Parser:
    def __init__(self, filename):
        self.lexer = PL0Lexer(filename)  # 创建词法分析器实例
        self.current_token = self.lexer.get_next_token()  # 当前词法单元
        self.intermediate_code_list = []  # 中间代码列表
        self.intermediate_code_index = 0  # 中间代码索引
        # 创建 InterCodeGen 的实例
        self.inter_code_gen = InterCodeGen()


    # 开始语法分析
    def parse(self):
        self.program()

    # 语法错误信息
    def raise_syntax_error(self, message):
        raise SyntaxError(message, self.lexer.get_line(), self.lexer.get_col())

    # # 在类中增加获取当前行列的方法
    # def get_line(self):
    #     return self.PL0Lexer.get_line()
    #
    # def get_col(self):
    #     return self.PL0Lexer.get_col()

    # 匹配当前词法单元，并将 currentIndex 移至下一个单元
    def match(self, expected_type):
        if self.current_token and self.current_token.type == expected_type:
            print("self.current_token.type")
            print(self.current_token.type)
            print("expected_type")
            print(expected_type)
            # if self.current_index < len(self.token_list) - 1:  # 读到最后一句时指针不再后移
            #     self.current_index += 1
            self.current_token = self.lexer.get_next_token()  # 读取下一个词法单元。如果读完文件，current_token的值为False
        else:
            # 处理错误，可以输出错误信息或进行其他错误处理
            self.raise_syntax_error(f"Unexpected token: {self.current_token.type}"
                                    f". Expected: {expected_type}")
            pass

    # <程序>-><程序首部><分程序>
    def program(self):
        try:
            # 程序首部
            self.program_header()
            # 分程序
            self.subprogram()
        except SyntaxError as e:
            print(f"SyntaxError: {e} at line {e.line}, col {e.col}")

    # <程序首部>->PROGRAM <标识符>
    def program_header(self):
        # 匹配关键字 PROGRAM
        self.match(TokenType.PROGRAMSYM)  # 否则缺少关键字
        # 匹配标识符
        self.match(TokenType.IDENT)  # 否则缺少标识符

    # <分程序>->[<常量说明>][<变量说明>]<语句>（注：[ ]中的项表示可选）
    def subprogram(self):
        # 如果是常量说明
        if self.current_token.type == TokenType.CONSTSYM:
            self.constant_declaration()

        # 如果是变量说明
        if self.current_token.type == TokenType.VARSYM:
            self.variable_declaration()

        # 解析语句
        self.statements()

    # <常量说明> -> CONST <常量定义>{, <常量定义>};
    def constant_declaration(self):
        # 匹配 CONST
        self.match(TokenType.CONSTSYM)
        # 匹配第一个常量定义
        self.constant_definition()

        # 解析额外的常量定义(如果有的话)
        while self.current_token.type == TokenType.COMMASYM:
            self.match(TokenType.COMMASYM)
            self.constant_definition()

        # 匹配结尾的分号
        self.match(TokenType.SEMICOLONSYM)

    # <常量定义> -> <标识符> = <无符号整数>
    def constant_definition(self):
        # 匹配标识符
        self.match(TokenType.IDENT)
        # 匹配等号
        self.match(TokenType.EQLSYM)
        # 匹配无符号整数
        self.unsigned_integer()

    # <无符号整数> -> <数字>{<数字>}
    def unsigned_integer(self):
        # 匹配第一个数字
        self.match(TokenType.NUMBER)

        # 匹配额外的数字
        while self.current_token.type == TokenType.NUMBER:
            self.match(TokenType.NUMBER)

    # <变量说明> -> VAR <标识符>{, <标识符>};
    def variable_declaration(self):
        # 匹配VAR
        self.match(TokenType.VARSYM)
        # 匹配第一个标识符
        self.identifier()

        # 循环解析额外的标识符(如果有的话)
        while self.current_token.type == TokenType.COMMASYM:
            self.match(TokenType.COMMASYM)  # 匹配逗号
            self.identifier()  # 匹配标识符

        # 匹配结尾的分号
        self.match(TokenType.SEMICOLONSYM)

    # <标识符> -> <字母>{<字母> | <数字>}
    def identifier(self):
        # 匹配第一个字母
        self.match(TokenType.IDENT)

        # 循环解析额外的字母或数字
        while self.current_token.type == TokenType.IDENT \
                or self.current_token.type == TokenType.NUMBER:
            if self.current_token.type == TokenType.IDENT:
                self.match(TokenType.IDENT)  # 匹配字母
            elif self.current_token.type == TokenType.NUMBER:
                self.match(TokenType.NUMBER)  # 匹配数字

    # <复合语句> -> BEGIN <语句>{; <语句>} END
    def compound_statement(self):
        self.match(TokenType.BEGINSYM)  # 匹配关键字 BEGIN
        self.statements()  # 解析第一个语句

        # 解析以分号分隔的附加语句
        while self.current_token.type == TokenType.SEMICOLONSYM:
            self.match(TokenType.SEMICOLONSYM)
            self.statements()

        if self.current_token.type == TokenType.ENDSYM:
            self.match(TokenType.ENDSYM)  # 匹配关键字 END
        else:
            self.raise_syntax_error("复合语句格式错误")

    # <语句> -> <赋值语句> | <条件语句> | <循环语句> | <复合语句> | <空语句>
    def statements(self):
        current_token_type = self.current_token.type

        # 检查当前符号的类型并调用相应的函数
        if current_token_type == TokenType.IDENT:
            self.assignment_statement()
        elif current_token_type == TokenType.IFSYM:
            self.conditional_statement()
        elif current_token_type == TokenType.WHILESYM:
            self.loop_statement()
        elif current_token_type == TokenType.BEGINSYM:
            self.compound_statement()
        # 处理 <空语句>
        elif current_token_type == TokenType.SEMICOLONSYM or current_token_type == TokenType.ENDSYM:
            pass
        else:
            self.raise_syntax_error("无法识别该语句种类")

    # <赋值语句> -> <标识符> := <表达式>
    # 赋值语句 需要进行中间代码生成
    def assignment_statement(self):
        var_name = self.current_token.value  # 获取标识符的名称
        print(var_name)
        self.identifier()  # 匹配标识符
        self.match(TokenType.BECOMESSYM)  # 匹配 :=
        expr_result = self.expression()  # 匹配表达式
        self.inter_code_gen.emit(':=', arg1=expr_result, arg2=None, result=var_name)
        print(1111)

    # <表达式> -> [+|-]项 | <表达式> <加法运算符> <项>
    def expression(self):
        # 是否是+、-号
        if self.current_token.type in [TokenType.PLUSSYM, TokenType.MINUSSYM]:
            self.match(self.current_token.type)

        # 解析第一个项
        term_result = self.term()

        # 循环解析表达式
        while self.is_addition_operator(self.current_token.type):
            self.match(self.current_token.type)
            self.term()

        return term_result

    # <项> -> <因子> | <项> <乘法运算符> <因子>
    def term(self):
        factor_result = self.factor()

        while self.is_multiplication_operator(self.current_token.type):
            self.match(self.current_token.type)
            self.factor()

        return factor_result

    # 测试简单的赋值语句
    # < 因子 > -> < 标识符 > | < 无符号整数 > | (< 表达式 >)
    def factor(self):
        if self.current_token.type == TokenType.IDENT:
            print("var")
            var_name = self.current_token.value
            self.identifier()
            return var_name  # 返回标识符
        elif self.current_token.type == TokenType.NUMBER:
            print("const")
            num_value = self.current_token.value
            self.match(TokenType.NUMBER)
            return num_value  # 返回数字值
        # 识别表达式
        elif self.current_token.type == TokenType.LPARENSYM:
            self.match(TokenType.LPARENSYM)
            expr_result = self.expression()
            self.match(TokenType.RPARENSYM)  # 否则缺少右括号
            return expr_result
        else:
            # 处理错误或报告问题
            self.raise_syntax_error("缺少因子或因子格式错误")
            pass

    # <加法运算符> -> + | -
    # 匹配加法运算符，返回true表示成功匹配，否则返回false
    def is_addition_operator(self, token_type):
        return token_type in [TokenType.PLUSSYM, TokenType.MINUSSYM]

    # <乘法运算符> -> * | /
    # 匹配乘法运算符，返回true表示成功匹配，否则返回false
    def is_multiplication_operator(self, token_type):
        return token_type in [TokenType.TIMESSYM, TokenType.SLASHSYM]

    # <条件语句> → IF <条件> THEN <语句>
    def conditional_statement(self):
        self.match(TokenType.IFSYM)  # 匹配关键字 IF
        self.condition()  # 解析条件
        self.match(TokenType.THENSYM)  # 匹配关键字 THEN
        self.statements()  # 解析语句

    # <循环语句> → WHILE <条件> DO <语句>
    def loop_statement(self):
        self.match(TokenType.WHILESYM)  # 匹配关键字 WHILE
        self.condition()  # 解析条件
        self.match(TokenType.DOSYM)  # 匹配关键字 DO
        self.statements()  # 解析语句

    # <条件> → <表达式> <关系运算符> <表达式>
    def condition(self):
        self.expression()  # 解析第一个表达式
        self.relational_operator()  # 解析关系运算符
        self.expression()  # 解析第二个表达式

    # <关系运算符> → = | <> | < | <= | > | >=
    def relational_operator(self):
        token_type = self.current_token.type
        if token_type in [TokenType.EQLSYM, TokenType.NEQSYM, TokenType.LESSYM, TokenType.LEQSYM, TokenType.GTRSYM,
                          TokenType.GEQSYM]:
            self.match(token_type)
        else:
            # 处理错误或报告问题
            self.raise_syntax_error("非法的关系运算符")
            pass


if __name__ == "__main__":
    filename = "pl0_program.txt"

    parser = PL0Parser(filename)
    parser.parse()
