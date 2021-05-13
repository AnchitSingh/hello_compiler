int main() {
    int i = 10;

    if (i == 10)
    {
        // First if statement
        if (i < 15){
           prints("i is smaller than 15", 20);
           printnl();
 
			// Nested - if statement
			// Will only be executed if statement above
			// is true
			if (i < 12){
				prints("i is smaller than 12 too", 24);
                printnl();
            }
		}
        else{
            prints("i is greater than 15", 20);
            printnl();
        }
    }
    return 0;
}