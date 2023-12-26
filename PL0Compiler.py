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

        # 地址写回
        def write_back(self, result):
            self.result = result
            # print("wrietback result:"+str(self.result))
            # print("回填地址过后的假出口：")
            # print(self)

    def __init__(self):
        self.code: dict[int: InterCodeGen.IntermediateCode] = {}  # 用dict便于回填
        self.temp_counter = 0  # 记录当前临时变量
        self.line_counter = 100  # 当前行数
        self.stack = []  # 用于存储当前读取到的产生式的值
        self.var_dict = {}  # 变量字典
        self.const_dict = {}  # 常量字典
        self.while_stack = []  # 记录循环开始的行和需要回填的行
        self.if_stack = []  # 记录需要回填的行

    def __str__(self):  # 字符串累计输出
        res = ''
        for c in self.code:
            res += f'{self.code[c]}\n'
        return res

    # 生成产生式
    def emit(self, op, result, arg1=None, arg2=None):
        arg1_str = '_' if arg1 is None else str(arg1)  # 使用下划线表示空
        arg2_str = '_' if arg2 is None else str(arg2)
        self.code[self.line_counter] = self.IntermediateCode(op, arg1_str, arg2_str, result, self.line_counter)
        # self.code[self.line_counter] = self.IntermediateCode('=', 1, None, 'x', self.line_counter )
        # print(f'emit: {self.code[self.line_counter]}')
        self.line_counter += 1

    # 为变量字典添加元素
    def add_var(self, name: str):
        if name in self.var_dict:
            raise RuntimeError(f'Redefinition in var {name}')
        self.var_dict[name] = ''

    # 更新变量字典
    def update_var(self, name: str, value: str):
        if name not in self.var_dict:
            if name in self.const_dict:
                raise RuntimeError(f'Cannot assign const {name}')
            else:
                raise RuntimeError(f'NotFound var {name}')
        self.var_dict[name] = value

    # 为常量字典添加元素
    def add_const(self, name: str, value: str):
        if name in self.const_dict:
            raise RuntimeError(f'Redefinition in const {name}')
        self.const_dict[name] = value

    # 构建新临时变量
    def new_temp(self):
        temp_var = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp_var


# 错误处理
class SyntaxError(Exception):
    def __init__(self, message, line, col):
        super().__init__(message)
        self.line = line
        self.col = col


class pre_pre_Token:
    def __init__(self):
        self.line = 0  # 词法单元类型
        self.col = 0  # 词法单元的值


class pre_Token:
    def __init__(self):
        self.line = 0  # 词法单元类型
        self.col = 0  # 词法单元的值


