// src/navigation/AppNavigator.js
import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {createStackNavigator} from '@react-navigation/stack';

// Import các màn hình Auth
import Login from '../screens/Auth/Login';
// Import bộ Tab vừa làm
import EmployerTabs from './EmployerTabs';
import { Provider } from 'react-native-paper';
import CandidateRegister from '../screens/Auth/CandidateRegister';
import EmployerRegister from '../screens/Auth/EmployerRegister';
import CandidateTabs from './CandidateTabs';
import {Provider} from 'react-native-paper';

const Stack = createStackNavigator();

export default function AppNavigator() {
    const isAuthenticated = true; // Giả lập đã đăng nhập
    const userRole = 'Employer'; // Giả lập role

    return (
        <Provider>
            <NavigationContainer>
                <Stack.Navigator screenOptions={{ headerShown: false }}>
                    {/* Logic điều hướng: Nếu chưa đăng nhập -> Login, Ngược lại vào Main */}
                    <Stack.Screen name="Login" component={Login} />
                    <Stack.Screen name="CandidateRegister" component={CandidateRegister} />
                    <Stack.Screen name="EmployerRegister" component={EmployerRegister} />
                    {/* Ví dụ đơn giản: Mặc định vào thẳng CandidateTabs để bạn test giao diện */}
                    <Stack.Screen name="EmployerMain" component={EmployerTabs} />
                    <Stack.Screen name="CandidateMain" component={CandidateTabs} />
                    {/* Sau này sẽ là:
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="RecruiterMain" component={RecruiterTabs} />
        */}
                </Stack.Navigator>
            </NavigationContainer>
        </Provider>
    );
}