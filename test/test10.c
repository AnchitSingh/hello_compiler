// C program for implementation of Bubble sort

void swap(int *xp, int *yp)
{
    int temp = *xp;
    *xp = *yp;
    *yp = temp;
}

// A function to implement bubble sort
void bubbleSort(int arr[], int n)
{
    int i, j;
    for (i = 0; i < n - 1; i++)
        // Last i elements are already in place
        for (j = 0; j < n - i - 1; j++)
            if (arr[j] > arr[j + 1])
                swap(&arr[j], &arr[j + 1]);
}

/* Function to print an array */
void printArray(int arr[], int size)
{
    int i;
    for (i = 0; i < size; i++){
        printi(arr[i]);
        printc(' ');
    }
    printnl();
}

// Driver program to test above functions
int main()
{
    int arr[7];
    int i;
    for(i = 0; i < 7; i++)
        scani(arr[i]);
    bubbleSort(arr, 7);
    printArray(arr, 7);
    return 0;
}