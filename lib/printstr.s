	.data
	printc_fmt:
		 .string "%c"
	printi_fmt:
		 .string "%d"
	printf_fmt:
		 .string "%f"
	printnl_fmt:
		 .string "\n"
	scanc_fmt:
		 .string "%c"
	scani_fmt:
		 .string "%d"
	.text
	.global func0
	.type func0, function
func0:
	push %ebp
	mov %esp, %ebp
	sub $28, %esp
	push %ebx
	push %ecx
	push %edx
	push %esi
	push %edi
	mov $0, %eax
	mov %eax, -8(%ebp)
	mov -8(%ebp), %eax
	mov %eax, -4(%ebp)
for_test0:
	mov -4(%ebp), %eax
	mov 12(%ebp), %ebx
	cmp %ebx, %eax
	mov $0, %ecx
	setl %cl
	mov %ecx, -12(%ebp)
	mov -12(%ebp), %eax
	cmp $0, %eax
	je for_after0
	mov $1, %eax
	mov -4(%ebp), %ebx
	imul %ebx, %eax
	mov %eax, -24(%ebp)
	mov 8(%ebp), %eax
	mov %eax, -20(%ebp)
	mov -20(%ebp), %eax
	mov -24(%ebp), %ebx
	add %ebx, %eax
	mov %eax, -28(%ebp)
	mov -28(%ebp), %esi
	movb (%esi), %al
	push %ebp
	mov %esp, %ebp
	push %eax
	push $printc_fmt
	call printf
	add $8, %esp
	mov %ebp, %esp
	pop %ebp
for_body0:
	mov -4(%ebp), %eax
	mov %eax, -16(%ebp)
	mov -4(%ebp), %eax
	inc %eax
	mov %eax, -4(%ebp)
	jmp for_test0
for_after0:
	nop
	pop %ebx
	pop %ecx
	pop %edx
	pop %esi
	pop %edi
	mov %ebp, %esp
	pop %ebp
	ret
	nop
	pop %ebx
	pop %ecx
	pop %edx
	pop %esi
	pop %edi
	mov %ebp, %esp
	pop %ebp
	ret
