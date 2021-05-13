int hofstaderFemale(int n);
int hofstaderMale(int n);
  
// Female function
int hofstaderFemale(int n)
{
    if (n < 0){
        return 0;
    }
    else{
        return (n == 0) ? 1 : n - hofstaderMale(n - 1);
    }
}
  
// Male function
int hofstaderMale(int n)
{
    if (n < 0){
        return 0;
    }
    else{
        return (n == 0) ? 0 : n - hofstaderFemale(n - 1);
    }
}
  
// hard coded driver function to run the program
int main()
{
    int i;
    printc('F');
    printc(':');
    printc(' ');
    for (i = 0; i < 20; i++){
        printi(hofstaderFemale(i));
        printc(' ');
    }
      
    printnl();
  
    printc('M');
    printc(':');
    printc(' ');
    for (i = 0; i < 20; i++){
        printi(hofstaderMale(i));
        printc(' ');
    }
    
    printnl();

    return 0;
}