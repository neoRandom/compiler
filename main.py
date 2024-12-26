import pprint
import sys
import os


COMMAND_LIST = [
    "print"
]


class Command:
    def __init__(self, raw_code: str, output_file: str):
        self.code_tokens = self.parse_code(raw_code)
        self.out_tokens = []

        self.generate_data()
        # self.generate_bss()
        self.generate_text()

        self.write_code(output_file)

    def parse_code(self, raw_code: str):
        out_tokens = {
            "bss": {},
            "data": {},
            "text": {}
        }

        # Remove duplicated spaces
        raw_code = " ".join([token for token in raw_code.split(" ") if token != ""])

        # Find strings
        i = 0
        while i < len(raw_code):
            if raw_code[i] == '"':
                string_size = 0

                # Get the size
                for j in range(i + 1, len(raw_code)):
                    # Verify if it's a quote and not a escape character
                    if raw_code[j] == '"' and raw_code[j-1] != "\\":
                        break
                    string_size += 1

                string_content = raw_code[i + 1 : i + string_size + 1]

                # Is there any string equal to this one
                is_repeated = False
                for string_attributes in out_tokens["data"].values():
                    if string_attributes["content"] == string_content:
                        is_repeated = True
                        break
                
                if is_repeated:
                    i += string_size + 2
                    continue

                # Add to the collection
                out_tokens["data"][f"__compilestring{len(out_tokens["data"])}__"] = {
                    "content": string_content,
                    "size": string_size,
                    "index": i
                }
                
                i += string_size + 1
            
            i += 1

        # Replace strings
        for string_name, string_attributes in out_tokens["data"].items():
            raw_code = raw_code.replace(f"\"{string_attributes["content"]}\"", string_name)
        
        # Add calling functions
        i = 0
        while i < len(raw_code):
            
            if raw_code[i] != " ":
                token_size = 1

                # Get the size
                for j in range(i + 1, len(raw_code)):
                    token_size += 1
                    if raw_code[j] == ")":
                        break
                    if raw_code[j] == " " and raw_code[j-1] != ",":
                        token_size -= 1
                        break

                token_content = raw_code[i:i+token_size]

                # Test if it is a function being called
                try:
                    count_open_parenthesis = token_content.count("(")
                    count_close_parenthesis = token_content.count(")")

                    if count_close_parenthesis == 0 or count_open_parenthesis == 0 or count_open_parenthesis != count_close_parenthesis:
                        raise RuntimeWarning

                    command_value, argument_value = token_content.replace(")", "").split("(")

                    if command_value not in COMMAND_LIST:
                        raise RuntimeWarning
                    
                    argument_list = argument_value.replace(", ", " ").replace(",", " ").split(" ")

                    out_tokens["text"][f"__callingfunction{len(out_tokens["text"])}__"] = {
                        "content": token_content,
                        "command": command_value,
                        "arguments": argument_list,
                        "size": token_size,
                        "index": i
                    }

                    i += token_size
                except RuntimeWarning:
                    raw_code = raw_code.replace(token_content, "")
                    continue

            i += 1
        
        # Replace calling functions
        for calling_function_name, calling_function_attributes in out_tokens["text"].items():
            raw_code = raw_code.replace(calling_function_attributes["content"], calling_function_name, count=1)

        pprint.pprint(out_tokens)

        print(raw_code)
        
        return out_tokens
    
    def generate_data(self):
        tokens = [
            ["section", ".data"]
        ]

        for string_name, string_attributes in self.code_tokens["data"].items():
            tokens.append(
                [f"{string_name}:", "db", f"\"{string_attributes["content"]}\", 0"]
            )

        for token in tokens:
            self.out_tokens.append(token)

    def generate_bss(self):
        ...
    
    def generate_text(self):
        tokens = [
            ["section", ".text"],
            ["global", "_start"],
            ["_start:"]
        ]

        for calling_function in self.code_tokens["text"].values():
            if calling_function["command"] == "print":
                string = self.code_tokens["data"][calling_function["arguments"][0]]
                file_descriptor = "0"
                content = calling_function["arguments"][0]
                size = string["size"]

                for token in self.text_write(file_descriptor, content, size):
                    tokens.append(token)
        
        for token in self.text_exit(0):
            tokens.append(token)

        for token in tokens:
            self.out_tokens.append(token)

    def text_init(self):
        return 
    
    def text_write(self, file_descriptor, content, size):
        return [
            ["mov", "rax,", "1"],
            ["mov", "rdi,", str(file_descriptor)],
            ["mov", "rsi,", str(content)],
            ["mov", "rdx,", str(size)],
            ["syscall"]
        ]

    def text_exit(self, exit_code):
        return [
            ["mov", "rax,", "60"],
            ["mov", "rdi,", str(exit_code)],
            ["syscall"]
        ]

    def write_code(self, output_file: str):
        out_code = "\n".join([" ".join(line) for line in self.out_tokens])

        with open(output_file, "w") as file:
            file.write(out_code)
        
        os.system(f"nasm {output_file} -o main.o -f elf64")
        os.system(f"ld main.o -o main.out")


def run():
    if len(sys.argv) < 2:
        print("Error: missing required argument (file path)")
        return
    
    filepath = sys.argv[1]
    content = ""

    with open(filepath, "r") as file:
        content = file.read()

    cmd = Command(content, "out.asm")


if __name__ == "__main__":
    run()
