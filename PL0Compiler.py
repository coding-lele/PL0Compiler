from lexer import *


class InterCodeGen:
    # IntermediateCode表示中间代码的一条指令
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
                    f'{self.arg1 if self.arg1 else "_"}, '
                    f'{self.arg2 if self.arg2 else "_"}, '
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
        self.code[self.line_counter] = self.IntermediateCode(op, arg1, arg2, result, self.line_counter)
        # self.code[self.line_counter] = self.IntermediateCode('=', 1, None, 'x', self.line_counter )
        # print(f'emit: {self.code[self.line_counter]}')
        self.line_counter += 1

    # 为变量字典添加元素
    def add_var(self, name: str):
        if name in self.var_dict:
            raise RuntimeError(f'该变量已存在，重复定义： {name}')
        if name in self.const_dict:
            raise RuntimeError(f'{name} 为常量，无法重复定义为变量')
        self.var_dict[name] = ''

    # 更新变量字典
    def update_var(self, name: str, value: str, line: int, col: int):
        if name not in self.var_dict:
            if name in self.const_dict:
                raise RuntimeError(f'赋值错误，因为是常量： {name}, at line {line}')
            else:
                raise RuntimeError(f'未定义的变量：{name}, at line {line}')
        self.var_dict[name] = value

    # 为常量字典添加元素
    def add_const(self, name: str, value: str):
        if name in self.const_dict:
            raise RuntimeError(f'该常量已存在，重复定义： {name}')
        self.const_dict[name] = value

    # 构建新临时变量
    def new_temp(self):
        temp_var = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp_var


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

    # 匹配当前词法单元，并将 currentIndex 移至下一个单元
    def match(self, expected_type):
        if self.current_token and self.current_token.type == expected_type:
            self.pre_token_info.line = self.token_info.line
            self.pre_token_info.col = self.token_info.col
            self.token_info.line = self.lexer.get_line()
            self.token_info.col = self.lexer.get_col()
            self.current_token = self.lexer.get_next_token()  # 读取下一个词法单元。如果读完文件，current_token的值为False
            # print("现在获取下一个字符是：", self.current_token.value)
        else:
            # 处理错误，可以输出错误信息或进行其他错误处理
            raise RuntimeError(f"Unexpected token: {TokenTypeName[self.current_token.type]}. "
                               f"Expected: {TokenTypeName[expected_type]}"
                               f", at line {self.lexer.get_line()}, col {self.lexer.get_col() - 1}")
            pass

    # <程序>-><程序首部><分程序>
    def program(self):
        # 程序首部
        self.program_header()
        # 分程序
        self.subprogram()

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
        if self.current_token.type == TokenType.SEMICOLONSYM:
            self.match(TokenType.SEMICOLONSYM)
        else:
            raise RuntimeError(
                f"常量说明缺少分号 at line {self.pre_token_info.line}, col {self.pre_token_info.col + 1}")

    # 新增修改 常量定义的等号是赋值符号
    # <常量定义> -> <标识符> := <无符号整数>
    def constant_definition(self):
        # 匹配标识符
        # self.match(TokenType.IDENT)
        name = self.identifier()
        # 匹配等号
        self.match(TokenType.BECOMESSYM)
        # 匹配无符号整数
        value = self.unsigned_integer()
        # 语义分析
        self.inter_code_gen.add_const(name, value)
        self.inter_code_gen.emit(':=', arg1=value, arg2=None, result=name)

    # <无符号整数> -> <数字>{<数字>}
    def unsigned_integer(self):
        # 匹配第一个数字
        number = self.current_token.value
        self.match(TokenType.NUMBER)

        # 匹配额外的数字
        while self.current_token.type == TokenType.NUMBER:
            self.match(TokenType.NUMBER)

        return number

    # <变量说明> -> VAR <标识符>{, <标识符>};
    def variable_declaration(self):
        # 匹配VAR
        self.match(TokenType.VARSYM)
        last_var_name = self.current_token.value
        # 匹配第一个标识符
        name = self.identifier()
        # 打印定义的变量
        # 语义 定义变量字典
        self.inter_code_gen.add_var(name)

        # 循环解析额外的标识符(如果有的话)
        while self.current_token.type == TokenType.COMMASYM:
            self.match(TokenType.COMMASYM)  # 匹配逗号
            name = self.identifier()  # 匹配标识符
            # yuyi 定义变量字典
            self.inter_code_gen.add_var(name)

        # 匹配结尾的分号
        if self.current_token.type != TokenType.SEMICOLONSYM:
            raise RuntimeError(f"变量说明缺少分号 at line {self.pre_token_info.line}, col {self.pre_token_info.col + 1}")
        else:
            self.match(TokenType.SEMICOLONSYM)

    # <标识符> -> <字母>{<字母> | <数字>}
    def identifier(self):
        # 匹配第一个字母
        ident = self.current_token.value
        self.match(TokenType.IDENT)
        return ident

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
            raise RuntimeError(f"复合语句缺少分号 at line {self.pre_token_info.line}, col {self.pre_token_info.col + 1}")
        else:
            raise RuntimeError(f"复合语句格式错误:缺少END")

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
        elif current_token_type == TokenType.SEMICOLONSYM or current_token_type == TokenType.ENDSYM or current_token_type == TokenType.EOF:
            pass
        else:
            raise RuntimeError(f"无法识别该语句种类 at line {self.lexer.get_line()}")

    # <赋值语句> -> <标识符> := <表达式>
    # 赋值语句 需要进行中间代码生成
    def assignment_statement(self):
        name = self.identifier()  # 匹配标识符
        self.match(TokenType.BECOMESSYM)  # 匹配 :=
        value = self.expression()  # 匹配表达式

        line = self.pre_token_info.line
        col = self.pre_token_info.col
        # 语义处理部分
        self.inter_code_gen.update_var(name, value, line, col)
        self.inter_code_gen.emit(':=', arg1=value, arg2=None, result=name)

    # <表达式> -> [+|-]项 | <表达式> <加法运算符> <项>
    def expression(self):
        flag = 0  # 用于判断是否有加减号
        op = "+"  # 默认是加号
        # 是否是+、-号
        if self.current_token.type in [TokenType.PLUSSYM, TokenType.MINUSSYM]:
            flag = 1
            op = self.current_token.value
            self.match(self.current_token.type)

        # 解析第一个项
        current_exp = self.term()

        if flag == 1:
            # 需要对加减号处理 加号不做处理
            # 对于减号 需要进行减号处理 替换为temp
            if op == '-':
                temp = self.inter_code_gen.new_temp()
                self.inter_code_gen.emit(op, temp, current_exp)
                current_exp = temp

        # 循环解析表达式
        # 解析加法运算符
        while self.is_addition_operator(self.current_token.type):
            # 加减法语义入栈
            op = self.current_token.value
            self.match(self.current_token.type)
            arg = self.term()
            temp = self.inter_code_gen.new_temp()
            self.inter_code_gen.emit(op, temp, current_exp, arg)
            current_exp = temp

        return current_exp

    # <项> -> <因子> | <项> <乘法运算符> <因子>
    def term(self):
        current_fac = self.factor()

        while self.is_multiplication_operator(self.current_token.type):
            # 乘除法语义入栈
            op = self.current_token.value
            self.match(self.current_token.type)
            fac = self.factor()
            temp = self.inter_code_gen.new_temp()
            self.inter_code_gen.emit(op, temp, current_fac, fac)
            current_fac = temp

        return current_fac

    # 测试简单的赋值语句
    # < 因子 > -> < 标识符 > | < 无符号整数 > | (< 表达式 >)
    def factor(self):
        if self.current_token.type == TokenType.IDENT:
            flag_var = 0
            # 错误处理：检查变量是否定义
            var_name = self.current_token.value
            if var_name not in self.inter_code_gen.var_dict:
                flag_var = 1  # 如果不在变量字典中则判断是否在常量字典中

            if flag_var == 1:
                if var_name not in self.inter_code_gen.const_dict:  # 如果不在常量字典中
                    raise RuntimeError(f"未定义的变量：{var_name}"
                                       f", at line {self.lexer.get_line()}, col {self.lexer.get_col() - 1}")
            else:
                # 检查变量是否已赋值
                if self.inter_code_gen.var_dict[var_name] == '':
                    raise RuntimeError(f"变量 '{var_name}' 在使用前未被赋值"
                                       f", at line {self.lexer.get_line()}, col {self.lexer.get_col() - 1}")
            fac = self.identifier()
        elif self.current_token.type == TokenType.NUMBER:
            # 新增修改 数字需要匹配 而不是 直接词法
            fac = self.unsigned_integer()
        # 识别表达式
        elif self.current_token.type == TokenType.LPARENSYM:
            self.match(TokenType.LPARENSYM)
            fac = self.expression()
            self.match(TokenType.RPARENSYM)  # 否则缺少右括号
        else:
            # 处理错误或报告问题
            raise RuntimeError(
                f"缺少因子或因子格式错误at line {self.pre_token_info.line}, col {self.pre_token_info.col + 1}")
            pass

        return fac  # 返回因子的值

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
        self.inter_code_gen.code[self.inter_code_gen.if_stack.pop()].write_back(
            self.inter_code_gen.line_counter)  # 回填 地址当前位linecount

    # <循环语句> → WHILE <条件> DO <语句>
    def loop_statement(self):
        self.match(TokenType.WHILESYM)  # 匹配关键字 WHILE
        # 这是循环开始的位置
        self.inter_code_gen.while_stack.append(self.inter_code_gen.line_counter)  # 记录循环开始的行
        self.condition("WHILE")  # 解析条件
        self.match(TokenType.DOSYM)  # 匹配关键字 DO
        self.statements()  # 解析语句

        write_back = self.inter_code_gen.while_stack.pop()  # 这是循环假出口的位置
        jump_back = self.inter_code_gen.while_stack.pop()  # 这是循环开始的位置

        self.inter_code_gen.emit('j', jump_back)  # 这是循环的最后一句 表示跳回循环判断
        self.inter_code_gen.code[write_back].write_back(self.inter_code_gen.line_counter)  # 再回填假出口 地址为当前linecount

    # <条件> → <表达式> <关系运算符> <表达式>
    def condition(self, flag):
        left = self.expression()  # 解析第一个表达式
        op = self.relational_operator()  # 解析关系运算符
        right = self.expression()  # 解析第二个表达式
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
            op = self.current_token.value
            self.match(token_type)
        else:
            # 处理错误或报告问题
            raise RuntimeError(f"非法的关系运算符 at line {self.lexer.get_line()}, col {self.lexer.get_col() - 1}")
            pass

        return op


if __name__ == "__main__":
    filename = "pl0_program.txt"

    parser = PL0Parser(filename)
    parser.parse()
    if parser.current_token.type != 27:
        raise RuntimeError(f"程序结尾存在非法语句或字符")
    print("result:")
    print(parser.inter_code_gen)

    # 把结果输出到文件中
    result = parser.inter_code_gen
    output_filename = "result.txt"
    with open(output_filename, "w") as output_file:
        output_file.write(str(result))

    print(f"Result written to {output_filename}")
