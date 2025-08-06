from collections import defaultdict
filename: str = ''

def retrieve(targetRegister):
    output = '@SP\n' + 'M=M-1\n' + 'A=M\n'
    if targetRegister == 'A':
        output += 'A=M\n'
    elif targetRegister == 'D':
        output += 'D=M\n'
    else:
        raise Exception('Sorry, the strings "A" and "D" are the only valid inputs')
    return output

def c_pop(segment, index):
    global filename
    output = ''
    memory = '@R13\n'
    temp = '@5\n'
    output += f'@{index}\n' + 'D=A\n'
    match segment:
        case 'argument':
            output += '@ARG\n'
        case 'local':
            output += '@LCL\n'
        case 'this':
            output += '@THIS\n'
        case 'that':
            output += '@THAT\n'
        case 'temp':
            output += temp + 'D=D+A\n' + memory + 'M=D\n' + retrieve('D') + memory + 'A=M\n' + 'M=D\n'
            return output
        case 'static':
            output = retrieve('D') + f'@{filename}.{index}\n' + 'M=D\n'
            return output
        case 'pointer':
            if index == '0':
                output = retrieve('D') + '@THIS\n' + 'M=D\n'
            else:
                output = retrieve('D') + '@THAT\n' + 'M=D\n'
            return output
    output += 'A=M\n' + 'D=D+A\n' + memory + 'M=D\n' + retrieve('D') + memory + 'A=M\n' + 'M=D\n'
    return output



def push(segment = 'None', index = 'None'):
    global filename
    output = ''
    temp = '@5\n'
    if index != 'None':
        output += f'@{index}\n' + 'D=A\n'
    match segment:
        case 'local':
            output += '@LCL\n' + 'A=D+M\n' + 'D=M\n'
        case 'this':
            output += '@THIS\n' + 'A=D+M\n' + 'D=M\n'
        case 'that':
            output += '@THAT\n' + 'A=D+M\n' + 'D=M\n'
        case 'argument':
            output += '@ARG\n' + 'A=D+M\n' + 'D=M\n'
        case 'temp':
            output += temp + 'A=D+A\n' + 'D=M\n'
        case 'pointer':
            if index == '0':
                output = '@THIS\n' + 'D=M\n'
            elif index == '1':
                output = '@THAT\n' + 'D=M\n'
        case 'static':
            output = f'@{filename}.{index}\n' + 'D=M\n'
    output += '@SP\n' + 'A=M\n' + 'M=D\n' + '@SP\n' + 'M=M+1\n'
    return output

def c_arithmetic(command, linecount):
    output = ''
    # sets target ram to 0 if comparison failed or -1 if comparison succeeded
    ramSetStart = '@SP\n' + 'A=M\n'
    ramSetEnd = '@SP\n' + 'M=M+1\n'
    falseValue = 'M=0\n'
    trueValue = 'M=-1\n'
    jumpStatement = f'@FINISH{linecount}\n' + '0;JMP\n'
    jumpTarget = f'(FINISH{linecount})\n'

    comparisonFailed = ramSetStart + falseValue + ramSetEnd + jumpStatement
    comparisonSuccess = ramSetStart + trueValue + ramSetEnd + jumpTarget
    match command:
        case 'add':
            output += retrieve('D') + retrieve('A') + 'D=D+A\n' + push()

        case 'sub':
            output += retrieve('D') + retrieve('A') + 'D=A-D\n' + push()

        case 'neg':
            output += retrieve('D') + 'M=-D\n' + '@SP' + '\n' + 'M=M+1' + '\n'

        # comparisons: -1 = true, 0 = false
        case 'eq':
            output += \
                (
                        retrieve('D') + retrieve('A') + 'D=A-D\n' + f'@EQ{linecount}\n' + 'D;JEQ\n' +
                        comparisonFailed + f'(EQ{linecount})\n' + comparisonSuccess
                )
        case 'gt':
            output += \
                (
                        retrieve('D') + retrieve('A') + 'D=A-D\n' f'@GT{linecount}\n' + 'D;JGT\n' +
                        comparisonFailed + f'(GT{linecount})\n' + comparisonSuccess
                )
        case 'lt':
            output += \
                (
                        retrieve('D') + retrieve('A') + 'D=A-D\n' + f'@LT{linecount}\n' + 'D;JLT\n' +
                        comparisonFailed + f'(LT{linecount})\n' + comparisonSuccess
                )
        case 'and':
            output += retrieve('D') + retrieve('A') + 'D=D&A\n' + push()

        case 'or':
            output += retrieve('D') + retrieve('A') + 'D=D|A\n' + push()

        case 'not':
            output += retrieve('D') + 'D=!D\n' + 'M=D\n' + '@SP\n' + 'M=M+1\n'
    return output

def c_label(label):
    output: str = ''
    if len(label) == 0:
        return output
    if label[0].isnumeric():
        raise Exception('labels cannot start with numbers')
    newLabel = label.upper()
    output += f'({newLabel})\n'
    return output

def c_goto(label):
    output = f'@{label}\n' + '0;JMP\n'
    return output

def c_if(label):
    output = retrieve('D') + f'@{label}\n' + 'D;JNE\n'
    return output

def c_return():
    pass

def c_function():
    pass

def parser(line):
    commandType = str()
    arg1 = str()
    arg2 = str()
    if len(line) > 1 and line[0] != '/':
        if line[0] =='\t':
            arguments = line[1:-1].split(' ')
        else:
            arguments = line[:-1].split(' ')

        match arguments[0]:
            case 'push':
                commandType = 'C_PUSH'
                arg1 = arguments[1]
                arg2 = arguments[2]
            case 'pop':
                commandType = 'C_POP'
                arg1 = arguments[1]
                arg2 = arguments[2]
            case 'label':
                commandType = 'C_LABEL'
                arg1 = arguments[1]
            case 'if-goto':
                commandType = 'C_IF'
                arg1 = arguments[1]
            case 'goto':
                commandType = 'C_GOTO'
                arg1 = arguments[1]
            case _:
                commandType = 'C_ARITHMETIC'
                arg1 = arguments[0]

    return commandType, arg1, arg2

def codeWriter(command, linecount):
    output = ''

    dispatch_table = defaultdict(list)
    dispatch_table['C_PUSH'].append(push(command[1], command[2]))
    dispatch_table['C_ARITHMETIC'].append(c_arithmetic(command[1], linecount))
    dispatch_table['C_POP'].append(c_pop(command[1], command[2]))
    dispatch_table['C_LABEL'].append(c_label(command[1]))
    dispatch_table['C_IF'].append(c_if(command[1]))
    dispatch_table['C_GOTO'].append(c_goto(command[1]))

    output = dispatch_table[command[0]]
    return output

def endCode():
    end = '@END\n' + '0;JMP\n' #put the (END) label back in after FibonacciSeries
    return end

def bootstrap():
    pass

def VirtualMachine2():
    global filename
    filename = input("Please input file name without extension: ")
    with open(filename + '.vm', 'r') as bytecode:
        with open(filename + ".asm", 'w') as machineCode:
            for lineCount, line in enumerate(bytecode):
                command = parser(line)
                output = codeWriter(command, lineCount)
                for item in output:
                    machineCode.write(item)
            end = endCode()
            machineCode.write(end)
            return

VirtualMachine2()