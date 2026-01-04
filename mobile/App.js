import React, {useEffect} from 'react';
import {Provider as PaperProvider, MD3LightTheme as DefaultTheme} from 'react-native-paper';
import {useFonts} from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';
import AppNavigator from './src/navigation/AppNavigator';
import CandidateHome from "./src/screens/Candidate/CandidateHome";

SplashScreen.preventAutoHideAsync();

const theme = {
    ...DefaultTheme,
    colors: {
        ...DefaultTheme.colors,
        primary: '#105be6ff',
        secondary: '#7d786cff',
        error: '#dc3545',
    },
};

export default function App() {
    const [fontsLoaded] = useFonts({
        // Regular weights (non-italic)
        'DMSans-Thin': require('./assets/fonts/DM_Sans/static/DMSans-Thin.ttf'),
        'DMSans-ExtraLight': require('./assets/fonts/DM_Sans/static/DMSans-ExtraLight.ttf'),
        'DMSans-Light': require('./assets/fonts/DM_Sans/static/DMSans-Light.ttf'),
        'DMSans-Regular': require('./assets/fonts/DM_Sans/static/DMSans-Regular.ttf'),
        'DMSans-Medium': require('./assets/fonts/DM_Sans/static/DMSans-Medium.ttf'),
        'DMSans-SemiBold': require('./assets/fonts/DM_Sans/static/DMSans-SemiBold.ttf'),
        'DMSans-Bold': require('./assets/fonts/DM_Sans/static/DMSans-Bold.ttf'),
        'DMSans-ExtraBold': require('./assets/fonts/DM_Sans/static/DMSans-ExtraBold.ttf'),
        'DMSans-Black': require('./assets/fonts/DM_Sans/static/DMSans-Black.ttf'),

        // Italic weights (optional - uncomment if you use italic)
        'DMSans-ThinItalic': require('./assets/fonts/DM_Sans/static/DMSans-ThinItalic.ttf'),
        'DMSans-ExtraLightItalic': require('./assets/fonts/DM_Sans/static/DMSans-ExtraLightItalic.ttf'),
        'DMSans-LightItalic': require('./assets/fonts/DM_Sans/static/DMSans-LightItalic.ttf'),
        'DMSans-Italic': require('./assets/fonts/DM_Sans/static/DMSans-Italic.ttf'),
        'DMSans-MediumItalic': require('./assets/fonts/DM_Sans/static/DMSans-MediumItalic.ttf'),
        'DMSans-SemiBoldItalic': require('./assets/fonts/DM_Sans/static/DMSans-SemiBoldItalic.ttf'),
        'DMSans-BoldItalic': require('./assets/fonts/DM_Sans/static/DMSans-BoldItalic.ttf'),
        'DMSans-ExtraBoldItalic': require('./assets/fonts/DM_Sans/static/DMSans-ExtraBoldItalic.ttf'),
        'DMSans-BlackItalic': require('./assets/fonts/DM_Sans/static/DMSans-BlackItalic.ttf'),
    });

    useEffect(() => {
        if (fontsLoaded) {
            SplashScreen.hideAsync();
        }
    }, [fontsLoaded]);

    if (!fontsLoaded) {
        return null;
    }

    return (
        <PaperProvider theme={theme}>
            <CandidateHome/>

        </PaperProvider>
    );
}
