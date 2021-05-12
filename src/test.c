void swap(int* a, int* b)
{
    int t;
    t = *a;
    *a = *b;
    *b = t;
}

int partition (int arr[], int low, int high)
{
    int pivot, i, j;
    pivot = arr[high]; 
    i = (low - 1); 
 
    for (j = low; j <= high - 1; j++)
    {
        if (arr[j] < pivot)
        {
            i++; 
            swap(&arr[i], &arr[j]);
        }
    }
    swap(&arr[i + 1], &arr[high]);
    return (i + 1);
}
 
void quickSort(int arr[], int low, int high)
{
    int pi;
    if (low < high)
    {
        pi = partition(arr, low, high);
        quickSort(arr, low, pi - 1);
        quickSort(arr, pi + 1, high);
    }
}
 
void printArray(int arr[], int size)
{
    int i;
    for (i = 0; i < size; i++){
        printi(arr[i]);
        printc(' ');
    }
    printnl();
}

int main()
{
    int i;
    int arr[6];
    for(i = 0; i < 6; i++){
        scani(arr[i]);
    }
    quickSort(arr, 0, 5);
    printArray(arr, 6);
    return 0;
}