// Test file to verify button functions
console.log('Testing button functions...');

// Test if functions exist
console.log('showAllSymbols function:', typeof showAllSymbols);
console.log('showPopularSymbols function:', typeof showPopularSymbols);
console.log('addCustomSymbol function:', typeof addCustomSymbol);

// Test global variables
console.log('allAvailableSymbols:', allAvailableSymbols);
console.log('availableSymbols:', availableSymbols);

// Test the functions directly
if (typeof showAllSymbols === 'function') {
    console.log('Testing showAllSymbols...');
    showAllSymbols();
}

if (typeof showPopularSymbols === 'function') {
    console.log('Testing showPopularSymbols...');
    showPopularSymbols();
}

if (typeof addCustomSymbol === 'function') {
    console.log('Testing addCustomSymbol...');
    // Don't actually call this as it uses prompt()
    console.log('addCustomSymbol function exists');
}
