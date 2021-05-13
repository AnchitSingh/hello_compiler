void print(int i)
{
   printi(i);
   printc(',');
   printc(' ');
}

int main()
{
   int t1 = 0, t2 = 1, nextTerm = 0, n;
   scani(n);

   // displays the first two terms which is always 0 and 1
   print(t1);
   print(t2);
   nextTerm = t1 + t2;

   while (nextTerm <= n)
   {
      print(nextTerm);
      t1 = t2;
      t2 = nextTerm;
      nextTerm = t1 + t2;
   }
   printnl();

   return 0;
}