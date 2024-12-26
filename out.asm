section .data
__compilestring0__: db "abc", 0
section .text
global _start
_start:
mov rax, 1
mov rdi, 0
mov rsi, __compilestring0__
mov rdx, 3
syscall
mov rax, 1
mov rdi, 0
mov rsi, __compilestring0__
mov rdx, 3
syscall
mov rax, 60
mov rdi, 0
syscall