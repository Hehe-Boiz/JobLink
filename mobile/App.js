// App.js
import React, { useReducer } from 'react';
import { Provider as PaperProvider, MD3LightTheme as DefaultTheme } from 'react-native-paper';
import AppNavigator from './src/navigation/AppNavigator'; // File điều hướng chính
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { MyUserContext } from './src/utils/contexts/MyContext';
import MyUserReducer from './src/utils/reducers/MyUserReducer';

// Định nghĩa Theme màu chủ đạo (ví dụ màu Xanh dương cho Job Portal)
const theme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: '#105be6ff', // Màu chính
    secondary: '#7d786cff',
    error: '#dc3545',
  },
};

export default function App() {
  const [user, dispatch] = useReducer(MyUserReducer, null);
  return (
    <SafeAreaProvider>
      <MyUserContext.Provider value={[user, dispatch]}>
        <PaperProvider theme={theme}>
          <AppNavigator />
        </PaperProvider>
      </MyUserContext.Provider>
    </SafeAreaProvider>
  );
}