# 语法分析器（包含中间代码生成）
class PL0Parser:
    def __init__(self, filename):
        self.lexer = PL0Lexer(filename)  # 创建词法分析器实例
       # self.previous = self.lexer.get_next_token()  # 上一个词法单元
        self.token_info = pre_Token()  # 创建实例
        self.pre_token_info = pre_pre_Token()  # 创建实例
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

    # 匹配当前词法单元，并将 currentIndex 移至下一个单元
    def match(self, expected_type):
        if self.current_token and self.current_token.type == expected_type:
            # print("self.current_token.type: ", self.current_token.type)
            # print("expected_type: ", expected_type)
            # if self.current_index < len(self.token_list) - 1:  # 读到最后一句时指针不再后移
            #     self.current_index += 1
            self.pre_token_info.line = self.token_info.line
            self.pre_token_info.col = self.token_info.col
            self.token_info.line = self.lexer.get_line()
            self.token_info.col = self.lexer.get_col()
            # self.previous = self.current_token
            self.current_token = self.lexer.get_next_token()  # 读取下一个词法单元。如果读完文件，current_token的值为False
            # print("现在获取下一个字符是：", self.current_token.value)
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
        # 在这里直接识别标识符 还是调用identifier()呢 可以调用但没必要 算了
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
        if self.current_token.type == TokenType.SEMICOLONSYM:
            self.match(TokenType.SEMICOLONSYM)
        else:
            raise SyntaxError("常量说明缺少分号", self.pre_token_info.line, self.pre_token_info.col + 1)
            # self.raise_syntax_error("常量说明缺少分号")

    # 新增修改 常量定义的等号是赋值符号
    # <常量定义> -> <标识符> := <无符号整数>
    def constant_definition(self):
        # 匹配标识符
        #self.match(TokenType.IDENT)
        self.identifier()
        # 匹配等号
        self.match(TokenType.BECOMESSYM)
        # 匹配无符号整数
        self.unsigned_integer()
        # 语义分析
        if len(self.inter_code_gen.stack) < 2:
            raise RuntimeError(f"Stack underflow")
        value = self.inter_code_gen.stack.pop()
        name = self.inter_code_gen.stack.pop()
        self.inter_code_gen.add_const(name, value)
        self.inter_code_gen.emit(':=', arg1=value, arg2=None, result=name)

    # <无符号整数> -> <数字>{<数字>}
    def unsigned_integer(self):
        # 匹配第一个数字
        # print("当前数字：" + self.current_token.value)
        # 数字入栈
        self.inter_code_gen.stack.append(self.current_token.value)
        # 输出栈内信息
        # for item in self.inter_code_gen.stack:
        #     print("栈内信息：" + item)
        self.match(TokenType.NUMBER)

        # 匹配额外的数字
        while self.current_token.type == TokenType.NUMBER:
            self.match(TokenType.NUMBER)

    # <变量说明> -> VAR <标识符>{, <标识符>};
    def variable_declaration(self):
        # 匹配VAR
        self.match(TokenType.VARSYM)
        last_var_name = self.current_token.value
        # 匹配第一个标识符
        self.identifier()
        # 打印定义的变量
        # print("VAR:" + last_var_name)
        # yuyi 定义变量字典
        if len(self.inter_code_gen.stack) < 1:
            raise RuntimeError(f"Stack underflow ")
        name = self.inter_code_gen.stack.pop()
        self.inter_code_gen.add_var(name)

        # 循环解析额外的标识符(如果有的话)
        while self.current_token.type == TokenType.COMMASYM:
            self.match(TokenType.COMMASYM)  # 匹配逗号
            # last_var_name = self.current_token.value
            self.identifier()  # 匹配标识符
            # print("VAR:" + last_var_name)
            # yuyi 定义变量字典
            if len(self.inter_code_gen.stack) < 1:
                raise RuntimeError(f"Stack underflow ")
            name = self.inter_code_gen.stack.pop()
            self.inter_code_gen.add_var(name)

        # 匹配结尾的分号
        if self.current_token.type != TokenType.SEMICOLONSYM:
            raise SyntaxError("变量说明缺少分号", self.pre_token_info.line, self.pre_token_info.col + 1)
        else:
            self.match(TokenType.SEMICOLONSYM)

    # <标识符> -> <字母>{<字母> | <数字>}
    def identifier(self):
        # 匹配第一个字母
        # print("当前标识符名称：" + self.current_token.value)
        self.inter_code_gen.stack.append(self.current_token.value)
        # 输出栈内信息
        # for item in self.inter_code_gen.stack:
        #     print("栈内信息：" + item)
        self.match(TokenType.IDENT)

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
        elif self.current_token.type != TokenType.ENDSYM and self.current_token.type != TokenType.SEMICOLONSYM:
            # self.raise_syntax_error("复合语句缺少分号")
            raise SyntaxError("复合语句缺少分号", self.pre_token_info.line, self.pre_token_info.col + 1)
        else:
            self.raise_syntax_error("复合语句格式错误:缺少END")

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
        # var_name = self.current_token.value  # 获取标识符的名称
        self.identifier()  # 匹配标识符
        self.match(TokenType.BECOMESSYM)  # 匹配 :=
        expr_result = self.expression()  # 匹配表达式

        # 语义处理部分
        if len(self.inter_code_gen.stack) < 2:
            raise RuntimeError(f"Stack underflow")
        value = self.inter_code_gen.stack.pop()
        name = self.inter_code_gen.stack.pop()
        self.inter_code_gen.update_var(name, value)
        self.inter_code_gen.emit(':=', arg1=value, arg2=None, result=name)
        #print(1111)

    # <表达式> -> [+|-]项 | <表达式> <加法运算符> <项>
    def expression(self):
        flag = 0  # 用于判断是否有加减号
        # 是否是+、-号
        if self.current_token.type in [TokenType.PLUSSYM, TokenType.MINUSSYM]:
            flag = 1
            # 把正负号入栈
            self.inter_code_gen.stack.append(self.current_token.value)
            self.match(self.current_token.type)

        # 解析第一个项
        self.term()

        if flag == 1:
            # 需要对加减号处理 加号不做处理 所以把当前值出栈再入栈就可以
            # 对于减号 需要进行减号处理 替换为temp
            if len(self.inter_code_gen.stack) < 2:
                raise RuntimeError(f"Stack underflow ")
            item = self.inter_code_gen.stack.pop()
            op = self.inter_code_gen.stack.pop()
            if op == '-':
                temp = self.inter_code_gen.new_temp()
                self.inter_code_gen.stack.append(temp)
                self.inter_code_gen.emit(op, temp, item)
            else:
                self.inter_code_gen.stack.append(item)

        while_count = 0  # 用于记录循环几次加法

        # 循环解析表达式
        # 解析加法运算符
        while self.is_addition_operator(self.current_token.type):
            while_count += 1
            # 加减法语义入栈
            # print("当前加法运算符:" + self.current_token.value)
            op = self.current_token.value
            self.inter_code_gen.stack.append(op)
            self.match(self.current_token.type)
            # 输出栈内信息
            # for item in self.inter_code_gen.stack:
            #     print("栈内信息：" + item)
            self.term()

        # print("while_count:"+str(while_count))

        # 用于循环处理多个+法 如 x+1+2+3+4
        while while_count != 0:
            if len(self.inter_code_gen.stack) < 3:
                raise RuntimeError(f"Stack underflow ")
            right = self.inter_code_gen.stack.pop()
            op = self.inter_code_gen.stack.pop()
            left = self.inter_code_gen.stack.pop()
            temp = self.inter_code_gen.new_temp()
            self.inter_code_gen.stack.append(temp)
            self.inter_code_gen.emit(op, temp, left, right)
            while_count -= 1

    # <项> -> <因子> | <项> <乘法运算符> <因子>
    def term(self):
        self.factor()

        while_count = 0  # 用于记录循环几次乘法

        while self.is_multiplication_operator(self.current_token.type):
            while_count += 1
            # 乘除法语义入栈
            # print("当前乘法运算符:" + self.current_token.value)
            op = self.current_token.value
            self.inter_code_gen.stack.append(op)
            self.match(self.current_token.type)
            # 输出栈内信息
            # for item in self.inter_code_gen.stack:
            #     print("栈内信息：" + item)
            self.factor()

        # print("while_count:" + str(while_count))

        # 用于循环处理多个*法
        while while_count != 0:
            if len(self.inter_code_gen.stack) < 3:
                raise RuntimeError(f"Stack underflow ")
            right = self.inter_code_gen.stack.pop()
            op = self.inter_code_gen.stack.pop()
            left = self.inter_code_gen.stack.pop()
            temp = self.inter_code_gen.new_temp()
            self.inter_code_gen.stack.append(temp)
            self.inter_code_gen.emit(op, temp, left, right)
            while_count -= 1

    # 测试简单的赋值语句
    # < 因子 > -> < 标识符 > | < 无符号整数 > | (< 表达式 >)
    def factor(self):
        if self.current_token.type == TokenType.IDENT:
            # print("var")
            self.identifier()
        elif self.current_token.type == TokenType.NUMBER:
            # print("const")
            # 新增修改 数字需要匹配 而不是 直接词法
            self.unsigned_integer()
        # 识别表达式
        elif self.current_token.type == TokenType.LPARENSYM:
            # print("express")
            self.match(TokenType.LPARENSYM)
            self.expression()
            self.match(TokenType.RPARENSYM)  # 否则缺少右括号
        else:
            # 处理错误或报告问题
            # raise SyntaxError("缺少因子或因子格式错误", self.token_info.line, self.token_info.col)
            raise SyntaxError("缺少因子或因子格式错误", self.pre_token_info.line, self.pre_token_info.col + 1)
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
        self.condition("IF")  # 解析条件
        self.match(TokenType.THENSYM)  # 匹配关键字 THEN
        self.statements()  # 解析语句
        # IF条件句在这里结束了 需要回填
        if len(self.inter_code_gen.if_stack) < 1:
            raise RuntimeError(f"Stack underflow ")
        self.inter_code_gen.code[self.inter_code_gen.if_stack.pop()].write_back(self.inter_code_gen.line_counter)  # 回填 地址当前位linecount

    # <循环语句> → WHILE <条件> DO <语句>
    def loop_statement(self):
        self.match(TokenType.WHILESYM)  # 匹配关键字 WHILE
        # 这是循环开始的位置
        self.inter_code_gen.while_stack.append(self.inter_code_gen.line_counter)  # 记录循环开始的行

        self.condition("WHILE")  # 解析条件
        self.match(TokenType.DOSYM)  # 匹配关键字 DO
        self.statements()  # 解析语句

        if len(self.inter_code_gen.while_stack) < 2:
            raise RuntimeError(f"Stack underflow ")
        write_back = self.inter_code_gen.while_stack.pop()  # 这是循环假出口的位置
        jump_back = self.inter_code_gen.while_stack.pop()  # 这是循环开始的位置

        self.inter_code_gen.emit('j', jump_back)  # 这是循环的最后一句 表示跳回循环判断
        self.inter_code_gen.code[write_back].write_back(self.inter_code_gen.line_counter)  # 再回填假出口 地址为当前linecount

    # <条件> → <表达式> <关系运算符> <表达式>
    def condition(self, flag):
        self.expression()  # 解析第一个表达式
        self.relational_operator()  # 解析关系运算符
        self.expression()  # 解析第二个表达式
        if len(self.inter_code_gen.stack) < 3:
            raise RuntimeError(f"Stack underflow ")
        right = self.inter_code_gen.stack.pop()
        op = self.inter_code_gen.stack.pop()
        left = self.inter_code_gen.stack.pop()
        # 处理真出口语句
        self.inter_code_gen.emit(f'j{op}', self.inter_code_gen.line_counter + 2, left, right)  # 跳转至真出口，即下下句
        if flag == "IF":
            # 处理IF假出口语句
            self.inter_code_gen.if_stack.append(self.inter_code_gen.line_counter)  # 记录假出口所在行
            self.inter_code_gen.emit('j', -1)  # 假出口，等待回填
        else:
            # WHILE 的条件判断处理的部分
            self.inter_code_gen.while_stack.append(self.inter_code_gen.line_counter)  # 记录假出口所在行 为了之后能找到这个位置来回填
            self.inter_code_gen.emit('j', -1)  # 假出口，等待回填

    # <关系运算符> → = | <> | < | <= | > | >=
    def relational_operator(self):
        token_type = self.current_token.type
        if token_type in [TokenType.EQLSYM, TokenType.NEQSYM, TokenType.LESSYM, TokenType.LEQSYM, TokenType.GTRSYM,
                          TokenType.GEQSYM]:
            # 对关系运算符的栈语义处理
            # print("当前关系运算符："+self.current_token.value)
            op = self.current_token.value
            self.inter_code_gen.stack.append(op)
            # 输出栈内信息
            # for item in self.inter_code_gen.stack:
            #     print("栈内信息：" + item)

            self.match(token_type)
        else:
            # 处理错误或报告问题
            # self.raise_syntax_error("非法的关系运算符")
            raise SyntaxError("非法的关系运算符", self.lexer.get_line(), self.lexer.get_col() - 1)
            pass


if __name__ == "__main__":
    filename = "pl0_program.txt"

    parser = PL0Parser(filename)
    parser.parse()
    print("result:")
    print(parser.inter_code_gen)

