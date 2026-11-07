import ast
import operator
import re
import sys
import os
import shutil
import subprocess
import tempfile


# =========================================================
# CraftLang — интерпретатор
# =========================================================

class CraftLangError(Exception):
    pass


# =========================================================
# Игровой движок
# =========================================================

GAME = None


class GameEngine:
    def __init__(self, width=800, height=600, title="CraftLang Game"):
        try:
            import pygame
        except ImportError:
            raise CraftLangError(
                "Pygame не установлен. Выполни: py -m pip install pygame"
            )

        self.pygame = pygame
        pygame.init()

        self.width = int(width)
        self.height = int(height)
        self.title = str(title)

        self.screen = pygame.display.set_mode(
            (self.width, self.height)
        )

        pygame.display.set_caption(self.title)

        self.clock = pygame.time.Clock()
        self.objects = []

        self.controls = {
            "w": "вверх",
            "s": "вниз",
            "a": "влево",
            "d": "вправо"
        }

        self.running = True
        self.background = (30, 30, 40)

    def create_rectangle(self, x=100, y=100, size=50, color="синий"):
        obj = {
            "тип": "прямоугольник",
            "x": int(x),
            "y": int(y),
            "ширина": int(size),
            "высота": int(size),
            "цвет": color,
            "скорость": 5
        }

        self.objects.append(obj)
        return obj

    def color_value(self, color):
        colors = {
            "синий": (60, 150, 255),
            "красный": (255, 60, 60),
            "зелёный": (60, 220, 100),
            "зеленый": (60, 220, 100),
            "жёлтый": (255, 220, 50),
            "желтый": (255, 220, 50),
            "белый": (255, 255, 255),
            "чёрный": (0, 0, 0),
            "черный": (0, 0, 0),
            "фиолетовый": (160, 80, 255),
            "оранжевый": (255, 140, 40)
        }

        if isinstance(color, (list, tuple)) and len(color) == 3:
            return tuple(int(x) for x in color)

        return colors.get(str(color).lower(), (60, 150, 255))

    def set_control(self, key, direction):
        self.controls[str(key).lower()] = str(direction).lower()

    def run(self):
        pygame = self.pygame

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            keys = pygame.key.get_pressed()

            for key, direction in self.controls.items():
                pygame_key = getattr(
                    pygame,
                    "K_" + key,
                    None
                )

                if pygame_key is None:
                    continue

                if keys[pygame_key]:
                    for obj in self.objects:
                        speed = obj.get("скорость", 5)

                        if direction == "вверх":
                            obj["y"] -= speed
                        elif direction == "вниз":
                            obj["y"] += speed
                        elif direction == "влево":
                            obj["x"] -= speed
                        elif direction == "вправо":
                            obj["x"] += speed

            self.screen.fill(self.background)

            for obj in self.objects:
                pygame.draw.rect(
                    self.screen,
                    self.color_value(obj.get("цвет", "синий")),
                    (
                        obj.get("x", 0),
                        obj.get("y", 0),
                        obj.get("ширина", 50),
                        obj.get("высота", 50)
                    )
                )

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


# =========================================================
# Вычисление выражений
# =========================================================

