// App.js
import React from 'react';
import { Provider as PaperProvider, MD3LightTheme as DefaultTheme } from 'react-native-paper';
import AppNavigator from './navigation/AppNavigator'; // File điều hướng chính

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
  return (
    <PaperProvider theme={theme}>
      <AppNavigator />
    </PaperProvider>
  );
}
