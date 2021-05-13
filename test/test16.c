struct Employee {
    int Id;
};

// return type of the function is structure
void set(struct Employee *E, int val)
{
    // Assigning the values to elements
    E->Id = val;
  
    // returning structure
    //return (E);
}
  
// Driver code
int main()
{
    // creating object of Employee
    struct Employee Emp;
  
    set(&Emp, 32);
    // display the output
    printi(Emp.Id);
    printnl();

    return 0;
}