def evaluate(expression, variables, objects):
    expression = expression.strip()

    if not expression:
        return None

    expression = re.sub(r"\bи\b", "and", expression)
    expression = re.sub(r"\bили\b", "or", expression)
    expression = re.sub(r"\bне\b", "not", expression)

    expression = re.sub(r"\bистина\b", "True", expression)
    expression = re.sub(r"\bложь\b", "False", expression)

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise CraftLangError(
            f"Неправильное выражение: {expression}"
        ) from error

    def calculate(node):
        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Name):
            if node.id in variables:
                return variables[node.id]

            if node.id in objects:
                return objects[node.id]

            raise CraftLangError(
                f"Неизвестное имя: {node.id}"
            )

        if isinstance(node, ast.BinOp):
            left = calculate(node.left)
            right = calculate(node.right)

            operations = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.FloorDiv: operator.floordiv,
                ast.Mod: operator.mod,
                ast.Pow: operator.pow
            }

            operation = operations.get(type(node.op))

            if operation is None:
                raise CraftLangError(
                    "Арифметический оператор не поддерживается"
                )

            return operation(left, right)

        if isinstance(node, ast.UnaryOp):
            value = calculate(node.operand)

            if isinstance(node.op, ast.USub):
                return -value

            if isinstance(node.op, ast.UAdd):
                return +value

            if isinstance(node.op, ast.Not):
                return not value

        if isinstance(node, ast.Compare):
            left = calculate(node.left)

            comparisons = {
                ast.Eq: operator.eq,
                ast.NotEq: operator.ne,
                ast.Lt: operator.lt,
                ast.LtE: operator.le,
                ast.Gt: operator.gt,
                ast.GtE: operator.ge
            }

            for op_node, right_node in zip(
                node.ops,
                node.comparators
            ):
                right = calculate(right_node)
                operation = comparisons.get(type(op_node))

                if operation is None:
                    raise CraftLangError(
                        "Оператор сравнения не поддерживается"
                    )

                if not operation(left, right):
                    return False

                left = right

            return True

        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return all(
                    calculate(value)
                    for value in node.values
                )

            if isinstance(node.op, ast.Or):
                return any(
                    calculate(value)
                    for value in node.values
                )

        if isinstance(node, ast.List):
            return [
                calculate(element)
                for element in node.elts
            ]

        if isinstance(node, ast.Tuple):
            return tuple(
                calculate(element)
                for element in node.elts
            )

        if isinstance(node, ast.Subscript):
            value = calculate(node.value)
            index = calculate(node.slice)
            return value[index]

        if isinstance(node, ast.Attribute):
            obj = calculate(node.value)

            if not isinstance(obj, dict):
                raise CraftLangError(
                    "Нельзя получить свойство у этого значения"
                )

            if node.attr not in obj:
                raise CraftLangError(
                    f"Свойство не найдено: {node.attr}"
                )

            return obj[node.attr]

        raise CraftLangError(
            f"Выражение не поддерживается: {type(node).__name__}"
        )

    return calculate(tree.body)


# =========================================================
# Поиск конца блока
# =========================================================

def find_block_end(lines, start):
    depth = 1

    for index in range(start + 1, len(lines)):
        line = lines[index].strip()

        if (
            line.startswith("если ")
            or line.startswith("пока ")
            or line.startswith("повтор ")
            or line.startswith("функция ")
            or line.startswith("создать объект ")
            or line == "управление игроком"
        ):
            depth += 1

        elif line == "end":
            depth -= 1

            if depth == 0:
                return index

    raise CraftLangError(
        f"Не найден end для строки {start + 1}"
    )


# =========================================================
# Поиск функций
# =========================================================

def find_functions(lines):
    functions = {}
    index = 0

    while index < len(lines):
        line = lines[index].strip()

        if line.startswith("функция "):
            name = line[len("функция "):].strip()
            end = find_block_end(lines, index)

            functions[name] = lines[index + 1:end]
            index = end + 1
        else:
            index += 1

    return functions


# =========================================================
# Исполнение CraftLang
# =========================================================

