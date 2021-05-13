int f = 4;

struct t {
    int a;
};

// redefinition delete this
struct t {
    char ch;
};

// recursive struct
struct s {
    int b;
    struct s c;
};

void too();

// these are dummy
void bar(int a);

int bar(int a){ return 0;}

void foo(int a, char b){}

void foo(int a, char b); // decl after definition

int main(){
    int e = 5, g, h = 'c';
    int e;
    void d;
    char ch1 = 'a';
    struct t u;
    int arr[5];
    int *ptr;
    
    // struct not there
    struct x y;
    
    struct t *v;
    
    // insufficient char arr length
    char str[4] = "abcde";

    // invalid assignment
    u = 5;
    e = ch1;
    ch1 = e;
    y = v;
    
    u = arr;
    // arr index not integer
    arr[u];
    a[4] = 4;

    
    v++; // b not int
    (*v).z = 4; // b not member of struct
    (*v)->a = 4; // b not struct pointer
    *e = 4; // a not pointer
    
    e(43); // a not a function

    // function call
    foo(a); // insufficient args
    foo(a, arr); // invalid args
    
    too(); // func not defined;

    -(*v); // b is struct
    -ptr; // u is pointer

    e % ch1; // a is int, ch is char
    (*v) % e; // b is struct, a is int

    v + ch1; // can't add char to pointer
    u + e; // correct, adding int to pointer

    e + g; // binary operators strict type checking

    // break continue out of control structures
    break;

    if(1){continue;}
    
    switch(a){
        case 0: ;
        case 1: break;
        case 0: ;
        default: ;
    }

    return;
}
