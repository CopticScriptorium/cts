(function () {

    const KEYBOARDS = [
        
        { id: 'cop', name: 'Keyboard_coptic_greek', label: 'Coptic' },
        { id: 'cop-copt', name: 'Keyboard_coptic_qwerty', label: 'Coptic Qwerty' },
        // Add more keyboards here in the same format
    ];
    var virtualKeyboardEnabled = localStorage.getItem('virtualKeyboardEnabled') === 'true';
    console.log('virtualKeyboardEnabled', virtualKeyboardEnabled);
    var storedKeyboard = localStorage.getItem('preferredKeyboard') || KEYBOARDS[0].id;
    localStorage.setItem('preferredKeyboard', storedKeyboard);

    console.log('storedKeyboard', storedKeyboard);
    // Create a named handler function that we can reference for both adding and removing
    function showOSKHandler(event) {
        console.log('Focus event triggered');
        if (!keyman.osk.isVisible()) {
            console.log('OSK not visible, showing it');
            keyman.osk.show(true);  // Force show
        }
    }

    function attachKeyboardToInput(input) {
        console.log('Attaching keyboard to input');
        if (!input._keymanAttached) {  // Prevent double attachment
            keyman.attachToControl(input);
            keyman.enableControl(input);
            input.addEventListener('focus', showOSKHandler);
            input._keymanAttached = true;
        }
    }

    function detachKeyboardFromInput(input) {
        console.log('Detaching keyboard from input');
        if (input._keymanAttached) {
            input.removeEventListener('focus', showOSKHandler);
            keyman.detachFromControl(input);
            keyman.disableControl(input);
            input._keymanAttached = false;
        }
    }

    function getKeyboardById(keyboardId) {
        return  KEYBOARDS.find(k => k.id === keyboardId);
        }    
    // Function to set active keyboard and update UI
    function setActiveKeyboard(keyboardId) {
        const keyboard = getKeyboardById(keyboardId);
        keyman.setActiveKeyboard(keyboard.name, keyboard.id);
        document.getElementById('current-language').textContent = keyboard.label;
    }

    // Update keyboard toggle handler
    function toggleLanguage() {
        console.log('Toggling language');
        const currentLang = document.getElementById('current-language').textContent;
        const currentIndex = KEYBOARDS.findIndex(k => k.label === currentLang);
        const nextIndex = (currentIndex + 1) % KEYBOARDS.length;
        setActiveKeyboard(KEYBOARDS[nextIndex].id);
        localStorage.setItem('preferredKeyboard', KEYBOARDS[nextIndex].id);
    }

    // Update save preferences function
    function savePreferences() {
        virtualKeyboardEnabled = document.getElementById('virtual-keyboard-toggle').checked;
        const fuzzySearchEnabled = document.getElementById('fuzzy-search-toggle').checked;
        localStorage.setItem('virtualKeyboardEnabled', virtualKeyboardEnabled);
        localStorage.setItem('fuzzySearchEnabled', fuzzySearchEnabled);
        applyPreferences();
        document.getElementById('preferences-modal').style.display = 'none';
    }

    async function initKeyman(virtualKeyboardEnabled) {
        let init;

        if (virtualKeyboardEnabled && !keyman.initialized) {
            console.log('Keyman Not Initialized. Initializing...');
            init = keyman.init({
                keyboardBaseUri: 'https://s.keyman.com/keyboard/',
                initialKeyboard: storedKeyboard,
                setActiveOnRegister: true,
                attachType: 'manual',
                useAlerts: false,
                osk: true,  // Ensure OSK is enabled
            }).then(function () {
                const keyboardIds = KEYBOARDS.map(keyboard => "@" + keyboard.id);
                console.log('Adding keyboards:', keyboardIds);
                return keyman.addKeyboards(keyboardIds);
            }).then(function () {
                console.log('Keyman initialized and keyboards added');
                document.getElementById('current-language').textContent = getKeyboardById(storedKeyboard).label;
                // Ensure OSK is ready
                keyman.osk.ready = true;
            }).catch(function (error) {
                console.error('Error initializing Keyman:', error);
            });
        } else {
            init = Promise.resolve(true);
        }
        return init;
    }

    async function applyPreferences() {

        const virtualKeyboardEnabled = localStorage.getItem('virtualKeyboardEnabled') === 'true';

        await initKeyman(virtualKeyboardEnabled);

        const searchInputs = document.querySelectorAll('input[type="text"][name="text"]');
        const languageSelector = document.getElementById('language-selector');
        const lastKeyboard = localStorage.getItem('preferredKeyboard') || KEYBOARDS[0].id;

        // Apply preferences
        if (virtualKeyboardEnabled) {
            languageSelector.style.display = 'flex';
            searchInputs.forEach(input => {
                attachKeyboardToInput(input);
            });
            if (!keyman.osk.isVisible()) {
                keyman.osk.show();
            }
        } else {
            console.log('Hiding OSK');
            if (keyman.initialized) {
                if (keyman.osk.isVisible()) {
                    keyman.osk.hide();
                }
                languageSelector.style.display = 'none';
                searchInputs.forEach(input =>
                    detachKeyboardFromInput(input)
                );
            }
        }
    }

    function showPreferences() {
        const preferencesModal = document.getElementById('preferences-modal');
        preferencesModal.style.display = 'block';
        // Load saved preferences
        const virtualKeyboardEnabled = localStorage.getItem('virtualKeyboardEnabled') === 'true';
        const fuzzySearchEnabled = localStorage.getItem('fuzzySearchEnabled') === 'true';
        document.getElementById('virtual-keyboard-toggle').checked = virtualKeyboardEnabled;
        document.getElementById('fuzzy-search-toggle').checked = fuzzySearchEnabled;
    }


    // Initialize after document is loaded
    document.addEventListener('DOMContentLoaded', function () {

        storedKeyboard = localStorage.getItem('preferredKeyboard') || KEYBOARDS[0].id;
        console.log('storedKeyboard', storedKeyboard);
        document.getElementById('language-toggle').addEventListener('click', toggleLanguage);
        document.getElementById('preferences-button').addEventListener('click', showPreferences);
        document.getElementById('save-preferences-button').addEventListener('click', savePreferences);
        console.log('Event listeners attached');
        applyPreferences();
    });

})();