def execute_block(
    lines,
    variables,
    objects,
    functions,
    depth=0
):
    global GAME

    if depth > 100:
        raise CraftLangError(
            "Слишком большая глубина вызовов"
        )

    index = 0

    while index < len(lines):
        line = lines[index].strip()
        index += 1

        if not line or line.startswith("#") or line == "end":
            continue

        # Игровое окно
        if line.startswith("окно = создать окно"):
            title_match = re.search(r'"([^"]*)"', line)

            title = (
                title_match.group(1)
                if title_match
                else "CraftLang Game"
            )

            width = variables.get("ширина", 800)
            height = variables.get("высота", 600)

            GAME = GameEngine(width, height, title)
            variables["окно"] = GAME
            continue

        # Создание прямоугольника
        if line.startswith("игрок = создать прямоугольник"):
            if GAME is None:
                GAME = GameEngine()

            x = variables.get("игрок_x", 100)
            y = variables.get("игрок_y", 100)
            size = variables.get("размер", 50)
            color = variables.get("цвет", "синий")

            player = GAME.create_rectangle(x, y, size, color)

            variables["игрок"] = player
            objects["игрок"] = player
            continue

        # Управление игроком
        if line == "управление игроком":
            end = find_block_end(lines, index - 1)

            if GAME is None:
                GAME = GameEngine()

            for control_line in lines[index:end]:
                control_line = control_line.strip()

                if "=" not in control_line:
                    continue

                key, direction = control_line.split("=", 1)

                GAME.set_control(
                    key.strip(),
                    direction.strip()
                )

            index = end + 1
            continue

        # Запуск игры
        if line == "запустить игру":
            if GAME is None:
                GAME = GameEngine()

            GAME.run()
            continue

        # Вывод (ИСПРАВЛЕНО: теперь умеет склеивать строки через +)
        if line.startswith("скажи "):
            expression = line[len("скажи "):].strip()
            
            if "+" in expression:
                parts = [p.strip() for p in expression.split("+")]
                output = ""
                for part in parts:
                    if (part.startswith('"') and part.endswith('"')) or (part.startswith("'") and part.endswith("'")):
                        output += part[1:-1]
                    else:
                        val = evaluate(part, variables, objects)
                        output += str(val)
                print(output)
            else:
                val = evaluate(expression, variables, objects)
                print(val)
            continue

        # Создание переменной
        if line.startswith("пусть "):
            statement = line[len("пусть "):]

            if "=" not in statement:
                raise CraftLangError(
                    "После переменной нужно написать ="
                )

            name, expression = statement.split("=", 1)
            name = name.strip()

            if not name.isidentifier():
                raise CraftLangError(
                    f"Неправильное имя переменной: {name}"
                )

            variables[name] = evaluate(
                expression,
                variables,
                objects
            )
            continue

        # Изменение переменной или свойства
        if line.startswith("изменить "):
            statement = line[len("изменить "):]

            if "=" not in statement:
                raise CraftLangError(
                    "После изменения нужно написать ="
                )

            target, expression = statement.split("=", 1)
            target = target.strip()

            value = evaluate(
                expression,
                variables,
                objects
            )

            if "." in target:
                object_name, property_name = target.split(".", 1)

                if object_name not in objects:
                    raise CraftLangError(
                        f"Объект не найден: {object_name}"
                    )

                objects[object_name][property_name] = value

            elif target in variables:
                variables[target] = value

            else:
                raise CraftLangError(
                    f"Переменная не найдена: {target}"
                )

            continue

        # Создание объекта
        if line.startswith("создать объект "):
            name = line[len("создать объект "):].strip()
            end = find_block_end(lines, index - 1)

            obj = {}

            for property_line in lines[index:end]:
                property_line = property_line.strip()

                if (
                    not property_line
                    or property_line.startswith("#")
                ):
                    continue

                if "=" not in property_line:
                    raise CraftLangError(
                        f"Неправильное свойство: {property_line}"
                    )

                property_name, expression = property_line.split(
                    "=",
                    1
                )

                obj[property_name.strip()] = evaluate(
                    expression,
                    variables,
                    objects
                )

            objects[name] = obj
            index = end + 1
            continue

        # Условие
        if line.startswith("если ") and line.endswith(" тогда"):
            condition = line[len("если "):-len(" тогда")]
            end = find_block_end(lines, index - 1)

            if evaluate(condition, variables, objects):
                execute_block(
                    lines[index:end],
                    variables,
                    objects,
                    functions,
                    depth
                )

            index = end + 1
            continue

        # Повтор
        if line.startswith("повтор ") and line.endswith(" раз"):
            count_expression = line[len("повтор "):-len(" раз")]

            count = evaluate(
                count_expression,
                variables,
                objects
            )

            end = find_block_end(lines, index - 1)

            for _ in range(int(count)):
                execute_block(
                    lines[index:end],
                    variables,
                    objects,
                    functions,
                    depth
                )

            index = end + 1
            continue

        # Пока
        if line.startswith("пока ") and line.endswith(" тогда"):
            condition = line[len("пока "):-len(" тогда")]
            end = find_block_end(lines, index - 1)

            while evaluate(condition, variables, objects):
                execute_block(
                    lines[index:end],
                    variables,
                    objects,
                    functions,
                    depth
                )

            index = end + 1
            continue

        # Вызов функции
        if line.startswith("вызвать "):
            name = line[len("вызвать "):].strip()

            if name not in functions:
                raise CraftLangError(
                    f"Функция не найдена: {name}"
                )

            execute_block(
                functions[name],
                variables,
                objects,
                functions,
                depth + 1
            )
            continue

        # Обычное присваивание
        if "=" in line:
            name, expression = line.split("=", 1)

            name = name.strip()
            expression = expression.strip()

            if name.isidentifier():
                variables[name] = evaluate(
                    expression,
                    variables,
                    objects
                )
                continue

        raise CraftLangError(
            f"Неизвестная команда в строке {index}: {line}"
        )

