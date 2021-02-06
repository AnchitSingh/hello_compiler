#include <stdio.h>
int main()
{
     
    // entered string
    char ch[50] = "GeeksforGeeks"; 
   
    // printing entered string
    printf("Entered String is:");
   
    // returns length of string
    // along printing string
    int len
        = printf("%s\n", ch); 
   
    printf("Length is:");
   
    // printing length
    printf("%d", len - 1); 
}
