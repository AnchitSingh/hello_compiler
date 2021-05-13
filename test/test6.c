int ack(int m, int n)
{
    if (m == 0)
    {
        return n + 1;
    }
    if ((m > 0) && (n == 0))
    {
        return ack(m - 1, 1);
    }
    if ((m > 0) && (n > 0))
    {
        return ack(m - 1, ack(m, n - 1));
    }
}

int main()
{
    int A;
    A = ack(2, 2);
    printi(A);
    printnl();
    return 0;
}