# =========================================================
# Типы проектов и сборка
# =========================================================

PROJECT_TYPES = {
    "cl",
    "сайт",
    "игра",
    "приложение",
    "cmd"
}

CODE_BLOCKS = {
    "html",
    "css",
    "js",
    "lua",
    "py",
    "python"
}


def parse_project(source):
    lines = source.splitlines()

    project_type = None

    if lines and lines[0].strip().lower() in PROJECT_TYPES:
        project_type = lines[0].strip().lower()
        lines = lines[1:]

    sections = {
        "html": [],
        "css": [],
        "js": [],
        "lua": [],
        "py": []
    }

    program_lines = []
    index = 0

    while index < len(lines):
        line = lines[index].strip()

        if line in CODE_BLOCKS:
            block_name = "py" if line == "python" else line
            index += 1
            block = []

            while (
                index < len(lines)
                and lines[index].strip() != "end"
            ):
                block.append(lines[index])
                index += 1

            if index >= len(lines):
                raise CraftLangError(
                    f"Не найден end для блока {block_name}"
                )

            sections[block_name].extend(block)
            index += 1
            continue

        program_lines.append(lines[index])
        index += 1

    return project_type, sections, program_lines


# =========================================================
# Запуск встроенных Python и Lua
# =========================================================

def run_embedded_scripts(sections, project_dir):
    os.makedirs(project_dir, exist_ok=True)

    python_code = "\n".join(
        sections.get("py", [])
    ).strip()

    if python_code:
        python_file = os.path.join(
            project_dir,
            "craftlang_embedded.py"
        )

        with open(
            python_file,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(python_code + "\n")

        if not getattr(sys, "frozen", False):
            python_command = [sys.executable]
        else:
            python_path = shutil.which("python")
            if python_path:
                python_command = [python_path]
            elif shutil.which("py"):
                python_command = ["py"]
            else:
                raise CraftLangError(
                    "Для Python-блока нужен установленный Python. "
                    "Сам CraftLang работает без Python, "
                    "но встроенный Python-код требует Python."
                )

        print("Запуск Python-блока...")
        result = subprocess.run(
            python_command + [python_file],
            cwd=project_dir
        )

        if result.returncode != 0:
            raise CraftLangError(
                f"Python завершился с кодом {result.returncode}"
            )

    lua_code = "\n".join(
        sections.get("lua", [])
    ).strip()

    if lua_code:
        lua_command = shutil.which("lua")

        if not lua_command:
            raise CraftLangError(
                "Lua не найден. Установи Lua и добавь lua.exe в PATH."
            )

        lua_file = os.path.join(
            project_dir,
            "craftlang_embedded.lua"
        )

        with open(
            lua_file,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(lua_code + "\n")

        print("Запуск Lua-блока...")
        result = subprocess.run(
            [lua_command, lua_file],
            cwd=project_dir
        )

        if result.returncode != 0:
            raise CraftLangError(
                f"Lua завершился с кодом {result.returncode}"
            )

# =========================================================
# Сборка проекта
# =========================================================

def build_project(filename, source, variables):
    project_type, sections, program_lines = parse_project(source)

    if project_type is None:
        raise CraftLangError(
            "В начале файла укажи тип: cl, сайт, игра, приложение или cmd"
        )

    project_dir = os.path.dirname(
        os.path.abspath(filename)
    )
    dist_dir = os.path.join(
        project_dir,
        "dist"
    )
    os.makedirs(dist_dir, exist_ok=True)

    # Сборка CMD
    if project_type == "cmd":
        commands = [
            "@echo off",
            "chcp 65001 >nul",
            "title CraftLang CMD Script",
            "rem --- Скрипт сгенерирован CraftLang ---"
        ]

        CMD_COMMANDS = {
            "создать_папку": "mkdir",
            "удалить_файл": "del /f /q",
            "копировать_файл": "copy /y",
            "перейти_в_папку": "cd /d",
            "удалить_папку": "rmdir /s /q",
            "очистить": "cls",
            "пауза": "pause",
            "список_файлов": "dir"
        }

        # 1. Переменные
        for var_name, var_value in variables.items():
            safe_name = var_name.replace("-", "_").replace(" ", "_")
            if isinstance(var_value, (str, int, float)):
                commands.append(f'set "{safe_name}={var_value}"')

        commands.append("")

        # 2. Основной код (ИСПРАВЛЕНО: логика вывода для .cmd)
        for line in program_lines:
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                continue

            if stripped.startswith("скажи "):
                payload = stripped[len("скажи "):].strip()
                
                if "+" in payload:
                    parts = [p.strip() for p in payload.split("+")]
                    cmd_line = "echo "
                    for part in parts:
                        if (part.startswith('"') and part.endswith('"')) or (part.startswith("'") and part.endswith("'")):
                            cmd_line += part[1:-1]
                        elif part in variables:
                            safe_name = part.replace("-", "_").replace(" ", "_")
                            cmd_line += f"%{safe_name}%"
                        else:
                            cmd_line += part
                    commands.append(cmd_line)
                
                elif (payload.startswith('"') and payload.endswith('"')) or (payload.startswith("'") and payload.endswith("'")):
                    commands.append(f'echo {payload[1:-1]}')
                
                elif payload in variables:
                    safe_name = payload.replace("-", "_").replace(" ", "_")
                    commands.append(f'echo %{safe_name}%')
                
                else:
                    commands.append(f'echo {payload}')

            elif stripped.startswith("пусть "):
                statement = stripped[len("пусть "):]
                if "=" in statement:
                    name, val = statement.split("=", 1)
                    safe_name = name.strip().replace("-", "_").replace(" ", "_")
                    val = val.strip()
                    if val.startswith('"') and val.endswith('"'):
                        val = val[1:-1]
                    commands.append(f'set "{safe_name}={val}"')

            elif stripped in CMD_COMMANDS:
                commands.append(CMD_COMMANDS[stripped])

            else:
                recognized = False
                for craft_cmd, cmd_cmd in CMD_COMMANDS.items():
                    if stripped.startswith(craft_cmd + " "):
                        args = stripped[len(craft_cmd):].strip()
                        if args.startswith('"') and args.endswith('"'):
                            args = args[1:-1]
                        commands.append(f'{cmd_cmd} {args}')
                        recognized = True
                        break
                
                if not recognized:
                    commands.append(f'echo [Ошибка CraftLang/CMD] Неизвестная команда: {stripped}')

        has_pause = any(line.strip().lower() == "пауза" for line in program_lines)
        if not has_pause:
            commands.append("pause")

        output = os.path.join(dist_dir, "Программа.cmd")
        with open(output, "w", encoding="utf-8", newline="\r\n") as file:
            file.write("\r\n".join(commands) + "\r\n")

        print(f"CMD-файл собран: {output}")
        return

    # Сборка сайта
    if project_type == "сайт":
        html = "\n".join(sections["html"]).strip()
        css = "\n".join(sections["css"]).strip()
        js = "\n".join(sections["js"]).strip()
        py_code = "\n".join(sections["py"]).strip()
        lua_code = "\n".join(sections["lua"]).strip()

        if not html:
            html = "<h1>Мой сайт CraftLang</h1>"

        page = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Сайт CraftLang</title>
<style>
{css}
</style>
</head>
<body>
{html}
<script>
{js}
</script>
</body>
</html>
"""

        output = os.path.join(dist_dir, "index.html")
        with open(output, "w", encoding="utf-8") as file:
            file.write(page)

        scripts_dir = os.path.join(dist_dir, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)

        if py_code:
            with open(os.path.join(scripts_dir, "main.py"), "w", encoding="utf-8") as file:
                file.write(py_code)
        if lua_code:
            with open(os.path.join(scripts_dir, "main.lua"), "w", encoding="utf-8") as file:
                file.write(lua_code)

        print(f"Сайт собран: {output}")
        return

    # Сборка EXE
    cleaned_source = "\n".join(program_lines) + "\n"
    exe_name = os.path.splitext(os.path.basename(filename))[0]

    with tempfile.TemporaryDirectory() as temp_dir:
        cl_path = os.path.join(temp_dir, "project.cl")
        with open(cl_path, "w", encoding="utf-8") as file:
            file.write(cleaned_source)

        runtime_path = os.path.join(temp_dir, "craftlang.py")
        shutil.copy2(os.path.abspath(__file__), runtime_path)

        runner_path = os.path.join(temp_dir, "runner.py")
        runner_code = """
import os
import sys
from craftlang import run_file

if getattr(sys, "frozen", False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

run_file(os.path.join(base_dir, "project.cl"))
"""
        with open(runner_path, "w", encoding="utf-8") as file:
            file.write(runner_code)

        build_dir = os.path.join(project_dir, "build")
        os.makedirs(build_dir, exist_ok=True)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--onefile",
                "--console",
                "--clean",
                "--noconfirm",
                "--name",
                exe_name,
                "--distpath",
                dist_dir,
                "--workpath",
                build_dir,
                "--specpath",
                temp_dir,
                "--paths",
                temp_dir,
                "--add-data",
                f"{cl_path};.",
                runner_path
            ],
            cwd=temp_dir
        )

        if result.returncode != 0:
            raise CraftLangError("PyInstaller не смог создать EXE")

    exe_output = os.path.join(dist_dir, exe_name + ".exe")
    print(f"EXE создан: {exe_output}")


# =========================================================
# Запуск CraftLang
# =========================================================

def run_file(filename):
    global GAME

    try:
        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as file:
            source = file.read()

    except FileNotFoundError:
        print(f"Файл не найден: {filename}")
        return

    try:
        project_type, sections, lines = parse_project(source)

        variables = {}
        objects = {}
        functions = find_functions(lines)

        main_lines = []
        index = 0
        while index < len(lines):
            line = lines[index].strip()
            if line.startswith("функция "):
                end = find_block_end(lines, index)
                index = end + 1
            else:
                main_lines.append(lines[index])
                index += 1

        GAME = None

        execute_block(
            main_lines,
            variables,
            objects,
            functions
        )

        project_dir = os.path.dirname(
            os.path.abspath(filename)
        )

        run_embedded_scripts(
            sections,
            project_dir
        )

    except CraftLangError as error:
        print(f"Ошибка CraftLang: {error}")

    except Exception as error:
        print(f"Ошибка выполнения: {error}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("CraftLang")
        print("Запуск: py craftlang.py hello.cl")
        print("Сборка: py craftlang.py hello.cl --build")

    else:
        filename = sys.argv[1]

        if (
            len(sys.argv) >= 3
            and sys.argv[2] == "--build"
        ):
            try:
                with open(
                    filename,
                    "r",
                    encoding="utf-8"
                ) as file:
                    source = file.read()

                project_type, sections, lines = parse_project(source)
                
                variables = {}
                objects = {}
                functions = find_functions(lines)

                main_lines = []
                index = 0
                while index < len(lines):
                    line = lines[index].strip()
                    if line.startswith("функция "):
                        end = find_block_end(lines, index)
                        index = end + 1
                    else:
                        main_lines.append(lines[index])
                        index += 1

                execute_block(
                    main_lines,
                    variables,
                    objects,
                    functions
                )

                build_project(filename, source, variables)

            except FileNotFoundError:
                print(f"Файл не найден: {filename}")

            except CraftLangError as error:
                print(f"Ошибка сборки CraftLang: {error}")

            except Exception as error:
                print(f"Ошибка сборки: {error}")

        else:
            run_file(filename)