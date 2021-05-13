void print(int exp, int val){
    printc('E');
    printc('v');
    printc('a');
    printc('l');
    printc(':');
    printc(' ');
    printi(exp);
    printc('V');
    printc('a');
    printc('l');
    printc(':');
    printc(' ');
    printi(val);
    printnl();
}

int main()
{
    // Short circuiting
    // logical "||"(OR)
    int a = 1, b = 1, c = 1;
  
    // a and b are equal
    if (a == b || c++) {
        print(1, c);
    }
    else {
        print(2, c);
    }
  
    // Short circuiting
    // logical "&&"(OR)
    if (a == b && c++) {
        print(2, c);
    }
    else {
        print(1, c);
    }
    return 0;
}