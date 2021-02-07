#include <stdio.h> 
#include <stdlib.h> 

int main() 
{ 
	FILE *file_p = fopen("abc.txt", "a"); 
	if (file_p == NULL) 
	{ 
		exit(0); 
	} 
	else
	{ 
		fputs("Entry in file", fp);  
		fclose(fp); 
	} 
	return 0; 
}
